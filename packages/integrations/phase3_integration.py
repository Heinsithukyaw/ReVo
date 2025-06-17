#!/usr/bin/env python3
"""
Phase 3 External Integration Resilience - Integration System
Unified system that brings together API Gateway, Webhook Manager, and Integration Monitor
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from .api_gateway import (
    APIGateway, IntegrationType, IntegrationConfig, APIRequest, APIResponse,
    RequestMethod, RetryStrategy, RateLimitConfig, RetryConfig, TimeoutConfig,
    get_api_gateway, shutdown_api_gateway
)
from .webhook_manager import (
    WebhookManager, WebhookEventType, WebhookConfig, WebhookHandler,
    get_webhook_manager, shutdown_webhook_manager
)
from .integration_monitor import (
    IntegrationMonitor, HealthCheck, AlertRule, AlertSeverity, Metric, MetricType,
    get_integration_monitor, shutdown_integration_monitor
)
from .enhanced_github_integration import get_github_integration

logger = logging.getLogger(__name__)

class IntegrationStatus(Enum):
    """Integration status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    OFFLINE = "offline"

@dataclass
class IntegrationEndpoint:
    """External integration endpoint configuration"""
    name: str
    integration_type: IntegrationType
    base_url: str
    health_endpoint: str
    api_key: Optional[str] = None
    webhook_secret: Optional[str] = None
    rate_limit_per_minute: int = 60
    timeout_seconds: float = 30.0
    cache_ttl_seconds: int = 3600
    enabled: bool = True

