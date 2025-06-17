#!/usr/bin/env python3
"""
JIRA Integration for reVoAgent
Complete JIRA API integration with issue management, automation, and workflow integration
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import base64

logger = logging.getLogger(__name__)

class JiraIssueType(Enum):
    BUG = "Bug"
    TASK = "Task"
    STORY = "Story"
    EPIC = "Epic"
    SUBTASK = "Sub-task"

class JiraIssuePriority(Enum):
    LOWEST = "Lowest"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    HIGHEST = "Highest"

class JiraIssueStatus(Enum):
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"
    BLOCKED = "Blocked"
    REVIEW = "In Review"

@dataclass
class JiraUser:
    """JIRA user information"""
    account_id: str
    display_name: str
    email_address: str
    active: bool

@dataclass
class JiraProject:
    """JIRA project information"""
    id: str
    key: str
    name: str
    project_type: str
    lead: JiraUser

@dataclass
class JiraIssue:
    """JIRA issue information"""
    id: str
    key: str
    summary: str
    description: str
    issue_type: str
    status: str
    priority: str
    assignee: Optional[JiraUser]
    reporter: JiraUser
    project: str
    created: str
    updated: str
    labels: List[str]
    components: List[str]

class JiraIntegration:
    """Complete JIRA integration for reVoAgent"""
    
    def __init__(self, base_url: str, username: str, api_token: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.api_token = api_token
        self.session = None
        
        # Create basic auth header
        auth_string = f"{username}:{api_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        self.auth_header = f"Basic {auth_b64}"
        
        logger.info("JIRA Integration initialized")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": self.auth_header,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    # Core JIRA API Methods
    
    async def get_myself(self) -> JiraUser:
        """Get current user information"""
        async with self.session.get(f"{self.base_url}/rest/api/3/myself") as response:
            response.raise_for_status()
            data = await response.json()
            
            return JiraUser(
                account_id=data["accountId"],
                display_name=data["displayName"],
                email_address=data["emailAddress"],
                active=data["active"]
            )
    
    async def get_projects(self) -> List[JiraProject]:
        """Get all projects"""
        async with self.session.get(f"{self.base_url}/rest/api/3/project") as response:
            response.raise_for_status()
            data = await response.json()
            
            projects = []
            for project_data in data:
                lead_data = project_data.get("lead", {})
                lead = JiraUser(
                    account_id=lead_data.get("accountId", ""),
                    display_name=lead_data.get("displayName", ""),
                    email_address=lead_data.get("emailAddress", ""),
                    active=lead_data.get("active", True)
                )
                
                projects.append(JiraProject(
                    id=project_data["id"],
                    key=project_data["key"],
                    name=project_data["name"],
                    project_type=project_data.get("projectTypeKey", ""),
                    lead=lead
                ))
            
            return projects
    
    async def get_project(self, project_key: str) -> JiraProject:
        """Get specific project"""
        async with self.session.get(f"{self.base_url}/rest/api/3/project/{project_key}") as response:
            response.raise_for_status()
            data = await response.json()
            
            lead_data = data.get("lead", {})
            lead = JiraUser(
                account_id=lead_data.get("accountId", ""),
                display_name=lead_data.get("displayName", ""),
                email_address=lead_data.get("emailAddress", ""),
                active=lead_data.get("active", True)
            )
            
            return JiraProject(
                id=data["id"],
                key=data["key"],
                name=data["name"],
                project_type=data.get("projectTypeKey", ""),
                lead=lead
            )
    
    async def search_issues(self, jql: str, fields: List[str] = None, max_results: int = 50) -> List[JiraIssue]:
        """Search issues using JQL"""
        if fields is None:
            fields = ["summary", "description", "issuetype", "status", "priority", 
                     "assignee", "reporter", "project", "created", "updated", "labels", "components"]
        
        data = {
            "jql": jql,
            "fields": fields,
            "maxResults": max_results
        }
        
        async with self.session.post(f"{self.base_url}/rest/api/3/search", json=data) as response:
            response.raise_for_status()
            result = await response.json()
            
            issues = []
            for issue_data in result["issues"]:
                issues.append(self._parse_issue(issue_data))
            
            return issues
    
    async def get_issue(self, issue_key: str) -> JiraIssue:
        """Get specific issue"""
        async with self.session.get(f"{self.base_url}/rest/api/3/issue/{issue_key}") as response:
            response.raise_for_status()
            data = await response.json()
            
            return self._parse_issue(data)
    
    async def create_issue(self, project_key: str, summary: str, description: str = None,
                          issue_type: JiraIssueType = JiraIssueType.TASK,
                          priority: JiraIssuePriority = JiraIssuePriority.MEDIUM,
                          assignee_id: str = None, labels: List[str] = None,
                          components: List[str] = None) -> JiraIssue:
        """Create a new issue"""
        fields = {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type.value},
            "priority": {"name": priority.value}
        }
        
        if description:
            fields["description"] = {
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
            }
        
        if assignee_id:
            fields["assignee"] = {"accountId": assignee_id}
        
        if labels:
            fields["labels"] = labels
        
        if components:
            fields["components"] = [{"name": comp} for comp in components]
        
        data = {"fields": fields}
        
        async with self.session.post(f"{self.base_url}/rest/api/3/issue", json=data) as response:
            response.raise_for_status()
            result = await response.json()
            
            # Get the created issue
            return await self.get_issue(result["key"])
    
    async def update_issue(self, issue_key: str, fields: Dict[str, Any]) -> JiraIssue:
        """Update an existing issue"""
        data = {"fields": fields}
        
        async with self.session.put(f"{self.base_url}/rest/api/3/issue/{issue_key}", json=data) as response:
            response.raise_for_status()
            
            # Get the updated issue
            return await self.get_issue(issue_key)
    
    async def transition_issue(self, issue_key: str, transition_id: str, comment: str = None) -> Dict[str, Any]:
        """Transition an issue to a new status"""
        data = {
            "transition": {"id": transition_id}
        }
        
        if comment:
            data["update"] = {
                "comment": [
                    {
                        "add": {
                            "body": {
                                "type": "doc",
                                "version": 1,
                                "content": [
                                    {
                                        "type": "paragraph",
                                        "content": [
                                            {
                                                "type": "text",
                                                "text": comment
                                            }
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                ]
            }
        
        async with self.session.post(f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions", json=data) as response:
            response.raise_for_status()
            return {"status": "transitioned"}
    
    async def get_transitions(self, issue_key: str) -> List[Dict[str, Any]]:
        """Get available transitions for an issue"""
        async with self.session.get(f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions") as response:
            response.raise_for_status()
            data = await response.json()
            
            return data["transitions"]
    
    async def add_comment(self, issue_key: str, comment: str) -> Dict[str, Any]:
        """Add a comment to an issue"""
        data = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": comment
                            }
                        ]
                    }
                ]
            }
        }
        
        async with self.session.post(f"{self.base_url}/rest/api/3/issue/{issue_key}/comment", json=data) as response:
            response.raise_for_status()
            return await response.json()
    
    async def get_comments(self, issue_key: str) -> List[Dict[str, Any]]:
        """Get comments for an issue"""
        async with self.session.get(f"{self.base_url}/rest/api/3/issue/{issue_key}/comment") as response:
            response.raise_for_status()
            data = await response.json()
            
            return data["comments"]
    
    async def assign_issue(self, issue_key: str, assignee_id: str) -> JiraIssue:
        """Assign an issue to a user"""
        data = {
            "accountId": assignee_id
        }
        
        async with self.session.put(f"{self.base_url}/rest/api/3/issue/{issue_key}/assignee", json=data) as response:
            response.raise_for_status()
            
            return await self.get_issue(issue_key)
    
    async def add_watcher(self, issue_key: str, user_id: str) -> Dict[str, Any]:
        """Add a watcher to an issue"""
        async with self.session.post(f"{self.base_url}/rest/api/3/issue/{issue_key}/watchers", 
                                   json=user_id, headers={"Content-Type": "application/json"}) as response:
            response.raise_for_status()
            return {"status": "watcher_added"}
    
    async def link_issues(self, inward_issue: str, outward_issue: str, link_type: str = "Relates") -> Dict[str, Any]:
        """Link two issues"""
        data = {
            "type": {"name": link_type},
            "inwardIssue": {"key": inward_issue},
            "outwardIssue": {"key": outward_issue}
        }
        
        async with self.session.post(f"{self.base_url}/rest/api/3/issueLink", json=data) as response:
            response.raise_for_status()
            return {"status": "issues_linked"}
    
    # Helper methods
    
    def _parse_issue(self, issue_data: Dict[str, Any]) -> JiraIssue:
        """Parse issue data from JIRA API response"""
        fields = issue_data["fields"]
        
        # Parse assignee
        assignee = None
        if fields.get("assignee"):
            assignee_data = fields["assignee"]
            assignee = JiraUser(
                account_id=assignee_data["accountId"],
                display_name=assignee_data["displayName"],
                email_address=assignee_data.get("emailAddress", ""),
                active=assignee_data["active"]
            )
        
        # Parse reporter
        reporter_data = fields["reporter"]
        reporter = JiraUser(
            account_id=reporter_data["accountId"],
            display_name=reporter_data["displayName"],
            email_address=reporter_data.get("emailAddress", ""),
            active=reporter_data["active"]
        )
        
        # Parse description
        description = ""
        if fields.get("description"):
            # Extract text from Atlassian Document Format
            description = self._extract_text_from_adf(fields["description"])
        
        return JiraIssue(
            id=issue_data["id"],
            key=issue_data["key"],
            summary=fields["summary"],
            description=description,
            issue_type=fields["issuetype"]["name"],
            status=fields["status"]["name"],
            priority=fields["priority"]["name"],
            assignee=assignee,
            reporter=reporter,
            project=fields["project"]["key"],
            created=fields["created"],
            updated=fields["updated"],
            labels=fields.get("labels", []),
            components=[comp["name"] for comp in fields.get("components", [])]
        )
    
    def _extract_text_from_adf(self, adf_content: Dict[str, Any]) -> str:
        """Extract plain text from Atlassian Document Format"""
        def extract_text(node):
            if node.get("type") == "text":
                return node.get("text", "")
            elif "content" in node:
                return "".join(extract_text(child) for child in node["content"])
            return ""
        
        return extract_text(adf_content)
    
    # High-level automation methods
    
    async def create_bug_from_error(self, project_key: str, error_info: Dict[str, Any]) -> JiraIssue:
        """Create a bug issue from error information"""
        summary = f"Bug: {error_info.get('title', 'Unknown Error')}"
        
        description = f"""
