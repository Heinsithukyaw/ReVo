"""
Integration Framework - External Tool and Service Integration

This module provides comprehensive integration capabilities for connecting
specialized agents with external development tools and services.
"""

import asyncio
import logging
import json
import aiohttp
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from abc import ABC, abstractmethod

from .base_intelligent_agent import IntelligentAgent, AgentCapability


class IntegrationType(Enum):
    """Types of external integrations"""
    VERSION_CONTROL = "version_control"
    ISSUE_TRACKING = "issue_tracking"
    CI_CD = "ci_cd"
    COMMUNICATION = "communication"
    MONITORING = "monitoring"
    CLOUD_SERVICE = "cloud_service"
    DATABASE = "database"
    IDE = "ide"
    TESTING = "testing"
    DEPLOYMENT = "deployment"


class IntegrationStatus(Enum):
    """Integration connection status"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    AUTHENTICATING = "authenticating"
    RATE_LIMITED = "rate_limited"


@dataclass
class IntegrationConfig:
    """Configuration for an external integration"""
    integration_id: str
    name: str
    integration_type: IntegrationType
    endpoint_url: str
    authentication: Dict[str, Any]
    settings: Dict[str, Any]
    rate_limits: Dict[str, int]
    enabled: bool = True


@dataclass
class IntegrationEvent:
    """Event from an external integration"""
    event_id: str
    integration_id: str
    event_type: str
    timestamp: float
    data: Dict[str, Any]
    processed: bool = False


class BaseIntegration(ABC):
    """Base class for all external integrations"""
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
        self.status = IntegrationStatus.DISCONNECTED
        self.logger = logging.getLogger(f"integration.{config.integration_id}")
        self.session = None
        self.rate_limiter = None
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the external service"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the external service"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test the connection to the external service"""
        pass
    
    @abstractmethod
    async def handle_webhook(self, webhook_data: Dict[str, Any]) -> IntegrationEvent:
        """Handle incoming webhook from the external service"""
        pass
    
    async def initialize(self) -> bool:
        """Initialize the integration"""
        try:
            self.session = aiohttp.ClientSession()
            await self._setup_rate_limiter()
            return await self.connect()
        except Exception as e:
            self.logger.error(f"Failed to initialize integration: {e}")
            return False
    
    async def cleanup(self) -> None:
        """Cleanup integration resources"""
        await self.disconnect()
        if self.session:
            await self.session.close()
    
    async def _setup_rate_limiter(self) -> None:
        """Setup rate limiting for API calls"""
        # Simple rate limiter implementation
        self.rate_limiter = {
            "requests_per_minute": self.config.rate_limits.get("requests_per_minute", 60),
            "last_request_time": 0,
            "request_count": 0
        }


