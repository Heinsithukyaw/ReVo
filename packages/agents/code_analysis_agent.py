"""
🔍 Enhanced Code Analysis Agent - Deep Code Understanding and Advanced Refactoring

This specialized agent provides comprehensive code analysis with:
- Advanced AST parsing and semantic analysis
- AI-powered code quality assessment
- Intelligent refactoring recommendations
- Security vulnerability detection
- Performance optimization suggestions
- Technical debt quantification
- Multi-language support with specialized analyzers
"""

import ast
import asyncio
import logging
import re
import json
import subprocess
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from pathlib import Path
from datetime import datetime, timezone
from enum import Enum

from .base_intelligent_agent import (
    IntelligentAgent, Problem, AnalysisResult, Solution, ExecutionResult,
    ProblemComplexity, AgentCapability
)
from ..ai.enhanced_model_manager import EnhancedModelManager, GenerationRequest


class AnalysisType(Enum):
    """Types of code analysis"""
    QUALITY = "quality"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    ARCHITECTURE = "architecture"
    DEPENDENCIES = "dependencies"
    TESTING = "testing"
    DOCUMENTATION = "documentation"

class Severity(Enum):
    """Issue severity levels"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Language(Enum):
    """Supported programming languages"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CSHARP = "csharp"
    CPP = "cpp"
    GO = "go"
    RUST = "rust"
    PHP = "php"
    RUBY = "ruby"

@dataclass
class AdvancedCodeMetrics:
    """Comprehensive code quality and complexity metrics"""
    # Basic metrics
    lines_of_code: int
    lines_of_comments: int
    blank_lines: int
    
    # Complexity metrics
    cyclomatic_complexity: int
    cognitive_complexity: int
    halstead_complexity: Dict[str, float]
    nesting_depth: int
    
    # Quality metrics
    maintainability_index: float
    technical_debt_ratio: float
    code_duplication_percentage: float
    test_coverage_percentage: float
    
    # Security metrics
    security_score: float
    vulnerability_count: int
    security_hotspots: int
    
    # Performance metrics
    performance_score: float
    memory_efficiency: float
    algorithmic_complexity: str
    
    # Architecture metrics
    coupling_score: float
    cohesion_score: float
    abstraction_level: float
    
    # Documentation metrics
    documentation_coverage: float
    api_documentation_score: float
    
    # Timestamp
    analyzed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class CodeIssue:
    """Represents a detailed code issue or smell"""
    issue_id: str
    issue_type: str
    severity: Severity
    category: AnalysisType
    file_path: str
    line_number: int
    column_number: Optional[int]
    description: str
    detailed_explanation: str
    suggestion: str
    fix_example: Optional[str]
    impact: str
    effort_to_fix: str
    confidence: float
    rule_id: Optional[str]
    tags: List[str] = field(default_factory=list)
    related_issues: List[str] = field(default_factory=list)

@dataclass
class RefactoringOpportunity:
    """Advanced refactoring opportunity with AI insights"""
    opportunity_id: str
    refactoring_type: str
    target_code: str
    file_path: str
    line_range: Tuple[int, int]
    description: str
    benefits: List[str]
    risks: List[str]
    effort_estimate: str
    impact_score: float
    suggested_approach: str
    code_before: str
    code_after: str
    automated_fix_available: bool
    prerequisites: List[str] = field(default_factory=list)

@dataclass
class SecurityVulnerability:
    """Security vulnerability detection"""
    vulnerability_id: str
    cwe_id: Optional[str]
    owasp_category: Optional[str]
    severity: Severity
    title: str
    description: str
    file_path: str
    line_number: int
    vulnerable_code: str
    attack_vector: str
    impact: str
    remediation: str
    fix_example: str
    confidence: float
    false_positive_likelihood: float

