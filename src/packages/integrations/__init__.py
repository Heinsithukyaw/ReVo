"""
External Integrations Package
GitHub, Slack, JIRA, and other enterprise integrations
"""

from .external_integrations import (
    ExternalIntegrationsManager,
    GitHubIntegration,
    SlackIntegration,
    JIRAIntegration,
    IntegrationConfig
)

__all__ = [
    'ExternalIntegrationsManager',
    'GitHubIntegration',
    'SlackIntegration', 
    'JIRAIntegration',
    'IntegrationConfig'
]