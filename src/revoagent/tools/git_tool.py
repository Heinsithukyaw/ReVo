"""Git tool for reVoAgent platform."""

import asyncio
import subprocess
from typing import Dict, Any, List
from pathlib import Path

from .base import BaseTool


class GitTool(BaseTool):
    """
    Git version control tool for reVoAgent platform.
    
    Capabilities:
    - Repository initialization and cloning
    - File staging and committing
    - Branch management
    - Remote operations
    - Status and history queries
    """
    
    def get_description(self) -> str:
        """Get tool description."""
        return "Git version control operations including commit, push, pull, branch management, and repository status"
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get parameter schema."""
        return {
            "required": ["action"],
            "optional": ["repository", "branch", "message", "files", "remote", "url"],
            "actions": [
                "init", "clone", "status", "add", "commit", "push", "pull",
                "branch", "checkout", "merge", "log", "diff", "remote"
            ]
        }
    
    def get_capabilities(self) -> List[str]:
        """Get tool capabilities."""
        return [
            "repository_management",
            "version_control",
            "branch_operations",
            "remote_operations",
            "file_tracking"
        ]
    
    def get_dependencies(self) -> List[str]:
        """Get tool dependencies."""
        return ["git"]  # Git must be installed on the system
    
    async def execute(self, parameters: Dict[str, Any]) -> Any:
        """Execute git operations."""
        # Apply sandbox restrictions
        safe_params = self._apply_sandbox_restrictions(parameters)
        
        # Validate parameters
        if not self.validate_parameters(safe_params):
            raise ValueError("Invalid parameters for git tool")
        
        action = safe_params["action"]
        
        # Execute the appropriate git action
        if action == "init":
            return await self._git_init(safe_params)
        elif action == "clone":
            return await self._git_clone(safe_params)
        elif action == "status":
            return await self._git_status(safe_params)
        elif action == "add":
            return await self._git_add(safe_params)
        elif action == "commit":
            return await self._git_commit(safe_params)
        elif action == "push":
            return await self._git_push(safe_params)
        elif action == "pull":
            return await self._git_pull(safe_params)
        elif action == "branch":
            return await self._git_branch(safe_params)
        elif action == "checkout":
            return await self._git_checkout(safe_params)
        elif action == "log":
            return await self._git_log(safe_params)
        elif action == "diff":
            return await self._git_diff(safe_params)
        else:
            raise ValueError(f"Unsupported git action: {action}")
    
    async def _execute_git_command(self, command: List[str], cwd: str = None) -> Dict[str, Any]:
        """Execute a git command and return the result."""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                "success": process.returncode == 0,
                "returncode": process.returncode,
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore'),
                "command": " ".join(command)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": " ".join(command)
            }
    
    async def _git_init(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize a git repository."""
        repo_path = parameters.get("repository", ".")
        
        # Ensure directory exists
        Path(repo_path).mkdir(parents=True, exist_ok=True)
        
        result = await self._execute_git_command(["git", "init"], cwd=repo_path)
        
        if result["success"]:
            result["message"] = f"Initialized git repository in {repo_path}"
        
        return result
    
    async def _git_clone(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Clone a git repository."""
        url = parameters.get("url")
        if not url:
            raise ValueError("URL is required for git clone")
        
        destination = parameters.get("repository", ".")
        command = ["git", "clone", url]
        
        if destination != ".":
            command.append(destination)
        
        result = await self._execute_git_command(command)
        
        if result["success"]:
            result["message"] = f"Cloned repository from {url}"
        
        return result
    
    async def _git_status(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get git repository status."""
        repo_path = parameters.get("repository", ".")
        
        result = await self._execute_git_command(["git", "status", "--porcelain"], cwd=repo_path)
        
        if result["success"]:
            # Parse status output
            status_lines = result["stdout"].strip().split('\n') if result["stdout"].strip() else []
            
            modified_files = []
            untracked_files = []
            staged_files = []
            
            for line in status_lines:
                if len(line) >= 3:
                    status_code = line[:2]
                    filename = line[3:]
                    
                    if status_code[0] in ['M', 'A', 'D', 'R', 'C']:
                        staged_files.append(filename)
                    if status_code[1] in ['M', 'D']:
                        modified_files.append(filename)
                    if status_code == '??':
                        untracked_files.append(filename)
            
            result["parsed_status"] = {
                "staged_files": staged_files,
                "modified_files": modified_files,
                "untracked_files": untracked_files,
                "clean": len(status_lines) == 0
            }
        
        return result
    
    async def _git_add(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Add files to git staging area."""
        repo_path = parameters.get("repository", ".")
        files = parameters.get("files", ["."])
        
        if isinstance(files, str):
            files = [files]
        
        command = ["git", "add"] + files
        result = await self._execute_git_command(command, cwd=repo_path)
        
        if result["success"]:
            result["message"] = f"Added files to staging: {', '.join(files)}"
        
        return result
    
    async def _git_commit(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Commit changes to git repository."""
        repo_path = parameters.get("repository", ".")
        message = parameters.get("message", "Automated commit")
        
        command = ["git", "commit", "-m", message]
        result = await self._execute_git_command(command, cwd=repo_path)
        
        if result["success"]:
            result["message"] = f"Committed changes: {message}"
        
        return result
    
    async def _git_push(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Push changes to remote repository."""
        repo_path = parameters.get("repository", ".")
        remote = parameters.get("remote", "origin")
        branch = parameters.get("branch", "main")
        
        command = ["git", "push", remote, branch]
        result = await self._execute_git_command(command, cwd=repo_path)
        
        if result["success"]:
            result["message"] = f"Pushed to {remote}/{branch}"
        
        return result
    
    async def _git_pull(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Pull changes from remote repository."""
        repo_path = parameters.get("repository", ".")
        remote = parameters.get("remote", "origin")
        branch = parameters.get("branch", "main")
        
        command = ["git", "pull", remote, branch]
        result = await self._execute_git_command(command, cwd=repo_path)
        
        if result["success"]:
            result["message"] = f"Pulled from {remote}/{branch}"
        
        return result
    
    async def _git_branch(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Manage git branches."""
        repo_path = parameters.get("repository", ".")
        branch_name = parameters.get("branch")
        
        if branch_name:
            # Create new branch
            command = ["git", "branch", branch_name]
        else:
            # List branches
            command = ["git", "branch", "-a"]
        
        result = await self._execute_git_command(command, cwd=repo_path)
        
        if result["success"] and not branch_name:
            # Parse branch list
            branches = []
            current_branch = None
            
            for line in result["stdout"].split('\n'):
                line = line.strip()
                if line:
                    if line.startswith('* '):
                        current_branch = line[2:]
                        branches.append(line[2:])
                    else:
                        branches.append(line)
            
            result["branches"] = branches
            result["current_branch"] = current_branch
        
        return result
    
    async def _git_checkout(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Checkout a git branch or commit."""
        repo_path = parameters.get("repository", ".")
        branch = parameters.get("branch")
        
        if not branch:
            raise ValueError("Branch name is required for checkout")
        
        command = ["git", "checkout", branch]
        result = await self._execute_git_command(command, cwd=repo_path)
        
        if result["success"]:
            result["message"] = f"Checked out branch: {branch}"
        
        return result
    
    async def _git_log(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get git commit history."""
        repo_path = parameters.get("repository", ".")
        limit = parameters.get("limit", 10)
        
        command = ["git", "log", "--oneline", f"-{limit}"]
        result = await self._execute_git_command(command, cwd=repo_path)
        
        if result["success"]:
            # Parse log output
            commits = []
            for line in result["stdout"].split('\n'):
                line = line.strip()
                if line:
                    parts = line.split(' ', 1)
                    if len(parts) == 2:
                        commits.append({
                            "hash": parts[0],
                            "message": parts[1]
                        })
            
            result["commits"] = commits
        
        return result
    
    async def _git_diff(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get git diff."""
        repo_path = parameters.get("repository", ".")
        files = parameters.get("files", [])
        
        command = ["git", "diff"]
        if files:
            if isinstance(files, str):
                files = [files]
            command.extend(files)
        
        result = await self._execute_git_command(command, cwd=repo_path)
        
        return result
    
    async def _tool_specific_health_check(self) -> bool:
        """Check if git is available."""
        try:
            result = await self._execute_git_command(["git", "--version"])
            return result["success"]
        except Exception:
            return False