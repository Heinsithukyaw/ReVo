#!/usr/bin/env python3
"""
GitHub Integration for reVoAgent
Complete GitHub API integration with webhooks, PR management, and repository operations
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import hmac
import hashlib
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class GitHubEventType(Enum):
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
    created_at: str
    updated_at: str
    mergeable: bool
    draft: bool

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
    created_at: str
    updated_at: str

class GitHubIntegration:
    """Complete GitHub integration for reVoAgent"""
    
    def __init__(self, token: str, webhook_secret: Optional[str] = None):
        self.token = token
        self.webhook_secret = webhook_secret
        self.base_url = "https://api.github.com"
        self.session = None
        
        # Event handlers
        self.event_handlers: Dict[GitHubEventType, List[callable]] = {
            event_type: [] for event_type in GitHubEventType
        }
        
        logger.info("GitHub Integration initialized")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "reVoAgent/1.0"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def register_event_handler(self, event_type: GitHubEventType, handler: callable):
        """Register an event handler for GitHub webhooks"""
        self.event_handlers[event_type].append(handler)
        logger.info(f"Registered handler for {event_type.value} events")
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify GitHub webhook signature"""
        if not self.webhook_secret:
            logger.warning("No webhook secret configured, skipping signature verification")
            return True
        
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected_signature}", signature)
    
    async def handle_webhook(self, payload: Dict[str, Any], event_type: str, signature: str = None) -> Dict[str, Any]:
        """Handle incoming GitHub webhook"""
        try:
            # Verify signature if provided
            if signature:
                payload_bytes = json.dumps(payload, separators=(',', ':')).encode()
                if not self.verify_webhook_signature(payload_bytes, signature):
                    raise ValueError("Invalid webhook signature")
            
            # Parse event type
            try:
                github_event = GitHubEventType(event_type)
            except ValueError:
                logger.warning(f"Unsupported GitHub event type: {event_type}")
                return {"status": "ignored", "reason": f"Unsupported event type: {event_type}"}
            
            # Process event
            result = await self._process_webhook_event(github_event, payload)
            
            # Call registered handlers
            for handler in self.event_handlers[github_event]:
                try:
                    await handler(payload, result)
                except Exception as e:
                    logger.error(f"Error in event handler: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _process_webhook_event(self, event_type: GitHubEventType, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process specific webhook events"""
        if event_type == GitHubEventType.PULL_REQUEST:
            return await self._handle_pull_request_event(payload)
        elif event_type == GitHubEventType.PUSH:
            return await self._handle_push_event(payload)
        elif event_type == GitHubEventType.ISSUES:
            return await self._handle_issue_event(payload)
        elif event_type == GitHubEventType.ISSUE_COMMENT:
            return await self._handle_issue_comment_event(payload)
        elif event_type == GitHubEventType.PULL_REQUEST_REVIEW:
            return await self._handle_pr_review_event(payload)
        else:
            return {"status": "processed", "event_type": event_type.value}
    
    async def _handle_pull_request_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pull request events"""
        action = payload.get("action")
        pr_data = payload.get("pull_request", {})
        
        pr = GitHubPullRequest(
            id=pr_data.get("id"),
            number=pr_data.get("number"),
            title=pr_data.get("title", ""),
            body=pr_data.get("body", ""),
            state=pr_data.get("state", ""),
            author=pr_data.get("user", {}).get("login", ""),
            base_branch=pr_data.get("base", {}).get("ref", ""),
            head_branch=pr_data.get("head", {}).get("ref", ""),
            created_at=pr_data.get("created_at", ""),
            updated_at=pr_data.get("updated_at", ""),
            mergeable=pr_data.get("mergeable", False),
            draft=pr_data.get("draft", False)
        )
        
        # Trigger automated code review for new PRs
        if action == "opened" and not pr.draft:
            await self._trigger_automated_review(payload.get("repository", {}), pr)
        
        return {
            "status": "processed",
            "event_type": "pull_request",
            "action": action,
            "pr_number": pr.number,
            "pr_title": pr.title
        }
    
    async def _handle_push_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle push events"""
        ref = payload.get("ref", "")
        commits = payload.get("commits", [])
        repository = payload.get("repository", {})
        
        # Trigger CI/CD workflows for main branch pushes
        if ref == f"refs/heads/{repository.get('default_branch', 'main')}":
            await self._trigger_ci_workflow(repository, commits)
        
        return {
            "status": "processed",
            "event_type": "push",
            "ref": ref,
            "commit_count": len(commits)
        }
    
    async def _handle_issue_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle issue events"""
        action = payload.get("action")
        issue_data = payload.get("issue", {})
        
        issue = GitHubIssue(
            id=issue_data.get("id"),
            number=issue_data.get("number"),
            title=issue_data.get("title", ""),
            body=issue_data.get("body", ""),
            state=issue_data.get("state", ""),
            author=issue_data.get("user", {}).get("login", ""),
            assignees=[a.get("login", "") for a in issue_data.get("assignees", [])],
            labels=[l.get("name", "") for l in issue_data.get("labels", [])],
            created_at=issue_data.get("created_at", ""),
            updated_at=issue_data.get("updated_at", "")
        )
        
        # Auto-assign issues based on labels
        if action == "opened":
            await self._auto_assign_issue(payload.get("repository", {}), issue)
        
        return {
            "status": "processed",
            "event_type": "issues",
            "action": action,
            "issue_number": issue.number
        }
    
    async def _handle_issue_comment_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle issue comment events"""
        action = payload.get("action")
        comment = payload.get("comment", {})
        issue = payload.get("issue", {})
        
        # Check for bot commands in comments
        if action == "created":
            await self._process_bot_commands(payload.get("repository", {}), issue, comment)
        
        return {
            "status": "processed",
            "event_type": "issue_comment",
            "action": action
        }
    
    async def _handle_pr_review_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pull request review events"""
        action = payload.get("action")
        review = payload.get("review", {})
        pr = payload.get("pull_request", {})
        
        return {
            "status": "processed",
            "event_type": "pull_request_review",
            "action": action,
            "review_state": review.get("state")
        }
    
    async def _trigger_automated_review(self, repository: Dict[str, Any], pr: GitHubPullRequest):
        """Trigger automated code review for a pull request"""
        try:
            # Get PR files
            files = await self.get_pr_files(repository["full_name"], pr.number)
            
            # Analyze code changes
            analysis_results = []
            for file in files:
                if file.get("patch"):  # Only analyze files with changes
                    # Here you would integrate with your code analysis agents
                    analysis = await self._analyze_code_changes(file)
                    analysis_results.append(analysis)
            
            # Post review comment
            if analysis_results:
                comment = self._format_review_comment(analysis_results)
                await self.create_pr_comment(repository["full_name"], pr.number, comment)
            
            logger.info(f"Automated review completed for PR #{pr.number}")
            
        except Exception as e:
            logger.error(f"Error in automated review: {e}")
    
    async def _trigger_ci_workflow(self, repository: Dict[str, Any], commits: List[Dict[str, Any]]):
        """Trigger CI/CD workflow for commits"""
        try:
            # Trigger workflow dispatch
            await self.trigger_workflow(
                repository["full_name"],
                "ci.yml",
                {"commits": [c.get("id") for c in commits]}
            )
            
            logger.info(f"CI workflow triggered for {len(commits)} commits")
            
        except Exception as e:
            logger.error(f"Error triggering CI workflow: {e}")
    
    async def _auto_assign_issue(self, repository: Dict[str, Any], issue: GitHubIssue):
        """Auto-assign issues based on labels and content"""
        try:
            assignee = None
            
            # Simple assignment logic based on labels
            if "bug" in issue.labels:
                assignee = "debug-team"
            elif "enhancement" in issue.labels:
                assignee = "feature-team"
            elif "documentation" in issue.labels:
                assignee = "docs-team"
            
            if assignee:
                await self.assign_issue(repository["full_name"], issue.number, [assignee])
                logger.info(f"Auto-assigned issue #{issue.number} to {assignee}")
            
        except Exception as e:
            logger.error(f"Error auto-assigning issue: {e}")
    
    async def _process_bot_commands(self, repository: Dict[str, Any], issue: Dict[str, Any], comment: Dict[str, Any]):
        """Process bot commands in issue comments"""
        try:
            body = comment.get("body", "").strip()
            
            if body.startswith("/revo"):
                command_parts = body.split()
                command = command_parts[1] if len(command_parts) > 1 else ""
                
                if command == "analyze":
                    await self._handle_analyze_command(repository, issue, comment)
                elif command == "review":
                    await self._handle_review_command(repository, issue, comment)
                elif command == "help":
                    await self._handle_help_command(repository, issue, comment)
            
        except Exception as e:
            logger.error(f"Error processing bot command: {e}")
    
    async def _analyze_code_changes(self, file: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code changes in a file"""
        # This would integrate with your code analysis agents
        return {
            "filename": file.get("filename"),
            "status": file.get("status"),
            "additions": file.get("additions", 0),
            "deletions": file.get("deletions", 0),
            "analysis": "Code analysis would go here",
            "suggestions": []
        }
    
    def _format_review_comment(self, analysis_results: List[Dict[str, Any]]) -> str:
        """Format automated review comment"""
        comment = "## 🤖 Automated Code Review\n\n"
        
        for result in analysis_results:
            comment += f"### {result['filename']}\n"
            comment += f"- **Status**: {result['status']}\n"
            comment += f"- **Changes**: +{result['additions']} -{result['deletions']}\n"
            comment += f"- **Analysis**: {result['analysis']}\n\n"
        
        comment += "---\n*This review was generated automatically by reVoAgent*"
        return comment
    
    # GitHub API Methods
    
    async def get_repository(self, repo_full_name: str) -> Dict[str, Any]:
        """Get repository information"""
        async with self.session.get(f"{self.base_url}/repos/{repo_full_name}") as response:
            response.raise_for_status()
            return await response.json()
    
    async def get_pull_requests(self, repo_full_name: str, state: str = "open") -> List[Dict[str, Any]]:
        """Get pull requests for a repository"""
        async with self.session.get(
            f"{self.base_url}/repos/{repo_full_name}/pulls",
            params={"state": state}
        ) as response:
            response.raise_for_status()
            return await response.json()
    
    async def get_pr_files(self, repo_full_name: str, pr_number: int) -> List[Dict[str, Any]]:
        """Get files changed in a pull request"""
        async with self.session.get(
            f"{self.base_url}/repos/{repo_full_name}/pulls/{pr_number}/files"
        ) as response:
            response.raise_for_status()
            return await response.json()
    
    async def create_pr_comment(self, repo_full_name: str, pr_number: int, body: str) -> Dict[str, Any]:
        """Create a comment on a pull request"""
        async with self.session.post(
            f"{self.base_url}/repos/{repo_full_name}/issues/{pr_number}/comments",
            json={"body": body}
        ) as response:
            response.raise_for_status()
            return await response.json()
    
    async def create_pr_review(self, repo_full_name: str, pr_number: int, 
                             event: str, body: str = None, comments: List[Dict] = None) -> Dict[str, Any]:
        """Create a review on a pull request"""
        data = {"event": event}
        if body:
            data["body"] = body
        if comments:
            data["comments"] = comments
        
        async with self.session.post(
            f"{self.base_url}/repos/{repo_full_name}/pulls/{pr_number}/reviews",
            json=data
        ) as response:
            response.raise_for_status()
            return await response.json()
    
    async def get_issues(self, repo_full_name: str, state: str = "open") -> List[Dict[str, Any]]:
        """Get issues for a repository"""
        async with self.session.get(
            f"{self.base_url}/repos/{repo_full_name}/issues",
            params={"state": state}
        ) as response:
            response.raise_for_status()
            return await response.json()
    
    async def create_issue(self, repo_full_name: str, title: str, body: str = None, 
                          assignees: List[str] = None, labels: List[str] = None) -> Dict[str, Any]:
        """Create a new issue"""
        data = {"title": title}
        if body:
            data["body"] = body
        if assignees:
            data["assignees"] = assignees
        if labels:
            data["labels"] = labels
        
        async with self.session.post(
            f"{self.base_url}/repos/{repo_full_name}/issues",
            json=data
        ) as response:
            response.raise_for_status()
            return await response.json()
    
    async def assign_issue(self, repo_full_name: str, issue_number: int, assignees: List[str]) -> Dict[str, Any]:
        """Assign users to an issue"""
        async with self.session.post(
            f"{self.base_url}/repos/{repo_full_name}/issues/{issue_number}/assignees",
            json={"assignees": assignees}
        ) as response:
            response.raise_for_status()
            return await response.json()
    
    async def trigger_workflow(self, repo_full_name: str, workflow_id: str, inputs: Dict[str, Any] = None) -> Dict[str, Any]:
        """Trigger a GitHub Actions workflow"""
        data = {"ref": "main"}
        if inputs:
            data["inputs"] = inputs
        
        async with self.session.post(
            f"{self.base_url}/repos/{repo_full_name}/actions/workflows/{workflow_id}/dispatches",
            json=data
        ) as response:
            response.raise_for_status()
            return {"status": "triggered"}
    
    async def get_workflow_runs(self, repo_full_name: str, workflow_id: str = None) -> List[Dict[str, Any]]:
        """Get workflow runs for a repository"""
        url = f"{self.base_url}/repos/{repo_full_name}/actions/runs"
        if workflow_id:
            url = f"{self.base_url}/repos/{repo_full_name}/actions/workflows/{workflow_id}/runs"
        
        async with self.session.get(url) as response:
            response.raise_for_status()
            data = await response.json()
            return data.get("workflow_runs", [])
    
    # Command handlers
    
    async def _handle_analyze_command(self, repository: Dict[str, Any], issue: Dict[str, Any], comment: Dict[str, Any]):
        """Handle /revo analyze command"""
        # Trigger code analysis
        analysis_result = "Code analysis initiated..."
        await self.create_issue_comment(repository["full_name"], issue["number"], 
                                       f"🔍 **Analysis Result**\n\n{analysis_result}")
    
    async def _handle_review_command(self, repository: Dict[str, Any], issue: Dict[str, Any], comment: Dict[str, Any]):
        """Handle /revo review command"""
        # Trigger code review
        review_result = "Code review initiated..."
        await self.create_issue_comment(repository["full_name"], issue["number"], 
                                       f"📝 **Review Result**\n\n{review_result}")
    
    async def _handle_help_command(self, repository: Dict[str, Any], issue: Dict[str, Any], comment: Dict[str, Any]):
        """Handle /revo help command"""
        help_text = """
## 🤖 reVoAgent Commands

- `/revo analyze` - Analyze code in the repository
- `/revo review` - Trigger automated code review
- `/revo help` - Show this help message

For more information, visit the [reVoAgent documentation](https://github.com/heinzdev11/reVoAgent).
        """
        await self.create_issue_comment(repository["full_name"], issue["number"], help_text)
    
    async def create_issue_comment(self, repo_full_name: str, issue_number: int, body: str) -> Dict[str, Any]:
        """Create a comment on an issue"""
        async with self.session.post(
            f"{self.base_url}/repos/{repo_full_name}/issues/{issue_number}/comments",
            json={"body": body}
        ) as response:
            response.raise_for_status()
            return await response.json()

# Example usage
async def example_usage():
    """Example usage of GitHub integration"""
    async with GitHubIntegration(token="your_github_token", webhook_secret="your_webhook_secret") as github:
        
        # Register event handlers
        async def handle_pr_opened(payload, result):
            print(f"PR opened: {result}")
        
        github.register_event_handler(GitHubEventType.PULL_REQUEST, handle_pr_opened)
        
        # Get repository info
        repo = await github.get_repository("owner/repo")
        print(f"Repository: {repo['name']}")
        
        # Get pull requests
        prs = await github.get_pull_requests("owner/repo")
        print(f"Open PRs: {len(prs)}")

if __name__ == "__main__":
    asyncio.run(example_usage())