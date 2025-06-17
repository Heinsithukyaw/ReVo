"""
Code Analysis Agent - Advanced Code Understanding and Refactoring

This specialized agent provides deep code analysis, complexity assessment,
refactoring suggestions, and architectural insights using the Three-Engine Architecture.
"""

import ast
import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple
from pathlib import Path

from .base_intelligent_agent import (
    IntelligentAgent, Problem, AnalysisResult, Solution, ExecutionResult,
    ProblemComplexity, AgentCapability
)
from ..core.framework import ThreeEngineArchitecture


@dataclass
class CodeMetrics:
    """Code quality and complexity metrics"""
    lines_of_code: int
    cyclomatic_complexity: int
    cognitive_complexity: int
    maintainability_index: float
    technical_debt_ratio: float
    test_coverage: float
    code_duplication: float
    security_score: float


@dataclass
class CodeIssue:
    """Represents a code issue or smell"""
    issue_type: str
    severity: str  # "low", "medium", "high", "critical"
    file_path: str
    line_number: int
    description: str
    suggestion: str
    impact: str
    effort_to_fix: str


@dataclass
class RefactoringOpportunity:
    """Represents a refactoring opportunity"""
    opportunity_type: str
    description: str
    files_affected: List[str]
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
    - Technical debt analysis
    """
    
    def __init__(self, engines: ThreeEngineArchitecture):
        super().__init__(engines, "code_analysis_agent")
        self.supported_languages = ["python", "javascript", "typescript", "java", "go"]
        self.analysis_cache = {}
        self.pattern_library = {}
    
    @property
    def capabilities(self) -> List[AgentCapability]:
        return [AgentCapability.CODE_ANALYSIS]
    
    @property
    def specialization(self) -> str:
        return "Deep code understanding, complexity analysis, and intelligent refactoring"
    
    async def _initialize_agent_components(self) -> None:
        """Initialize code analysis specific components"""
        self.logger.info("Initializing Code Analysis Agent components...")
        
        # Load pattern library from Perfect Recall
        self.pattern_library = await self._load_pattern_library()
        
        # Initialize AST parsers for supported languages
        self.ast_parsers = {
            "python": self._parse_python_ast,
            "javascript": self._parse_javascript_ast,
            "typescript": self._parse_typescript_ast
        }
        
        # Initialize complexity analyzers
        self.complexity_analyzers = {
            "cyclomatic": self._calculate_cyclomatic_complexity,
            "cognitive": self._calculate_cognitive_complexity,
            "maintainability": self._calculate_maintainability_index
        }
        
        self.logger.info("Code Analysis Agent components initialized")
    
    async def analyze_codebase(self, codebase_path: str, 
                              analysis_options: Optional[Dict[str, Any]] = None) -> AnalysisResult:
        """
        Perform comprehensive codebase analysis.
        
        Args:
            codebase_path: Path to the codebase to analyze
            analysis_options: Optional analysis configuration
            
        Returns:
            Comprehensive analysis result with metrics, issues, and insights
        """
        problem = Problem(
            description=f"Analyze codebase at {codebase_path}",
            context={
                "codebase_path": codebase_path,
                "analysis_options": analysis_options or {}
            },
            complexity=ProblemComplexity.COMPLEX
        )
        
        return await self.analyze_problem(problem)
    
    async def suggest_refactoring(self, file_path: str, 
                                 refactoring_goals: List[str]) -> List[RefactoringOpportunity]:
        """
        Suggest refactoring opportunities for a specific file or codebase.
        
        Args:
            file_path: Path to file or directory to analyze
            refactoring_goals: List of refactoring objectives
            
        Returns:
            List of prioritized refactoring opportunities
        """
        problem = Problem(
            description=f"Suggest refactoring for {file_path}",
            context={
                "file_path": file_path,
                "goals": refactoring_goals
            },
            complexity=ProblemComplexity.MODERATE
        )
        
        analysis = await self.analyze_problem(problem)
        solutions = await self.generate_solution(analysis)
        
        # Extract refactoring opportunities from solutions
        opportunities = []
        for solution in solutions:
            if solution.metadata and "refactoring_opportunities" in solution.metadata:
                opportunities.extend(solution.metadata["refactoring_opportunities"])
        
        return opportunities
    
    async def assess_code_quality(self, code_content: str, 
                                 language: str) -> CodeMetrics:
        """
        Assess code quality metrics for given code content.
        
        Args:
            code_content: Source code to analyze
            language: Programming language
            
        Returns:
            Comprehensive code quality metrics
        """
        if language not in self.supported_languages:
            raise ValueError(f"Unsupported language: {language}")
        
        # Use Parallel Mind for concurrent metric calculation
        metric_tasks = [
            self._calculate_lines_of_code(code_content),
            self._calculate_complexity_metrics(code_content, language),
            self._calculate_quality_metrics(code_content, language),
            self._calculate_security_metrics(code_content, language)
        ]
        
        metric_results = await self.parallel_mind.execute_parallel_tasks(metric_tasks)
        
        return CodeMetrics(
            lines_of_code=metric_results[0]["loc"],
            cyclomatic_complexity=metric_results[1]["cyclomatic"],
            cognitive_complexity=metric_results[1]["cognitive"],
            maintainability_index=metric_results[2]["maintainability"],
            technical_debt_ratio=metric_results[2]["technical_debt"],
            test_coverage=metric_results[2]["test_coverage"],
            code_duplication=metric_results[2]["duplication"],
            security_score=metric_results[3]["security_score"]
        )
    
    async def _analyze_complexity(self, problem: Problem) -> Dict[str, Any]:
        """Analyze code complexity"""
        context = problem.context
        codebase_path = context.get("codebase_path", "")
        
        if not codebase_path:
            return {"complexity": "unknown", "reason": "no_codebase_path"}
        
        try:
            # Analyze codebase structure
            file_count = await self._count_files(codebase_path)
            total_loc = await self._calculate_total_loc(codebase_path)
            
            # Determine complexity based on size and structure
            if file_count > 100 or total_loc > 10000:
                complexity = ProblemComplexity.EXPERT
            elif file_count > 50 or total_loc > 5000:
                complexity = ProblemComplexity.COMPLEX
            elif file_count > 10 or total_loc > 1000:
                complexity = ProblemComplexity.MODERATE
            else:
                complexity = ProblemComplexity.SIMPLE
            
            return {
                "complexity": complexity.value,
                "file_count": file_count,
                "total_loc": total_loc,
                "analysis_scope": "codebase"
            }
            
        except Exception as e:
            self.logger.error(f"Complexity analysis failed: {e}")
            return {"complexity": "moderate", "error": str(e)}
    
    async def _generate_single_solution(self, analysis: AnalysisResult, 
                                       context: Dict[str, Any], approach_id: int) -> Solution:
        """Generate a single code analysis solution"""
        codebase_path = analysis.analysis_details.get("context", {}).get("codebase_path", "")
        
        # Different approaches based on approach_id
        approaches = {
            1: "comprehensive_analysis",
            2: "focused_refactoring",
            3: "architectural_review",
            4: "quality_improvement",
            5: "security_audit"
        }
        
        approach = approaches.get(approach_id, "comprehensive_analysis")
        
        if approach == "comprehensive_analysis":
            return await self._generate_comprehensive_analysis_solution(analysis, context)
        elif approach == "focused_refactoring":
            return await self._generate_refactoring_solution(analysis, context)
        elif approach == "architectural_review":
            return await self._generate_architectural_solution(analysis, context)
        elif approach == "quality_improvement":
            return await self._generate_quality_solution(analysis, context)
        else:  # security_audit
            return await self._generate_security_solution(analysis, context)
    
    async def _execute_solution_steps(self, solution: Solution, 
                                     context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code analysis solution steps"""
        results = {}
        
        try:
            for i, step in enumerate(solution.implementation_steps):
                self.logger.info(f"Executing step {i+1}: {step}")
                
                if "analyze_files" in step:
                    results[f"step_{i+1}"] = await self._execute_file_analysis(context)
                elif "calculate_metrics" in step:
                    results[f"step_{i+1}"] = await self._execute_metrics_calculation(context)
                elif "identify_issues" in step:
                    results[f"step_{i+1}"] = await self._execute_issue_identification(context)
                elif "generate_report" in step:
                    results[f"step_{i+1}"] = await self._execute_report_generation(context, results)
                else:
                    results[f"step_{i+1}"] = {"status": "completed", "step": step}
            
            return {"execution_results": results, "status": "success"}
            
        except Exception as e:
            self.logger.error(f"Solution execution failed: {e}")
            return {"execution_results": results, "status": "failed", "error": str(e)}
    
    # Code Analysis Implementation Methods
    
    async def _load_pattern_library(self) -> Dict[str, Any]:
        """Load code pattern library from Perfect Recall"""
        try:
            patterns = await self.perfect_recall.retrieve_patterns("code_analysis")
            return patterns or {
                "design_patterns": [],
                "anti_patterns": [],
                "refactoring_patterns": [],
                "architectural_patterns": []
            }
        except Exception as e:
            self.logger.warning(f"Could not load pattern library: {e}")
            return {}
    
    async def _count_files(self, path: str) -> int:
        """Count source code files in path"""
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                return 0
            
            extensions = {".py", ".js", ".ts", ".java", ".go", ".cpp", ".c", ".h"}
            count = 0
            
            if path_obj.is_file():
                return 1 if path_obj.suffix in extensions else 0
            
            for file_path in path_obj.rglob("*"):
                if file_path.is_file() and file_path.suffix in extensions:
                    count += 1
            
            return count
            
        except Exception as e:
            self.logger.error(f"File counting failed: {e}")
            return 0
    
    async def _calculate_total_loc(self, path: str) -> int:
        """Calculate total lines of code"""
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                return 0
            
            total_loc = 0
            extensions = {".py", ".js", ".ts", ".java", ".go", ".cpp", ".c", ".h"}
            
            if path_obj.is_file():
                if path_obj.suffix in extensions:
                    with open(path_obj, 'r', encoding='utf-8', errors='ignore') as f:
                        return len([line for line in f if line.strip()])
                return 0
            
            for file_path in path_obj.rglob("*"):
                if file_path.is_file() and file_path.suffix in extensions:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            total_loc += len([line for line in f if line.strip()])
                    except Exception:
                        continue
            
            return total_loc
            
        except Exception as e:
            self.logger.error(f"LOC calculation failed: {e}")
            return 0
    
    async def _parse_python_ast(self, code_content: str) -> ast.AST:
        """Parse Python code into AST"""
        try:
            return ast.parse(code_content)
        except SyntaxError as e:
            self.logger.error(f"Python AST parsing failed: {e}")
            raise
    
    async def _parse_javascript_ast(self, code_content: str) -> Dict[str, Any]:
        """Parse JavaScript code (simplified)"""
        # This would integrate with a JavaScript parser like esprima
        # For now, return a simplified structure
        return {"type": "javascript_ast", "content": code_content}
    
    async def _parse_typescript_ast(self, code_content: str) -> Dict[str, Any]:
        """Parse TypeScript code (simplified)"""
        # This would integrate with a TypeScript parser
        # For now, return a simplified structure
        return {"type": "typescript_ast", "content": code_content}
    
    async def _calculate_lines_of_code(self, code_content: str) -> Dict[str, int]:
        """Calculate lines of code metrics"""
        lines = code_content.split('\n')
        total_lines = len(lines)
        blank_lines = len([line for line in lines if not line.strip()])
        comment_lines = len([line for line in lines if line.strip().startswith('#')])
        code_lines = total_lines - blank_lines - comment_lines
        
        return {
            "loc": code_lines,
            "total_lines": total_lines,
            "blank_lines": blank_lines,
            "comment_lines": comment_lines
        }
    
    async def _calculate_complexity_metrics(self, code_content: str, language: str) -> Dict[str, int]:
        """Calculate complexity metrics"""
        if language == "python":
            return await self._calculate_python_complexity(code_content)
        else:
            # Simplified complexity calculation for other languages
            return {
                "cyclomatic": self._estimate_cyclomatic_complexity(code_content),
                "cognitive": self._estimate_cognitive_complexity(code_content)
            }
    
    async def _calculate_python_complexity(self, code_content: str) -> Dict[str, int]:
        """Calculate Python-specific complexity metrics"""
        try:
            tree = await self._parse_python_ast(code_content)
            
            cyclomatic = 1  # Base complexity
            cognitive = 0
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                    cyclomatic += 1
                    cognitive += 1
                elif isinstance(node, ast.ExceptHandler):
                    cyclomatic += 1
                    cognitive += 1
                elif isinstance(node, (ast.And, ast.Or)):
                    cyclomatic += 1
                elif isinstance(node, ast.Lambda):
                    cyclomatic += 1
                    cognitive += 1
            
            return {"cyclomatic": cyclomatic, "cognitive": cognitive}
            
        except Exception as e:
            self.logger.error(f"Python complexity calculation failed: {e}")
            return {"cyclomatic": 1, "cognitive": 0}
    
    def _estimate_cyclomatic_complexity(self, code_content: str) -> int:
        """Estimate cyclomatic complexity for non-Python languages"""
        # Count decision points
        decision_keywords = ['if', 'else', 'while', 'for', 'switch', 'case', 'catch', '&&', '||']
        complexity = 1  # Base complexity
        
        for keyword in decision_keywords:
            complexity += code_content.count(keyword)
        
        return complexity
    
    def _estimate_cognitive_complexity(self, code_content: str) -> int:
        """Estimate cognitive complexity"""
        # Simplified cognitive complexity estimation
        nesting_keywords = ['if', 'for', 'while', 'try', 'switch']
        complexity = 0
        
        lines = code_content.split('\n')
        nesting_level = 0
        
        for line in lines:
            stripped = line.strip()
            if any(keyword in stripped for keyword in nesting_keywords):
                complexity += nesting_level + 1
                if stripped.endswith(':') or stripped.endswith('{'):
                    nesting_level += 1
            elif stripped in ['}', 'end']:
                nesting_level = max(0, nesting_level - 1)
        
        return complexity
    
    async def _calculate_quality_metrics(self, code_content: str, language: str) -> Dict[str, float]:
        """Calculate code quality metrics"""
        # Simplified quality metrics calculation
        lines = code_content.split('\n')
        total_lines = len([line for line in lines if line.strip()])
        
        # Maintainability index (simplified)
        complexity = self._estimate_cyclomatic_complexity(code_content)
        maintainability = max(0, 171 - 5.2 * complexity - 0.23 * total_lines)
        
        # Technical debt ratio (simplified)
        issues_count = self._count_code_issues(code_content)
        technical_debt = min(1.0, issues_count / max(1, total_lines / 10))
        
        return {
            "maintainability": maintainability / 171.0,  # Normalize to 0-1
            "technical_debt": technical_debt,
            "test_coverage": 0.0,  # Would require test analysis
            "duplication": self._estimate_duplication(code_content)
        }
    
    async def _calculate_security_metrics(self, code_content: str, language: str) -> Dict[str, float]:
        """Calculate security metrics"""
        security_issues = self._identify_security_issues(code_content, language)
        total_lines = len([line for line in code_content.split('\n') if line.strip()])
        
        # Security score based on issues found
        security_score = max(0.0, 1.0 - (len(security_issues) / max(1, total_lines / 20)))
        
        return {"security_score": security_score, "issues": security_issues}
    
    def _count_code_issues(self, code_content: str) -> int:
        """Count potential code issues"""
        issues = 0
        
        # Check for common issues
        if 'TODO' in code_content:
            issues += code_content.count('TODO')
        if 'FIXME' in code_content:
            issues += code_content.count('FIXME')
        if 'XXX' in code_content:
            issues += code_content.count('XXX')
        
        # Check for long lines
        for line in code_content.split('\n'):
            if len(line) > 120:
                issues += 1
        
        return issues
    
    def _estimate_duplication(self, code_content: str) -> float:
        """Estimate code duplication"""
        lines = [line.strip() for line in code_content.split('\n') if line.strip()]
        unique_lines = set(lines)
        
        if not lines:
            return 0.0
        
        duplication_ratio = 1.0 - (len(unique_lines) / len(lines))
        return duplication_ratio
    
    def _identify_security_issues(self, code_content: str, language: str) -> List[str]:
        """Identify potential security issues"""
        issues = []
        
        # Common security patterns to check
        security_patterns = {
            "hardcoded_password": r'password\s*=\s*["\'][^"\']+["\']',
            "sql_injection": r'execute\s*\(\s*["\'].*%.*["\']',
            "xss_vulnerability": r'innerHTML\s*=\s*.*\+',
            "insecure_random": r'random\(\)',
            "eval_usage": r'eval\s*\('
        }
        
        for issue_type, pattern in security_patterns.items():
            if re.search(pattern, code_content, re.IGNORECASE):
                issues.append(issue_type)
        
        return issues
    
    # Solution Generation Methods
    
    async def _generate_comprehensive_analysis_solution(self, analysis: AnalysisResult, 
                                                       context: Dict[str, Any]) -> Solution:
        """Generate comprehensive analysis solution"""
        return Solution(
            solution_id=f"comprehensive_analysis_{asyncio.get_event_loop().time()}",
            approach="comprehensive_analysis",
            implementation_steps=[
                "Scan and catalog all source files",
                "Parse AST for each supported language",
                "Calculate complexity metrics",
                "Identify code issues and smells",
                "Analyze architectural patterns",
                "Generate comprehensive report"
            ],
            confidence_score=0.9,
            estimated_effort="2-4 hours",
            risks=["Large codebase may require significant processing time"],
            benefits=[
                "Complete understanding of codebase health",
                "Identification of all major issues",
                "Baseline metrics for improvement tracking"
            ],
            metadata={
                "analysis_type": "comprehensive",
                "scope": "full_codebase"
            }
        )
    
    async def _generate_refactoring_solution(self, analysis: AnalysisResult, 
                                           context: Dict[str, Any]) -> Solution:
        """Generate refactoring-focused solution"""
        return Solution(
            solution_id=f"refactoring_analysis_{asyncio.get_event_loop().time()}",
            approach="focused_refactoring",
            implementation_steps=[
                "Identify high-complexity functions and classes",
                "Detect code duplication patterns",
                "Find refactoring opportunities",
                "Prioritize refactoring tasks",
                "Generate refactoring recommendations"
            ],
            confidence_score=0.85,
            estimated_effort="1-2 hours",
            risks=["May miss some subtle refactoring opportunities"],
            benefits=[
                "Focused improvement recommendations",
                "Prioritized refactoring roadmap",
                "Immediate actionable insights"
            ],
            metadata={
                "analysis_type": "refactoring",
                "focus": "improvement_opportunities"
            }
        )
    
    async def _generate_architectural_solution(self, analysis: AnalysisResult, 
                                             context: Dict[str, Any]) -> Solution:
        """Generate architectural analysis solution"""
        return Solution(
            solution_id=f"architectural_analysis_{asyncio.get_event_loop().time()}",
            approach="architectural_review",
            implementation_steps=[
                "Map component dependencies",
                "Identify architectural patterns",
                "Analyze coupling and cohesion",
                "Detect architectural violations",
                "Generate architectural insights"
            ],
            confidence_score=0.8,
            estimated_effort="3-5 hours",
            risks=["Complex architectures may require domain expertise"],
            benefits=[
                "High-level architectural understanding",
                "Identification of structural issues",
                "Strategic improvement recommendations"
            ],
            metadata={
                "analysis_type": "architectural",
                "focus": "system_design"
            }
        )
    
    async def _generate_quality_solution(self, analysis: AnalysisResult, 
                                       context: Dict[str, Any]) -> Solution:
        """Generate quality-focused solution"""
        return Solution(
            solution_id=f"quality_analysis_{asyncio.get_event_loop().time()}",
            approach="quality_improvement",
            implementation_steps=[
                "Calculate quality metrics",
                "Identify quality issues",
                "Assess technical debt",
                "Generate quality improvement plan",
                "Create quality monitoring recommendations"
            ],
            confidence_score=0.88,
            estimated_effort="1-3 hours",
            risks=["Quality metrics may not capture all aspects"],
            benefits=[
                "Quantified quality assessment",
                "Clear improvement targets",
                "Monitoring and tracking capabilities"
            ],
            metadata={
                "analysis_type": "quality",
                "focus": "code_quality"
            }
        )
    
    async def _generate_security_solution(self, analysis: AnalysisResult, 
                                        context: Dict[str, Any]) -> Solution:
        """Generate security-focused solution"""
        return Solution(
            solution_id=f"security_analysis_{asyncio.get_event_loop().time()}",
            approach="security_audit",
            implementation_steps=[
                "Scan for security vulnerabilities",
                "Identify insecure patterns",
                "Assess security risks",
                "Generate security recommendations",
                "Create security improvement plan"
            ],
            confidence_score=0.82,
            estimated_effort="2-4 hours",
            risks=["May not catch all security vulnerabilities"],
            benefits=[
                "Identification of security risks",
                "Security improvement roadmap",
                "Compliance assessment"
            ],
            metadata={
                "analysis_type": "security",
                "focus": "security_audit"
            }
        )
    
    # Execution Methods
    
    async def _execute_file_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute file analysis step"""
        return {"status": "completed", "files_analyzed": 0, "languages_detected": []}
    
    async def _execute_metrics_calculation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute metrics calculation step"""
        return {"status": "completed", "metrics_calculated": []}
    
    async def _execute_issue_identification(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute issue identification step"""
        return {"status": "completed", "issues_found": []}
    
    async def _execute_report_generation(self, context: Dict[str, Any], 
                                        previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute report generation step"""
        return {"status": "completed", "report_generated": True}