**Error Details:**
- Service: {error_info.get('service', 'Unknown')}
- Error Message: {error_info.get('message', 'No message')}
- Timestamp: {error_info.get('timestamp', 'Unknown')}
- Severity: {error_info.get('severity', 'Unknown')}

**Stack Trace:**
```
{error_info.get('stack_trace', 'No stack trace available')}
```

**Environment:**
- Environment: {error_info.get('environment', 'Unknown')}
- Version: {error_info.get('version', 'Unknown')}

*This issue was automatically created by reVoAgent.*
        """
        
        priority = JiraIssuePriority.HIGH if error_info.get('severity') == 'critical' else JiraIssuePriority.MEDIUM
        
        return await self.create_issue(
            project_key=project_key,
            summary=summary,
            description=description,
            issue_type=JiraIssueType.BUG,
            priority=priority,
            labels=["auto-generated", "error", error_info.get('service', 'unknown')]
        )
    
    async def create_task_from_pr(self, project_key: str, pr_info: Dict[str, Any]) -> JiraIssue:
        """Create a task from pull request information"""
        summary = f"Review PR: {pr_info.get('title', 'Unknown PR')}"
        
        description = f"""
**Pull Request Details:**
- Repository: {pr_info.get('repository', 'Unknown')}
- PR Number: #{pr_info.get('number', 'Unknown')}
- Author: {pr_info.get('author', 'Unknown')}
- Branch: {pr_info.get('head_branch', 'Unknown')} → {pr_info.get('base_branch', 'Unknown')}

