"""
Platform Core - Core System Management Components

This module provides the foundational components for platform operation:
- Workflow Engine: Orchestrates complex multi-agent workflows
- Project Manager: Handles project organization and lifecycle
- Resource Manager: Optimizes system resource utilization
- Configuration Manager: Manages system and user preferences
"""

from .workflow_engine import WorkflowEngine, Workflow, WorkflowStep
from .project_manager import ProjectManager, Project, ProjectType
from .resource_manager import ResourceManager, ResourceMonitor
from .configuration_manager import ConfigurationManager

__all__ = [
    'WorkflowEngine',
    'Workflow', 
    'WorkflowStep',
    'ProjectManager',
    'Project',
    'ProjectType',
    'ResourceManager',
    'ResourceMonitor',
    'ConfigurationManager'
]