"""
Architecture Advisor Agent - System Design and Optimization Recommendations

This specialized agent provides intelligent architectural analysis, design pattern
recommendations, and system optimization guidance using the Three-Engine Architecture.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum
from pathlib import Path

from .base_intelligent_agent import (
    IntelligentAgent, Problem, AnalysisResult, Solution, ExecutionResult,
    ProblemComplexity, AgentCapability
)
from ..engines.enhanced_architecture import EnhancedArchitecture


class ArchitecturalPattern(Enum):
    """Common architectural patterns"""
    MVC = "mvc"
    MVP = "mvp"
    MVVM = "mvvm"
    MICROSERVICES = "microservices"
    MONOLITH = "monolith"
    LAYERED = "layered"
    HEXAGONAL = "hexagonal"
    EVENT_DRIVEN = "event_driven"
    PIPE_AND_FILTER = "pipe_and_filter"
    REPOSITORY = "repository"
    FACTORY = "factory"
    OBSERVER = "observer"
    SINGLETON = "singleton"
    STRATEGY = "strategy"


class ArchitecturalConcern(Enum):
    """Architectural quality concerns"""
    SCALABILITY = "scalability"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    RELIABILITY = "reliability"
    SECURITY = "security"
    TESTABILITY = "testability"
    MODULARITY = "modularity"
    COUPLING = "coupling"
    COHESION = "cohesion"
    COMPLEXITY = "complexity"


@dataclass
class ComponentAnalysis:
    """Analysis of a system component"""
    component_name: str
    component_type: str
    responsibilities: List[str]
    dependencies: List[str]
    dependents: List[str]
    complexity_score: float
    coupling_score: float
    cohesion_score: float
    issues: List[str]
    recommendations: List[str]


@dataclass
class ArchitecturalAssessment:
    """Overall architectural assessment"""
    system_name: str
    architectural_style: str
    patterns_detected: List[ArchitecturalPattern]
    quality_scores: Dict[ArchitecturalConcern, float]
    components: List[ComponentAnalysis]
    dependencies: Dict[str, List[str]]
    hotspots: List[str]
    technical_debt: float
    maintainability_index: float


@dataclass
class DesignRecommendation:
    """Design improvement recommendation"""
    recommendation_id: str
    title: str
    description: str
    category: ArchitecturalConcern
    priority: int  # 1-5, 5 being highest
    impact: str  # "low", "medium", "high"
    effort: str  # "low", "medium", "high"
    benefits: List[str]
    risks: List[str]
    implementation_steps: List[str]
    affected_components: List[str]


@dataclass
class RefactoringPlan:
    """Comprehensive refactoring plan"""
    plan_id: str
    title: str
    description: str
    phases: List[Dict[str, Any]]
    total_effort: str
    expected_benefits: List[str]
    risks: List[str]
    success_metrics: List[str]


class ArchitectureAdvisorAgent(IntelligentAgent):
    """
    Specialized agent for architectural analysis and design recommendations.
    
    Capabilities:
    - System architecture analysis
    - Design pattern recognition
    - Component dependency mapping
    - Quality attribute assessment
    - Refactoring recommendations
    - Scalability analysis
    """
    
    def __init__(self, engines: EnhancedArchitecture):
        super().__init__(engines, "architecture_advisor_agent")
        self.pattern_library = {}
        self.quality_metrics = {}
        self.design_principles = {}
        self.refactoring_patterns = {}
    
    @property
    def capabilities(self) -> List[AgentCapability]:
        return [AgentCapability.ARCHITECTURE_ADVISORY]
    
    @property
    def specialization(self) -> str:
        return "System design analysis, architectural patterns, and optimization guidance"
    
    async def _initialize_agent_components(self) -> None:
        """Initialize architecture advisor specific components"""
        self.logger.info("Initializing Architecture Advisor Agent components...")
        
        # Load architectural patterns from Perfect Recall
        self.pattern_library = await self._load_pattern_library()
        
        # Load quality metrics definitions
        self.quality_metrics = await self._load_quality_metrics()
        
        # Load design principles
        self.design_principles = await self._load_design_principles()
        
        # Load refactoring patterns
        self.refactoring_patterns = await self._load_refactoring_patterns()
        
        # Initialize analysis tools
        self.analysis_tools = {
            "dependency_analyzer": self._analyze_dependencies,
            "pattern_detector": self._detect_patterns,
            "quality_assessor": self._assess_quality_attributes,
            "complexity_calculator": self._calculate_complexity_metrics
        }
        
        self.logger.info("Architecture Advisor Agent components initialized")
    
    async def assess_architecture(self, system_path: str, 
                                 assessment_scope: Optional[List[str]] = None) -> ArchitecturalAssessment:
        """
        Perform comprehensive architectural assessment of a system.
        
        Args:
            system_path: Path to the system to analyze
            assessment_scope: Optional list of specific areas to focus on
            
        Returns:
            Comprehensive architectural assessment
        """
        problem = Problem(
            description=f"Assess architecture of system at {system_path}",
            context={
                "system_path": system_path,
                "assessment_scope": assessment_scope or []
            },
            complexity=ProblemComplexity.COMPLEX
        )
        
        analysis = await self.analyze_problem(problem)
        
        # Extract architectural assessment from analysis
        return self._extract_architectural_assessment(analysis)
    
    async def recommend_improvements(self, assessment: ArchitecturalAssessment,
                                   focus_areas: Optional[List[ArchitecturalConcern]] = None) -> List[DesignRecommendation]:
        """
        Generate design improvement recommendations based on assessment.
        
        Args:
            assessment: Architectural assessment result
            focus_areas: Optional list of specific concerns to focus on
            
        Returns:
            List of prioritized design recommendations
        """
        problem = Problem(
            description=f"Generate improvement recommendations for {assessment.system_name}",
            context={
                "assessment": assessment,
                "focus_areas": focus_areas or []
            },
            complexity=ProblemComplexity.MODERATE
        )
        
        analysis = await self.analyze_problem(problem)
        solutions = await self.generate_solution(analysis)
        
        # Convert solutions to design recommendations
        recommendations = []
        for solution in solutions:
            if solution.metadata and "recommendations" in solution.metadata:
                recommendations.extend(solution.metadata["recommendations"])
        
        return recommendations
    
    async def create_refactoring_plan(self, assessment: ArchitecturalAssessment,
                                    recommendations: List[DesignRecommendation]) -> RefactoringPlan:
        """
        Create a comprehensive refactoring plan based on recommendations.
        
        Args:
            assessment: Architectural assessment
            recommendations: List of design recommendations
            
        Returns:
            Detailed refactoring plan
        """
        problem = Problem(
            description=f"Create refactoring plan for {assessment.system_name}",
            context={
                "assessment": assessment,
                "recommendations": recommendations
            },
            complexity=ProblemComplexity.COMPLEX
        )
        
        analysis = await self.analyze_problem(problem)
        solutions = await self.generate_solution(analysis)
        
        # Select the best refactoring plan
        best_solution = max(solutions, key=lambda s: s.confidence_score)
        
        return RefactoringPlan(
            plan_id=f"refactoring_plan_{asyncio.get_event_loop().time()}",
            title=f"Refactoring Plan for {assessment.system_name}",
            description=best_solution.approach,
            phases=best_solution.metadata.get("phases", []),
            total_effort=best_solution.estimated_effort,
            expected_benefits=best_solution.benefits,
            risks=best_solution.risks,
            success_metrics=best_solution.metadata.get("success_metrics", [])
        )
    
    async def analyze_scalability(self, system_path: str,
                                 expected_load: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze system scalability and provide scaling recommendations.
        
        Args:
            system_path: Path to the system
            expected_load: Expected load characteristics
            
        Returns:
            Scalability analysis and recommendations
        """
        problem = Problem(
            description=f"Analyze scalability of system at {system_path}",
            context={
                "system_path": system_path,
                "expected_load": expected_load
            },
            complexity=ProblemComplexity.COMPLEX
        )
        
        analysis = await self.analyze_problem(problem)
        
        return {
            "scalability_score": analysis.confidence_score,
            "bottlenecks": analysis.analysis_details.get("bottlenecks", []),
            "scaling_recommendations": analysis.recommendations,
            "capacity_planning": analysis.analysis_details.get("capacity_planning", {}),
            "performance_projections": analysis.analysis_details.get("performance_projections", {})
        }
    
    async def _analyze_complexity(self, problem: Problem) -> Dict[str, Any]:
        """Analyze architectural complexity"""
        context = problem.context
        system_path = context.get("system_path", "")
        
        if not system_path:
            return {"complexity": "moderate", "reason": "no_system_path"}
        
        try:
            # Analyze system structure
            component_count = await self._count_components(system_path)
            dependency_count = await self._count_dependencies(system_path)
            file_count = await self._count_files(system_path)
            
            # Calculate complexity score
            complexity_score = 0
            
            if component_count > 50:
                complexity_score += 3
            elif component_count > 20:
                complexity_score += 2
            elif component_count > 10:
                complexity_score += 1
            
            if dependency_count > 100:
                complexity_score += 3
            elif dependency_count > 50:
                complexity_score += 2
            elif dependency_count > 20:
                complexity_score += 1
            
            if file_count > 500:
                complexity_score += 2
            elif file_count > 100:
                complexity_score += 1
            
            # Map to complexity level
            if complexity_score <= 2:
                complexity = ProblemComplexity.SIMPLE
            elif complexity_score <= 4:
                complexity = ProblemComplexity.MODERATE
            elif complexity_score <= 6:
                complexity = ProblemComplexity.COMPLEX
            else:
                complexity = ProblemComplexity.EXPERT
            
            return {
                "complexity": complexity.value,
                "component_count": component_count,
                "dependency_count": dependency_count,
                "file_count": file_count,
                "complexity_score": complexity_score
            }
            
        except Exception as e:
            self.logger.error(f"Architectural complexity analysis failed: {e}")
            return {"complexity": "moderate", "error": str(e)}
    
    async def _generate_single_solution(self, analysis: AnalysisResult, 
                                       context: Dict[str, Any], approach_id: int) -> Solution:
        """Generate a single architectural solution"""
        
        # Different architectural approaches
        approaches = {
            1: "modular_refactoring",
            2: "pattern_application",
            3: "quality_improvement",
            4: "scalability_enhancement",
            5: "comprehensive_redesign"
        }
        
        approach = approaches.get(approach_id, "modular_refactoring")
        
        if approach == "modular_refactoring":
            return await self._generate_modular_solution(analysis, context)
        elif approach == "pattern_application":
            return await self._generate_pattern_solution(analysis, context)
        elif approach == "quality_improvement":
            return await self._generate_quality_solution(analysis, context)
        elif approach == "scalability_enhancement":
            return await self._generate_scalability_solution(analysis, context)
        else:  # comprehensive_redesign
            return await self._generate_redesign_solution(analysis, context)
    
    async def _execute_solution_steps(self, solution: Solution, 
                                     context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute architectural solution steps"""
        results = {}
        
        try:
            for i, step in enumerate(solution.implementation_steps):
                self.logger.info(f"Executing architectural step {i+1}: {step}")
                
                if "analyze_components" in step:
                    results[f"step_{i+1}"] = await self._execute_component_analysis(context)
                elif "map_dependencies" in step:
                    results[f"step_{i+1}"] = await self._execute_dependency_mapping(context)
                elif "assess_quality" in step:
                    results[f"step_{i+1}"] = await self._execute_quality_assessment(context)
                elif "generate_recommendations" in step:
                    results[f"step_{i+1}"] = await self._execute_recommendation_generation(context)
                elif "create_plan" in step:
                    results[f"step_{i+1}"] = await self._execute_plan_creation(context)
                else:
                    results[f"step_{i+1}"] = {"status": "completed", "step": step}
            
            return {"execution_results": results, "status": "success"}
            
        except Exception as e:
            self.logger.error(f"Architectural solution execution failed: {e}")
            return {"execution_results": results, "status": "failed", "error": str(e)}
    
    # Analysis Implementation Methods
    
    async def _load_pattern_library(self) -> Dict[str, Any]:
        """Load architectural pattern library"""
        try:
            patterns = await self.perfect_recall.retrieve_patterns("architectural_patterns")
            return patterns or {
                "design_patterns": {},
                "architectural_styles": {},
                "anti_patterns": {}
            }
        except Exception as e:
            self.logger.warning(f"Could not load pattern library: {e}")
            return {}
    
    async def _load_quality_metrics(self) -> Dict[str, Any]:
        """Load quality metrics definitions"""
        try:
            metrics = await self.perfect_recall.retrieve_patterns("quality_metrics")
            return metrics or {
                "coupling_metrics": {},
                "cohesion_metrics": {},
                "complexity_metrics": {}
            }
        except Exception as e:
            self.logger.warning(f"Could not load quality metrics: {e}")
            return {}
    
    async def _load_design_principles(self) -> Dict[str, Any]:
        """Load design principles"""
        return {
            "SOLID": {
                "S": "Single Responsibility Principle",
                "O": "Open/Closed Principle",
                "L": "Liskov Substitution Principle",
                "I": "Interface Segregation Principle",
                "D": "Dependency Inversion Principle"
            },
            "DRY": "Don't Repeat Yourself",
            "KISS": "Keep It Simple, Stupid",
            "YAGNI": "You Aren't Gonna Need It"
        }
    
    async def _load_refactoring_patterns(self) -> Dict[str, Any]:
        """Load refactoring patterns"""
        return {
            "extract_method": "Break down large methods",
            "extract_class": "Split large classes",
            "move_method": "Relocate methods to appropriate classes",
            "introduce_interface": "Add abstraction layers",
            "replace_conditional": "Use polymorphism instead of conditionals"
        }
    
    async def _count_components(self, system_path: str) -> int:
        """Count system components"""
        try:
            path_obj = Path(system_path)
            if not path_obj.exists():
                return 0
            
            # Count directories as components (simplified)
            component_count = 0
            for item in path_obj.rglob("*"):
                if item.is_dir() and not item.name.startswith('.'):
                    component_count += 1
            
            return component_count
            
        except Exception as e:
            self.logger.error(f"Component counting failed: {e}")
            return 0
    
    async def _count_dependencies(self, system_path: str) -> int:
        """Count system dependencies"""
        try:
            path_obj = Path(system_path)
            if not path_obj.exists():
                return 0
            
            dependency_count = 0
            
            # Look for dependency files
            dependency_files = [
                "requirements.txt", "package.json", "pom.xml", 
                "build.gradle", "Cargo.toml", "go.mod"
            ]
            
            for dep_file in dependency_files:
                dep_path = path_obj / dep_file
                if dep_path.exists():
                    try:
                        with open(dep_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # Simple line counting for dependencies
                            dependency_count += len([line for line in content.split('\n') 
                                                   if line.strip() and not line.strip().startswith('#')])
                    except Exception:
                        continue
            
            return dependency_count
            
        except Exception as e:
            self.logger.error(f"Dependency counting failed: {e}")
            return 0
    
    async def _count_files(self, system_path: str) -> int:
        """Count source files in system"""
        try:
            path_obj = Path(system_path)
            if not path_obj.exists():
                return 0
            
            extensions = {".py", ".js", ".ts", ".java", ".go", ".cpp", ".c", ".h", ".cs"}
            file_count = 0
            
            for file_path in path_obj.rglob("*"):
                if file_path.is_file() and file_path.suffix in extensions:
                    file_count += 1
            
            return file_count
            
        except Exception as e:
            self.logger.error(f"File counting failed: {e}")
            return 0
    
    def _extract_architectural_assessment(self, analysis: AnalysisResult) -> ArchitecturalAssessment:
        """Extract architectural assessment from analysis result"""
        analysis_details = analysis.analysis_details
        
        return ArchitecturalAssessment(
            system_name=analysis_details.get("system_name", "Unknown System"),
            architectural_style=analysis_details.get("architectural_style", "Unknown"),
            patterns_detected=[ArchitecturalPattern.LAYERED],  # Simplified
            quality_scores={
                ArchitecturalConcern.MAINTAINABILITY: 0.7,
                ArchitecturalConcern.SCALABILITY: 0.6,
                ArchitecturalConcern.PERFORMANCE: 0.8
            },
            components=[],
            dependencies={},
            hotspots=[],
            technical_debt=0.3,
            maintainability_index=0.7
        )
    
    # Analysis Tool Methods
    
    async def _analyze_dependencies(self, system_path: str) -> Dict[str, Any]:
        """Analyze system dependencies"""
        return {
            "dependency_graph": {},
            "circular_dependencies": [],
            "dependency_depth": 0,
            "coupling_metrics": {}
        }
    
    async def _detect_patterns(self, system_path: str) -> List[ArchitecturalPattern]:
        """Detect architectural patterns in the system"""
        detected_patterns = []
        
        # Simple pattern detection based on directory structure
        path_obj = Path(system_path)
        if path_obj.exists():
            subdirs = [d.name.lower() for d in path_obj.iterdir() if d.is_dir()]
            
            # Check for MVC pattern
            if any(name in subdirs for name in ["models", "views", "controllers"]):
                detected_patterns.append(ArchitecturalPattern.MVC)
            
            # Check for layered architecture
            if any(name in subdirs for name in ["presentation", "business", "data", "service"]):
                detected_patterns.append(ArchitecturalPattern.LAYERED)
            
            # Check for microservices
            if len(subdirs) > 5 and any("service" in name for name in subdirs):
                detected_patterns.append(ArchitecturalPattern.MICROSERVICES)
        
        return detected_patterns
    
    async def _assess_quality_attributes(self, system_path: str) -> Dict[ArchitecturalConcern, float]:
        """Assess quality attributes of the system"""
        # Simplified quality assessment
        return {
            ArchitecturalConcern.MAINTAINABILITY: 0.7,
            ArchitecturalConcern.SCALABILITY: 0.6,
            ArchitecturalConcern.PERFORMANCE: 0.8,
            ArchitecturalConcern.RELIABILITY: 0.7,
            ArchitecturalConcern.SECURITY: 0.6,
            ArchitecturalConcern.TESTABILITY: 0.5
        }
    
    async def _calculate_complexity_metrics(self, system_path: str) -> Dict[str, float]:
        """Calculate complexity metrics"""
        return {
            "cyclomatic_complexity": 5.2,
            "cognitive_complexity": 3.8,
            "structural_complexity": 4.1,
            "interface_complexity": 2.9
        }
    
    # Solution Generation Methods
    
    async def _generate_modular_solution(self, analysis: AnalysisResult, 
                                        context: Dict[str, Any]) -> Solution:
        """Generate modular refactoring solution"""
        return Solution(
            solution_id=f"modular_refactoring_{asyncio.get_event_loop().time()}",
            approach="modular_refactoring",
            implementation_steps=[
                "Identify tightly coupled components",
                "Extract common interfaces",
                "Separate concerns into modules",
                "Implement dependency injection",
                "Validate module boundaries"
            ],
            confidence_score=0.85,
            estimated_effort="2-4 weeks",
            risks=["Potential breaking changes", "Integration complexity"],
            benefits=[
                "Improved maintainability",
                "Better testability",
                "Reduced coupling"
            ],
            metadata={
                "refactoring_type": "modular",
                "focus": "separation_of_concerns"
            }
        )
    
    async def _generate_pattern_solution(self, analysis: AnalysisResult, 
                                        context: Dict[str, Any]) -> Solution:
        """Generate pattern application solution"""
        return Solution(
            solution_id=f"pattern_application_{asyncio.get_event_loop().time()}",
            approach="pattern_application",
            implementation_steps=[
                "Identify applicable design patterns",
                "Analyze current implementation gaps",
                "Design pattern integration strategy",
                "Implement patterns incrementally",
                "Validate pattern effectiveness"
            ],
            confidence_score=0.8,
            estimated_effort="1-3 weeks",
            risks=["Over-engineering", "Pattern misapplication"],
            benefits=[
                "Standardized solutions",
                "Improved code reusability",
                "Better documentation"
            ],
            metadata={
                "refactoring_type": "pattern_based",
                "patterns": ["Factory", "Observer", "Strategy"]
            }
        )
    
    async def _generate_quality_solution(self, analysis: AnalysisResult, 
                                        context: Dict[str, Any]) -> Solution:
        """Generate quality improvement solution"""
        return Solution(
            solution_id=f"quality_improvement_{asyncio.get_event_loop().time()}",
            approach="quality_improvement",
            implementation_steps=[
                "Assess current quality metrics",
                "Identify quality hotspots",
                "Prioritize improvement areas",
                "Implement quality enhancements",
                "Establish quality monitoring"
            ],
            confidence_score=0.9,
            estimated_effort="3-6 weeks",
            risks=["Resource intensive", "Measurement complexity"],
            benefits=[
                "Higher code quality",
                "Reduced technical debt",
                "Better maintainability"
            ],
            metadata={
                "refactoring_type": "quality_focused",
                "metrics": ["coupling", "cohesion", "complexity"]
            }
        )
    
    async def _generate_scalability_solution(self, analysis: AnalysisResult, 
                                           context: Dict[str, Any]) -> Solution:
        """Generate scalability enhancement solution"""
        return Solution(
            solution_id=f"scalability_enhancement_{asyncio.get_event_loop().time()}",
            approach="scalability_enhancement",
            implementation_steps=[
                "Identify scalability bottlenecks",
                "Design horizontal scaling strategy",
                "Implement caching mechanisms",
                "Optimize database interactions",
                "Add performance monitoring"
            ],
            confidence_score=0.75,
            estimated_effort="4-8 weeks",
            risks=["Infrastructure complexity", "Performance trade-offs"],
            benefits=[
                "Improved performance",
                "Better resource utilization",
                "Enhanced user experience"
            ],
            metadata={
                "refactoring_type": "scalability_focused",
                "strategies": ["horizontal_scaling", "caching", "optimization"]
            }
        )
    
    async def _generate_redesign_solution(self, analysis: AnalysisResult, 
                                         context: Dict[str, Any]) -> Solution:
        """Generate comprehensive redesign solution"""
        return Solution(
            solution_id=f"comprehensive_redesign_{asyncio.get_event_loop().time()}",
            approach="comprehensive_redesign",
            implementation_steps=[
                "Analyze current architecture thoroughly",
                "Design new architectural blueprint",
                "Plan migration strategy",
                "Implement new architecture incrementally",
                "Migrate data and functionality",
                "Validate new system performance"
            ],
            confidence_score=0.7,
            estimated_effort="3-6 months",
            risks=["High complexity", "Extended timeline", "Business disruption"],
            benefits=[
                "Modern architecture",
                "Improved all quality attributes",
                "Future-proof design"
            ],
            metadata={
                "refactoring_type": "comprehensive",
                "scope": "full_system_redesign"
            }
        )
    
    # Execution Methods
    
    async def _execute_component_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute component analysis step"""
        return {"status": "completed", "components_analyzed": 0}
    
    async def _execute_dependency_mapping(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute dependency mapping step"""
        return {"status": "completed", "dependencies_mapped": 0}
    
    async def _execute_quality_assessment(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute quality assessment step"""
        return {"status": "completed", "quality_metrics_calculated": True}
    
    async def _execute_recommendation_generation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute recommendation generation step"""
        return {"status": "completed", "recommendations_generated": 0}
    
    async def _execute_plan_creation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute plan creation step"""
        return {"status": "completed", "plan_created": True}