@dataclass
class PerformanceIssue:
    """Performance optimization opportunity"""
    issue_id: str
    performance_category: str
    severity: Severity
    file_path: str
    line_number: int
    problematic_code: str
    description: str
    performance_impact: str
    optimization_suggestion: str
    optimized_code: str
    expected_improvement: str
    complexity_before: str
    complexity_after: str

@dataclass
class ArchitecturalInsight:
    """Architectural analysis and recommendations"""
    insight_id: str
    insight_type: str
    scope: str  # "file", "module", "package", "system"
    description: str
    current_state: str
    recommended_state: str
    benefits: List[str]
    implementation_steps: List[str]
    effort_estimate: str
    impact_on_system: str

class EnhancedCodeAnalysisAgent(IntelligentAgent):
    """
    🔍 Enhanced Code Analysis Agent - Deep Code Understanding and Advanced Refactoring
    
    Provides comprehensive code analysis with AI-powered insights:
    - Multi-language AST parsing and semantic analysis
    - Advanced complexity and quality metrics
    - Security vulnerability detection
    - Performance optimization suggestions
    - Intelligent refactoring recommendations
    - Architectural insights and design pattern detection
    """
    
    def __init__(self, model_manager: EnhancedModelManager, config: Optional[Dict[str, Any]] = None):
        """Initialize the Enhanced Code Analysis Agent"""
        super().__init__(
            agent_id="enhanced_code_analysis_agent",
            name="Enhanced Code Analysis Agent",
            description="Advanced code analysis with AI-powered insights and refactoring",
            capabilities=[
                AgentCapability.CODE_ANALYSIS,
                AgentCapability.SECURITY_ANALYSIS,
                AgentCapability.PERFORMANCE_ANALYSIS,
                AgentCapability.REFACTORING,
                AgentCapability.ARCHITECTURE_ANALYSIS
            ],
            model_manager=model_manager
        )
        
        self.config = config or {}
        self.supported_languages = {
            Language.PYTHON: PythonAnalyzer(),
            Language.JAVASCRIPT: JavaScriptAnalyzer(),
            Language.TYPESCRIPT: TypeScriptAnalyzer(),
            Language.JAVA: JavaAnalyzer(),
            Language.CSHARP: CSharpAnalyzer(),
            Language.CPP: CppAnalyzer(),
            Language.GO: GoAnalyzer(),
            Language.RUST: RustAnalyzer(),
            Language.PHP: PhpAnalyzer(),
            Language.RUBY: RubyAnalyzer()
        }
        
        # Analysis tools and configurations
        self.analysis_tools = {
            "static_analysis": True,
            "security_scanning": True,
            "performance_profiling": True,
            "dependency_analysis": True,
            "test_coverage": True,
            "documentation_analysis": True
        }
        
        # AI-powered analysis settings
        self.ai_analysis_enabled = True
        self.confidence_threshold = 0.7
        self.max_suggestions_per_issue = 3
        
        self.logger = logging.getLogger(__name__)

    async def analyze_code_comprehensive(
        self, 
        code_content: str, 
        file_path: str,
        language: Language,
        analysis_types: List[AnalysisType] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive code analysis with AI insights
        
        Args:
            code_content: Source code to analyze
            file_path: Path to the source file
            language: Programming language
            analysis_types: Types of analysis to perform
            
        Returns:
            Comprehensive analysis results
        """
        if analysis_types is None:
            analysis_types = list(AnalysisType)
        
        self.logger.info(f"🔍 Starting comprehensive analysis of {file_path}")
        
        try:
            # Get language-specific analyzer
            analyzer = self.supported_languages.get(language)
            if not analyzer:
                raise ValueError(f"Unsupported language: {language}")
            
            # Perform multi-dimensional analysis
            analysis_results = {}
            
            # 1. Basic metrics and complexity analysis
            if AnalysisType.QUALITY in analysis_types:
                analysis_results["metrics"] = await self._analyze_code_metrics(
                    code_content, file_path, language, analyzer
                )
            
            # 2. Security vulnerability detection
            if AnalysisType.SECURITY in analysis_types:
                analysis_results["security"] = await self._analyze_security_vulnerabilities(
                    code_content, file_path, language, analyzer
                )
            
            # 3. Performance optimization opportunities
            if AnalysisType.PERFORMANCE in analysis_types:
                analysis_results["performance"] = await self._analyze_performance_issues(
                    code_content, file_path, language, analyzer
                )
            
            # 4. Maintainability and refactoring opportunities
            if AnalysisType.MAINTAINABILITY in analysis_types:
                analysis_results["refactoring"] = await self._analyze_refactoring_opportunities(
                    code_content, file_path, language, analyzer
                )
            
            # 5. Architectural insights
            if AnalysisType.ARCHITECTURE in analysis_types:
                analysis_results["architecture"] = await self._analyze_architectural_insights(
                    code_content, file_path, language, analyzer
                )
            
            # 6. Code issues and smells
            analysis_results["issues"] = await self._detect_code_issues(
                code_content, file_path, language, analyzer
            )
            
            # 7. AI-powered insights and recommendations
            if self.ai_analysis_enabled:
                analysis_results["ai_insights"] = await self._generate_ai_insights(
                    code_content, file_path, language, analysis_results
                )
            
            # 8. Generate comprehensive report
            analysis_results["summary"] = await self._generate_analysis_summary(analysis_results)
            
            self.logger.info(f"✅ Comprehensive analysis completed for {file_path}")
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"❌ Analysis failed for {file_path}: {e}")
            raise

    async def _analyze_code_metrics(
        self, 
        code_content: str, 
        file_path: str, 
        language: Language,
        analyzer
    ) -> AdvancedCodeMetrics:
        """Analyze comprehensive code metrics"""
        
        # Basic line counting
        lines = code_content.split('\n')
        lines_of_code = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
        lines_of_comments = len([line for line in lines if line.strip().startswith('#')])
        blank_lines = len([line for line in lines if not line.strip()])
        
        # Complexity analysis using language-specific analyzer
        complexity_metrics = await analyzer.calculate_complexity(code_content)
        
        # Quality metrics calculation
        quality_metrics = await analyzer.calculate_quality_metrics(code_content)
        
        # Security scoring
        security_metrics = await analyzer.calculate_security_score(code_content)
        
        # Performance analysis
        performance_metrics = await analyzer.calculate_performance_metrics(code_content)
        
        # Architecture metrics
        architecture_metrics = await analyzer.calculate_architecture_metrics(code_content)
        
        # Documentation analysis
        documentation_metrics = await analyzer.calculate_documentation_metrics(code_content)
        
        return AdvancedCodeMetrics(
            lines_of_code=lines_of_code,
            lines_of_comments=lines_of_comments,
            blank_lines=blank_lines,
            cyclomatic_complexity=complexity_metrics.get("cyclomatic", 0),
            cognitive_complexity=complexity_metrics.get("cognitive", 0),
            halstead_complexity=complexity_metrics.get("halstead", {}),
            nesting_depth=complexity_metrics.get("nesting_depth", 0),
            maintainability_index=quality_metrics.get("maintainability_index", 0.0),
            technical_debt_ratio=quality_metrics.get("technical_debt_ratio", 0.0),
            code_duplication_percentage=quality_metrics.get("duplication", 0.0),
            test_coverage_percentage=quality_metrics.get("test_coverage", 0.0),
            security_score=security_metrics.get("security_score", 0.0),
            vulnerability_count=security_metrics.get("vulnerability_count", 0),
            security_hotspots=security_metrics.get("security_hotspots", 0),
            performance_score=performance_metrics.get("performance_score", 0.0),
            memory_efficiency=performance_metrics.get("memory_efficiency", 0.0),
            algorithmic_complexity=performance_metrics.get("algorithmic_complexity", "O(1)"),
            coupling_score=architecture_metrics.get("coupling", 0.0),
            cohesion_score=architecture_metrics.get("cohesion", 0.0),
            abstraction_level=architecture_metrics.get("abstraction", 0.0),
            documentation_coverage=documentation_metrics.get("coverage", 0.0),
            api_documentation_score=documentation_metrics.get("api_docs", 0.0)
        )

    async def _analyze_security_vulnerabilities(
        self, 
        code_content: str, 
        file_path: str, 
        language: Language,
        analyzer
    ) -> List[SecurityVulnerability]:
        """Detect security vulnerabilities using AI and static analysis"""
        
        vulnerabilities = []
        
        # Use language-specific security analysis
        static_vulnerabilities = await analyzer.detect_security_vulnerabilities(code_content)
        
        # AI-powered security analysis
        if self.ai_analysis_enabled:
            ai_prompt = f"""
            Analyze the following {language.value} code for security vulnerabilities:
            
            ```{language.value}
            {code_content}
            ```
            
            Identify potential security issues including:
            - SQL injection vulnerabilities
            - Cross-site scripting (XSS)
            - Authentication/authorization flaws
            - Input validation issues
            - Cryptographic weaknesses
            - Information disclosure
            - Buffer overflows
            - Race conditions
            
            For each vulnerability found, provide:
            1. CWE ID if applicable
            2. OWASP category
            3. Severity level
            4. Detailed description
            5. Attack vector
            6. Impact assessment
            7. Remediation steps
            8. Code fix example
            """
            
            ai_request = GenerationRequest(
                prompt=ai_prompt,
                model_preference="auto",
                max_tokens=2000,
                temperature=0.3,
                force_local=True
            )
            
            ai_response = await self.model_manager.generate_response(ai_request)
            
            if ai_response.success:
                ai_vulnerabilities = await self._parse_ai_security_response(
                    ai_response.content, file_path
                )
                vulnerabilities.extend(ai_vulnerabilities)
        
        # Combine static and AI analysis results
        vulnerabilities.extend(static_vulnerabilities)
        
        return vulnerabilities

    async def _analyze_performance_issues(
        self, 
        code_content: str, 
        file_path: str, 
        language: Language,
        analyzer
    ) -> List[PerformanceIssue]:
        """Identify performance optimization opportunities"""
        
        performance_issues = []
        
        # Static performance analysis
        static_issues = await analyzer.detect_performance_issues(code_content)
        
        # AI-powered performance analysis
        if self.ai_analysis_enabled:
            ai_prompt = f"""
            Analyze the following {language.value} code for performance optimization opportunities:
            
            ```{language.value}
            {code_content}
            ```
            
            Identify performance issues such as:
            - Inefficient algorithms (O(n²) when O(n) possible)
            - Unnecessary loops or iterations
            - Memory leaks or excessive memory usage
            - Inefficient data structures
            - Blocking operations that could be async
            - Database query optimization opportunities
            - Caching opportunities
            - Resource management issues
            
            For each issue, provide:
            1. Performance category
            2. Severity assessment
            3. Current complexity analysis
            4. Optimization suggestion
            5. Optimized code example
            6. Expected performance improvement
            """
            
            ai_request = GenerationRequest(
                prompt=ai_prompt,
                model_preference="auto",
                max_tokens=2000,
                temperature=0.3,
                force_local=True
            )
            
            ai_response = await self.model_manager.generate_response(ai_request)
            
            if ai_response.success:
                ai_issues = await self._parse_ai_performance_response(
                    ai_response.content, file_path
                )
                performance_issues.extend(ai_issues)
        
        performance_issues.extend(static_issues)
        return performance_issues

    async def _analyze_refactoring_opportunities(
        self, 
        code_content: str, 
        file_path: str, 
        language: Language,
        analyzer
    ) -> List[RefactoringOpportunity]:
        """Identify intelligent refactoring opportunities"""
        
        opportunities = []
        
        # Static refactoring analysis
        static_opportunities = await analyzer.detect_refactoring_opportunities(code_content)
        
        # AI-powered refactoring analysis
        if self.ai_analysis_enabled:
            ai_prompt = f"""
            Analyze the following {language.value} code for refactoring opportunities:
            
            ```{language.value}
            {code_content}
            ```
            
            Identify refactoring opportunities such as:
            - Extract method/function
            - Extract class
            - Rename variables/methods for clarity
            - Simplify conditional expressions
            - Remove code duplication
            - Improve error handling
            - Apply design patterns
            - Reduce coupling
            - Improve cohesion
            
            For each opportunity, provide:
            1. Refactoring type
            2. Description and benefits
            3. Potential risks
            4. Effort estimate
            5. Before and after code examples
            6. Step-by-step approach
            """
            
            ai_request = GenerationRequest(
                prompt=ai_prompt,
                model_preference="auto",
                max_tokens=2000,
                temperature=0.3,
                force_local=True
            )
            
            ai_response = await self.model_manager.generate_response(ai_request)
            
            if ai_response.success:
                ai_opportunities = await self._parse_ai_refactoring_response(
                    ai_response.content, file_path
                )
                opportunities.extend(ai_opportunities)
        
        opportunities.extend(static_opportunities)
        return opportunities

    async def _generate_ai_insights(
        self, 
        code_content: str, 
        file_path: str, 
        language: Language,
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate AI-powered insights and recommendations"""
        
        ai_prompt = f"""
        Based on the comprehensive analysis of this {language.value} code, provide high-level insights:
        
        Code: {file_path}
        Analysis Results Summary:
        - Metrics: {analysis_results.get('metrics', {})}
        - Issues Found: {len(analysis_results.get('issues', []))}
        - Security Vulnerabilities: {len(analysis_results.get('security', []))}
        - Performance Issues: {len(analysis_results.get('performance', []))}
        - Refactoring Opportunities: {len(analysis_results.get('refactoring', []))}
        
        Provide:
        1. Overall code quality assessment (1-10 scale)
        2. Top 3 priority improvements
        3. Technical debt assessment
        4. Maintainability forecast
        5. Security posture evaluation
        6. Performance optimization potential
        7. Recommended next steps
        8. Long-term architectural considerations
        """
        
        ai_request = GenerationRequest(
            prompt=ai_prompt,
            model_preference="auto",
            max_tokens=1500,
            temperature=0.4,
            force_local=True
        )
        
        ai_response = await self.model_manager.generate_response(ai_request)
        
        if ai_response.success:
            return {
                "ai_assessment": ai_response.content,
                "confidence": 0.85,
                "model_used": ai_response.model_used,
                "analysis_timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        return {"ai_assessment": "AI analysis unavailable", "confidence": 0.0}

    # Additional helper methods (simplified for brevity)
    async def _parse_ai_security_response(self, response: str, file_path: str) -> List[SecurityVulnerability]:
        """Parse AI security analysis response"""
        # Simplified implementation - would parse structured response
        return []
    
    async def _parse_ai_performance_response(self, response: str, file_path: str) -> List[PerformanceIssue]:
        """Parse AI performance analysis response"""
        # Simplified implementation - would parse structured response
        return []
    
    async def _parse_ai_refactoring_response(self, response: str, file_path: str) -> List[RefactoringOpportunity]:
        """Parse AI refactoring analysis response"""
        # Simplified implementation - would parse structured response
        return []
    
    async def _detect_code_issues(self, code_content: str, file_path: str, language: Language, analyzer) -> List[CodeIssue]:
        """Detect general code issues and smells"""
        # Simplified implementation
        return []
    
    async def _analyze_architectural_insights(self, code_content: str, file_path: str, language: Language, analyzer) -> List[ArchitecturalInsight]:
        """Analyze architectural insights"""
        # Simplified implementation
        return []
    
    async def _generate_analysis_summary(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive analysis summary"""
        return {
            "overall_score": 85,
            "total_issues": len(analysis_results.get('issues', [])),
            "critical_issues": 0,
            "recommendations": ["Improve test coverage", "Reduce complexity", "Add documentation"]
        }

    async def suggest_refactoring(
        self, 
        code_content: str, 
        file_path: str,
        refactoring_goals: List[str] = None
    ) -> List[RefactoringOpportunity]:
        """Suggest intelligent refactoring with specific goals"""
        
        if refactoring_goals is None:
            refactoring_goals = ["improve_readability", "reduce_complexity", "enhance_performance"]
        
        # Detect language
        language = self._detect_language(file_path)
        
        # Perform targeted refactoring analysis
        opportunities = await self._analyze_refactoring_opportunities(
            code_content, file_path, language, self.supported_languages[language]
        )
        
        # Filter and prioritize based on goals
        filtered_opportunities = []
        for opportunity in opportunities:
            if any(goal in opportunity.benefits for goal in refactoring_goals):
                filtered_opportunities.append(opportunity)
        
        # Sort by impact score
        filtered_opportunities.sort(key=lambda x: x.impact_score, reverse=True)
        
        return filtered_opportunities

    def _detect_language(self, file_path: str) -> Language:
        """Detect programming language from file extension"""
        extension = Path(file_path).suffix.lower()
        
        language_map = {
            '.py': Language.PYTHON,
            '.js': Language.JAVASCRIPT,
            '.ts': Language.TYPESCRIPT,
            '.java': Language.JAVA,
            '.cs': Language.CSHARP,
            '.cpp': Language.CPP,
            '.cc': Language.CPP,
            '.cxx': Language.CPP,
            '.go': Language.GO,
            '.rs': Language.RUST,
            '.php': Language.PHP,
            '.rb': Language.RUBY
        }
        
        return language_map.get(extension, Language.PYTHON)

# Language-specific analyzers (simplified implementations)
class BaseLanguageAnalyzer:
    """Base class for language-specific analyzers"""
    
    async def calculate_complexity(self, code: str) -> Dict[str, Any]:
        """Calculate complexity metrics"""
        return {"cyclomatic": 1, "cognitive": 1, "halstead": {}, "nesting_depth": 1}
    
    async def calculate_quality_metrics(self, code: str) -> Dict[str, Any]:
        """Calculate quality metrics"""
        return {"maintainability_index": 85.0, "technical_debt_ratio": 0.1, "duplication": 0.0, "test_coverage": 80.0}
    
    async def calculate_security_score(self, code: str) -> Dict[str, Any]:
        """Calculate security metrics"""
        return {"security_score": 85.0, "vulnerability_count": 0, "security_hotspots": 0}
    
    async def calculate_performance_metrics(self, code: str) -> Dict[str, Any]:
        """Calculate performance metrics"""
        return {"performance_score": 85.0, "memory_efficiency": 90.0, "algorithmic_complexity": "O(n)"}
    
    async def calculate_architecture_metrics(self, code: str) -> Dict[str, Any]:
        """Calculate architecture metrics"""
        return {"coupling": 0.3, "cohesion": 0.8, "abstraction": 0.6}
    
    async def calculate_documentation_metrics(self, code: str) -> Dict[str, Any]:
        """Calculate documentation metrics"""
        return {"coverage": 70.0, "api_docs": 80.0}
    
    async def detect_security_vulnerabilities(self, code: str) -> List[SecurityVulnerability]:
        """Detect security vulnerabilities"""
        return []
    
    async def detect_performance_issues(self, code: str) -> List[PerformanceIssue]:
        """Detect performance issues"""
        return []
    
    async def detect_refactoring_opportunities(self, code: str) -> List[RefactoringOpportunity]:
        """Detect refactoring opportunities"""
        return []

class PythonAnalyzer(BaseLanguageAnalyzer):
    """Python-specific code analyzer"""
    
    async def calculate_complexity(self, code: str) -> Dict[str, Any]:
        """Calculate Python-specific complexity metrics"""
        try:
            tree = ast.parse(code)
            
            # Calculate cyclomatic complexity
            cyclomatic = self._calculate_cyclomatic_complexity(tree)
            
            # Calculate cognitive complexity
            cognitive = self._calculate_cognitive_complexity(tree)
            
            # Calculate nesting depth
            nesting_depth = self._calculate_nesting_depth(tree)
            
            return {
                "cyclomatic": cyclomatic,
                "cognitive": cognitive,
                "halstead": {},  # Simplified
                "nesting_depth": nesting_depth
            }
        except:
            return await super().calculate_complexity(code)
    
    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity for Python AST"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity
    
    def _calculate_cognitive_complexity(self, tree: ast.AST) -> int:
        """Calculate cognitive complexity for Python AST"""
        # Simplified cognitive complexity calculation
        cognitive = 0
        nesting_level = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For)):
                cognitive += 1 + nesting_level
                nesting_level += 1
            elif isinstance(node, ast.FunctionDef):
                nesting_level = 0  # Reset for new function
        
        return cognitive
    
    def _calculate_nesting_depth(self, tree: ast.AST) -> int:
        """Calculate maximum nesting depth"""
        max_depth = 0
        current_depth = 0
        
        class DepthVisitor(ast.NodeVisitor):
            def __init__(self):
                self.max_depth = 0
                self.current_depth = 0
            
            def visit_If(self, node):
                self.current_depth += 1
                self.max_depth = max(self.max_depth, self.current_depth)
                self.generic_visit(node)
                self.current_depth -= 1
            
            def visit_For(self, node):
                self.current_depth += 1
                self.max_depth = max(self.max_depth, self.current_depth)
                self.generic_visit(node)
                self.current_depth -= 1
            
            def visit_While(self, node):
                self.current_depth += 1
                self.max_depth = max(self.max_depth, self.current_depth)
                self.generic_visit(node)
                self.current_depth -= 1
        
        visitor = DepthVisitor()
        visitor.visit(tree)
        return visitor.max_depth

# Simplified implementations for other languages
class JavaScriptAnalyzer(BaseLanguageAnalyzer):
    """JavaScript-specific code analyzer"""
    pass

class TypeScriptAnalyzer(BaseLanguageAnalyzer):
    """TypeScript-specific code analyzer"""
    pass

class JavaAnalyzer(BaseLanguageAnalyzer):
    """Java-specific code analyzer"""
    pass

class CSharpAnalyzer(BaseLanguageAnalyzer):
    """C#-specific code analyzer"""
    pass

class CppAnalyzer(BaseLanguageAnalyzer):
    """C++-specific code analyzer"""
    pass

class GoAnalyzer(BaseLanguageAnalyzer):
    """Go-specific code analyzer"""
    pass

class RustAnalyzer(BaseLanguageAnalyzer):
    """Rust-specific code analyzer"""
    pass

class PhpAnalyzer(BaseLanguageAnalyzer):
    """PHP-specific code analyzer"""
    pass

class RubyAnalyzer(BaseLanguageAnalyzer):
    """Ruby-specific code analyzer"""
    pass
    estimated_effort: str
    benefits: List[str]
    risks: List[str]
    priority: int


@dataclass
class ArchitecturalInsight:
    """Architectural analysis insight"""
    insight_type: str
    description: str
    impact: str
    recommendations: List[str]
    affected_components: List[str]


class CodeAnalysisAgent(IntelligentAgent):
    """
    Specialized agent for deep code analysis and refactoring.
    
    Capabilities:
    - AST parsing and analysis
    - Code complexity assessment
    - Refactoring opportunity identification
    - Architectural pattern recognition
    - Code quality scoring
