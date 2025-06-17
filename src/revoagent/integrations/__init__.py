"""
Integrations - External Platform and Service Integrations

This module provides integrations with external platforms and services:
- OpenHands: Multi-modal AI agent capabilities
- SWE-agent: Software engineering agent patterns
- browser-use: Browser automation
- All-Hands.dev: Cloud deployment and collaboration
"""

from .openhands_integration import OpenHandsIntegration
from .swe_agent_integration import SWEAgentIntegration
from .browser_use_integration import BrowserUseIntegration
from .allhands_integration import AllHandsIntegration

__all__ = [
    'OpenHandsIntegration',
    'SWEAgentIntegration', 
    'BrowserUseIntegration',
    'AllHandsIntegration'
]