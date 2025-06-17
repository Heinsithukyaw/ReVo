#!/usr/bin/env python3
"""
Enhanced Quality Gates for reVoAgent
Enterprise-grade security and quality validation system
"""

import asyncio
import logging
import re
import ast
import json
import hashlib
import time
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import subprocess
import tempfile
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    """Security severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class QualityLevel(Enum):
    """Quality assessment levels"""
    EXCELLENT = "excellent"  # 95-100%
    GOOD = "good"           # 85-94%
    ACCEPTABLE = "acceptable" # 70-84%
    POOR = "poor"           # 50-69%
    CRITICAL = "critical"   # <50%

@dataclass
class SecurityIssue:
    """Security issue details"""
    issue_type: str
    severity: SecurityLevel
    description: str
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    recommendation: str = ""
    cwe_id: Optional[str] = None  # Common Weakness Enumeration ID

@dataclass
class QualityMetrics:
    """Enhanced quality metrics"""
    syntax_score: float = 0.0
    security_score: float = 0.0
    performance_score: float = 0.0
    maintainability_score: float = 0.0
    documentation_score: float = 0.0
    test_coverage_score: float = 0.0
    complexity_score: float = 0.0
    best_practices_score: float = 0.0
    overall_score: float = 0.0
    
    def __post_init__(self):
        """Calculate overall score"""
        scores = [
            self.syntax_score,
            self.security_score,
            self.performance_score,
            self.maintainability_score,
            self.documentation_score,
            self.test_coverage_score,
            self.complexity_score,
            self.best_practices_score
        ]
        self.overall_score = sum(scores) / len(scores) if scores else 0.0

@dataclass
class QualityReport:
    """Enhanced quality report"""
    validation_id: str
    agent_id: str
    validation_type: str
    content_hash: str
    quality_metrics: QualityMetrics
    security_issues: List[SecurityIssue] = field(default_factory=list)
    performance_issues: List[Dict[str, Any]] = field(default_factory=list)
    syntax_errors: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    validation_passed: bool = False
    quality_level: QualityLevel = QualityLevel.CRITICAL
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

class EnhancedQualityGates:
    """Enterprise-grade quality gates with advanced security scanning"""
    
    def __init__(self):
        self.quality_thresholds = {
            "syntax_minimum": 98.0,      # Increased from 95%
            "security_minimum": 95.0,    # Increased from 85%
            "performance_minimum": 85.0,  # Increased from 70%
            "maintainability_minimum": 90.0,
            "documentation_minimum": 85.0,
            "test_coverage_minimum": 90.0,  # Increased from 80%
            "complexity_minimum": 80.0,
            "best_practices_minimum": 90.0,
            "overall_minimum": 90.0      # Increased from 80%
        }
        
        self.security_patterns = self._initialize_security_patterns()
        self.validation_history: Dict[str, List[Dict[str, Any]]] = {}
        self.blocked_patterns: Set[str] = set()
        self.enterprise_compliance = {
            "owasp_top_10": True,
            "pci_dss": True,
            "gdpr": True,
            "soc2": True,
            "iso27001": True
        }
        
    def _initialize_security_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize comprehensive security vulnerability patterns"""
        return {
            "sql_injection": [
                {
                    "pattern": r'["\'][^"\']*\+[^"\']*["\'][^"\']*(?:SELECT|INSERT|UPDATE|DELETE|DROP)',
                    "severity": SecurityLevel.CRITICAL,
                    "cwe": "CWE-89",
                    "description": "Potential SQL injection vulnerability"
                },
                {
                    "pattern": r'execute[^(]*\([^)]*\+[^)]*\)',
                    "severity": SecurityLevel.HIGH,
                    "cwe": "CWE-89",
                    "description": "Dynamic SQL execution with concatenation"
                }
            ],
            "xss": [
                {
                    "pattern": r'innerHTML.*=.*\+',
                    "severity": SecurityLevel.HIGH,
                    "cwe": "CWE-79",
                    "description": "Potential XSS vulnerability in innerHTML"
                },
                {
                    "pattern": r'document\.write.*\+',
                    "severity": SecurityLevel.HIGH,
                    "cwe": "CWE-79",
                    "description": "Potential XSS vulnerability in document.write"
                }
            ],
            "command_injection": [
                {
                    "pattern": r'(?:os\.system|subprocess\.call|exec|eval)\s*\([^)]*\+',
                    "severity": SecurityLevel.CRITICAL,
                    "cwe": "CWE-78",
                    "description": "Potential command injection vulnerability"
                }
            ],
            "hardcoded_secrets": [
                {
                    "pattern": r'(?:password|secret|key|token)\s*=\s*["\'][^"\']{8,}["\']',
                    "severity": SecurityLevel.HIGH,
                    "cwe": "CWE-798",
                    "description": "Hardcoded credentials detected"
                },
                {
                    "pattern": r'(?:api_key|access_token)\s*=\s*["\'][A-Za-z0-9+/=]{20,}["\']',
                    "severity": SecurityLevel.HIGH,
                    "cwe": "CWE-798",
                    "description": "Hardcoded API key detected"
                }
            ],
            "path_traversal": [
                {
                    "pattern": r'\.\.[\\/]',
                    "severity": SecurityLevel.MEDIUM,
                    "cwe": "CWE-22",
                    "description": "Potential path traversal vulnerability"
                }
            ],
            "weak_crypto": [
                {
                    "pattern": r'(?:md5|sha1)\s*\(',
                    "severity": SecurityLevel.MEDIUM,
                    "cwe": "CWE-327",
                    "description": "Weak cryptographic algorithm"
                }
            ],
            "unsafe_deserialization": [
                {
                    "pattern": r'pickle\.loads?\s*\(',
                    "severity": SecurityLevel.HIGH,
                    "cwe": "CWE-502",
                    "description": "Unsafe deserialization with pickle"
                }
            ],
            "debug_code": [
                {
                    "pattern": r'(?:print|console\.log|debugger)\s*\(',
                    "severity": SecurityLevel.LOW,
                    "cwe": "CWE-489",
                    "description": "Debug code in production"
                }
            ]
        }
    
    async def validate_generated_code(
        self, 
        content: str, 
        agent_id: str, 
        validation_type: str = "code",
        language: str = "python"
    ) -> QualityReport:
        """Perform comprehensive quality validation"""
        start_time = time.time()
        validation_id = hashlib.md5(f"{agent_id}_{content}_{time.time()}".encode()).hexdigest()
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        logger.info(f"🔍 Starting enhanced quality validation: {validation_id}")
        
        # Initialize report
        report = QualityReport(
            validation_id=validation_id,
            agent_id=agent_id,
            validation_type=validation_type,
            content_hash=content_hash,
            quality_metrics=QualityMetrics()
        )
        
        try:
            # Perform all quality checks
            await self._validate_syntax(content, language, report)
            await self._validate_security(content, language, report)
            await self._validate_performance(content, language, report)
            await self._validate_maintainability(content, language, report)
            await self._validate_documentation(content, language, report)
            await self._validate_test_coverage(content, language, report)
            await self._validate_complexity(content, language, report)
            await self._validate_best_practices(content, language, report)
            
            # Calculate overall metrics
            report.quality_metrics.__post_init__()
            
            # Determine quality level
            report.quality_level = self._determine_quality_level(report.quality_metrics.overall_score)
            
            # Check if validation passed
            report.validation_passed = self._check_validation_passed(report)
            
            # Generate recommendations
            report.recommendations = await self._generate_recommendations(report)
            
            # Record execution time
            report.execution_time = time.time() - start_time
            
            # Update validation history
            await self._update_validation_history(agent_id, report)
            
            logger.info(f"✅ Quality validation complete: {report.quality_metrics.overall_score:.1f}% ({report.quality_level.value})")
            
        except Exception as e:
            logger.error(f"❌ Quality validation failed: {e}")
            report.validation_passed = False
            report.quality_level = QualityLevel.CRITICAL
            report.execution_time = time.time() - start_time
        
        return report
    
    async def _validate_syntax(self, content: str, language: str, report: QualityReport):
        """Enhanced syntax validation"""
        try:
            if language.lower() == "python":
                # Use AST for comprehensive Python syntax checking
                try:
                    ast.parse(content)
                    report.quality_metrics.syntax_score = 100.0
                except SyntaxError as e:
                    report.syntax_errors.append({
                        "type": "syntax_error",
                        "message": str(e),
                        "line": e.lineno,
                        "offset": e.offset
                    })
                    report.quality_metrics.syntax_score = max(0.0, 100.0 - len(report.syntax_errors) * 20)
                
                # Additional Python-specific checks
                if "import *" in content:
                    report.syntax_errors.append({
                        "type": "bad_practice",
                        "message": "Wildcard imports should be avoided",
                        "severity": "medium"
                    })
                    report.quality_metrics.syntax_score -= 5.0
                    
            elif language.lower() in ["javascript", "typescript"]:
                # Basic JavaScript/TypeScript syntax checks
                if self._check_js_syntax(content):
                    report.quality_metrics.syntax_score = 95.0
                else:
                    report.quality_metrics.syntax_score = 70.0
                    
            else:
                # Generic syntax validation
                report.quality_metrics.syntax_score = 90.0 if content.strip() else 0.0
                
        except Exception as e:
            logger.error(f"Syntax validation error: {e}")
            report.quality_metrics.syntax_score = 50.0
    
    async def _validate_security(self, content: str, language: str, report: QualityReport):
        """Comprehensive security validation"""
        security_score = 100.0
        
        # Check against all security patterns
        for category, patterns in self.security_patterns.items():
            for pattern_info in patterns:
                matches = re.finditer(pattern_info["pattern"], content, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    line_number = content[:match.start()].count('\n') + 1
                    
                    issue = SecurityIssue(
                        issue_type=category,
                        severity=pattern_info["severity"],
                        description=pattern_info["description"],
                        line_number=line_number,
                        code_snippet=self._extract_code_snippet(content, line_number),
                        recommendation=self._get_security_recommendation(category),
                        cwe_id=pattern_info.get("cwe")
                    )
                    
                    report.security_issues.append(issue)
                    
                    # Deduct points based on severity
                    severity_penalties = {
                        SecurityLevel.CRITICAL: 25.0,
                        SecurityLevel.HIGH: 15.0,
                        SecurityLevel.MEDIUM: 8.0,
                        SecurityLevel.LOW: 3.0,
                        SecurityLevel.INFO: 1.0
                    }
                    security_score -= severity_penalties.get(pattern_info["severity"], 5.0)
        
        # Additional security checks
        security_score = await self._additional_security_checks(content, language, security_score, report)
        
        report.quality_metrics.security_score = max(0.0, security_score)
    
    async def _additional_security_checks(self, content: str, language: str, security_score: float, report: QualityReport) -> float:
        """Additional comprehensive security checks"""
        
        # Check for input validation
        if language.lower() == "python":
            if "input(" in content and "validate" not in content.lower():
                report.security_issues.append(SecurityIssue(
                    issue_type="input_validation",
                    severity=SecurityLevel.MEDIUM,
                    description="User input without validation",
                    recommendation="Always validate and sanitize user input"
                ))
                security_score -= 10.0
        
        # Check for proper error handling
        if "try:" in content and "except:" in content:
            security_score += 5.0  # Bonus for error handling
        elif any(keyword in content for keyword in ["raise", "throw", "error"]):
            security_score += 2.0
        
        # Check for logging security
        if any(pattern in content.lower() for pattern in ["log", "print", "console"]):
            if any(sensitive in content.lower() for sensitive in ["password", "secret", "key", "token"]):
                report.security_issues.append(SecurityIssue(
                    issue_type="information_disclosure",
                    severity=SecurityLevel.HIGH,
                    description="Potential sensitive information in logs",
                    recommendation="Never log sensitive information"
                ))
                security_score -= 15.0
        
        return security_score
    
    async def _validate_performance(self, content: str, language: str, report: QualityReport):
        """Enhanced performance validation"""
        performance_score = 100.0
        
        # Check for performance anti-patterns
        performance_issues = []
        
        if language.lower() == "python":
            # Check for inefficient loops
            if re.search(r'for.*in.*range\(len\(', content):
                performance_issues.append({
                    "type": "inefficient_loop",
                    "description": "Use enumerate() instead of range(len())",
                    "impact": "medium"
                })
                performance_score -= 10.0
            
            # Check for string concatenation in loops
            if re.search(r'for.*:\s*.*\+=.*["\']', content):
                performance_issues.append({
                    "type": "string_concatenation",
                    "description": "Use join() for string concatenation in loops",
                    "impact": "high"
                })
                performance_score -= 15.0
            
            # Check for global variables
            if re.search(r'^global\s+', content, re.MULTILINE):
                performance_issues.append({
                    "type": "global_variables",
                    "description": "Avoid global variables for better performance",
                    "impact": "medium"
                })
                performance_score -= 8.0
        
        # Check for recursive functions without memoization
        if "def " in content and "return " in content:
            functions = re.findall(r'def\s+(\w+)', content)
            for func in functions:
                if func in content.split(f"def {func}")[1:][0] if len(content.split(f"def {func}")) > 1 else "":
                    performance_issues.append({
                        "type": "recursion_without_memoization",
                        "description": f"Function {func} appears to be recursive without memoization",
                        "impact": "high"
                    })
                    performance_score -= 12.0
        
        report.performance_issues = performance_issues
        report.quality_metrics.performance_score = max(0.0, performance_score)
    
    async def _validate_maintainability(self, content: str, language: str, report: QualityReport):
        """Validate code maintainability"""
        maintainability_score = 100.0
        
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        # Check function length
        if language.lower() == "python":
            functions = re.findall(r'def\s+\w+.*?(?=\ndef|\nclass|\Z)', content, re.DOTALL)
            for func in functions:
                func_lines = len([line for line in func.split('\n') if line.strip()])
                if func_lines > 50:
                    maintainability_score -= 15.0
                elif func_lines > 30:
                    maintainability_score -= 8.0
        
        # Check for magic numbers
        magic_numbers = re.findall(r'\b(?<![\w.])\d{2,}\b(?![\w.])', content)
        if len(magic_numbers) > 3:
            maintainability_score -= 10.0
        
        # Check for code duplication
        line_counts = {}
        for line in non_empty_lines:
            stripped = line.strip()
            if len(stripped) > 10:  # Only check substantial lines
                line_counts[stripped] = line_counts.get(stripped, 0) + 1
        
        duplicated_lines = sum(1 for count in line_counts.values() if count > 1)
        if duplicated_lines > 5:
            maintainability_score -= 20.0
        elif duplicated_lines > 2:
            maintainability_score -= 10.0
        
        report.quality_metrics.maintainability_score = max(0.0, maintainability_score)
    
    async def _validate_documentation(self, content: str, language: str, report: QualityReport):
        """Enhanced documentation validation"""
        documentation_score = 0.0
        
        if language.lower() == "python":
            # Check for docstrings
            docstring_patterns = [r'""".*?"""', r"'''.*?'''"]
            docstrings = 0
            for pattern in docstring_patterns:
                docstrings += len(re.findall(pattern, content, re.DOTALL))
            
            # Check for function/class documentation
            functions = len(re.findall(r'def\s+\w+', content))
            classes = len(re.findall(r'class\s+\w+', content))
            
            if functions > 0:
                documentation_score += min(50.0, (docstrings / functions) * 50.0)
            
            if classes > 0:
                documentation_score += min(25.0, (docstrings / classes) * 25.0)
            
            # Check for inline comments
            comment_lines = len(re.findall(r'^\s*#', content, re.MULTILINE))
            code_lines = len([line for line in content.split('\n') if line.strip() and not line.strip().startswith('#')])
            
            if code_lines > 0:
                comment_ratio = comment_lines / code_lines
                documentation_score += min(25.0, comment_ratio * 100)
        
        elif language.lower() in ["javascript", "typescript"]:
            # Check for JSDoc comments
            jsdoc_comments = len(re.findall(r'/\*\*.*?\*/', content, re.DOTALL))
            functions = len(re.findall(r'function\s+\w+|=>\s*{', content))
            
            if functions > 0:
                documentation_score += min(60.0, (jsdoc_comments / functions) * 60.0)
            
            # Check for inline comments
            inline_comments = len(re.findall(r'//.*$', content, re.MULTILINE))
            documentation_score += min(40.0, inline_comments * 5)
        
        report.quality_metrics.documentation_score = min(100.0, documentation_score)
    
    async def _validate_test_coverage(self, content: str, language: str, report: QualityReport):
        """Validate test coverage and quality"""
        test_score = 0.0
        
        # Check if this is test code
        is_test_code = any(keyword in content.lower() for keyword in [
            'test_', 'def test', 'it(', 'describe(', 'assert', 'expect'
        ])
        
        if is_test_code:
            # This is test code, evaluate test quality
            test_score = 80.0  # Base score for having tests
            
            # Check for different types of assertions
            assertion_types = [
                r'assert\s+',
                r'assertEqual',
                r'assertTrue',
                r'assertFalse',
                r'expect\(',
                r'should\.'
            ]
            
            assertion_count = 0
            for pattern in assertion_types:
                assertion_count += len(re.findall(pattern, content))
            
            if assertion_count > 5:
                test_score += 15.0
            elif assertion_count > 2:
                test_score += 10.0
            
            # Check for edge case testing
            edge_case_keywords = ['empty', 'null', 'none', 'zero', 'negative', 'boundary']
            edge_cases = sum(1 for keyword in edge_case_keywords if keyword in content.lower())
            test_score += min(5.0, edge_cases * 1.0)
            
        else:
            # This is production code, check if it's testable
            functions = len(re.findall(r'def\s+\w+', content))
            classes = len(re.findall(r'class\s+\w+', content))
            
            if functions > 0 or classes > 0:
                # Assume some test coverage exists (would need actual coverage tool)
                test_score = 60.0  # Moderate score for testable code
            else:
                test_score = 40.0  # Lower score for non-testable code
        
        report.quality_metrics.test_coverage_score = min(100.0, test_score)
    
    async def _validate_complexity(self, content: str, language: str, report: QualityReport):
        """Validate code complexity"""
        complexity_score = 100.0
        
        # Cyclomatic complexity estimation
        complexity_keywords = [
            'if', 'elif', 'else', 'for', 'while', 'try', 'except', 'finally',
            'and', 'or', '&&', '||', '?', 'case', 'switch'
        ]
        
        complexity_count = 0
        for keyword in complexity_keywords:
            complexity_count += len(re.findall(rf'\b{keyword}\b', content))
        
        # Estimate complexity per function
        functions = len(re.findall(r'def\s+\w+|function\s+\w+', content))
        if functions > 0:
            avg_complexity = complexity_count / functions
            if avg_complexity > 15:
                complexity_score -= 30.0
            elif avg_complexity > 10:
                complexity_score -= 20.0
            elif avg_complexity > 7:
                complexity_score -= 10.0
        
        # Check nesting depth
        max_nesting = self._calculate_max_nesting_depth(content)
        if max_nesting > 5:
            complexity_score -= 25.0
        elif max_nesting > 3:
            complexity_score -= 15.0
        
        report.quality_metrics.complexity_score = max(0.0, complexity_score)
    
    async def _validate_best_practices(self, content: str, language: str, report: QualityReport):
        """Validate adherence to best practices"""
        best_practices_score = 100.0
        
        if language.lower() == "python":
            # PEP 8 checks
            if re.search(r'^\s{1,3}\S', content, re.MULTILINE):  # Check indentation
                best_practices_score -= 10.0
            
            # Check for proper naming conventions
            if re.search(r'def\s+[A-Z]', content):  # Function names should be lowercase
                best_practices_score -= 5.0
            
            if re.search(r'class\s+[a-z]', content):  # Class names should be PascalCase
                best_practices_score -= 5.0
            
            # Check for type hints
            if 'def ' in content and '->' not in content and ':' not in content:
                best_practices_score -= 10.0
            
            # Check for proper imports
            if re.search(r'^import\s+\w+\.\w+', content, re.MULTILINE):
                best_practices_score -= 5.0  # Prefer from X import Y
        
        elif language.lower() in ["javascript", "typescript"]:
            # Check for const/let usage
            if 'var ' in content:
                best_practices_score -= 15.0
            
            # Check for arrow functions
            if 'function(' in content and '=>' not in content:
                best_practices_score -= 5.0
        
        report.quality_metrics.best_practices_score = max(0.0, best_practices_score)
    
    def _check_js_syntax(self, content: str) -> bool:
        """Basic JavaScript syntax validation"""
        # Simple checks for common syntax issues
        open_braces = content.count('{')
        close_braces = content.count('}')
        open_parens = content.count('(')
        close_parens = content.count(')')
        
        return open_braces == close_braces and open_parens == close_parens
    
    def _extract_code_snippet(self, content: str, line_number: int, context: int = 2) -> str:
        """Extract code snippet around a specific line"""
        lines = content.split('\n')
        start = max(0, line_number - context - 1)
        end = min(len(lines), line_number + context)
        return '\n'.join(lines[start:end])
    
    def _get_security_recommendation(self, issue_type: str) -> str:
        """Get security recommendation for issue type"""
        recommendations = {
            "sql_injection": "Use parameterized queries or prepared statements",
            "xss": "Sanitize user input and use proper encoding",
            "command_injection": "Avoid dynamic command execution, use safe alternatives",
            "hardcoded_secrets": "Use environment variables or secure key management",
            "path_traversal": "Validate and sanitize file paths",
            "weak_crypto": "Use strong cryptographic algorithms (SHA-256, AES)",
            "unsafe_deserialization": "Use safe serialization formats like JSON",
            "debug_code": "Remove debug code before production deployment"
        }
        return recommendations.get(issue_type, "Follow security best practices")
    
    def _calculate_max_nesting_depth(self, content: str) -> int:
        """Calculate maximum nesting depth"""
        max_depth = 0
        current_depth = 0
        
        for line in content.split('\n'):
            stripped = line.strip()
            if any(keyword in stripped for keyword in ['if', 'for', 'while', 'try', 'def', 'class']):
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif stripped.startswith(('else', 'elif', 'except', 'finally')):
                continue
            elif stripped == '' or stripped.startswith('#'):
                continue
            else:
                # Estimate depth reduction (simplified)
                if current_depth > 0:
                    current_depth = max(0, current_depth - 0.1)
        
        return int(max_depth)
    
    def _determine_quality_level(self, score: float) -> QualityLevel:
        """Determine quality level based on score"""
        if score >= 95.0:
            return QualityLevel.EXCELLENT
        elif score >= 85.0:
            return QualityLevel.GOOD
        elif score >= 70.0:
            return QualityLevel.ACCEPTABLE
        elif score >= 50.0:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL
    
    def _check_validation_passed(self, report: QualityReport) -> bool:
        """Check if validation passed based on thresholds"""
        metrics = report.quality_metrics
        
        # Check all thresholds
        checks = [
            metrics.syntax_score >= self.quality_thresholds["syntax_minimum"],
            metrics.security_score >= self.quality_thresholds["security_minimum"],
            metrics.performance_score >= self.quality_thresholds["performance_minimum"],
            metrics.maintainability_score >= self.quality_thresholds["maintainability_minimum"],
            metrics.documentation_score >= self.quality_thresholds["documentation_minimum"],
            metrics.test_coverage_score >= self.quality_thresholds["test_coverage_minimum"],
            metrics.complexity_score >= self.quality_thresholds["complexity_minimum"],
            metrics.best_practices_score >= self.quality_thresholds["best_practices_minimum"],
            metrics.overall_score >= self.quality_thresholds["overall_minimum"]
        ]
        
        # Check for critical security issues
        critical_security_issues = [
            issue for issue in report.security_issues 
            if issue.severity in [SecurityLevel.CRITICAL, SecurityLevel.HIGH]
        ]
        
        return all(checks) and len(critical_security_issues) == 0
    
    async def _generate_recommendations(self, report: QualityReport) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        metrics = report.quality_metrics
        
        if metrics.syntax_score < self.quality_thresholds["syntax_minimum"]:
            recommendations.append("Fix syntax errors and improve code structure")
        
        if metrics.security_score < self.quality_thresholds["security_minimum"]:
            recommendations.append("Address security vulnerabilities immediately")
            if report.security_issues:
                critical_issues = [i for i in report.security_issues if i.severity == SecurityLevel.CRITICAL]
                if critical_issues:
                    recommendations.append(f"CRITICAL: Fix {len(critical_issues)} critical security issues")
        
        if metrics.performance_score < self.quality_thresholds["performance_minimum"]:
            recommendations.append("Optimize performance bottlenecks")
        
        if metrics.maintainability_score < self.quality_thresholds["maintainability_minimum"]:
            recommendations.append("Improve code maintainability and reduce complexity")
        
        if metrics.documentation_score < self.quality_thresholds["documentation_minimum"]:
            recommendations.append("Add comprehensive documentation and comments")
        
        if metrics.test_coverage_score < self.quality_thresholds["test_coverage_minimum"]:
            recommendations.append("Increase test coverage and add edge case tests")
        
        if metrics.complexity_score < self.quality_thresholds["complexity_minimum"]:
            recommendations.append("Reduce code complexity and nesting depth")
        
        if metrics.best_practices_score < self.quality_thresholds["best_practices_minimum"]:
            recommendations.append("Follow language-specific best practices and conventions")
        
        return recommendations
    
    async def _update_validation_history(self, agent_id: str, report: QualityReport):
        """Update validation history for agent"""
        if agent_id not in self.validation_history:
            self.validation_history[agent_id] = []
        
        history_entry = {
            "validation_id": report.validation_id,
            "timestamp": report.timestamp.isoformat(),
            "overall_score": report.quality_metrics.overall_score,
            "quality_level": report.quality_level.value,
            "validation_passed": report.validation_passed,
            "security_issues_count": len(report.security_issues),
            "critical_issues_count": len([i for i in report.security_issues if i.severity == SecurityLevel.CRITICAL])
        }
        
        self.validation_history[agent_id].append(history_entry)
        
        # Keep only last 100 entries per agent
        if len(self.validation_history[agent_id]) > 100:
            self.validation_history[agent_id] = self.validation_history[agent_id][-100:]
    
    def get_enterprise_compliance_status(self) -> Dict[str, Any]:
        """Get enterprise compliance status"""
        return {
            "compliance_frameworks": self.enterprise_compliance,
            "quality_thresholds": self.quality_thresholds,
            "security_patterns_count": sum(len(patterns) for patterns in self.security_patterns.values()),
            "validation_history_count": sum(len(history) for history in self.validation_history.values()),
            "enterprise_ready": all(self.enterprise_compliance.values())
        }
    
    def get_agent_performance_analytics(self, agent_id: str) -> Dict[str, Any]:
        """Get comprehensive agent performance analytics"""
        if agent_id not in self.validation_history:
            return {"error": "No validation history found for agent"}
        
        history = self.validation_history[agent_id]
        
        if not history:
            return {"error": "No validation data available"}
        
        # Calculate analytics
        total_validations = len(history)
        passed_validations = sum(1 for entry in history if entry["validation_passed"])
        success_rate = passed_validations / total_validations if total_validations > 0 else 0
        
        scores = [entry["overall_score"] for entry in history]
        average_score = sum(scores) / len(scores) if scores else 0
        
        recent_scores = scores[-10:] if len(scores) >= 10 else scores
        recent_average = sum(recent_scores) / len(recent_scores) if recent_scores else 0
        
        # Determine trend
        if len(scores) >= 5:
            early_avg = sum(scores[:len(scores)//2]) / (len(scores)//2)
            late_avg = sum(scores[len(scores)//2:]) / (len(scores) - len(scores)//2)
            trend = "improving" if late_avg > early_avg + 5 else "declining" if late_avg < early_avg - 5 else "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "agent_id": agent_id,
            "total_validations": total_validations,
            "success_rate": success_rate,
            "average_score": average_score,
            "recent_average": recent_average,
            "trend": trend,
            "quality_distribution": {
                "excellent": sum(1 for s in scores if s >= 95),
                "good": sum(1 for s in scores if 85 <= s < 95),
                "acceptable": sum(1 for s in scores if 70 <= s < 85),
                "poor": sum(1 for s in scores if 50 <= s < 70),
                "critical": sum(1 for s in scores if s < 50)
            },
            "security_metrics": {
                "total_security_issues": sum(entry.get("security_issues_count", 0) for entry in history),
                "critical_security_issues": sum(entry.get("critical_issues_count", 0) for entry in history),
                "security_improvement": self._calculate_security_improvement(history)
            }
        }
    
    def _calculate_security_improvement(self, history: List[Dict[str, Any]]) -> str:
        """Calculate security improvement trend"""
        if len(history) < 5:
            return "insufficient_data"
        
        recent_issues = sum(entry.get("security_issues_count", 0) for entry in history[-5:])
        early_issues = sum(entry.get("security_issues_count", 0) for entry in history[:5])
        
        if recent_issues < early_issues * 0.5:
            return "significant_improvement"
        elif recent_issues < early_issues:
            return "improving"
        elif recent_issues > early_issues * 1.5:
            return "declining"
        else:
            return "stable"
    
    def update_quality_thresholds(self, new_thresholds: Dict[str, float]):
        """Update quality thresholds for enterprise requirements"""
        for key, value in new_thresholds.items():
            if key in self.quality_thresholds:
                self.quality_thresholds[key] = value
                logger.info(f"Updated quality threshold {key}: {value}%")


# Factory function for easy integration
def create_enhanced_quality_gates() -> EnhancedQualityGates:
    """Create enhanced quality gates instance"""
    gates = EnhancedQualityGates()
    logger.info("🛡️ Enhanced Quality Gates initialized with enterprise security")
    return gates


if __name__ == "__main__":
    # Test the enhanced quality gates
    async def test_enhanced_quality_gates():
        gates = create_enhanced_quality_gates()
        
        # Test with secure code
        secure_code = '''
def calculate_fibonacci(n: int) -> int:
    """
    Calculate the nth Fibonacci number using dynamic programming.
    
    Args:
        n (int): The position in the Fibonacci sequence
        
    Returns:
        int: The nth Fibonacci number
        
    Raises:
        ValueError: If n is negative
    """
    if not isinstance(n, int) or n < 0:
        raise ValueError("n must be a non-negative integer")
    
    if n <= 1:
        return n
    
    # Use dynamic programming for efficiency
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    
    return b

def test_fibonacci():
    """Test the fibonacci function."""
    assert calculate_fibonacci(0) == 0
    assert calculate_fibonacci(1) == 1
    assert calculate_fibonacci(5) == 5
    assert calculate_fibonacci(10) == 55
'''
        
        report = await gates.validate_generated_code(secure_code, "test-agent", "code", "python")
        
        print(f"✅ Quality Report:")
        print(f"📊 Overall Score: {report.quality_metrics.overall_score:.1f}%")
        print(f"🛡️ Security Score: {report.quality_metrics.security_score:.1f}%")
        print(f"⚡ Performance Score: {report.quality_metrics.performance_score:.1f}%")
        print(f"📚 Documentation Score: {report.quality_metrics.documentation_score:.1f}%")
        print(f"🧪 Test Coverage Score: {report.quality_metrics.test_coverage_score:.1f}%")
        print(f"✅ Validation Passed: {report.validation_passed}")
        print(f"🏆 Quality Level: {report.quality_level.value}")
        print(f"🔍 Security Issues: {len(report.security_issues)}")
        
        # Test enterprise compliance
        compliance = gates.get_enterprise_compliance_status()
        print(f"🏢 Enterprise Compliance: {compliance}")
    
    asyncio.run(test_enhanced_quality_gates())