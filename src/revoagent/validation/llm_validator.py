"""
LLM Response Validation Module

Provides utilities to validate responses from LLM models for:
1. Content quality and relevance
2. Code syntax correctness
3. Hallucination detection
4. Response structure validation
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
import ast
import subprocess
from enum import Enum

logger = logging.getLogger("revoagent.validation")

class ValidationType(Enum):
    """Types of validation that can be performed"""
    CODE_SYNTAX = "code_syntax"
    RELEVANCE = "relevance"
    STRUCTURE = "structure"
    HALLUCINATION = "hallucination"
    SECURITY = "security"
    ALL = "all"

class ValidationLevel(Enum):
    """Validation strictness levels"""
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"

class ValidationResult:
    """Result of a validation operation"""
    
    def __init__(self, 
                 is_valid: bool, 
                 validation_type: ValidationType,
                 score: float = 0.0,
                 issues: Optional[List[Dict[str, Any]]] = None,
                 details: Optional[Dict[str, Any]] = None):
        self.is_valid = is_valid
        self.validation_type = validation_type
        self.score = score  # 0.0-1.0 quality score
        self.issues = issues or []
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "is_valid": self.is_valid,
            "validation_type": self.validation_type.value,
            "score": self.score,
            "issues": self.issues,
            "details": self.details
        }
    
    @staticmethod
    def merge_results(results: List['ValidationResult']) -> 'ValidationResult':
        """Merge multiple validation results into one"""
        if not results:
            return ValidationResult(True, ValidationType.ALL)
        
        # Overall validity is the AND of all individual validations
        is_valid = all(r.is_valid for r in results)
        
        # Average score
        score = sum(r.score for r in results) / len(results)
        
        # Combine issues
        all_issues = []
        for r in results:
            all_issues.extend(r.issues)
        
        # Combine details
        all_details = {}
        for r in results:
            all_details[r.validation_type.value] = r.details
        
        return ValidationResult(
            is_valid=is_valid,
            validation_type=ValidationType.ALL,
            score=score,
            issues=all_issues,
            details=all_details
        )

class LLMValidator:
    """
    Validator for LLM responses
    
    Provides methods to check various aspects of LLM responses
    for quality, correctness, and appropriateness.
    """
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        self.validation_level = validation_level
    
    async def validate_response(self, 
                         response: str, 
                         prompt: Optional[str] = None,
                         validation_types: List[ValidationType] = None) -> ValidationResult:
        """
        Validate an LLM response using the specified validation types
        
        Args:
            response: The LLM response text to validate
            prompt: Optional prompt that generated the response
            validation_types: List of validation types to perform
            
        Returns:
            ValidationResult with validation details
        """
        if validation_types is None:
            validation_types = [ValidationType.CODE_SYNTAX, ValidationType.RELEVANCE]
            
        results = []
        
        for validation_type in validation_types:
            if validation_type == ValidationType.CODE_SYNTAX:
                results.append(self.validate_code_syntax(response))
            elif validation_type == ValidationType.RELEVANCE:
                results.append(self.validate_relevance(response, prompt))
            elif validation_type == ValidationType.STRUCTURE:
                results.append(self.validate_structure(response))
            elif validation_type == ValidationType.HALLUCINATION:
                results.append(self.validate_hallucinations(response))
            elif validation_type == ValidationType.SECURITY:
                results.append(self.validate_security(response))
            elif validation_type == ValidationType.ALL:
                # Validate everything except ALL to avoid recursion
                all_types = [vt for vt in ValidationType if vt != ValidationType.ALL]
                return await self.validate_response(response, prompt, all_types)
        
        return ValidationResult.merge_results(results)
    
    def validate_code_syntax(self, code: str) -> ValidationResult:
        """
        Validate Python code syntax
        
        Args:
            code: Python code to validate
            
        Returns:
            ValidationResult with syntax check details
        """
        # Extract code blocks from markdown if present
        code_blocks = self._extract_code_blocks(code)
        
        if not code_blocks:
            # No code blocks found, check if the entire response is code
            code_blocks = [code]
        
        issues = []
        total_blocks = len(code_blocks)
        valid_blocks = 0
        
        for i, block in enumerate(code_blocks):
            try:
                # Try to parse the code to check syntax
                ast.parse(block)
                valid_blocks += 1
            except SyntaxError as e:
                issues.append({
                    "block_index": i,
                    "line": e.lineno,
                    "column": e.offset,
                    "message": str(e),
                    "text": e.text
                })
            except Exception as e:
                issues.append({
                    "block_index": i,
                    "message": str(e)
                })
        
        # Calculate score based on ratio of valid blocks
        score = valid_blocks / total_blocks if total_blocks > 0 else 0.0
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            validation_type=ValidationType.CODE_SYNTAX,
            score=score,
            issues=issues,
            details={
                "total_blocks": total_blocks,
                "valid_blocks": valid_blocks
            }
        )
    
    def validate_relevance(self, 
                           response: str, 
                           prompt: Optional[str] = None) -> ValidationResult:
        """
        Validate relevance of the response to the prompt
        
        Args:
            response: Response to validate
            prompt: Original prompt for comparison
            
        Returns:
            ValidationResult with relevance details
        """
        if not prompt:
            # Can't validate relevance without a prompt
            return ValidationResult(
                is_valid=True,
                validation_type=ValidationType.RELEVANCE,
                score=1.0
            )
        
        issues = []
        
        # Basic relevance checks
        # 1. Response length check
        if len(response) < 10:
            issues.append({
                "type": "length",
                "message": "Response is too short"
            })
        
        # 2. Check if response contains any prompt keywords
        # Extract important keywords from the prompt
        keywords = self._extract_keywords(prompt)
        found_keywords = [kw for kw in keywords if kw.lower() in response.lower()]
        keyword_ratio = len(found_keywords) / len(keywords) if keywords else 1.0
        
        if keyword_ratio < 0.3:  # Less than 30% of keywords found
            issues.append({
                "type": "keywords",
                "message": "Response doesn't contain many prompt keywords",
                "details": {
                    "keywords_found": found_keywords,
                    "keywords_total": keywords
                }
            })
        
        # More sophisticated relevance scoring could be implemented here
        # For now, use a simple approach based on keyword matching
        score = max(0.3, keyword_ratio)
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            validation_type=ValidationType.RELEVANCE,
            score=score,
            issues=issues,
            details={
                "keyword_ratio": keyword_ratio,
                "prompt_length": len(prompt) if prompt else 0,
                "response_length": len(response)
            }
        )
    
    def validate_structure(self, response: str) -> ValidationResult:
        """
        Validate the structure of the response
        
        Args:
            response: Response to validate
            
        Returns:
            ValidationResult with structure validation details
        """
        issues = []
        
        # Check for JSON validity if response appears to be JSON
        if response.strip().startswith('{') and response.strip().endswith('}'):
            try:
                json.loads(response)
            except json.JSONDecodeError as e:
                issues.append({
                    "type": "json",
                    "message": f"Invalid JSON: {str(e)}"
                })
        
        # Check for markdown structure
        markdown_score = self._evaluate_markdown_quality(response)
        
        # Calculate overall structure score
        if issues:
            score = 0.5  # Penalize for structural issues
        else:
            score = markdown_score
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            validation_type=ValidationType.STRUCTURE,
            score=score,
            issues=issues,
            details={
                "markdown_score": markdown_score
            }
        )
    
    def validate_hallucinations(self, response: str) -> ValidationResult:
        """
        Basic hallucination detection
        
        Args:
            response: Response to check for hallucinations
            
        Returns:
            ValidationResult with hallucination detection details
        """
        # This is a simplified placeholder for hallucination detection
        # A more sophisticated approach would require:
        # 1. Knowledge base integration
        # 2. Fact checking
        # 3. Possibly running the response through another LLM specifically trained to detect hallucinations
        
        issues = []
        
        # Look for phrases that suggest uncertainty
        uncertainty_phrases = [
            "I think", "I believe", "probably", "might be",
            "could be", "I'm not sure", "possibly"
        ]
        
        found_phrases = [phrase for phrase in uncertainty_phrases if phrase.lower() in response.lower()]
        
        if found_phrases and len(found_phrases) > 3:
            issues.append({
                "type": "uncertainty",
                "message": "Response contains multiple phrases suggesting uncertainty",
                "details": {
                    "phrases": found_phrases
                }
            })
        
        # Check for inconsistencies within the response
        # (This would require more sophisticated NLP which is beyond the scope of this basic validator)
        
        # For simplicity, assign a score based on uncertainty phrases
        score = max(0.5, 1.0 - (len(found_phrases) / 10))
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            validation_type=ValidationType.HALLUCINATION,
            score=score,
            issues=issues,
            details={
                "uncertainty_phrases": found_phrases
            }
        )
    
    def validate_security(self, response: str) -> ValidationResult:
        """
        Check for security issues in the response
        
        Args:
            response: Response to check for security issues
            
        Returns:
            ValidationResult with security check details
        """
        issues = []
        
        # Check for potential security issues in code
        security_patterns = [
            (r"os\.system\(", "Potential command injection"),
            (r"subprocess\.(?:call|run|Popen)", "Potential command injection"),
            (r"eval\(", "Potential code injection"),
            (r"exec\(", "Potential code injection"),
            (r"(?:password|secret|token|key)\s*=\s*['\"][^'\"]+['\"]", "Hardcoded credential"),
            (r"SELECT\s+.*\s+FROM\s+.*\s+WHERE.*=\s*'\s*\+", "Potential SQL injection"),
            (r"<script>", "Potential XSS")
        ]
        
        for pattern, issue_type in security_patterns:
            matches = re.finditer(pattern, response, re.IGNORECASE)
            for match in matches:
                issues.append({
                    "type": "security",
                    "subtype": issue_type,
                    "message": f"Potential security issue: {issue_type}",
                    "position": match.start()
                })
        
        # Calculate score based on issues found
        # More critical issues could be weighted more heavily
        score = 1.0 if not issues else max(0.1, 1.0 - (len(issues) * 0.2))
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            validation_type=ValidationType.SECURITY,
            score=score,
            issues=issues,
            details={
                "total_issues": len(issues)
            }
        )
    
    # Helper methods
    def _extract_code_blocks(self, text: str) -> List[str]:
        """Extract code blocks from markdown text"""
        code_blocks = []
        
        # Match both ```python and ``` code blocks
        pattern = r"```(?:python)?\s*(.*?)```"
        matches = re.finditer(pattern, text, re.DOTALL)
        
        for match in matches:
            code_blocks.append(match.group(1).strip())
        
        return code_blocks
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        # This is a simplified keyword extraction
        # A more sophisticated approach would use NLP techniques
        
        if not text:
            return []
        
        # Remove common words and keep only significant ones
        stop_words = {"a", "an", "the", "and", "or", "but", "if", "then", "else", "when",
                     "at", "from", "by", "for", "with", "about", "against", "between",
                     "into", "through", "during", "before", "after", "above", "below",
                     "to", "of", "in", "on", "is", "are", "was", "were", "be", "been",
                     "being", "have", "has", "had", "having", "do", "does", "did",
                     "doing", "can", "could", "should", "would", "may", "might"}
        
        # Tokenize and filter
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 3]
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(keywords))
    
    def _evaluate_markdown_quality(self, text: str) -> float:
        """Evaluate the quality of markdown formatting"""
        # Check for markdown elements
        has_headers = bool(re.search(r'^#{1,6}\s', text, re.MULTILINE))
        has_lists = bool(re.search(r'^\s*[-*+]\s', text, re.MULTILINE))
        has_code_blocks = bool(re.search(r'```', text))
        has_links = bool(re.search(r'\[.*?\]\(.*?\)', text))
        has_emphasis = bool(re.search(r'\*\*.*?\*\*|\*.*?\*|__.*?__|_.*?_', text))
        
        # Calculate a simple score based on markdown feature usage
        features = [has_headers, has_lists, has_code_blocks, has_links, has_emphasis]
        score = sum(1 for feature in features if feature) / len(features)
        
        return score

# Create a singleton instance
llm_validator = LLMValidator()