@dataclass
class SystemMetrics:
    """System-wide integration metrics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    cache_hit_rate: float = 0.0
    active_webhooks: int = 0
    processed_webhooks: int = 0
    active_alerts: int = 0
    healthy_integrations: int = 0
    total_integrations: int = 0

class Phase3IntegrationSystem:
    """Main Phase 3 integration system"""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url
        self.api_gateway: Optional[APIGateway] = None
        self.webhook_manager: Optional[WebhookManager] = None
        self.monitor: Optional[IntegrationMonitor] = None
        
        self.integrations: Dict[str, IntegrationEndpoint] = {}
        self.integration_instances: Dict[str, Any] = {}
        self.system_started = False
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {}
        
    async def start(self):
        """Start the Phase 3 integration system"""
        if self.system_started:
            return
            
        logger.info("🚀 Starting Phase 3 External Integration Resilience System...")
        
        # Initialize core components
        self.api_gateway = await get_api_gateway(self.redis_url)
        self.webhook_manager = await get_webhook_manager(self.redis_url)
        self.monitor = await get_integration_monitor(self.redis_url)
        
        # Register system-wide alert handler
        self.monitor.register_alert_handler(self._handle_system_alert)
        
        # Configure default integrations
        await self._configure_default_integrations()
        
        self.system_started = True
        logger.info("✅ Phase 3 Integration System started successfully")
        
    async def stop(self):
        """Stop the Phase 3 integration system"""
        if not self.system_started:
            return
            
        logger.info("🛑 Stopping Phase 3 Integration System...")
        
        # Shutdown components
        await shutdown_api_gateway()
        await shutdown_webhook_manager()
        await shutdown_integration_monitor()
        
        self.system_started = False
        logger.info("✅ Phase 3 Integration System stopped")
        
    async def register_integration(self, endpoint: IntegrationEndpoint):
        """Register a new external integration"""
        if not self.system_started:
            await self.start()
            
        self.integrations[endpoint.name] = endpoint
        
        if not endpoint.enabled:
            logger.info(f"Integration {endpoint.name} registered but disabled")
            return
            
        # Configure API Gateway
        integration_config = IntegrationConfig(
            integration_type=endpoint.integration_type,
            base_url=endpoint.base_url,
            api_key=endpoint.api_key,
            headers=self._get_default_headers(endpoint),
            rate_limit=RateLimitConfig(
                requests_per_minute=endpoint.rate_limit_per_minute,
                burst_limit=min(endpoint.rate_limit_per_minute // 4, 50)
            ),
            retry=RetryConfig(
                max_attempts=3,
                strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                base_delay=1.0,
                max_delay=30.0
            ),
            timeout=TimeoutConfig(
                connect_timeout=10.0,
                read_timeout=endpoint.timeout_seconds,
                total_timeout=endpoint.timeout_seconds + 10.0
            ),
            cache_ttl=endpoint.cache_ttl_seconds
        )
        
        self.api_gateway.register_integration(integration_config)
        
        # Configure health monitoring
        health_check = HealthCheck(
            name=endpoint.name,
            endpoint=endpoint.health_endpoint,
            method="GET",
            timeout=endpoint.timeout_seconds,
            interval=60.0,
            expected_status=200,
            headers=self._get_default_headers(endpoint)
        )
        
        self.monitor.register_health_check(health_check)
        
        # Configure alerts
        await self._configure_integration_alerts(endpoint.name)
        
        # Configure webhooks if secret provided
        if endpoint.webhook_secret:
            await self._configure_integration_webhooks(endpoint)
            
        logger.info(f"✅ Registered integration: {endpoint.name} ({endpoint.integration_type.value})")
        
    async def get_integration_client(self, integration_name: str) -> Any:
        """Get a client instance for the integration"""
        if integration_name not in self.integrations:
            raise ValueError(f"Integration {integration_name} not registered")
            
        if integration_name in self.integration_instances:
            return self.integration_instances[integration_name]
            
        endpoint = self.integrations[integration_name]
        
        # Create specialized client based on integration type
        if endpoint.integration_type == IntegrationType.GITHUB:
            client = await get_github_integration(
                api_token=endpoint.api_key,
                webhook_secret=endpoint.webhook_secret,
                redis_url=self.redis_url
            )
            self.integration_instances[integration_name] = client
            return client
        else:
            # Return generic API gateway for other integrations
            return self.api_gateway
            
    async def make_request(
        self,
        integration_name: str,
        request: APIRequest
    ) -> APIResponse:
        """Make an API request through the integration system"""
        if integration_name not in self.integrations:
            raise ValueError(f"Integration {integration_name} not registered")
            
        endpoint = self.integrations[integration_name]
        
        if not endpoint.enabled:
            raise Exception(f"Integration {integration_name} is disabled")
            
        # Record request metrics
        start_time = datetime.now()
        
        try:
            response = await self.api_gateway.make_request(
                endpoint.integration_type,
                request
            )
            
            # Record success metrics
            await self._record_request_metrics(
                integration_name,
                (datetime.now() - start_time).total_seconds(),
                True
            )
            
            return response
            
        except Exception as e:
            # Record failure metrics
            await self._record_request_metrics(
                integration_name,
                (datetime.now() - start_time).total_seconds(),
                False
            )
            raise e
            
    async def receive_webhook(
        self,
        integration_name: str,
        event_type: WebhookEventType,
        headers: Dict[str, str],
        payload: Dict[str, Any]
    ) -> str:
        """Receive and process a webhook"""
        if integration_name not in self.integrations:
            raise ValueError(f"Integration {integration_name} not registered")
            
        signature = headers.get("X-Hub-Signature-256") or headers.get("X-Hub-Signature")
        
        event_id = await self.webhook_manager.receive_webhook(
            event_type=event_type,
            source=integration_name,
            headers=headers,
            payload=payload,
            signature=signature
        )
        
        # Record webhook metrics
        await self.monitor.record_metric(Metric(
            name="webhook_received",
            value=1,
            metric_type=MetricType.COUNTER,
            labels={"integration": integration_name, "event_type": event_type.value}
        ))
        
        return event_id
        
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        if not self.system_started:
            return {"status": "not_started"}
            
        # Get component statuses
        api_gateway_health = await self.api_gateway.get_system_health()
        webhook_health = await self.webhook_manager.get_health_status()
        monitor_health = await self.monitor.get_system_status()
        
        # Get integration statuses
        integration_statuses = {}
        for name in self.integrations:
            try:
                status = await self.monitor.get_integration_status(name)
                # Convert IntegrationStatus object to dict if needed
                if hasattr(status, '__dict__'):
                    status_dict = status.__dict__.copy()
                    # Convert datetime objects to strings
                    for key, value in status_dict.items():
                        if isinstance(value, datetime):
                            status_dict[key] = value.isoformat()
                    integration_statuses[name] = status_dict
                else:
                    integration_statuses[name] = status
            except Exception as e:
                integration_statuses[name] = {
                    "status": "error",
                    "error": str(e)
                }
                
        # Calculate system metrics
        metrics = await self._calculate_system_metrics()
        
        # Determine overall system status
        overall_status = self._determine_overall_status(
            api_gateway_health,
            webhook_health,
            monitor_health,
            integration_statuses
        )
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "components": {
                "api_gateway": api_gateway_health,
                "webhook_manager": webhook_health,
                "integration_monitor": monitor_health
            },
            "integrations": integration_statuses,
            "metrics": metrics.__dict__,
            "registered_integrations": len(self.integrations),
            "enabled_integrations": sum(1 for i in self.integrations.values() if i.enabled)
        }
        
    async def get_integration_status(self, integration_name: str) -> Dict[str, Any]:
        """Get detailed status for specific integration"""
        if integration_name not in self.integrations:
            raise ValueError(f"Integration {integration_name} not registered")
            
        endpoint = self.integrations[integration_name]
        
        # Get health status
        health_status = await self.monitor.get_integration_status(integration_name)
        
        # Get API gateway status
        gateway_health = await self.api_gateway.get_integration_health(endpoint.integration_type)
        
        # Get webhook stats if applicable
        webhook_stats = {}
        if endpoint.webhook_secret:
            webhook_stats = await self.webhook_manager.get_webhook_stats()
            
        return {
            "name": integration_name,
            "type": endpoint.integration_type.value,
            "enabled": endpoint.enabled,
            "base_url": endpoint.base_url,
            "health": health_status,
            "api_gateway": gateway_health,
            "webhooks": webhook_stats,
            "configuration": {
                "rate_limit_per_minute": endpoint.rate_limit_per_minute,
                "timeout_seconds": endpoint.timeout_seconds,
                "cache_ttl_seconds": endpoint.cache_ttl_seconds
            }
        }
        
    async def enable_integration(self, integration_name: str):
        """Enable an integration"""
        if integration_name not in self.integrations:
            raise ValueError(f"Integration {integration_name} not registered")
            
        self.integrations[integration_name].enabled = True
        logger.info(f"✅ Enabled integration: {integration_name}")
        
    async def disable_integration(self, integration_name: str):
        """Disable an integration"""
        if integration_name not in self.integrations:
            raise ValueError(f"Integration {integration_name} not registered")
            
        self.integrations[integration_name].enabled = False
        logger.info(f"🚫 Disabled integration: {integration_name}")
        
    async def register_event_handler(self, event_type: str, handler: Callable):
        """Register an event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        
    async def _configure_default_integrations(self):
        """Configure default integrations"""
        # GitHub integration (if API token available)
        github_token = None  # Would be loaded from environment/config
        if github_token:
            github_endpoint = IntegrationEndpoint(
                name="github",
                integration_type=IntegrationType.GITHUB,
                base_url="https://api.github.com",
                health_endpoint="https://api.github.com/rate_limit",
                api_key=github_token,
                rate_limit_per_minute=5000,
                timeout_seconds=30.0,
                cache_ttl_seconds=3600
            )
            await self.register_integration(github_endpoint)
            
        # Slack integration (if token available)
        slack_token = None  # Would be loaded from environment/config
        if slack_token:
            slack_endpoint = IntegrationEndpoint(
                name="slack",
                integration_type=IntegrationType.SLACK,
                base_url="https://slack.com/api",
                health_endpoint="https://slack.com/api/api.test",
                api_key=slack_token,
                rate_limit_per_minute=100,
                timeout_seconds=15.0,
                cache_ttl_seconds=1800
            )
            await self.register_integration(slack_endpoint)
            
        # JIRA integration (if credentials available)
        jira_url = None  # Would be loaded from environment/config
        jira_token = None
        if jira_url and jira_token:
            jira_endpoint = IntegrationEndpoint(
                name="jira",
                integration_type=IntegrationType.JIRA,
                base_url=jira_url,
                health_endpoint=f"{jira_url}/rest/api/2/serverInfo",
                api_key=jira_token,
                rate_limit_per_minute=300,
                timeout_seconds=45.0,
                cache_ttl_seconds=14400  # 4 hours
            )
            await self.register_integration(jira_endpoint)
            
    def _get_default_headers(self, endpoint: IntegrationEndpoint) -> Dict[str, str]:
        """Get default headers for integration"""
        headers = {
            "User-Agent": "reVoAgent/1.0",
            "Accept": "application/json"
        }
        
        if endpoint.api_key:
            if endpoint.integration_type == IntegrationType.GITHUB:
                headers["Authorization"] = f"token {endpoint.api_key}"
            elif endpoint.integration_type == IntegrationType.SLACK:
                headers["Authorization"] = f"Bearer {endpoint.api_key}"
            elif endpoint.integration_type == IntegrationType.JIRA:
                headers["Authorization"] = f"Bearer {endpoint.api_key}"
                
        return headers
        
    async def _configure_integration_alerts(self, integration_name: str):
        """Configure alerts for integration"""
        alert_rules = [
            AlertRule(
                name=f"{integration_name}_high_error_rate",
                metric_name=f"{integration_name}_error_rate",
                condition="> 5",
                severity=AlertSeverity.WARNING,
                description=f"{integration_name} API error rate is high"
            ),
            AlertRule(
                name=f"{integration_name}_slow_response",
                metric_name=f"{integration_name}_response_time",
                condition="> 5",
                severity=AlertSeverity.WARNING,
                description=f"{integration_name} API response time is slow"
            ),
            AlertRule(
                name=f"{integration_name}_health_check_failed",
                metric_name=f"health_check_status",
                condition="== 0",
                severity=AlertSeverity.CRITICAL,
                description=f"{integration_name} health check failed"
            )
        ]
        
        for rule in alert_rules:
            self.monitor.register_alert_rule(rule)
            
    async def _configure_integration_webhooks(self, endpoint: IntegrationEndpoint):
        """Configure webhooks for integration"""
        if endpoint.integration_type == IntegrationType.GITHUB:
            webhook_events = [
                WebhookEventType.GITHUB_PUSH,
                WebhookEventType.GITHUB_PR,
                WebhookEventType.GITHUB_ISSUE
            ]
        elif endpoint.integration_type == IntegrationType.SLACK:
            webhook_events = [
                WebhookEventType.SLACK_MESSAGE,
                WebhookEventType.SLACK_MENTION
            ]
        elif endpoint.integration_type == IntegrationType.JIRA:
            webhook_events = [
                WebhookEventType.JIRA_ISSUE,
                WebhookEventType.JIRA_COMMENT
            ]
        else:
            webhook_events = [WebhookEventType.CUSTOM]
            
        for event_type in webhook_events:
            webhook_config = WebhookConfig(
                event_type=event_type,
                endpoint=f"/webhooks/{endpoint.name}",
                secret=endpoint.webhook_secret,
                max_retries=3,
                retry_delay=5.0,
                timeout=endpoint.timeout_seconds,
                rate_limit=endpoint.rate_limit_per_minute
            )
            self.webhook_manager.register_webhook(webhook_config)
            
    async def _record_request_metrics(
        self,
        integration_name: str,
        response_time: float,
        success: bool
    ):
        """Record request metrics"""
        # Record response time
        await self.monitor.record_metric(Metric(
            name=f"{integration_name}_response_time",
            value=response_time,
            metric_type=MetricType.GAUGE,
            labels={"integration": integration_name}
        ))
        
        # Record success/failure
        metric_name = f"{integration_name}_request_success" if success else f"{integration_name}_request_failure"
        await self.monitor.record_metric(Metric(
            name=metric_name,
            value=1,
            metric_type=MetricType.COUNTER,
            labels={"integration": integration_name}
        ))
        
    async def _calculate_system_metrics(self) -> SystemMetrics:
        """Calculate system-wide metrics"""
        metrics = SystemMetrics()
        
        # Calculate from individual integration metrics
        for integration_name in self.integrations:
            try:
                # Get API gateway health
                endpoint = self.integrations[integration_name]
                gateway_health = await self.api_gateway.get_integration_health(endpoint.integration_type)
                
                metrics.total_requests += gateway_health.get("total_requests", 0)
                metrics.successful_requests += gateway_health.get("total_success", 0)
                metrics.failed_requests += gateway_health.get("total_errors", 0)
                
                if gateway_health.get("avg_response_time_ms", 0) > 0:
                    metrics.avg_response_time += gateway_health["avg_response_time_ms"] / 1000.0
                    
                if gateway_health.get("status") == "healthy":
                    metrics.healthy_integrations += 1
                    
                metrics.total_integrations += 1
                
            except Exception as e:
                logger.warning(f"Failed to get metrics for {integration_name}: {e}")
                
        # Get webhook metrics
        webhook_stats = await self.webhook_manager.get_webhook_stats()
        if isinstance(webhook_stats, dict) and "total_stats" in webhook_stats:
            for stats in webhook_stats["total_stats"].values():
                metrics.processed_webhooks += stats.get("processed", 0)
                
        metrics.active_webhooks = webhook_stats.get("queue_size", 0)
        
        # Get alert metrics
        active_alerts = await self.monitor.alert_manager.get_active_alerts()
        metrics.active_alerts = len(active_alerts)
        
        # Calculate averages
        if metrics.total_integrations > 0:
            metrics.avg_response_time /= metrics.total_integrations
            
        return metrics
        
    def _determine_overall_status(
        self,
        api_gateway_health: Dict[str, Any],
        webhook_health: Dict[str, Any],
        monitor_health: Dict[str, Any],
        integration_statuses: Dict[str, Any]
    ) -> str:
        """Determine overall system status"""
        # Check critical components
        if api_gateway_health.get("status") == "unhealthy":
            return IntegrationStatus.CRITICAL.value
            
        if webhook_health.get("status") == "unhealthy":
            return IntegrationStatus.CRITICAL.value
            
        # Check integration health
        critical_integrations = sum(
            1 for status in integration_statuses.values()
            if status.get("status") == "critical"
        )
        
        degraded_integrations = sum(
            1 for status in integration_statuses.values()
            if status.get("status") in ["warning", "degraded"]
        )
        
        total_integrations = len(integration_statuses)
        
        if total_integrations == 0:
            return IntegrationStatus.HEALTHY.value
            
        # Determine status based on integration health
        if critical_integrations > total_integrations * 0.5:
            return IntegrationStatus.CRITICAL.value
        elif critical_integrations > 0 or degraded_integrations > total_integrations * 0.3:
            return IntegrationStatus.DEGRADED.value
        else:
            return IntegrationStatus.HEALTHY.value
            
    async def _handle_system_alert(self, alert):
        """Handle system-wide alerts"""
        logger.warning(f"🚨 System Alert: {alert.description} (Severity: {alert.severity.value})")
        
        # Trigger event handlers
        for handler in self.event_handlers.get("alert", []):
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")

# Global Phase 3 system instance
_phase3_system_instance: Optional[Phase3IntegrationSystem] = None

async def get_phase3_system(redis_url: Optional[str] = None) -> Phase3IntegrationSystem:
    """Get or create the global Phase 3 integration system instance"""
    global _phase3_system_instance
    
    if _phase3_system_instance is None:
        _phase3_system_instance = Phase3IntegrationSystem(redis_url)
        await _phase3_system_instance.start()
        
    return _phase3_system_instance

async def shutdown_phase3_system():
    """Shutdown the global Phase 3 integration system instance"""
    global _phase3_system_instance
    
    if _phase3_system_instance:
        await _phase3_system_instance.stop()
        _phase3_system_instance = None