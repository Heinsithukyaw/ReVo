"""
Alert Manager for Phase 4 Comprehensive Monitoring

Manages comprehensive alerting strategy with critical alerts (PagerDuty/immediate),
warning alerts (Slack/email), alert escalation, and management.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import json
import aiofiles
from pathlib import Path
import aiohttp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import hashlib
from collections import defaultdict

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

class NotificationChannel(Enum):
    """Notification channels"""
    EMAIL = "email"
    SLACK = "slack"
    PAGERDUTY = "pagerduty"
    WEBHOOK = "webhook"
    SMS = "sms"

@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    condition: str
    severity: AlertSeverity
    threshold: float
    duration_minutes: int
    channels: List[NotificationChannel]
    description: str
    enabled: bool = True
    cooldown_minutes: int = 15
    escalation_rules: Optional[List[Dict[str, Any]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['severity'] = self.severity.value
        data['channels'] = [c.value for c in self.channels]
        return data

@dataclass
class Alert:
    """Alert instance"""
    id: str
    rule_name: str
    severity: AlertSeverity
    status: AlertStatus
    title: str
    description: str
    value: float
    threshold: float
    timestamp: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    tags: Dict[str, str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['severity'] = self.severity.value
        data['status'] = self.status.value
        data['timestamp'] = self.timestamp.isoformat()
        data['acknowledged_at'] = self.acknowledged_at.isoformat() if self.acknowledged_at else None
        data['resolved_at'] = self.resolved_at.isoformat() if self.resolved_at else None
        return data

@dataclass
class NotificationConfig:
    """Notification configuration"""
    channel: NotificationChannel
    config: Dict[str, Any]
    enabled: bool = True

class AlertManager:
    """
    Comprehensive alert manager with multi-channel notifications,
    escalation rules, and alert lifecycle management
    """
    
    def __init__(self,
                 storage_path: str = "monitoring/alerts",
                 check_interval: float = 30.0):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.check_interval = check_interval
        
        # Alert management
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.notification_configs: Dict[NotificationChannel, NotificationConfig] = {}
        
        # Alert suppression and cooldowns
        self.alert_cooldowns: Dict[str, datetime] = {}
        self.suppressed_alerts: Dict[str, datetime] = {}
        
        # Metrics for alert evaluation
        self.metrics_cache: Dict[str, Any] = {}
        self.metric_providers: List[Callable] = []
        
        # Notification state
        self.notification_queue: asyncio.Queue = asyncio.Queue()
        self.is_running = False
        
        # Default alert rules
        self._setup_default_rules()
        
        logger.info("AlertManager initialized")
    
    def _setup_default_rules(self):
        """Setup default alert rules"""
        default_rules = [
            AlertRule(
                name="high_cpu_usage",
                condition="cpu_percent > threshold",
                severity=AlertSeverity.WARNING,
                threshold=80.0,
                duration_minutes=5,
                channels=[NotificationChannel.SLACK, NotificationChannel.EMAIL],
                description="CPU usage is above 80% for 5 minutes",
                cooldown_minutes=15
            ),
            AlertRule(
                name="critical_cpu_usage",
                condition="cpu_percent > threshold",
                severity=AlertSeverity.CRITICAL,
                threshold=95.0,
                duration_minutes=2,
                channels=[NotificationChannel.PAGERDUTY, NotificationChannel.SLACK],
                description="CPU usage is above 95% for 2 minutes",
                cooldown_minutes=10,
                escalation_rules=[
                    {"delay_minutes": 15, "channels": ["pagerduty"], "escalate_to": "oncall_manager"}
                ]
            ),
            AlertRule(
                name="high_memory_usage",
                condition="memory_percent > threshold",
                severity=AlertSeverity.WARNING,
                threshold=85.0,
                duration_minutes=5,
                channels=[NotificationChannel.SLACK, NotificationChannel.EMAIL],
                description="Memory usage is above 85% for 5 minutes",
                cooldown_minutes=15
            ),
            AlertRule(
                name="critical_memory_usage",
                condition="memory_percent > threshold",
                severity=AlertSeverity.CRITICAL,
                threshold=95.0,
                duration_minutes=2,
                channels=[NotificationChannel.PAGERDUTY, NotificationChannel.SLACK],
                description="Memory usage is above 95% for 2 minutes",
                cooldown_minutes=10
            ),
            AlertRule(
                name="high_disk_usage",
                condition="disk_percent > threshold",
                severity=AlertSeverity.WARNING,
                threshold=85.0,
                duration_minutes=10,
                channels=[NotificationChannel.SLACK, NotificationChannel.EMAIL],
                description="Disk usage is above 85% for 10 minutes",
                cooldown_minutes=30
            ),
            AlertRule(
                name="api_high_error_rate",
                condition="error_rate > threshold",
                severity=AlertSeverity.WARNING,
                threshold=0.05,  # 5%
                duration_minutes=3,
                channels=[NotificationChannel.SLACK, NotificationChannel.EMAIL],
                description="API error rate is above 5% for 3 minutes",
                cooldown_minutes=10
            ),
            AlertRule(
                name="api_critical_error_rate",
                condition="error_rate > threshold",
                severity=AlertSeverity.CRITICAL,
                threshold=0.15,  # 15%
                duration_minutes=1,
                channels=[NotificationChannel.PAGERDUTY, NotificationChannel.SLACK],
                description="API error rate is above 15% for 1 minute",
                cooldown_minutes=5
            ),
            AlertRule(
                name="slow_api_response",
                condition="avg_response_time_ms > threshold",
                severity=AlertSeverity.WARNING,
                threshold=2000.0,  # 2 seconds
                duration_minutes=5,
                channels=[NotificationChannel.SLACK, NotificationChannel.EMAIL],
                description="API average response time is above 2 seconds for 5 minutes",
                cooldown_minutes=15
            ),
            AlertRule(
                name="service_down",
                condition="service_health == 'down'",
                severity=AlertSeverity.CRITICAL,
                threshold=1.0,
                duration_minutes=1,
                channels=[NotificationChannel.PAGERDUTY, NotificationChannel.SLACK],
                description="Service is down",
                cooldown_minutes=5
            )
        ]
        
        for rule in default_rules:
            self.alert_rules[rule.name] = rule
    
    async def start(self):
        """Start alert manager"""
        if self.is_running:
            logger.warning("AlertManager already running")
            return
        
        self.is_running = True
        logger.info("Starting AlertManager")
        
        # Start background tasks
        asyncio.create_task(self._alert_evaluation_loop())
        asyncio.create_task(self._notification_processor())
    
    async def stop(self):
        """Stop alert manager"""
        self.is_running = False
        logger.info("Stopped AlertManager")
    
    async def _alert_evaluation_loop(self):
        """Main alert evaluation loop"""
        while self.is_running:
            try:
                await self._evaluate_alerts()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in alert evaluation loop: {e}")
                await asyncio.sleep(10)
    
    async def _notification_processor(self):
        """Process notification queue"""
        while self.is_running:
            try:
                # Get notification from queue with timeout
                try:
                    notification = await asyncio.wait_for(
                        self.notification_queue.get(), timeout=1.0
                    )
                    await self._send_notification(notification)
                except asyncio.TimeoutError:
                    continue
            except Exception as e:
                logger.error(f"Error processing notification: {e}")
    
    async def _evaluate_alerts(self):
        """Evaluate all alert rules against current metrics"""
        try:
            # Update metrics cache
            await self._update_metrics_cache()
            
            for rule_name, rule in self.alert_rules.items():
                if not rule.enabled:
                    continue
                
                # Check if rule is in cooldown
                if self._is_in_cooldown(rule_name):
                    continue
                
                # Evaluate rule condition
                should_alert = await self._evaluate_rule_condition(rule)
                
                if should_alert:
                    await self._trigger_alert(rule)
                else:
                    # Check if we should resolve existing alert
                    await self._check_alert_resolution(rule_name)
            
        except Exception as e:
            logger.error(f"Error evaluating alerts: {e}")
    
    async def _update_metrics_cache(self):
        """Update metrics cache from all providers"""
        try:
            for provider in self.metric_providers:
                try:
                    metrics = await provider()
                    if isinstance(metrics, dict):
                        self.metrics_cache.update(metrics)
                except Exception as e:
                    logger.warning(f"Error getting metrics from provider: {e}")
        except Exception as e:
            logger.error(f"Error updating metrics cache: {e}")
    
    async def _evaluate_rule_condition(self, rule: AlertRule) -> bool:
        """Evaluate if alert rule condition is met"""
        try:
            # Simple condition evaluation
            # In a real implementation, you'd use a proper expression evaluator
            
            if rule.condition == "cpu_percent > threshold":
                cpu_percent = self.metrics_cache.get('cpu_percent', 0)
                return cpu_percent > rule.threshold
            
            elif rule.condition == "memory_percent > threshold":
                memory_percent = self.metrics_cache.get('memory_percent', 0)
                return memory_percent > rule.threshold
            
            elif rule.condition == "disk_percent > threshold":
                disk_percent = self.metrics_cache.get('disk_percent', 0)
                return disk_percent > rule.threshold
            
            elif rule.condition == "error_rate > threshold":
                error_rate = self.metrics_cache.get('error_rate', 0)
                return error_rate > rule.threshold
            
            elif rule.condition == "avg_response_time_ms > threshold":
                response_time = self.metrics_cache.get('avg_response_time_ms', 0)
                return response_time > rule.threshold
            
            elif rule.condition == "service_health == 'down'":
                service_health = self.metrics_cache.get('service_health', 'up')
                return service_health == 'down'
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating rule condition for {rule.name}: {e}")
            return False
    
    async def _trigger_alert(self, rule: AlertRule):
        """Trigger an alert"""
        try:
            # Generate alert ID
            alert_id = self._generate_alert_id(rule)
            
            # Check if alert already exists
            if alert_id in self.active_alerts:
                return  # Alert already active
            
            # Get current metric value
            metric_value = self._get_metric_value_for_rule(rule)
            
            # Create alert
            alert = Alert(
                id=alert_id,
                rule_name=rule.name,
                severity=rule.severity,
                status=AlertStatus.ACTIVE,
                title=f"{rule.name.replace('_', ' ').title()}",
                description=rule.description,
                value=metric_value,
                threshold=rule.threshold,
                timestamp=datetime.now(),
                tags={"rule": rule.name, "severity": rule.severity.value}
            )
            
            # Add to active alerts
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)
            
            # Set cooldown
            self.alert_cooldowns[rule.name] = datetime.now() + timedelta(minutes=rule.cooldown_minutes)
            
            # Queue notifications
            for channel in rule.channels:
                notification = {
                    "alert": alert,
                    "channel": channel,
                    "rule": rule
                }
                await self.notification_queue.put(notification)
            
            # Save alert
            await self._save_alert(alert)
            
            logger.info(f"Triggered alert: {alert.title} (ID: {alert_id})")
            
        except Exception as e:
            logger.error(f"Error triggering alert for rule {rule.name}: {e}")
    
    async def _check_alert_resolution(self, rule_name: str):
        """Check if alerts should be resolved"""
        try:
            # Find active alerts for this rule
            alerts_to_resolve = [
                alert for alert in self.active_alerts.values()
                if alert.rule_name == rule_name and alert.status == AlertStatus.ACTIVE
            ]
            
            for alert in alerts_to_resolve:
                await self._resolve_alert(alert.id, "Condition no longer met")
                
        except Exception as e:
            logger.error(f"Error checking alert resolution for {rule_name}: {e}")
    
    def _generate_alert_id(self, rule: AlertRule) -> str:
        """Generate unique alert ID"""
        content = f"{rule.name}_{rule.threshold}_{datetime.now().strftime('%Y%m%d_%H')}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _get_metric_value_for_rule(self, rule: AlertRule) -> float:
        """Get current metric value for rule"""
        if "cpu_percent" in rule.condition:
            return self.metrics_cache.get('cpu_percent', 0)
        elif "memory_percent" in rule.condition:
            return self.metrics_cache.get('memory_percent', 0)
        elif "disk_percent" in rule.condition:
            return self.metrics_cache.get('disk_percent', 0)
        elif "error_rate" in rule.condition:
            return self.metrics_cache.get('error_rate', 0)
        elif "response_time" in rule.condition:
            return self.metrics_cache.get('avg_response_time_ms', 0)
        else:
            return 0.0
    
    def _is_in_cooldown(self, rule_name: str) -> bool:
        """Check if rule is in cooldown period"""
        if rule_name not in self.alert_cooldowns:
            return False
        return datetime.now() < self.alert_cooldowns[rule_name]
    
    async def _send_notification(self, notification: Dict[str, Any]):
        """Send notification through specified channel"""
        try:
            alert = notification["alert"]
            channel = notification["channel"]
            rule = notification["rule"]
            
            if channel not in self.notification_configs:
                logger.warning(f"No configuration for notification channel: {channel.value}")
                return
            
            config = self.notification_configs[channel]
            if not config.enabled:
                return
            
            if channel == NotificationChannel.EMAIL:
                await self._send_email_notification(alert, config.config)
            elif channel == NotificationChannel.SLACK:
                await self._send_slack_notification(alert, config.config)
            elif channel == NotificationChannel.PAGERDUTY:
                await self._send_pagerduty_notification(alert, config.config)
            elif channel == NotificationChannel.WEBHOOK:
                await self._send_webhook_notification(alert, config.config)
            
            logger.info(f"Sent {channel.value} notification for alert {alert.id}")
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    async def _send_email_notification(self, alert: Alert, config: Dict[str, Any]):
        """Send email notification"""
        try:
            smtp_server = config.get('smtp_server', 'localhost')
            smtp_port = config.get('smtp_port', 587)
            username = config.get('username')
            password = config.get('password')
            from_email = config.get('from_email')
            to_emails = config.get('to_emails', [])
            
            if not to_emails:
                logger.warning("No email recipients configured")
                return
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
            
            body = f"""