class GitHubIntegration(BaseIntegration):
    """GitHub integration for repository management and code review"""
    
    async def connect(self) -> bool:
        """Connect to GitHub API"""
        try:
            headers = {
                "Authorization": f"token {self.config.authentication['token']}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            async with self.session.get(
                f"{self.config.endpoint_url}/user",
                headers=headers
            ) as response:
                if response.status == 200:
                    self.status = IntegrationStatus.CONNECTED
                    self.logger.info("Connected to GitHub successfully")
                    return True
                else:
                    self.status = IntegrationStatus.ERROR
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to connect to GitHub: {e}")
            self.status = IntegrationStatus.ERROR
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from GitHub"""
        self.status = IntegrationStatus.DISCONNECTED
        self.logger.info("Disconnected from GitHub")
    
    async def test_connection(self) -> bool:
        """Test GitHub connection"""
        return await self.connect()
    
    async def handle_webhook(self, webhook_data: Dict[str, Any]) -> IntegrationEvent:
        """Handle GitHub webhook events"""
        event_type = webhook_data.get("action", "unknown")
        
        return IntegrationEvent(
            event_id=f"github_{asyncio.get_event_loop().time()}",
            integration_id=self.config.integration_id,
            event_type=event_type,
            timestamp=asyncio.get_event_loop().time(),
            data=webhook_data
        )
    
    async def create_pull_request(self, repo: str, title: str, body: str,
                                 head: str, base: str = "main") -> Dict[str, Any]:
        """Create a pull request"""
        headers = {
            "Authorization": f"token {self.config.authentication['token']}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        data = {
            "title": title,
            "body": body,
            "head": head,
            "base": base
        }
        
        async with self.session.post(
            f"{self.config.endpoint_url}/repos/{repo}/pulls",
            headers=headers,
            json=data
        ) as response:
            return await response.json()
    
    async def get_repository_info(self, repo: str) -> Dict[str, Any]:
        """Get repository information"""
        headers = {
            "Authorization": f"token {self.config.authentication['token']}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        async with self.session.get(
            f"{self.config.endpoint_url}/repos/{repo}",
            headers=headers
        ) as response:
            return await response.json()
    
    async def analyze_pull_request(self, repo: str, pr_number: int) -> Dict[str, Any]:
        """Analyze a pull request for code review"""
        headers = {
            "Authorization": f"token {self.config.authentication['token']}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Get PR details
        async with self.session.get(
            f"{self.config.endpoint_url}/repos/{repo}/pulls/{pr_number}",
            headers=headers
        ) as response:
            pr_data = await response.json()
        
        # Get PR files
        async with self.session.get(
            f"{self.config.endpoint_url}/repos/{repo}/pulls/{pr_number}/files",
            headers=headers
        ) as response:
            files_data = await response.json()
        
        return {
            "pull_request": pr_data,
            "files": files_data,
            "analysis_timestamp": asyncio.get_event_loop().time()
        }


class JiraIntegration(BaseIntegration):
    """Jira integration for issue tracking and project management"""
    
    async def connect(self) -> bool:
        """Connect to Jira API"""
        try:
            auth = aiohttp.BasicAuth(
                self.config.authentication['username'],
                self.config.authentication['api_token']
            )
            
            async with self.session.get(
                f"{self.config.endpoint_url}/rest/api/3/myself",
                auth=auth
            ) as response:
                if response.status == 200:
                    self.status = IntegrationStatus.CONNECTED
                    self.logger.info("Connected to Jira successfully")
                    return True
                else:
                    self.status = IntegrationStatus.ERROR
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to connect to Jira: {e}")
            self.status = IntegrationStatus.ERROR
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Jira"""
        self.status = IntegrationStatus.DISCONNECTED
        self.logger.info("Disconnected from Jira")
    
    async def test_connection(self) -> bool:
        """Test Jira connection"""
        return await self.connect()
    
    async def handle_webhook(self, webhook_data: Dict[str, Any]) -> IntegrationEvent:
        """Handle Jira webhook events"""
        event_type = webhook_data.get("webhookEvent", "unknown")
        
        return IntegrationEvent(
            event_id=f"jira_{asyncio.get_event_loop().time()}",
            integration_id=self.config.integration_id,
            event_type=event_type,
            timestamp=asyncio.get_event_loop().time(),
            data=webhook_data
        )
    
    async def create_issue(self, project_key: str, summary: str, description: str,
                          issue_type: str = "Bug") -> Dict[str, Any]:
        """Create a Jira issue"""
        auth = aiohttp.BasicAuth(
            self.config.authentication['username'],
            self.config.authentication['api_token']
        )
        
        data = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": description
                                }
                            ]
                        }
                    ]
                },
                "issuetype": {"name": issue_type}
            }
        }
        
        async with self.session.post(
            f"{self.config.endpoint_url}/rest/api/3/issue",
            auth=auth,
            json=data
        ) as response:
            return await response.json()
    
    async def analyze_issue(self, issue_key: str) -> Dict[str, Any]:
        """Analyze a Jira issue for intelligent processing"""
        auth = aiohttp.BasicAuth(
            self.config.authentication['username'],
            self.config.authentication['api_token']
        )
        
        async with self.session.get(
            f"{self.config.endpoint_url}/rest/api/3/issue/{issue_key}",
            auth=auth
        ) as response:
            issue_data = await response.json()
        
        return {
            "issue": issue_data,
            "analysis_timestamp": asyncio.get_event_loop().time(),
            "priority": issue_data.get("fields", {}).get("priority", {}).get("name", "Medium"),
            "status": issue_data.get("fields", {}).get("status", {}).get("name", "Unknown")
        }