**Description:**
{pr_info.get('description', 'No description provided')}

**Link:** {pr_info.get('url', 'No URL')}

*This task was automatically created by reVoAgent.*
        """
        
        return await self.create_issue(
            project_key=project_key,
            summary=summary,
            description=description,
            issue_type=JiraIssueType.TASK,
            priority=JiraIssuePriority.MEDIUM,
            labels=["auto-generated", "code-review", "pr"]
        )
    
    async def update_issue_from_deployment(self, issue_key: str, deployment_info: Dict[str, Any]):
        """Update issue with deployment information"""
        comment = f"""
**Deployment Update:**
- Environment: {deployment_info.get('environment', 'Unknown')}
- Version: {deployment_info.get('version', 'Unknown')}
- Status: {deployment_info.get('status', 'Unknown')}
- Duration: {deployment_info.get('duration', 'Unknown')}
- Timestamp: {deployment_info.get('timestamp', 'Unknown')}

*Updated automatically by reVoAgent.*
        """
        
        await self.add_comment(issue_key, comment)
        
        # If deployment was successful, transition to done
        if deployment_info.get('status') == 'success':
            transitions = await self.get_transitions(issue_key)
            done_transition = next((t for t in transitions if 'done' in t['name'].lower()), None)
            
            if done_transition:
                await self.transition_issue(issue_key, done_transition['id'], 
                                          "Automatically resolved after successful deployment.")
    
    async def auto_assign_based_on_labels(self, issue_key: str, assignment_rules: Dict[str, str]):
        """Auto-assign issues based on labels and predefined rules"""
        issue = await self.get_issue(issue_key)
        
        for label in issue.labels:
            if label in assignment_rules:
                assignee_id = assignment_rules[label]
                await self.assign_issue(issue_key, assignee_id)
                await self.add_comment(issue_key, f"Automatically assigned based on label: {label}")
                break
    
    async def create_epic_from_feature_request(self, project_key: str, feature_info: Dict[str, Any]) -> JiraIssue:
        """Create an epic from feature request"""
        summary = f"Epic: {feature_info.get('title', 'New Feature')}"
        
        description = f"""
