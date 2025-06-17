"""
reVoAgent - Revolutionary Agentic Coding System Platform

A modular, extensible platform that integrates the best features from leading AI coding agents:
- SWE-agent: Agent-Computer Interface for autonomous software engineering
- OpenHands: Multi-modal AI agents with collaborative capabilities
- browser-use: AI-powered browser automation and web interaction
- OpenManus: General AI agent framework with workflow management
"""

__version__ = "1.0.0"
__author__ = "reVoAgent Team"
__email__ = "team@revoagent.dev"
__license__ = "MIT"

from .core.framework import AgentFramework
from .core.config import Config
from .agents.base import BaseAgent
from .agents.code_generator import CodeGeneratorAgent
from .agents.browser_agent import BrowserAgent
from .agents.debugging_agent import DebuggingAgent
from .agents.testing_agent import TestingAgent

__all__ = [
    "AgentFramework",
    "Config",
    "BaseAgent",
    "CodeGeneratorAgent", 
    "BrowserAgent",
    "DebuggingAgent",
    "TestingAgent",
]