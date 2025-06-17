#!/usr/bin/env python3
"""
Enhanced GitHub Integration with API Gateway and Resilience Patterns
Improved GitHub integration using the API Gateway for rate limiting, retry logic, and monitoring
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .api_gateway import (
    APIGateway, IntegrationType, IntegrationConfig, APIRequest, APIResponse,
    RequestMethod, RetryStrategy, RateLimitConfig, RetryConfig, TimeoutConfig,
    get_api_gateway
)
from .webhook_manager import (
    WebhookManager, WebhookEventType, WebhookConfig, WebhookHandler,
    get_webhook_manager
)
from .integration_monitor import (
    IntegrationMonitor, HealthCheck, AlertRule, AlertSeverity, Metric, MetricType,
    get_integration_monitor
)

logger = logging.getLogger(__name__)

class GitHubEventType(Enum):
    """GitHub webhook event types"""
    PUSH = "push"
    PULL_REQUEST = "pull_request"
    ISSUES = "issues"
    ISSUE_COMMENT = "issue_comment"
    PULL_REQUEST_REVIEW = "pull_request_review"
    RELEASE = "release"
    WORKFLOW_RUN = "workflow_run"

@dataclass
class GitHubRepository:
    """GitHub repository information"""
    id: int
    name: str
    full_name: str
    owner: str
    private: bool
    clone_url: str
    ssh_url: str
    default_branch: str
    description: Optional[str] = None
    language: Optional[str] = None
    stars: int = 0
    forks: int = 0
    open_issues: int = 0

@dataclass
class GitHubPullRequest:
    """GitHub pull request information"""
    id: int
    number: int
    title: str
    body: str
    state: str
    author: str
    base_branch: str
    head_branch: str
    mergeable: Optional[bool] = None
    draft: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class GitHubIssue:
    """GitHub issue information"""
    id: int
    number: int
    title: str
    body: str
    state: str
    author: str
    assignees: List[str]
    labels: List[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class EnhancedGitHubIntegration:
    """Enhanced GitHub integration with resilience patterns"""
    
    def __init__(
        self, 
        api_token: str,
        webhook_secret: Optional[str] = None,
        redis_url: Optional[str] = None
    ):
        self.api_token = api_token
        self.webhook_secret = webhook_secret
        self.redis_url = redis_url
        
        self.api_gateway: Optional[APIGateway] = None
        self.webhook_manager: Optional[WebhookManager] = None
        self.monitor: Optional[IntegrationMonitor] = None
        
        # Cache for frequently accessed data
        self.repo_cache: Dict[str, GitHubRepository] = {}
        self.user_cache: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self):
        """Initialize the GitHub integration"""
        # Get shared instances
        self.api_gateway = await get_api_gateway(self.redis_url)
        self.webhook_manager = await get_webhook_manager(self.redis_url)
        self.monitor = await get_integration_monitor(self.redis_url)
        
        # Configure GitHub integration
        github_config = IntegrationConfig(
            integration_type=IntegrationType.GITHUB,
            base_url="https://api.github.com",
            api_key=self.api_token,
            headers={
                "Authorization": f"token {self.api_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "reVoAgent/1.0"
            },
            rate_limit=RateLimitConfig(
                requests_per_minute=5000,  # GitHub's rate limit
                requests_per_hour=5000,
                burst_limit=100
            ),
            retry=RetryConfig(
                max_attempts=3,
                strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                base_delay=1.0,
                max_delay=60.0
            ),
            timeout=TimeoutConfig(
                connect_timeout=10.0,
                read_timeout=30.0,
                total_timeout=60.0
            ),
            cache_ttl=3600  # 1 hour cache for repository metadata
        )
        
        self.api_gateway.register_integration(github_config)
        
        # Configure webhook handling
        if self.webhook_secret:
            webhook_config = WebhookConfig(
                event_type=WebhookEventType.GITHUB_PUSH,
                endpoint="/webhooks/github",
                secret=self.webhook_secret,
                max_retries=3,
                retry_delay=5.0,
                timeout=30.0,
                rate_limit=1000
            )
            self.webhook_manager.register_webhook(webhook_config)
            
            # Register webhook handlers
            for event_type in [
                WebhookEventType.GITHUB_PUSH,
                WebhookEventType.GITHUB_PR,
                WebhookEventType.GITHUB_ISSUE
            ]:
                handler = WebhookHandler(
                    event_type=event_type,
                    handler_func=self._handle_webhook_event,
                    async_handler=True,
                    priority=1
                )
                self.webhook_manager.register_handler(handler)
        
        # Configure monitoring
        health_check = HealthCheck(
            name="github_api",
            endpoint="https://api.github.com/rate_limit",
            method="GET",
            timeout=10.0,
            interval=60.0,
            expected_status=200,
            headers={"Authorization": f"token {self.api_token}"}
        )
        self.monitor.register_health_check(health_check)
        
        # Configure alerts
        alert_rules = [
            AlertRule(
                name="github_high_error_rate",
                metric_name="github_error_rate",
                condition="> 5",
                severity=AlertSeverity.WARNING,
                description="GitHub API error rate is high"
            ),
            AlertRule(
                name="github_slow_response",
                metric_name="github_response_time",
                condition="> 5",
                severity=AlertSeverity.WARNING,
                description="GitHub API response time is slow"
            ),
            AlertRule(
                name="github_rate_limit_exceeded",
                metric_name="github_rate_limit_remaining",
                condition="< 100",
                severity=AlertSeverity.CRITICAL,
                description="GitHub API rate limit nearly exceeded"
            )
        ]
        
        for rule in alert_rules:
            self.monitor.register_alert_rule(rule)
            
        logger.info("Enhanced GitHub integration initialized")
        
    async def get_repository(self, owner: str, repo: str) -> GitHubRepository:
        """Get repository information with caching"""
        cache_key = f"{owner}/{repo}"
        
        # Check cache first
        if cache_key in self.repo_cache:
            cached_repo = self.repo_cache[cache_key]
            # Cache for 1 hour
            if (datetime.now() - getattr(cached_repo, '_cached_at', datetime.min)).total_seconds() < 3600:
                return cached_repo
        
        # Make API request
        request = APIRequest(
            method=RequestMethod.GET,
            endpoint=f"/repos/{owner}/{repo}",
            cache_key=f"repo_{owner}_{repo}",
            cache_ttl=3600
        )
        
        try:
            response = await self.api_gateway.make_request(IntegrationType.GITHUB, request)
            
            if response.status_code == 200:
                data = response.data
                repository = GitHubRepository(
                    id=data["id"],
                    name=data["name"],
                    full_name=data["full_name"],
                    owner=data["owner"]["login"],
                    private=data["private"],
                    clone_url=data["clone_url"],
                    ssh_url=data["ssh_url"],
                    default_branch=data["default_branch"],
                    description=data.get("description"),
                    language=data.get("language"),
                    stars=data.get("stargazers_count", 0),
                    forks=data.get("forks_count", 0),
                    open_issues=data.get("open_issues_count", 0)
                )
                
                # Cache the result
                setattr(repository, '_cached_at', datetime.now())
                self.repo_cache[cache_key] = repository
                
                # Record metrics
                await self._record_api_metrics("get_repository", response.response_time, True)
                
                return repository
            else:
                await self._record_api_metrics("get_repository", response.response_time, False)
                raise Exception(f"GitHub API error: {response.status_code}")
                
        except Exception as e:
            await self._record_api_metrics("get_repository", 0, False)
            logger.error(f"Failed to get repository {owner}/{repo}: {e}")
            raise e
            
    async def get_pull_requests(
        self, 
        owner: str, 
        repo: str, 
        state: str = "open",
        limit: int = 30
    ) -> List[GitHubPullRequest]:
        """Get pull requests for repository"""
        request = APIRequest(
            method=RequestMethod.GET,
            endpoint=f"/repos/{owner}/{repo}/pulls",
            params={
                "state": state,
                "per_page": min(limit, 100),
                "sort": "updated",
                "direction": "desc"
            },
            cache_key=f"prs_{owner}_{repo}_{state}",
            cache_ttl=300  # 5 minutes cache
        )
        
        try:
            response = await self.api_gateway.make_request(IntegrationType.GITHUB, request)
            
            if response.status_code == 200:
                pull_requests = []
                for pr_data in response.data:
                    pr = GitHubPullRequest(
                        id=pr_data["id"],
                        number=pr_data["number"],
                        title=pr_data["title"],
                        body=pr_data["body"] or "",
                        state=pr_data["state"],
                        author=pr_data["user"]["login"],
                        base_branch=pr_data["base"]["ref"],
                        head_branch=pr_data["head"]["ref"],
                        mergeable=pr_data.get("mergeable"),
                        draft=pr_data.get("draft", False),
                        created_at=datetime.fromisoformat(pr_data["created_at"].replace("Z", "+00:00")),
                        updated_at=datetime.fromisoformat(pr_data["updated_at"].replace("Z", "+00:00"))
                    )
                    pull_requests.append(pr)
                    
                await self._record_api_metrics("get_pull_requests", response.response_time, True)
                return pull_requests
            else:
                await self._record_api_metrics("get_pull_requests", response.response_time, False)
                raise Exception(f"GitHub API error: {response.status_code}")
                
        except Exception as e:
            await self._record_api_metrics("get_pull_requests", 0, False)
            logger.error(f"Failed to get pull requests for {owner}/{repo}: {e}")
            raise e
            
    async def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main"
    ) -> GitHubPullRequest:
        """Create a new pull request"""
        request = APIRequest(
            method=RequestMethod.POST,
            endpoint=f"/repos/{owner}/{repo}/pulls",
            json_data={
                "title": title,
                "body": body,
                "head": head_branch,
                "base": base_branch
            }
        )
        
        try:
            response = await self.api_gateway.make_request(IntegrationType.GITHUB, request)
            
            if response.status_code == 201:
                pr_data = response.data
                pr = GitHubPullRequest(
                    id=pr_data["id"],
                    number=pr_data["number"],
                    title=pr_data["title"],
                    body=pr_data["body"] or "",
                    state=pr_data["state"],
                    author=pr_data["user"]["login"],
                    base_branch=pr_data["base"]["ref"],
                    head_branch=pr_data["head"]["ref"],
                    mergeable=pr_data.get("mergeable"),
                    draft=pr_data.get("draft", False),
                    created_at=datetime.fromisoformat(pr_data["created_at"].replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(pr_data["updated_at"].replace("Z", "+00:00"))
                )
                
                await self._record_api_metrics("create_pull_request", response.response_time, True)
                logger.info(f"Created pull request #{pr.number} in {owner}/{repo}")
                return pr
            else:
                await self._record_api_metrics("create_pull_request", response.response_time, False)
                raise Exception(f"GitHub API error: {response.status_code} - {response.data}")
                
        except Exception as e:
            await self._record_api_metrics("create_pull_request", 0, False)
            logger.error(f"Failed to create pull request in {owner}/{repo}: {e}")
            raise e
            
    async def get_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        limit: int = 30
    ) -> List[GitHubIssue]:
        """Get issues for repository"""
        request = APIRequest(
            method=RequestMethod.GET,
            endpoint=f"/repos/{owner}/{repo}/issues",
            params={
                "state": state,
                "per_page": min(limit, 100),
                "sort": "updated",
                "direction": "desc"
            },
            cache_key=f"issues_{owner}_{repo}_{state}",
            cache_ttl=300  # 5 minutes cache
        )
        
        try:
            response = await self.api_gateway.make_request(IntegrationType.GITHUB, request)
            
            if response.status_code == 200:
                issues = []
                for issue_data in response.data:
                    # Skip pull requests (they appear in issues API)
                    if "pull_request" in issue_data:
                        continue
                        
                    issue = GitHubIssue(
                        id=issue_data["id"],
                        number=issue_data["number"],
                        title=issue_data["title"],
                        body=issue_data["body"] or "",
                        state=issue_data["state"],
                        author=issue_data["user"]["login"],
                        assignees=[assignee["login"] for assignee in issue_data.get("assignees", [])],
                        labels=[label["name"] for label in issue_data.get("labels", [])],
                        created_at=datetime.fromisoformat(issue_data["created_at"].replace("Z", "+00:00")),
                        updated_at=datetime.fromisoformat(issue_data["updated_at"].replace("Z", "+00:00"))
                    )
                    issues.append(issue)
                    
                await self._record_api_metrics("get_issues", response.response_time, True)
                return issues
            else:
                await self._record_api_metrics("get_issues", response.response_time, False)
                raise Exception(f"GitHub API error: {response.status_code}")
                
        except Exception as e:
            await self._record_api_metrics("get_issues", 0, False)
            logger.error(f"Failed to get issues for {owner}/{repo}: {e}")
            raise e
            
    async def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None
    ) -> GitHubIssue:
        """Create a new issue"""
        issue_data = {
            "title": title,
            "body": body
        }
        
        if labels:
            issue_data["labels"] = labels
        if assignees:
            issue_data["assignees"] = assignees
            
        request = APIRequest(
            method=RequestMethod.POST,
            endpoint=f"/repos/{owner}/{repo}/issues",
            json_data=issue_data
        )
        
        try:
            response = await self.api_gateway.make_request(IntegrationType.GITHUB, request)
            
            if response.status_code == 201:
                issue_data = response.data
                issue = GitHubIssue(
                    id=issue_data["id"],
                    number=issue_data["number"],
                    title=issue_data["title"],
                    body=issue_data["body"] or "",
                    state=issue_data["state"],
                    author=issue_data["user"]["login"],
                    assignees=[assignee["login"] for assignee in issue_data.get("assignees", [])],
                    labels=[label["name"] for label in issue_data.get("labels", [])],
                    created_at=datetime.fromisoformat(issue_data["created_at"].replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(issue_data["updated_at"].replace("Z", "+00:00"))
                )
                
                await self._record_api_metrics("create_issue", response.response_time, True)
                logger.info(f"Created issue #{issue.number} in {owner}/{repo}")
                return issue
            else:
                await self._record_api_metrics("create_issue", response.response_time, False)
                raise Exception(f"GitHub API error: {response.status_code} - {response.data}")
                
        except Exception as e:
            await self._record_api_metrics("create_issue", 0, False)
            logger.error(f"Failed to create issue in {owner}/{repo}: {e}")
            raise e
            
    async def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status"""
        request = APIRequest(
            method=RequestMethod.GET,
            endpoint="/rate_limit"
        )
        
        try:
            response = await self.api_gateway.make_request(IntegrationType.GITHUB, request)
            
            if response.status_code == 200:
                rate_limit_data = response.data["rate"]
                
                # Record rate limit metrics
                await self.monitor.record_metric(Metric(
                    name="github_rate_limit_remaining",
                    value=rate_limit_data["remaining"],
                    metric_type=MetricType.GAUGE
                ))
                
                await self.monitor.record_metric(Metric(
                    name="github_rate_limit_used",
                    value=rate_limit_data["used"],
                    metric_type=MetricType.GAUGE
                ))
                
                return {
                    "limit": rate_limit_data["limit"],
                    "remaining": rate_limit_data["remaining"],
                    "used": rate_limit_data["used"],
                    "reset_at": datetime.fromtimestamp(rate_limit_data["reset"])
                }
            else:
                raise Exception(f"GitHub API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to get rate limit status: {e}")
            raise e
            
    async def _handle_webhook_event(self, event):
        """Handle GitHub webhook events"""
        try:
            event_type = event.payload.get("action", "unknown")
            
            if event.event_type == WebhookEventType.GITHUB_PUSH:
                await self._handle_push_event(event.payload)
            elif event.event_type == WebhookEventType.GITHUB_PR:
                await self._handle_pull_request_event(event.payload)
            elif event.event_type == WebhookEventType.GITHUB_ISSUE:
                await self._handle_issue_event(event.payload)
                
            logger.info(f"Processed GitHub webhook: {event.event_type.value} - {event_type}")
            
        except Exception as e:
            logger.error(f"Error handling GitHub webhook: {e}")
            raise e
            
    async def _handle_push_event(self, payload: Dict[str, Any]):
        """Handle push webhook event"""
        repository = payload["repository"]["full_name"]
        branch = payload["ref"].replace("refs/heads/", "")
        commits = payload["commits"]
        
        logger.info(f"Push to {repository}:{branch} with {len(commits)} commits")
        
        # Record metrics
        await self.monitor.record_metric(Metric(
            name="github_push_events",
            value=1,
            metric_type=MetricType.COUNTER,
            labels={"repository": repository, "branch": branch}
        ))
        
    async def _handle_pull_request_event(self, payload: Dict[str, Any]):
        """Handle pull request webhook event"""
        action = payload["action"]
        pr = payload["pull_request"]
        repository = payload["repository"]["full_name"]
        
        logger.info(f"Pull request {action} in {repository}: #{pr['number']}")
        
        # Record metrics
        await self.monitor.record_metric(Metric(
            name="github_pr_events",
            value=1,
            metric_type=MetricType.COUNTER,
            labels={"repository": repository, "action": action}
        ))
        
    async def _handle_issue_event(self, payload: Dict[str, Any]):
        """Handle issue webhook event"""
        action = payload["action"]
        issue = payload["issue"]
        repository = payload["repository"]["full_name"]
        
        logger.info(f"Issue {action} in {repository}: #{issue['number']}")
        
        # Record metrics
        await self.monitor.record_metric(Metric(
            name="github_issue_events",
            value=1,
            metric_type=MetricType.COUNTER,
            labels={"repository": repository, "action": action}
        ))
        
    async def _record_api_metrics(self, operation: str, response_time: float, success: bool):
        """Record API operation metrics"""
        if self.monitor:
            # Record response time
            await self.monitor.record_metric(Metric(
                name="github_response_time",
                value=response_time,
                metric_type=MetricType.GAUGE,
                labels={"operation": operation}
            ))
            
            # Record success/failure
            await self.monitor.record_metric(Metric(
                name="github_operation_success" if success else "github_operation_failure",
                value=1,
                metric_type=MetricType.COUNTER,
                labels={"operation": operation}
            ))
            
    async def get_integration_status(self) -> Dict[str, Any]:
        """Get integration status and health"""
        if self.monitor:
            return await self.monitor.get_integration_status("github_api")
        else:
            return {"status": "not_monitored"}

# Global GitHub integration instance
_github_integration_instance: Optional[EnhancedGitHubIntegration] = None

async def get_github_integration(
    api_token: str,
    webhook_secret: Optional[str] = None,
    redis_url: Optional[str] = None
) -> EnhancedGitHubIntegration:
    """Get or create the global GitHub integration instance"""
    global _github_integration_instance
    
    if _github_integration_instance is None:
        _github_integration_instance = EnhancedGitHubIntegration(
            api_token=api_token,
            webhook_secret=webhook_secret,
            redis_url=redis_url
        )
        await _github_integration_instance.initialize()
        
    return _github_integration_instance