Alert: {alert.title}
Severity: {alert.severity.value.upper()}
Description: {alert.description}
Value: {alert.value}
Threshold: {alert.threshold}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Alert ID: {alert.id}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if username and password:
                    server.starttls()
                    server.login(username, password)
                server.send_message(msg)
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
    
    async def _send_slack_notification(self, alert: Alert, config: Dict[str, Any]):
        """Send Slack notification"""
        try:
            webhook_url = config.get('webhook_url')
            if not webhook_url:
                logger.warning("No Slack webhook URL configured")
                return
            
            # Create Slack message
            color = {
                AlertSeverity.INFO: "good",
                AlertSeverity.WARNING: "warning", 
                AlertSeverity.CRITICAL: "danger"
            }.get(alert.severity, "warning")
            
            payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": f"[{alert.severity.value.upper()}] {alert.title}",
                        "text": alert.description,
                        "fields": [
                            {"title": "Value", "value": str(alert.value), "short": True},
                            {"title": "Threshold", "value": str(alert.threshold), "short": True},
                            {"title": "Time", "value": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S'), "short": True},
                            {"title": "Alert ID", "value": alert.id, "short": True}
                        ],
                        "footer": "reVoAgent Monitoring",
                        "ts": int(alert.timestamp.timestamp())
                    }
                ]
            }
            
            # Send to Slack
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status != 200:
                        logger.error(f"Slack notification failed: {response.status}")
            
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
    
    async def _send_pagerduty_notification(self, alert: Alert, config: Dict[str, Any]):
        """Send PagerDuty notification"""
        try:
            integration_key = config.get('integration_key')
            if not integration_key:
                logger.warning("No PagerDuty integration key configured")
                return
            
            # Create PagerDuty event
            payload = {
                "routing_key": integration_key,
                "event_action": "trigger",
                "dedup_key": alert.id,
                "payload": {
                    "summary": f"{alert.title}: {alert.description}",
                    "severity": alert.severity.value,
                    "source": "reVoAgent",
                    "component": alert.rule_name,
                    "custom_details": {
                        "value": alert.value,
                        "threshold": alert.threshold,
                        "alert_id": alert.id,
                        "timestamp": alert.timestamp.isoformat()
                    }
                }
            }
            
            # Send to PagerDuty
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://events.pagerduty.com/v2/enqueue",
                    json=payload
                ) as response:
                    if response.status != 202:
                        logger.error(f"PagerDuty notification failed: {response.status}")
            
        except Exception as e:
            logger.error(f"Error sending PagerDuty notification: {e}")
    
    async def _send_webhook_notification(self, alert: Alert, config: Dict[str, Any]):
        """Send webhook notification"""
        try:
            webhook_url = config.get('url')
            if not webhook_url:
                logger.warning("No webhook URL configured")
                return
            
            # Create webhook payload
            payload = {
                "alert": alert.to_dict(),
                "timestamp": datetime.now().isoformat(),
                "source": "revoagent_monitoring"
            }
            
            # Send webhook
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status not in [200, 201, 202]:
                        logger.error(f"Webhook notification failed: {response.status}")
            
        except Exception as e:
            logger.error(f"Error sending webhook notification: {e}")
    
    async def _save_alert(self, alert: Alert):
        """Save alert to storage"""
        try:
            alert_file = self.storage_path / f"alert_{alert.id}.json"
            async with aiofiles.open(alert_file, 'w') as f:
                await f.write(json.dumps(alert.to_dict(), indent=2))
        except Exception as e:
            logger.error(f"Error saving alert: {e}")
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert"""
        try:
            if alert_id not in self.active_alerts:
                return False
            
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.now()
            alert.acknowledged_by = acknowledged_by
            
            await self._save_alert(alert)
            logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
            return True
            
        except Exception as e:
            logger.error(f"Error acknowledging alert {alert_id}: {e}")
            return False
    
    async def resolve_alert(self, alert_id: str, resolved_by: str = "system") -> bool:
        """Resolve an alert"""
        try:
            if alert_id not in self.active_alerts:
                return False
            
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now()
            
            # Remove from active alerts
            del self.active_alerts[alert_id]
            
            await self._save_alert(alert)
            logger.info(f"Alert {alert_id} resolved by {resolved_by}")
            return True
            
        except Exception as e:
            logger.error(f"Error resolving alert {alert_id}: {e}")
            return False
    
    async def _resolve_alert(self, alert_id: str, reason: str):
        """Internal method to resolve alert"""
        await self.resolve_alert(alert_id, f"auto: {reason}")
    
    def add_metric_provider(self, provider: Callable):
        """Add a metric provider function"""
        self.metric_providers.append(provider)
    
    def configure_notification_channel(self, channel: NotificationChannel, config: Dict[str, Any]):
        """Configure notification channel"""
        self.notification_configs[channel] = NotificationConfig(
            channel=channel,
            config=config,
            enabled=True
        )
        logger.info(f"Configured notification channel: {channel.value}")
    
    def add_alert_rule(self, rule: AlertRule):
        """Add custom alert rule"""
        self.alert_rules[rule.name] = rule
        logger.info(f"Added alert rule: {rule.name}")
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary"""
        active_by_severity = defaultdict(int)
        for alert in self.active_alerts.values():
            active_by_severity[alert.severity.value] += 1
        
        return {
            "total_rules": len(self.alert_rules),
            "enabled_rules": len([r for r in self.alert_rules.values() if r.enabled]),
            "active_alerts": len(self.active_alerts),
            "alerts_by_severity": dict(active_by_severity),
            "total_alert_history": len(self.alert_history),
            "notification_channels": len(self.notification_configs),
            "is_running": self.is_running
        }
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """Get alert history for specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [alert for alert in self.alert_history if alert.timestamp > cutoff_time]

# Global instance
_alert_manager = None

async def get_alert_manager() -> AlertManager:
    """Get or create global alert manager instance"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager