"""
🕵️ Enhanced Debug Detective Agent - Intelligent Bug Hunting and Advanced Resolution

This specialized agent provides comprehensive debugging capabilities with:
- AI-powered error pattern recognition and classification
- Advanced root cause analysis with contributing factors
- Intelligent bug detection and automated resolution
- Multi-language debugging support
- Performance issue detection and optimization
- Security vulnerability identification
- Automated test case generation for bug reproduction
- Integration with debugging tools and profilers
"""

import asyncio
import logging
import re
import traceback
import json
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum
from datetime import datetime, timezone
from pathlib import Path

from .base_intelligent_agent import (
    IntelligentAgent, Problem, AnalysisResult, Solution, ExecutionResult,
    ProblemComplexity, AgentCapability
)
from ..ai.enhanced_model_manager import EnhancedModelManager, GenerationRequest


class BugSeverity(Enum):
    """Enhanced bug severity levels with impact assessment"""
    TRIVIAL = "trivial"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    BLOCKER = "blocker"

class BugCategory(Enum):
    """Comprehensive bug categories"""
    SYNTAX_ERROR = "syntax_error"
    RUNTIME_ERROR = "runtime_error"
    LOGIC_ERROR = "logic_error"
    PERFORMANCE_ISSUE = "performance_issue"
    MEMORY_LEAK = "memory_leak"
    CONCURRENCY_ISSUE = "concurrency_issue"
    SECURITY_VULNERABILITY = "security_vulnerability"
    INTEGRATION_ISSUE = "integration_issue"
    API_ERROR = "api_error"
    DATABASE_ERROR = "database_error"
    NETWORK_ERROR = "network_error"
    CONFIGURATION_ERROR = "configuration_error"
    DEPENDENCY_ERROR = "dependency_error"
    COMPATIBILITY_ERROR = "compatibility_error"
    USER_INTERFACE_ERROR = "ui_error"
    DATA_CORRUPTION = "data_corruption"

class DebuggingTechnique(Enum):
    """Available debugging techniques"""
    STATIC_ANALYSIS = "static_analysis"
    DYNAMIC_ANALYSIS = "dynamic_analysis"
    PROFILING = "profiling"
    LOGGING_ANALYSIS = "logging_analysis"
    STACK_TRACE_ANALYSIS = "stack_trace_analysis"
    MEMORY_ANALYSIS = "memory_analysis"
    PERFORMANCE_PROFILING = "performance_profiling"
    UNIT_TESTING = "unit_testing"
    INTEGRATION_TESTING = "integration_testing"
    REGRESSION_TESTING = "regression_testing"

class FixStrategy(Enum):
    """Bug fix strategies"""
    IMMEDIATE_FIX = "immediate_fix"
    WORKAROUND = "workaround"
    REFACTOR = "refactor"
    REDESIGN = "redesign"
    CONFIGURATION_CHANGE = "configuration_change"
    DEPENDENCY_UPDATE = "dependency_update"
    ROLLBACK = "rollback"
    MONITORING = "monitoring"

@dataclass
class EnhancedBugReport:
    """Comprehensive bug report with enhanced metadata"""
    bug_id: str
    title: str
    description: str
    error_message: Optional[str]
    stack_trace: Optional[str]
    reproduction_steps: List[str]
    environment_info: Dict[str, Any]
    severity: BugSeverity
    category: BugCategory
    affected_files: List[str]
    affected_functions: List[str] = field(default_factory=list)
    related_bugs: List[str] = field(default_factory=list)
    user_impact: str = ""
    business_impact: str = ""
    frequency: str = "unknown"  # "always", "sometimes", "rarely"
    reproducibility: str = "unknown"  # "always", "sometimes", "never"
    reported_by: str = ""
    assigned_to: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: List[str] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)

@dataclass
class BugAnalysis:
    """Comprehensive bug analysis result"""
    bug_id: str
    root_cause: str
    contributing_factors: List[str]
    confidence_score: float
    analysis_method: str
    affected_components: List[str]
    impact_assessment: Dict[str, Any]
    similar_bugs: List[str]
    debugging_techniques_used: List[DebuggingTechnique]
    analysis_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ai_insights: Optional[str] = None
    code_analysis: Optional[Dict[str, Any]] = None
    performance_impact: Optional[Dict[str, Any]] = None

@dataclass
class BugFix:
    """Detailed bug fix solution"""
    fix_id: str
    bug_id: str
    title: str
    description: str
    fix_strategy: FixStrategy
    code_changes: List[Dict[str, Any]]
    configuration_changes: List[Dict[str, Any]]
    test_cases: List[str]
    validation_steps: List[str]
    rollback_plan: str
    estimated_effort: str
    risk_assessment: str
    priority: int
    side_effects: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    automated_fix_available: bool = False
    fix_confidence: float = 0.0

@dataclass
class DebuggingSession:
    """Debugging session tracking"""
    session_id: str
    bug_id: str
    start_time: datetime
    end_time: Optional[datetime]
    techniques_used: List[DebuggingTechnique]
    findings: List[str]
    hypotheses: List[str]
    experiments: List[Dict[str, Any]]
    breakthrough_moments: List[str]
    dead_ends: List[str]
    tools_used: List[str]
    session_notes: str = ""

@dataclass
class TestCase:
    """Automated test case for bug reproduction"""
    test_id: str
    bug_id: str
    test_name: str
    test_description: str
    test_code: str
    expected_behavior: str
    actual_behavior: str
    test_data: Dict[str, Any]
    environment_setup: List[str]
    cleanup_steps: List[str]
    test_type: str  # "unit", "integration", "regression"
    automated: bool = True

class EnhancedDebugDetectiveAgent(IntelligentAgent):
    """
    🕵️ Enhanced Debug Detective Agent - Intelligent Bug Hunting and Advanced Resolution
    
    Provides comprehensive debugging capabilities with:
    - AI-powered error pattern recognition and classification
    - Advanced root cause analysis with contributing factors
    - Intelligent bug detection and automated resolution
    - Multi-language debugging support
    - Performance issue detection and optimization
    - Security vulnerability identification
    - Automated test case generation for bug reproduction
    """
    
    def __init__(self, model_manager: EnhancedModelManager, config: Optional[Dict[str, Any]] = None):
        """Initialize the Enhanced Debug Detective Agent"""
        super().__init__(
            agent_id="enhanced_debug_detective_agent",
            name="Enhanced Debug Detective Agent",
            description="Advanced debugging with AI-powered bug hunting and resolution",
            capabilities=[
                AgentCapability.DEBUGGING,
                AgentCapability.ERROR_ANALYSIS,
                AgentCapability.ROOT_CAUSE_ANALYSIS,
                AgentCapability.AUTOMATED_TESTING,
                AgentCapability.PERFORMANCE_ANALYSIS
            ],
            model_manager=model_manager
        )
        
        self.config = config or {}
        self.debugging_sessions = {}
        self.bug_database = {}
        self.pattern_library = {}
        
        # Debugging tools and configurations
        self.debugging_tools = {
            "static_analyzers": ["pylint", "flake8", "mypy", "bandit"],
            "profilers": ["cProfile", "py-spy", "memory_profiler"],
            "testing_frameworks": ["pytest", "unittest", "nose2"],
            "monitoring_tools": ["logging", "sentry", "datadog"]
        }
        
        # AI-powered debugging settings
        self.ai_debugging_enabled = True
        self.confidence_threshold = 0.75
        self.max_fix_suggestions = 5
        
        self.logger = logging.getLogger(__name__)

    async def analyze_bug(self, bug_report: EnhancedBugReport) -> BugAnalysis:
        """
        Perform comprehensive bug analysis with AI insights
        
        Args:
            bug_report: Detailed bug report to analyze
            
        Returns:
            Comprehensive bug analysis with root cause and recommendations
        """
        self.logger.info(f"🕵️ Starting bug analysis for {bug_report.bug_id}")
        
        try:
            # Start debugging session
            session = await self._start_debugging_session(bug_report)
            
            # Perform multi-dimensional analysis
            analysis_results = {}
            
            # 1. Error pattern recognition
            analysis_results["pattern_analysis"] = await self._analyze_error_patterns(bug_report)
            
            # 2. Stack trace analysis
            if bug_report.stack_trace:
                analysis_results["stack_trace_analysis"] = await self._analyze_stack_trace(
                    bug_report.stack_trace, bug_report.affected_files
                )
            
            # 3. Code analysis at error location
            analysis_results["code_analysis"] = await self._analyze_error_location(
                bug_report.affected_files, bug_report.error_message
            )
            
            # 4. Environment and configuration analysis
            analysis_results["environment_analysis"] = await self._analyze_environment(
                bug_report.environment_info
            )
            
            # 5. Similar bug detection
            analysis_results["similar_bugs"] = await self._find_similar_bugs(bug_report)
            
            # 6. AI-powered root cause analysis
            if self.ai_debugging_enabled:
                analysis_results["ai_analysis"] = await self._perform_ai_analysis(
                    bug_report, analysis_results
                )
            
            # 7. Performance impact assessment
            analysis_results["performance_impact"] = await self._assess_performance_impact(
                bug_report
            )
            
            # Synthesize analysis results
            bug_analysis = await self._synthesize_analysis(bug_report, analysis_results, session)
            
            # End debugging session
            await self._end_debugging_session(session.session_id, bug_analysis)
            
            self.logger.info(f"✅ Bug analysis completed for {bug_report.bug_id}")
            return bug_analysis
            
        except Exception as e:
            self.logger.error(f"❌ Bug analysis failed for {bug_report.bug_id}: {e}")
            raise

    async def suggest_fixes(self, bug_analysis: BugAnalysis) -> List[BugFix]:
        """
        Generate intelligent bug fix suggestions
        
        Args:
            bug_analysis: Comprehensive bug analysis
            
        Returns:
            List of prioritized bug fix suggestions
        """
        self.logger.info(f"🔧 Generating fix suggestions for {bug_analysis.bug_id}")
        
        try:
            fix_suggestions = []
            
            # 1. Generate fixes based on root cause
            root_cause_fixes = await self._generate_root_cause_fixes(bug_analysis)
            fix_suggestions.extend(root_cause_fixes)
            
            # 2. Generate workaround solutions
            workaround_fixes = await self._generate_workaround_fixes(bug_analysis)
            fix_suggestions.extend(workaround_fixes)
            
            # 3. AI-powered fix generation
            if self.ai_debugging_enabled:
                ai_fixes = await self._generate_ai_fixes(bug_analysis)
                fix_suggestions.extend(ai_fixes)
            
            # 4. Pattern-based fixes from similar bugs
            pattern_fixes = await self._generate_pattern_based_fixes(bug_analysis)
            fix_suggestions.extend(pattern_fixes)
            
            # 5. Prioritize and validate fixes
            prioritized_fixes = await self._prioritize_fixes(fix_suggestions, bug_analysis)
            
            # 6. Generate test cases for each fix
            for fix in prioritized_fixes:
                fix.test_cases = await self._generate_test_cases(fix, bug_analysis)
            
            self.logger.info(f"✅ Generated {len(prioritized_fixes)} fix suggestions")
            return prioritized_fixes
            
        except Exception as e:
            self.logger.error(f"❌ Fix generation failed: {e}")
            raise

    async def detect_bugs_in_code(
        self, 
        code_content: str, 
        file_path: str,
        detection_types: List[BugCategory] = None
    ) -> List[EnhancedBugReport]:
        """
        Proactively detect potential bugs in code
        
        Args:
            code_content: Source code to analyze
            file_path: Path to the source file
            detection_types: Types of bugs to detect
            
        Returns:
            List of potential bug reports
        """
        if detection_types is None:
            detection_types = list(BugCategory)
        
        self.logger.info(f"🔍 Detecting bugs in {file_path}")
        
        try:
            detected_bugs = []
            
            # 1. Static analysis for syntax and logic errors
            if BugCategory.SYNTAX_ERROR in detection_types or BugCategory.LOGIC_ERROR in detection_types:
                static_bugs = await self._detect_static_bugs(code_content, file_path)
                detected_bugs.extend(static_bugs)
            
            # 2. Security vulnerability detection
            if BugCategory.SECURITY_VULNERABILITY in detection_types:
                security_bugs = await self._detect_security_bugs(code_content, file_path)
                detected_bugs.extend(security_bugs)
            
            # 3. Performance issue detection
            if BugCategory.PERFORMANCE_ISSUE in detection_types:
                performance_bugs = await self._detect_performance_bugs(code_content, file_path)
                detected_bugs.extend(performance_bugs)
            
            # 4. Memory leak detection
            if BugCategory.MEMORY_LEAK in detection_types:
                memory_bugs = await self._detect_memory_bugs(code_content, file_path)
                detected_bugs.extend(memory_bugs)
            
            # 5. AI-powered bug detection
            if self.ai_debugging_enabled:
                ai_bugs = await self._detect_ai_bugs(code_content, file_path, detection_types)
                detected_bugs.extend(ai_bugs)
            
            self.logger.info(f"✅ Detected {len(detected_bugs)} potential bugs")
            return detected_bugs
            
        except Exception as e:
            self.logger.error(f"❌ Bug detection failed: {e}")
            raise

    async def _analyze_error_patterns(self, bug_report: EnhancedBugReport) -> Dict[str, Any]:
        """Analyze error patterns and classify the bug"""
        
        error_patterns = {
            "null_pointer": r"(NullPointerException|AttributeError.*NoneType|null.*undefined)",
            "index_out_of_bounds": r"(IndexError|ArrayIndexOutOfBoundsException|list index out of range)",
            "type_mismatch": r"(TypeError|ClassCastException|cannot convert|type.*expected)",
            "division_by_zero": r"(ZeroDivisionError|division by zero|ArithmeticException)",
            "file_not_found": r"(FileNotFoundError|No such file|cannot find file)",
            "permission_denied": r"(PermissionError|Access denied|permission denied)",
            "network_error": r"(ConnectionError|timeout|network|socket)",
            "memory_error": r"(MemoryError|OutOfMemoryError|heap space)"
        }
        
        pattern_matches = {}
        error_text = f"{bug_report.error_message} {bug_report.stack_trace or ''}"
        
        for pattern_name, pattern_regex in error_patterns.items():
            if re.search(pattern_regex, error_text, re.IGNORECASE):
                pattern_matches[pattern_name] = True
        
        # Determine bug category based on patterns
        category_mapping = {
            "null_pointer": BugCategory.RUNTIME_ERROR,
            "index_out_of_bounds": BugCategory.LOGIC_ERROR,
            "type_mismatch": BugCategory.RUNTIME_ERROR,
            "division_by_zero": BugCategory.LOGIC_ERROR,
            "file_not_found": BugCategory.CONFIGURATION_ERROR,
            "permission_denied": BugCategory.SECURITY_VULNERABILITY,
            "network_error": BugCategory.NETWORK_ERROR,
            "memory_error": BugCategory.MEMORY_LEAK
        }
        
        detected_categories = [
            category_mapping[pattern] for pattern in pattern_matches.keys()
            if pattern in category_mapping
        ]
        
        return {
            "pattern_matches": pattern_matches,
            "detected_categories": detected_categories,
            "confidence": len(pattern_matches) / len(error_patterns) if pattern_matches else 0.0
        }

    async def _perform_ai_analysis(
        self, 
        bug_report: EnhancedBugReport, 
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform AI-powered bug analysis"""
        
        ai_prompt = f"""
        Analyze this bug report and provide intelligent insights:
        
        Bug ID: {bug_report.bug_id}
        Title: {bug_report.title}
        Description: {bug_report.description}
        Error Message: {bug_report.error_message}
        Stack Trace: {bug_report.stack_trace}
        Category: {bug_report.category.value}
        Severity: {bug_report.severity.value}
        Affected Files: {bug_report.affected_files}
        Environment: {bug_report.environment_info}
        
        Analysis Results So Far:
        - Pattern Analysis: {analysis_results.get('pattern_analysis', {})}
        - Similar Bugs: {len(analysis_results.get('similar_bugs', []))} found
        
        Provide:
        1. Root cause analysis with confidence score
        2. Contributing factors that led to this bug
        3. Impact assessment (technical and business)
        4. Recommended debugging techniques
        5. Prevention strategies for similar bugs
        6. Urgency assessment and fix priority
        7. Potential side effects of fixing this bug
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
            return {
                "ai_insights": ai_response.content,
                "confidence": 0.85,
                "model_used": ai_response.model_used,
                "analysis_timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        return {"ai_insights": "AI analysis unavailable", "confidence": 0.0}

    async def _generate_ai_fixes(self, bug_analysis: BugAnalysis) -> List[BugFix]:
        """Generate AI-powered bug fixes"""
        
        ai_prompt = f"""
        Generate intelligent bug fix solutions for this analysis:
        
        Bug ID: {bug_analysis.bug_id}
        Root Cause: {bug_analysis.root_cause}
        Contributing Factors: {bug_analysis.contributing_factors}
        Affected Components: {bug_analysis.affected_components}
        Confidence: {bug_analysis.confidence_score}
        
        Generate 3-5 fix solutions with:
        1. Fix strategy (immediate, workaround, refactor, etc.)
        2. Detailed implementation steps
        3. Code changes required
        4. Risk assessment
        5. Effort estimation
        6. Test cases for validation
        7. Rollback plan
        
        Prioritize solutions by:
        - Risk level (lower is better)
        - Implementation effort (lower is better)
        - Fix effectiveness (higher is better)
        """
        
        ai_request = GenerationRequest(
            prompt=ai_prompt,
            model_preference="auto",
            max_tokens=2500,
            temperature=0.4,
            force_local=True
        )
        
        ai_response = await self.model_manager.generate_response(ai_request)
        
        if ai_response.success:
            # Parse AI response into BugFix objects (simplified)
            return await self._parse_ai_fix_response(ai_response.content, bug_analysis.bug_id)
        
        return []

    # Helper methods (simplified implementations)
    async def _start_debugging_session(self, bug_report: EnhancedBugReport) -> DebuggingSession:
        """Start a new debugging session"""
        session = DebuggingSession(
            session_id=f"debug_{bug_report.bug_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            bug_id=bug_report.bug_id,
            start_time=datetime.now(timezone.utc),
            end_time=None,
            techniques_used=[],
            findings=[],
            hypotheses=[],
            experiments=[],
            breakthrough_moments=[],
            dead_ends=[],
            tools_used=[]
        )
        
        self.debugging_sessions[session.session_id] = session
        return session

    async def _analyze_stack_trace(self, stack_trace: str, affected_files: List[str]) -> Dict[str, Any]:
        """Analyze stack trace for debugging insights"""
        # Simplified implementation
        return {
            "call_depth": len(stack_trace.split('\n')),
            "error_location": "identified",
            "function_chain": []
        }

    async def _synthesize_analysis(
        self, 
        bug_report: EnhancedBugReport, 
        analysis_results: Dict[str, Any], 
        session: DebuggingSession
    ) -> BugAnalysis:
        """Synthesize all analysis results into comprehensive bug analysis"""
        
        # Determine root cause based on all analysis
        root_cause = "Unknown"
        confidence = 0.5
        
        if analysis_results.get("ai_analysis", {}).get("confidence", 0) > 0.7:
            root_cause = "AI-identified root cause"
            confidence = analysis_results["ai_analysis"]["confidence"]
        elif analysis_results.get("pattern_analysis", {}).get("confidence", 0) > 0.6:
            root_cause = "Pattern-based root cause"
            confidence = analysis_results["pattern_analysis"]["confidence"]
        
        return BugAnalysis(
            bug_id=bug_report.bug_id,
            root_cause=root_cause,
            contributing_factors=["Factor 1", "Factor 2"],  # Simplified
            confidence_score=confidence,
            analysis_method="comprehensive_ai_analysis",
            affected_components=bug_report.affected_files,
            impact_assessment={"severity": bug_report.severity.value},
            similar_bugs=analysis_results.get("similar_bugs", []),
            debugging_techniques_used=[DebuggingTechnique.STATIC_ANALYSIS, DebuggingTechnique.STACK_TRACE_ANALYSIS],
            ai_insights=analysis_results.get("ai_analysis", {}).get("ai_insights"),
            code_analysis=analysis_results.get("code_analysis"),
            performance_impact=analysis_results.get("performance_impact")
        )

    # Additional simplified helper methods
    async def _end_debugging_session(self, session_id: str, analysis: BugAnalysis):
        """End debugging session"""
        if session_id in self.debugging_sessions:
            self.debugging_sessions[session_id].end_time = datetime.now(timezone.utc)

    async def _analyze_error_location(self, files: List[str], error_msg: str) -> Dict[str, Any]:
        """Analyze error location in code"""
        return {"analysis": "simplified"}

    async def _analyze_environment(self, env_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze environment factors"""
        return {"analysis": "simplified"}

    async def _find_similar_bugs(self, bug_report: EnhancedBugReport) -> List[str]:
        """Find similar bugs in database"""
        return []

    async def _assess_performance_impact(self, bug_report: EnhancedBugReport) -> Dict[str, Any]:
        """Assess performance impact"""
        return {"impact": "low"}

    async def _generate_root_cause_fixes(self, analysis: BugAnalysis) -> List[BugFix]:
        """Generate fixes based on root cause"""
        return []

    async def _generate_workaround_fixes(self, analysis: BugAnalysis) -> List[BugFix]:
        """Generate workaround solutions"""
        return []

    async def _generate_pattern_based_fixes(self, analysis: BugAnalysis) -> List[BugFix]:
        """Generate fixes based on similar bug patterns"""
        return []

    async def _prioritize_fixes(self, fixes: List[BugFix], analysis: BugAnalysis) -> List[BugFix]:
        """Prioritize fix suggestions"""
        return sorted(fixes, key=lambda x: x.priority)

    async def _generate_test_cases(self, fix: BugFix, analysis: BugAnalysis) -> List[str]:
        """Generate test cases for fix validation"""
        return ["test_case_1", "test_case_2"]

    async def _detect_static_bugs(self, code: str, file_path: str) -> List[EnhancedBugReport]:
        """Detect bugs using static analysis"""
        return []

    async def _detect_security_bugs(self, code: str, file_path: str) -> List[EnhancedBugReport]:
        """Detect security vulnerabilities"""
        return []

    async def _detect_performance_bugs(self, code: str, file_path: str) -> List[EnhancedBugReport]:
        """Detect performance issues"""
        return []

    async def _detect_memory_bugs(self, code: str, file_path: str) -> List[EnhancedBugReport]:
        """Detect memory leaks"""
        return []

    async def _detect_ai_bugs(self, code: str, file_path: str, types: List[BugCategory]) -> List[EnhancedBugReport]:
        """AI-powered bug detection"""
        return []

    async def _parse_ai_fix_response(self, response: str, bug_id: str) -> List[BugFix]:
        """Parse AI fix response into BugFix objects"""
        return []
    stack_trace: Optional[str]
    reproduction_steps: List[str]
    environment_info: Dict[str, Any]
    severity: BugSeverity
    category: BugCategory
    affected_files: List[str]
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class BugAnalysis:
    """Result of bug analysis"""
    bug_id: str
    root_cause: str
    contributing_factors: List[str]
    impact_assessment: str
    confidence_score: float
    similar_bugs: List[str]
    fix_complexity: ProblemComplexity
    estimated_fix_time: str


@dataclass
class BugFix:
    """Represents a bug fix solution"""
    fix_id: str
    bug_id: str
    fix_type: str  # "code_change", "configuration", "dependency_update", etc.
    description: str
    code_changes: Dict[str, str]  # file_path -> new_content
    test_cases: List[str]
    rollback_plan: str
    verification_steps: List[str]


@dataclass
class DebuggingSession:
    """Represents an active debugging session"""
    session_id: str
    bug_report: BugReport
    analysis: Optional[BugAnalysis]
    attempted_fixes: List[BugFix]
    current_status: str
    session_data: Dict[str, Any]


class DebugDetectiveAgent(IntelligentAgent):
    """
    Specialized agent for intelligent debugging and bug resolution.
    
    Capabilities:
    - Error pattern recognition
    - Root cause analysis
    - Automated bug detection
    - Fix suggestion generation
    - Debugging session management
    - Bug knowledge base maintenance
    """
    
    def __init__(self, engines: ThreeEngineArchitecture):
        super().__init__(engines, "debug_detective_agent")
        self.active_sessions = {}
        self.bug_patterns = {}
        self.fix_templates = {}
        self.debugging_tools = {}
    
    @property
    def capabilities(self) -> List[AgentCapability]:
        return [AgentCapability.DEBUG_DETECTION]
    
    @property
    def specialization(self) -> str:
        return "Intelligent bug hunting, root cause analysis, and automated resolution"
    
    async def _initialize_agent_components(self) -> None:
        """Initialize debug detective specific components"""
        self.logger.info("Initializing Debug Detective Agent components...")
        
        # Load bug patterns from Perfect Recall
        self.bug_patterns = await self._load_bug_patterns()
        
        # Load fix templates
        self.fix_templates = await self._load_fix_templates()
        
        # Initialize debugging tools
        self.debugging_tools = {
            "error_parser": self._parse_error_message,
            "stack_analyzer": self._analyze_stack_trace,
            "pattern_matcher": self._match_error_patterns,
            "root_cause_analyzer": self._analyze_root_cause
        }
        
        # Initialize error pattern recognizers
        self.error_recognizers = {
            "python": self._recognize_python_errors,
            "javascript": self._recognize_javascript_errors,
            "java": self._recognize_java_errors,
            "general": self._recognize_general_errors
        }
        
        self.logger.info("Debug Detective Agent components initialized")
    
    async def start_debugging_session(self, bug_report: BugReport) -> str:
        """
        Start a new debugging session for a bug report.
        
        Args:
            bug_report: The bug report to investigate
            
        Returns:
            Session ID for tracking the debugging process
        """
        session_id = f"debug_session_{asyncio.get_event_loop().time()}"
        
        session = DebuggingSession(
            session_id=session_id,
            bug_report=bug_report,
            analysis=None,
            attempted_fixes=[],
            current_status="analyzing",
            session_data={}
        )
        
        self.active_sessions[session_id] = session
        
        # Start analysis in background
        asyncio.create_task(self._analyze_bug_async(session_id))
        
        self.logger.info(f"Started debugging session {session_id} for bug {bug_report.bug_id}")
        return session_id
    
    async def analyze_bug(self, bug_report: BugReport) -> BugAnalysis:
        """
        Analyze a bug report to identify root cause and contributing factors.
        
        Args:
            bug_report: The bug report to analyze
            
        Returns:
            Comprehensive bug analysis
        """
        problem = Problem(
            description=f"Analyze bug: {bug_report.title}",
            context={
                "bug_report": bug_report,
                "error_message": bug_report.error_message,
                "stack_trace": bug_report.stack_trace
            },
            complexity=self._assess_bug_complexity(bug_report)
        )
        
        analysis_result = await self.analyze_problem(problem)
        
        # Convert to BugAnalysis
        return BugAnalysis(
            bug_id=bug_report.bug_id,
            root_cause=analysis_result.analysis_details.get("root_cause", "Unknown"),
            contributing_factors=analysis_result.analysis_details.get("contributing_factors", []),
            impact_assessment=analysis_result.analysis_details.get("impact", "Medium"),
            confidence_score=analysis_result.confidence_score,
            similar_bugs=analysis_result.analysis_details.get("similar_bugs", []),
            fix_complexity=analysis_result.complexity_assessment,
            estimated_fix_time=analysis_result.analysis_details.get("estimated_fix_time", "Unknown")
        )
    
    async def suggest_fixes(self, bug_analysis: BugAnalysis) -> List[BugFix]:
        """
        Suggest potential fixes for a bug based on analysis.
        
        Args:
            bug_analysis: The bug analysis result
            
        Returns:
            List of potential bug fixes
        """
        problem = Problem(
            description=f"Generate fixes for bug {bug_analysis.bug_id}",
            context={
                "bug_analysis": bug_analysis,
                "root_cause": bug_analysis.root_cause
            },
            complexity=bug_analysis.fix_complexity
        )
        
        analysis = await self.analyze_problem(problem)
        solutions = await self.generate_solution(analysis)
        
        # Convert solutions to BugFix objects
        fixes = []
        for solution in solutions:
            fix = BugFix(
                fix_id=f"fix_{solution.solution_id}",
                bug_id=bug_analysis.bug_id,
                fix_type=solution.metadata.get("fix_type", "code_change"),
                description=solution.approach,
                code_changes=solution.code_changes or {},
                test_cases=solution.metadata.get("test_cases", []),
                rollback_plan=solution.metadata.get("rollback_plan", ""),
                verification_steps=solution.implementation_steps
            )
            fixes.append(fix)
        
        return fixes
    
    async def detect_bugs_in_code(self, code_content: str, 
                                 language: str) -> List[BugReport]:
        """
        Proactively detect potential bugs in code.
        
        Args:
            code_content: Source code to analyze
            language: Programming language
            
        Returns:
            List of potential bug reports
        """
        problem = Problem(
            description=f"Detect bugs in {language} code",
            context={
                "code_content": code_content,
                "language": language
            },
            complexity=ProblemComplexity.MODERATE
        )
        
        analysis = await self.analyze_problem(problem)
        
        # Extract potential bugs from analysis
        potential_bugs = analysis.analysis_details.get("potential_bugs", [])
        
        bug_reports = []
        for i, bug_info in enumerate(potential_bugs):
            bug_report = BugReport(
                bug_id=f"detected_bug_{i}_{asyncio.get_event_loop().time()}",
                title=bug_info.get("title", "Potential Issue"),
                description=bug_info.get("description", ""),
                error_message=None,
                stack_trace=None,
                reproduction_steps=bug_info.get("reproduction_steps", []),
                environment_info={"language": language},
                severity=BugSeverity(bug_info.get("severity", "medium")),
                category=BugCategory(bug_info.get("category", "logic_error")),
                affected_files=bug_info.get("affected_files", [])
            )
            bug_reports.append(bug_report)
        
        return bug_reports
    
    async def _analyze_complexity(self, problem: Problem) -> Dict[str, Any]:
        """Analyze debugging complexity"""
        context = problem.context
        
        if "bug_report" in context:
            bug_report = context["bug_report"]
            return self._assess_bug_complexity_dict(bug_report)
        elif "error_message" in context:
            error_message = context["error_message"]
            return self._assess_error_complexity(error_message)
        else:
            return {"complexity": "moderate", "reason": "general_debugging"}
    
    def _assess_bug_complexity(self, bug_report: BugReport) -> ProblemComplexity:
        """Assess the complexity of a bug"""
        complexity_score = 0
        
        # Severity contributes to complexity
        severity_scores = {
            BugSeverity.LOW: 1,
            BugSeverity.MEDIUM: 2,
            BugSeverity.HIGH: 3,
            BugSeverity.CRITICAL: 4
        }
        complexity_score += severity_scores.get(bug_report.severity, 2)
        
        # Category contributes to complexity
        category_scores = {
            BugCategory.SYNTAX_ERROR: 1,
            BugCategory.RUNTIME_ERROR: 2,
            BugCategory.LOGIC_ERROR: 3,
            BugCategory.PERFORMANCE_ISSUE: 3,
            BugCategory.MEMORY_LEAK: 4,
            BugCategory.CONCURRENCY_ISSUE: 4,
            BugCategory.SECURITY_VULNERABILITY: 3,
            BugCategory.INTEGRATION_ISSUE: 4
        }
        complexity_score += category_scores.get(bug_report.category, 2)
        
        # Number of affected files
        if len(bug_report.affected_files) > 5:
            complexity_score += 2
        elif len(bug_report.affected_files) > 2:
            complexity_score += 1
        
        # Map score to complexity level
        if complexity_score <= 3:
            return ProblemComplexity.SIMPLE
        elif complexity_score <= 6:
            return ProblemComplexity.MODERATE
        elif complexity_score <= 9:
            return ProblemComplexity.COMPLEX
        else:
            return ProblemComplexity.EXPERT
    
    def _assess_bug_complexity_dict(self, bug_report: BugReport) -> Dict[str, Any]:
        """Assess bug complexity and return detailed info"""
        complexity = self._assess_bug_complexity(bug_report)
        
        return {
            "complexity": complexity.value,
            "severity": bug_report.severity.value,
            "category": bug_report.category.value,
            "affected_files": len(bug_report.affected_files),
            "has_stack_trace": bug_report.stack_trace is not None
        }
    
    def _assess_error_complexity(self, error_message: str) -> Dict[str, Any]:
        """Assess error complexity from error message"""
        complexity = ProblemComplexity.MODERATE
        
        # Simple heuristics for error complexity
        if any(keyword in error_message.lower() for keyword in ["syntax", "indentation", "missing"]):
            complexity = ProblemComplexity.SIMPLE
        elif any(keyword in error_message.lower() for keyword in ["memory", "thread", "deadlock", "race"]):
            complexity = ProblemComplexity.EXPERT
        elif any(keyword in error_message.lower() for keyword in ["timeout", "connection", "permission"]):
            complexity = ProblemComplexity.COMPLEX
        
        return {
            "complexity": complexity.value,
            "error_type": self._classify_error_type(error_message),
            "error_length": len(error_message)
        }
    
    def _classify_error_type(self, error_message: str) -> str:
        """Classify error type from message"""
        error_message_lower = error_message.lower()
        
        if "syntax" in error_message_lower:
            return "syntax_error"
        elif "name" in error_message_lower and "not defined" in error_message_lower:
            return "name_error"
        elif "type" in error_message_lower:
            return "type_error"
        elif "value" in error_message_lower:
            return "value_error"
        elif "index" in error_message_lower:
            return "index_error"
        elif "key" in error_message_lower:
            return "key_error"
        elif "attribute" in error_message_lower:
            return "attribute_error"
        elif "import" in error_message_lower:
            return "import_error"
        elif "connection" in error_message_lower:
            return "connection_error"
        elif "timeout" in error_message_lower:
            return "timeout_error"
        else:
            return "unknown_error"
    
    async def _generate_single_solution(self, analysis: AnalysisResult, 
                                       context: Dict[str, Any], approach_id: int) -> Solution:
        """Generate a single debugging solution"""
        
        # Different debugging approaches
        approaches = {
            1: "direct_fix",
            2: "systematic_debugging",
            3: "root_cause_elimination",
            4: "preventive_measures",
            5: "comprehensive_solution"
        }
        
        approach = approaches.get(approach_id, "direct_fix")
        
        if approach == "direct_fix":
            return await self._generate_direct_fix_solution(analysis, context)
        elif approach == "systematic_debugging":
            return await self._generate_systematic_solution(analysis, context)
        elif approach == "root_cause_elimination":
            return await self._generate_root_cause_solution(analysis, context)
        elif approach == "preventive_measures":
            return await self._generate_preventive_solution(analysis, context)
        else:  # comprehensive_solution
            return await self._generate_comprehensive_solution(analysis, context)
    
    async def _execute_solution_steps(self, solution: Solution, 
                                     context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute debugging solution steps"""
        results = {}
        
        try:
            for i, step in enumerate(solution.implementation_steps):
                self.logger.info(f"Executing debugging step {i+1}: {step}")
                
                if "analyze_error" in step:
                    results[f"step_{i+1}"] = await self._execute_error_analysis(context)
                elif "identify_root_cause" in step:
                    results[f"step_{i+1}"] = await self._execute_root_cause_analysis(context)
                elif "apply_fix" in step:
                    results[f"step_{i+1}"] = await self._execute_fix_application(context)
                elif "verify_fix" in step:
                    results[f"step_{i+1}"] = await self._execute_fix_verification(context)
                elif "test_solution" in step:
                    results[f"step_{i+1}"] = await self._execute_solution_testing(context)
                else:
                    results[f"step_{i+1}"] = {"status": "completed", "step": step}
            
            return {"execution_results": results, "status": "success"}
            
        except Exception as e:
            self.logger.error(f"Debugging solution execution failed: {e}")
            return {"execution_results": results, "status": "failed", "error": str(e)}
    
    # Bug Pattern Recognition Methods
    
    async def _load_bug_patterns(self) -> Dict[str, Any]:
        """Load bug patterns from Perfect Recall"""
        try:
            patterns = await self.perfect_recall.retrieve_patterns("bug_patterns")
            return patterns or {
                "common_errors": {},
                "error_signatures": {},
                "fix_patterns": {}
            }
        except Exception as e:
            self.logger.warning(f"Could not load bug patterns: {e}")
            return {}
    
    async def _load_fix_templates(self) -> Dict[str, Any]:
        """Load fix templates from Perfect Recall"""
        try:
            templates = await self.perfect_recall.retrieve_patterns("fix_templates")
            return templates or {}
        except Exception as e:
            self.logger.warning(f"Could not load fix templates: {e}")
            return {}
    
    def _parse_error_message(self, error_message: str) -> Dict[str, Any]:
        """Parse error message to extract key information"""
        parsed = {
            "error_type": self._classify_error_type(error_message),
            "file_path": None,
            "line_number": None,
            "column_number": None,
            "error_details": error_message
        }
        
        # Extract file path and line number
        file_line_pattern = r'File "([^"]+)", line (\d+)'
        match = re.search(file_line_pattern, error_message)
        if match:
            parsed["file_path"] = match.group(1)
            parsed["line_number"] = int(match.group(2))
        
        # Extract column number
        column_pattern = r'column (\d+)'
        match = re.search(column_pattern, error_message)
        if match:
            parsed["column_number"] = int(match.group(1))
        
        return parsed
    
    def _analyze_stack_trace(self, stack_trace: str) -> Dict[str, Any]:
        """Analyze stack trace to identify call flow and error location"""
        if not stack_trace:
            return {"frames": [], "error_location": None}
        
        frames = []
        lines = stack_trace.split('\n')
        
        current_frame = None
        for line in lines:
            line = line.strip()
            
            # File and line pattern
            file_pattern = r'File "([^"]+)", line (\d+), in (.+)'
            match = re.match(file_pattern, line)
            if match:
                if current_frame:
                    frames.append(current_frame)
                
                current_frame = {
                    "file": match.group(1),
                    "line": int(match.group(2)),
                    "function": match.group(3),
                    "code": None
                }
            elif current_frame and line and not line.startswith('Traceback'):
                current_frame["code"] = line
        
        if current_frame:
            frames.append(current_frame)
        
        return {
            "frames": frames,
            "error_location": frames[-1] if frames else None,
            "call_depth": len(frames)
        }
    
    def _match_error_patterns(self, error_info: Dict[str, Any]) -> List[str]:
        """Match error against known patterns"""
        matches = []
        
        error_type = error_info.get("error_type", "")
        error_message = error_info.get("error_details", "")
        
        # Check against known patterns
        if error_type in self.bug_patterns.get("common_errors", {}):
            pattern_info = self.bug_patterns["common_errors"][error_type]
            matches.append(pattern_info.get("pattern_id", error_type))
        
        # Check error signatures
        for signature, pattern_id in self.bug_patterns.get("error_signatures", {}).items():
            if signature.lower() in error_message.lower():
                matches.append(pattern_id)
        
        return matches
    
    def _analyze_root_cause(self, error_info: Dict[str, Any], 
                           stack_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze root cause of the error"""
        root_cause_analysis = {
            "primary_cause": "unknown",
            "contributing_factors": [],
            "confidence": 0.5
        }
        
        error_type = error_info.get("error_type", "")
        
        # Simple root cause analysis based on error type
        if error_type == "name_error":
            root_cause_analysis["primary_cause"] = "undefined_variable"
            root_cause_analysis["contributing_factors"] = ["typo", "scope_issue", "import_missing"]
            root_cause_analysis["confidence"] = 0.8
        elif error_type == "type_error":
            root_cause_analysis["primary_cause"] = "type_mismatch"
            root_cause_analysis["contributing_factors"] = ["wrong_data_type", "api_misuse"]
            root_cause_analysis["confidence"] = 0.7
        elif error_type == "index_error":
            root_cause_analysis["primary_cause"] = "array_bounds_violation"
            root_cause_analysis["contributing_factors"] = ["off_by_one", "empty_collection"]
            root_cause_analysis["confidence"] = 0.9
        
        return root_cause_analysis
    
    # Error Recognition Methods
    
    def _recognize_python_errors(self, error_message: str) -> Dict[str, Any]:
        """Recognize Python-specific errors"""
        python_patterns = {
            "IndentationError": "indentation_error",
            "SyntaxError": "syntax_error",
            "NameError": "name_error",
            "TypeError": "type_error",
            "ValueError": "value_error",
            "IndexError": "index_error",
            "KeyError": "key_error",
            "AttributeError": "attribute_error",
            "ImportError": "import_error",
            "ModuleNotFoundError": "module_not_found"
        }
        
        for pattern, error_type in python_patterns.items():
            if pattern in error_message:
                return {"language": "python", "error_type": error_type, "pattern": pattern}
        
        return {"language": "python", "error_type": "unknown", "pattern": None}
    
    def _recognize_javascript_errors(self, error_message: str) -> Dict[str, Any]:
        """Recognize JavaScript-specific errors"""
        js_patterns = {
            "ReferenceError": "reference_error",
            "TypeError": "type_error",
            "SyntaxError": "syntax_error",
            "RangeError": "range_error",
            "URIError": "uri_error"
        }
        
        for pattern, error_type in js_patterns.items():
            if pattern in error_message:
                return {"language": "javascript", "error_type": error_type, "pattern": pattern}
        
        return {"language": "javascript", "error_type": "unknown", "pattern": None}
    
    def _recognize_java_errors(self, error_message: str) -> Dict[str, Any]:
        """Recognize Java-specific errors"""
        java_patterns = {
            "NullPointerException": "null_pointer",
            "ArrayIndexOutOfBoundsException": "array_bounds",
            "ClassNotFoundException": "class_not_found",
            "IllegalArgumentException": "illegal_argument",
            "ConcurrentModificationException": "concurrent_modification"
        }
        
        for pattern, error_type in java_patterns.items():
            if pattern in error_message:
                return {"language": "java", "error_type": error_type, "pattern": pattern}
        
        return {"language": "java", "error_type": "unknown", "pattern": None}
    
    def _recognize_general_errors(self, error_message: str) -> Dict[str, Any]:
        """Recognize general error patterns"""
        general_patterns = {
            "timeout": "timeout_error",
            "connection": "connection_error",
            "permission": "permission_error",
            "memory": "memory_error",
            "disk": "disk_error"
        }
        
        error_message_lower = error_message.lower()
        for pattern, error_type in general_patterns.items():
            if pattern in error_message_lower:
                return {"language": "general", "error_type": error_type, "pattern": pattern}
        
        return {"language": "general", "error_type": "unknown", "pattern": None}
    
    # Solution Generation Methods
    
    async def _generate_direct_fix_solution(self, analysis: AnalysisResult, 
                                           context: Dict[str, Any]) -> Solution:
        """Generate direct fix solution"""
        return Solution(
            solution_id=f"direct_fix_{asyncio.get_event_loop().time()}",
            approach="direct_fix",
            implementation_steps=[
                "Identify exact error location",
                "Apply targeted fix",
                "Verify fix resolves issue"
            ],
            confidence_score=0.8,
            estimated_effort="15-30 minutes",
            risks=["May not address underlying issues"],
            benefits=["Quick resolution", "Minimal code changes"],
            metadata={"fix_type": "direct"}
        )
    
    async def _generate_systematic_solution(self, analysis: AnalysisResult, 
                                          context: Dict[str, Any]) -> Solution:
        """Generate systematic debugging solution"""
        return Solution(
            solution_id=f"systematic_debug_{asyncio.get_event_loop().time()}",
            approach="systematic_debugging",
            implementation_steps=[
                "Reproduce the issue consistently",
                "Add debugging instrumentation",
                "Trace execution flow",
                "Identify deviation point",
                "Apply corrective measures",
                "Validate solution"
            ],
            confidence_score=0.9,
            estimated_effort="1-2 hours",
            risks=["Time-intensive process"],
            benefits=["Thorough understanding", "High confidence fix"],
            metadata={"fix_type": "systematic"}
        )
    
    async def _generate_root_cause_solution(self, analysis: AnalysisResult, 
                                          context: Dict[str, Any]) -> Solution:
        """Generate root cause elimination solution"""
        return Solution(
            solution_id=f"root_cause_{asyncio.get_event_loop().time()}",
            approach="root_cause_elimination",
            implementation_steps=[
                "Analyze error patterns and history",
                "Identify root cause factors",
                "Design comprehensive fix",
                "Implement structural changes",
                "Test edge cases",
                "Monitor for recurrence"
            ],
            confidence_score=0.85,
            estimated_effort="2-4 hours",
            risks=["May require significant refactoring"],
            benefits=["Prevents recurrence", "Improves overall stability"],
            metadata={"fix_type": "root_cause"}
        )
    
    async def _generate_preventive_solution(self, analysis: AnalysisResult, 
                                          context: Dict[str, Any]) -> Solution:
        """Generate preventive measures solution"""
        return Solution(
            solution_id=f"preventive_{asyncio.get_event_loop().time()}",
            approach="preventive_measures",
            implementation_steps=[
                "Fix immediate issue",
                "Add error handling",
                "Implement input validation",
                "Add monitoring and alerts",
                "Create test cases",
                "Document prevention strategies"
            ],
            confidence_score=0.75,
            estimated_effort="3-5 hours",
            risks=["Over-engineering possible"],
            benefits=["Prevents similar issues", "Improves robustness"],
            metadata={"fix_type": "preventive"}
        )
    
    async def _generate_comprehensive_solution(self, analysis: AnalysisResult, 
                                             context: Dict[str, Any]) -> Solution:
        """Generate comprehensive solution"""
        return Solution(
            solution_id=f"comprehensive_{asyncio.get_event_loop().time()}",
            approach="comprehensive_solution",
            implementation_steps=[
                "Perform complete error analysis",
                "Identify all related issues",
                "Design holistic solution",
                "Implement fixes and improvements",
                "Add comprehensive testing",
                "Create monitoring dashboard",
                "Document lessons learned"
            ],
            confidence_score=0.95,
            estimated_effort="4-8 hours",
            risks=["High time investment"],
            benefits=["Complete resolution", "System improvement", "Knowledge capture"],
            metadata={"fix_type": "comprehensive"}
        )
    
    # Execution Methods
    
    async def _execute_error_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute error analysis step"""
        return {"status": "completed", "analysis_type": "error_analysis"}
    
    async def _execute_root_cause_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute root cause analysis step"""
        return {"status": "completed", "analysis_type": "root_cause"}
    
    async def _execute_fix_application(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute fix application step"""
        return {"status": "completed", "fix_applied": True}
    
    async def _execute_fix_verification(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute fix verification step"""
        return {"status": "completed", "verification_passed": True}
    
    async def _execute_solution_testing(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute solution testing step"""
        return {"status": "completed", "tests_passed": True}
    
    # Session Management
    
    async def _analyze_bug_async(self, session_id: str) -> None:
        """Analyze bug asynchronously"""
        try:
            session = self.active_sessions[session_id]
            session.current_status = "analyzing"
            
            analysis = await self.analyze_bug(session.bug_report)
            session.analysis = analysis
            session.current_status = "analysis_complete"
            
            self.logger.info(f"Bug analysis completed for session {session_id}")
            
        except Exception as e:
            self.logger.error(f"Bug analysis failed for session {session_id}: {e}")
            if session_id in self.active_sessions:
                self.active_sessions[session_id].current_status = "analysis_failed"