**Feature Request:**
{feature_info.get('description', 'No description provided')}

**Requirements:**
{feature_info.get('requirements', 'No requirements specified')}

**Acceptance Criteria:**
{feature_info.get('acceptance_criteria', 'No acceptance criteria specified')}

**Priority:** {feature_info.get('priority', 'Medium')}
**Estimated Effort:** {feature_info.get('effort', 'Unknown')}

*This epic was automatically created by reVoAgent.*
        """
        
        return await self.create_issue(
            project_key=project_key,
            summary=summary,
            description=description,
            issue_type=JiraIssueType.EPIC,
            priority=getattr(JiraIssuePriority, feature_info.get('priority', 'MEDIUM').upper()),
            labels=["auto-generated", "feature-request", "epic"]
        )
    
    # Reporting and analytics
    
    async def get_project_metrics(self, project_key: str) -> Dict[str, Any]:
        """Get project metrics and statistics"""
        # Get all issues for the project
        issues = await self.search_issues(f"project = {project_key}", max_results=1000)
        
        # Calculate metrics
        total_issues = len(issues)
        status_counts = {}
        priority_counts = {}
        type_counts = {}
        
        for issue in issues:
            # Count by status
            status_counts[issue.status] = status_counts.get(issue.status, 0) + 1
            
            # Count by priority
            priority_counts[issue.priority] = priority_counts.get(issue.priority, 0) + 1
            
            # Count by type
            type_counts[issue.issue_type] = type_counts.get(issue.issue_type, 0) + 1
        
        return {
            "project_key": project_key,
            "total_issues": total_issues,
            "status_distribution": status_counts,
            "priority_distribution": priority_counts,
            "type_distribution": type_counts,
            "generated_at": datetime.now().isoformat()
        }
    
    async def get_user_workload(self, user_id: str) -> Dict[str, Any]:
        """Get workload information for a user"""
        # Get assigned issues
        assigned_issues = await self.search_issues(f"assignee = {user_id} AND status != Done")
        
        # Calculate workload metrics
        total_assigned = len(assigned_issues)
        priority_breakdown = {}
        
        for issue in assigned_issues:
            priority_breakdown[issue.priority] = priority_breakdown.get(issue.priority, 0) + 1
        
        return {
            "user_id": user_id,
            "total_assigned": total_assigned,
            "priority_breakdown": priority_breakdown,
            "issues": [{"key": issue.key, "summary": issue.summary, "priority": issue.priority} 
                      for issue in assigned_issues],
            "generated_at": datetime.now().isoformat()
        }

# Example usage
async def example_usage():
    """Example usage of JIRA integration"""
    async with JiraIntegration(
        base_url="https://your-domain.atlassian.net",
        username="your-email@example.com",
        api_token="your-api-token"
    ) as jira:
        
        # Get current user
        user = await jira.get_myself()
        print(f"Current user: {user.display_name}")
        
        # Get projects
        projects = await jira.get_projects()
        print(f"Projects: {[p.name for p in projects]}")
        
        # Create a bug issue
        bug_info = {
            "title": "API Error 500",
            "service": "user-service",
            "message": "Internal server error",
            "severity": "high",
            "timestamp": datetime.now().isoformat()
        }
        
        if projects:
            bug_issue = await jira.create_bug_from_error(projects[0].key, bug_info)
            print(f"Created bug: {bug_issue.key}")

if __name__ == "__main__":
    asyncio.run(example_usage())