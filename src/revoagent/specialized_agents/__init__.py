"""
Specialized Agents - Phase 4 Intelligent Agent Ecosystem

This module provides the Phase 4 specialized agents with advanced capabilities:
- Base Intelligent Agent: Foundation for all specialized agents
- Code Analysis Agent: Deep code understanding and refactoring
- Debug Detective Agent: Intelligent bug hunting and resolution
- Architecture Advisor Agent: System design and optimization recommendations
- Performance Optimizer Agent: Automated performance tuning
- Security Auditor Agent: Comprehensive security analysis and fixes
- Workflow Intelligence: Multi-step problem solving and agent coordination
- Agent Dashboard: Real-time monitoring and control interface
"""

# Phase 4 Specialized Agents
from .base_intelligent_agent import (
    IntelligentAgent, Problem, AnalysisResult, Solution, ExecutionResult,
    ProblemComplexity, AgentCapability
)
from .code_analysis_agent import CodeAnalysisAgent, CodeMetrics, CodeIssue, RefactoringOpportunity
from .debug_detective_agent import (
    DebugDetectiveAgent, BugReport, BugAnalysis, BugFix, DebuggingSession,
    BugSeverity, BugCategory
)
from .architecture_advisor_agent import (
    ArchitectureAdvisorAgent, ArchitecturalAssessment, DesignRecommendation, RefactoringPlan,
    ArchitecturalPattern, ArchitecturalConcern
)
from .performance_optimizer_agent import (
    PerformanceOptimizerAgent, PerformanceProfile, PerformanceBottleneck, OptimizationRecommendation,
    PerformanceMetric, BottleneckType, OptimizationStrategy
)
from .security_auditor_agent import (
    SecurityAuditorAgent, SecurityAssessment, SecurityVulnerability, SecurityFix, ThreatModel,
    VulnerabilityType, SecuritySeverity, ComplianceStandard
)
from .workflow_intelligence import (
    WorkflowIntelligence, WorkflowDefinition, WorkflowExecution, AgentCollaboration,
    WorkflowType, WorkflowStatus, AgentRole
)
from .agent_dashboard import (
    AgentDashboard, DashboardState, AgentStatus, WorkflowMetrics, SystemAlert,
    DashboardMetric, AlertLevel
)

__all__ = [
    # Base Classes
    'IntelligentAgent',
    'Problem',
    'AnalysisResult', 
    'Solution',
    'ExecutionResult',
    'ProblemComplexity',
    'AgentCapability',
    
    # Code Analysis Agent
    'CodeAnalysisAgent',
    'CodeMetrics',
    'CodeIssue',
    'RefactoringOpportunity',
    
    # Debug Detective Agent
    'DebugDetectiveAgent',
    'BugReport',
    'BugAnalysis',
    'BugFix',
    'DebuggingSession',
    'BugSeverity',
    'BugCategory',
    
    # Architecture Advisor Agent
    'ArchitectureAdvisorAgent',
    'ArchitecturalAssessment',
    'DesignRecommendation',
    'RefactoringPlan',
    'ArchitecturalPattern',
    'ArchitecturalConcern',
    
    # Performance Optimizer Agent
    'PerformanceOptimizerAgent',
    'PerformanceProfile',
    'PerformanceBottleneck',
    'OptimizationRecommendation',
    'PerformanceMetric',
    'BottleneckType',
    'OptimizationStrategy',
    
    # Security Auditor Agent
    'SecurityAuditorAgent',
    'SecurityAssessment',
    'SecurityVulnerability',
    'SecurityFix',
    'ThreatModel',
    'VulnerabilityType',
    'SecuritySeverity',
    'ComplianceStandard',
    
    # Workflow Intelligence
    'WorkflowIntelligence',
    'WorkflowDefinition',
    'WorkflowExecution',
    'AgentCollaboration',
    'WorkflowType',
    'WorkflowStatus',
    'AgentRole',
    
    # Agent Dashboard
    'AgentDashboard',
    'DashboardState',
    'AgentStatus',
    'WorkflowMetrics',
    'SystemAlert',
    'DashboardMetric',
    'AlertLevel'
]