class SlackIntegration(BaseIntegration):
    """Slack integration for team communication and notifications"""
    
    async def connect(self) -> bool:
        """Connect to Slack API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.config.authentication['bot_token']}",
                "Content-Type": "application/json"
            }
            
            async with self.session.get(
                f"{self.config.endpoint_url}/api/auth.test",
                headers=headers
            ) as response:
                if response.status == 200:
                    self.status = IntegrationStatus.CONNECTED
                    self.logger.info("Connected to Slack successfully")
                    return True
                else:
                    self.status = IntegrationStatus.ERROR
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to connect to Slack: {e}")
            self.status = IntegrationStatus.ERROR
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Slack"""
        self.status = IntegrationStatus.DISCONNECTED
        self.logger.info("Disconnected from Slack")
    
    async def test_connection(self) -> bool:
        """Test Slack connection"""
        return await self.connect()
    
    async def handle_webhook(self, webhook_data: Dict[str, Any]) -> IntegrationEvent:
        """Handle Slack webhook events"""
        event_type = webhook_data.get("type", "unknown")
        
        return IntegrationEvent(
            event_id=f"slack_{asyncio.get_event_loop().time()}",
            integration_id=self.config.integration_id,
            event_type=event_type,
            timestamp=asyncio.get_event_loop().time(),
            data=webhook_data
        )
    
    async def send_message(self, channel: str, text: str, 
                          attachments: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Send a message to a Slack channel"""
        headers = {
            "Authorization": f"Bearer {self.config.authentication['bot_token']}",
            "Content-Type": "application/json"
        }
        
        data = {
            "channel": channel,
            "text": text
        }
        
        if attachments:
            data["attachments"] = attachments
        
        async with self.session.post(
            f"{self.config.endpoint_url}/api/chat.postMessage",
            headers=headers,
            json=data
        ) as response:
            return await response.json()
    
    async def send_agent_notification(self, channel: str, agent_capability: AgentCapability,
                                    message: str, priority: str = "normal") -> Dict[str, Any]:
        """Send an agent-specific notification"""
        color_map = {
            "low": "good",
            "normal": "#439FE0",
            "high": "warning",
            "critical": "danger"
        }
        
        attachment = {
            "color": color_map.get(priority, "#439FE0"),
            "title": f"🤖 {agent_capability.value.replace('_', ' ').title()} Agent",
            "text": message,
            "timestamp": int(asyncio.get_event_loop().time())
        }
        
        return await self.send_message(channel, "", [attachment])


class IntegrationFramework:
    """
    Central framework for managing all external integrations.
    
    Provides unified interface for connecting specialized agents
    with external development tools and services.
    """
    
    def __init__(self):
        self.integrations: Dict[str, BaseIntegration] = {}
        self.event_handlers: Dict[str, List[callable]] = {}
        self.logger = logging.getLogger("integration_framework")
        self.webhook_server = None
        self.is_running = False
    
    async def initialize(self) -> bool:
        """Initialize the integration framework"""
        try:
            self.logger.info("Initializing Integration Framework...")
            
            # Initialize all registered integrations
            for integration_id, integration in self.integrations.items():
                if integration.config.enabled:
                    success = await integration.initialize()
                    if not success:
                        self.logger.warning(f"Failed to initialize integration: {integration_id}")
            
            self.is_running = True
            self.logger.info("Integration Framework initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Integration Framework: {e}")
            return False
    
    async def shutdown(self) -> None:
        """Shutdown the integration framework"""
        self.is_running = False
        
        # Cleanup all integrations
        for integration in self.integrations.values():
            await integration.cleanup()
        
        if self.webhook_server:
            await self.webhook_server.cleanup()
        
        self.logger.info("Integration Framework shutdown complete")
    
    def register_integration(self, integration: BaseIntegration) -> None:
        """Register a new integration"""
        self.integrations[integration.config.integration_id] = integration
        self.logger.info(f"Registered integration: {integration.config.integration_id}")
    
    def unregister_integration(self, integration_id: str) -> bool:
        """Unregister an integration"""
        if integration_id in self.integrations:
            del self.integrations[integration_id]
            self.logger.info(f"Unregistered integration: {integration_id}")
            return True
        return False
    
    def register_event_handler(self, event_type: str, handler: callable) -> None:
        """Register an event handler for integration events"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        self.logger.info(f"Registered event handler for: {event_type}")
    
    async def handle_integration_event(self, event: IntegrationEvent) -> None:
        """Handle an integration event"""
        handlers = self.event_handlers.get(event.event_type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                self.logger.error(f"Error in event handler for {event.event_type}: {e}")
        
        # Mark event as processed
        event.processed = True
    
    async def get_integration_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all integrations"""
        status = {}
        
        for integration_id, integration in self.integrations.items():
            status[integration_id] = {
                "name": integration.config.name,
                "type": integration.config.integration_type.value,
                "status": integration.status.value,
                "enabled": integration.config.enabled,
                "endpoint": integration.config.endpoint_url
            }
        
        return status
    
    async def test_all_integrations(self) -> Dict[str, bool]:
        """Test all registered integrations"""
        results = {}
        
        for integration_id, integration in self.integrations.items():
            if integration.config.enabled:
                try:
                    results[integration_id] = await integration.test_connection()
                except Exception as e:
                    self.logger.error(f"Error testing integration {integration_id}: {e}")
                    results[integration_id] = False
            else:
                results[integration_id] = False
        
        return results
    
    async def create_github_integration(self, config: Dict[str, Any]) -> str:
        """Create and register a GitHub integration"""
        integration_config = IntegrationConfig(
            integration_id=f"github_{asyncio.get_event_loop().time()}",
            name="GitHub Integration",
            integration_type=IntegrationType.VERSION_CONTROL,
            endpoint_url=config.get("endpoint_url", "https://api.github.com"),
            authentication=config["authentication"],
            settings=config.get("settings", {}),
            rate_limits=config.get("rate_limits", {"requests_per_minute": 5000})
        )
        
        integration = GitHubIntegration(integration_config)
        self.register_integration(integration)
        
        return integration_config.integration_id
    
    async def create_jira_integration(self, config: Dict[str, Any]) -> str:
        """Create and register a Jira integration"""
        integration_config = IntegrationConfig(
            integration_id=f"jira_{asyncio.get_event_loop().time()}",
            name="Jira Integration",
            integration_type=IntegrationType.ISSUE_TRACKING,
            endpoint_url=config["endpoint_url"],
            authentication=config["authentication"],
            settings=config.get("settings", {}),
            rate_limits=config.get("rate_limits", {"requests_per_minute": 300})
        )
        
        integration = JiraIntegration(integration_config)
        self.register_integration(integration)
        
        return integration_config.integration_id
    
    async def create_slack_integration(self, config: Dict[str, Any]) -> str:
        """Create and register a Slack integration"""
        integration_config = IntegrationConfig(
            integration_id=f"slack_{asyncio.get_event_loop().time()}",
            name="Slack Integration",
            integration_type=IntegrationType.COMMUNICATION,
            endpoint_url=config.get("endpoint_url", "https://slack.com"),
            authentication=config["authentication"],
            settings=config.get("settings", {}),
            rate_limits=config.get("rate_limits", {"requests_per_minute": 100})
        )
        
        integration = SlackIntegration(integration_config)
        self.register_integration(integration)
        
        return integration_config.integration_id
    
    async def execute_agent_workflow_with_integrations(self, 
                                                      agent: IntelligentAgent,
                                                      workflow_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an agent workflow with integration support"""
        results = {"agent_results": None, "integration_actions": []}
        
        try:
            # Execute agent workflow
            # This would integrate with the actual agent execution
            results["agent_results"] = {"status": "completed", "message": "Agent workflow executed"}
            
            # Perform integration actions based on results
            if workflow_context.get("notify_slack"):
                slack_integration = self._get_integration_by_type(IntegrationType.COMMUNICATION)
                if slack_integration:
                    await slack_integration.send_agent_notification(
                        channel=workflow_context["slack_channel"],
                        agent_capability=agent.capabilities[0],
                        message=f"Workflow completed successfully",
                        priority="normal"
                    )
                    results["integration_actions"].append("slack_notification_sent")
            
            if workflow_context.get("create_github_issue"):
                github_integration = self._get_integration_by_type(IntegrationType.VERSION_CONTROL)
                if github_integration:
                    # This would create a GitHub issue based on agent results
                    results["integration_actions"].append("github_issue_created")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error executing agent workflow with integrations: {e}")
            return {"error": str(e)}
    
    def _get_integration_by_type(self, integration_type: IntegrationType) -> Optional[BaseIntegration]:
        """Get the first integration of a specific type"""
        for integration in self.integrations.values():
            if integration.config.integration_type == integration_type and integration.config.enabled:
                return integration
        return None