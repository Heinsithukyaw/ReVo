"""
OpenHands Integration - Multi-modal AI Agent Capabilities

Integrates OpenHands platform capabilities into reVoAgent for enhanced
software development automation and multi-modal agent interactions.
"""

import asyncio
import logging
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import httpx

logger = logging.getLogger(__name__)


class OpenHandsAgentType(Enum):
    """OpenHands agent types."""
    CODEACT = "codeact_agent"
    BROWSING = "browsing_agent"
    VISUAL_BROWSING = "visualbrowsing_agent"
    LOC = "loc_agent"
    READONLY = "readonly_agent"


class OpenHandsRuntime(Enum):
    """OpenHands runtime types."""
    DOCKER = "docker"
    E2B = "e2b"
    LOCAL = "local"


@dataclass
class OpenHandsConfig:
    """Configuration for OpenHands integration."""
    agent_type: OpenHandsAgentType = OpenHandsAgentType.CODEACT
    runtime: OpenHandsRuntime = OpenHandsRuntime.DOCKER
    model_name: str = "local/deepseek-coder"
    max_iterations: int = 30
    workspace_dir: Optional[str] = None
    sandbox_container_image: str = "docker.all-hands.dev/all-hands-ai/runtime:0.41-nikolaik"
    enable_auto_lint: bool = True
    enable_browsing: bool = True
    enable_github_integration: bool = False
    github_token: Optional[str] = None
    custom_instructions: Optional[str] = None


@dataclass
class OpenHandsTask:
    """Task definition for OpenHands."""
    instruction: str
    task_type: str = "general"
    files: Optional[List[str]] = None
    repository_url: Optional[str] = None
    issue_number: Optional[int] = None
    context: Optional[Dict[str, Any]] = None


@dataclass
class OpenHandsResult:
    """Result from OpenHands execution."""
    success: bool
    task_id: str
    agent_type: str
    iterations: int
    final_state: str
    outputs: List[Dict[str, Any]]
    files_modified: List[str]
    commands_executed: List[str]
    error_message: Optional[str] = None
    execution_time: Optional[float] = None


class OpenHandsIntegration:
    """Integration with OpenHands platform for enhanced agent capabilities."""
    
    def __init__(self, config: OpenHandsConfig):
        self.config = config
        self.client = httpx.AsyncClient(timeout=300.0)
        self.server_process: Optional[subprocess.Popen] = None
        self.server_url = "http://localhost:3000"
        self.is_running = False
        self.workspace_dir = Path(config.workspace_dir or tempfile.mkdtemp())
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
    async def start_server(self) -> bool:
        """Start OpenHands server."""
        if self.is_running:
            return True
            
        try:
            # Check if OpenHands is available
            openhands_path = self._find_openhands_installation()
            if not openhands_path:
                logger.error("OpenHands installation not found")
                return False
            
            # Start OpenHands server
            env = self._prepare_environment()
            cmd = [
                "python", "-m", "openhands.server.listen",
                "--host", "0.0.0.0",
                "--port", "3000",
                "--workspace-dir", str(self.workspace_dir)
            ]
            
            logger.info(f"Starting OpenHands server: {' '.join(cmd)}")
            
            self.server_process = subprocess.Popen(
                cmd,
                cwd=openhands_path,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server to be ready
            if await self._wait_for_server():
                self.is_running = True
                logger.info("OpenHands server started successfully")
                return True
            else:
                logger.error("Failed to start OpenHands server")
                await self.stop_server()
                return False
                
        except Exception as e:
            logger.error(f"Error starting OpenHands server: {e}")
            return False
    
    async def stop_server(self):
        """Stop OpenHands server."""
        if self.server_process:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
                self.server_process.wait()
            self.server_process = None
        
        self.is_running = False
        await self.client.aclose()
        logger.info("OpenHands server stopped")
    
    async def execute_task(self, task: OpenHandsTask) -> OpenHandsResult:
        """Execute a task using OpenHands."""
        if not self.is_running:
            if not await self.start_server():
                return OpenHandsResult(
                    success=False,
                    task_id="",
                    agent_type=self.config.agent_type.value,
                    iterations=0,
                    final_state="error",
                    outputs=[],
                    files_modified=[],
                    commands_executed=[],
                    error_message="Failed to start OpenHands server"
                )
        
        try:
            import time
            start_time = time.time()
            
            # Create session
            session_data = await self._create_session(task)
            if not session_data:
                raise RuntimeError("Failed to create OpenHands session")
            
            session_id = session_data["session_id"]
            
            # Execute task
            result = await self._execute_session(session_id, task)
            
            execution_time = time.time() - start_time
            result.execution_time = execution_time
            
            logger.info(f"OpenHands task completed in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error executing OpenHands task: {e}")
            return OpenHandsResult(
                success=False,
                task_id=task.instruction[:50],
                agent_type=self.config.agent_type.value,
                iterations=0,
                final_state="error",
                outputs=[],
                files_modified=[],
                commands_executed=[],
                error_message=str(e)
            )
    
    async def _create_session(self, task: OpenHandsTask) -> Optional[Dict[str, Any]]:
        """Create a new OpenHands session."""
        try:
            payload = {
                "agent": self.config.agent_type.value,
                "runtime": self.config.runtime.value,
                "model": self.config.model_name,
                "max_iterations": self.config.max_iterations,
                "workspace_dir": str(self.workspace_dir),
                "sandbox_container_image": self.config.sandbox_container_image,
                "enable_auto_lint": self.config.enable_auto_lint,
                "enable_browsing": self.config.enable_browsing
            }
            
            if self.config.custom_instructions:
                payload["custom_instructions"] = self.config.custom_instructions
            
            if task.repository_url:
                payload["repository_url"] = task.repository_url
            
            response = await self.client.post(
                f"{self.server_url}/api/sessions",
                json=payload
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return None
    
    async def _execute_session(self, session_id: str, task: OpenHandsTask) -> OpenHandsResult:
        """Execute a task in an OpenHands session."""
        try:
            # Send initial instruction
            message_payload = {
                "message": task.instruction,
                "type": "user"
            }
            
            if task.files:
                message_payload["files"] = task.files
            
            if task.context:
                message_payload["context"] = task.context
            
            response = await self.client.post(
                f"{self.server_url}/api/sessions/{session_id}/messages",
                json=message_payload
            )
            response.raise_for_status()
            
            # Poll for completion
            result = await self._poll_session_completion(session_id)
            return result
            
        except Exception as e:
            logger.error(f"Error executing session: {e}")
            return OpenHandsResult(
                success=False,
                task_id=session_id,
                agent_type=self.config.agent_type.value,
                iterations=0,
                final_state="error",
                outputs=[],
                files_modified=[],
                commands_executed=[],
                error_message=str(e)
            )
    
    async def _poll_session_completion(self, session_id: str) -> OpenHandsResult:
        """Poll session until completion."""
        max_polls = 300  # 5 minutes with 1s intervals
        poll_count = 0
        
        outputs = []
        files_modified = []
        commands_executed = []
        iterations = 0
        
        while poll_count < max_polls:
            try:
                response = await self.client.get(
                    f"{self.server_url}/api/sessions/{session_id}/status"
                )
                response.raise_for_status()
                
                status_data = response.json()
                state = status_data.get("state", "running")
                
                # Get latest events
                events_response = await self.client.get(
                    f"{self.server_url}/api/sessions/{session_id}/events"
                )
                events_response.raise_for_status()
                
                events = events_response.json().get("events", [])
                
                # Process events
                for event in events:
                    if event.get("type") == "action":
                        action_type = event.get("action", {}).get("action")
                        if action_type == "run":
                            command = event.get("action", {}).get("command", "")
                            if command and command not in commands_executed:
                                commands_executed.append(command)
                        elif action_type == "write":
                            file_path = event.get("action", {}).get("path", "")
                            if file_path and file_path not in files_modified:
                                files_modified.append(file_path)
                    
                    elif event.get("type") == "observation":
                        outputs.append(event)
                
                iterations = len([e for e in events if e.get("type") == "action"])
                
                # Check if completed
                if state in ["finished", "completed", "success"]:
                    return OpenHandsResult(
                        success=True,
                        task_id=session_id,
                        agent_type=self.config.agent_type.value,
                        iterations=iterations,
                        final_state=state,
                        outputs=outputs,
                        files_modified=files_modified,
                        commands_executed=commands_executed
                    )
                elif state in ["error", "failed"]:
                    error_msg = status_data.get("error", "Unknown error")
                    return OpenHandsResult(
                        success=False,
                        task_id=session_id,
                        agent_type=self.config.agent_type.value,
                        iterations=iterations,
                        final_state=state,
                        outputs=outputs,
                        files_modified=files_modified,
                        commands_executed=commands_executed,
                        error_message=error_msg
                    )
                
                await asyncio.sleep(1)
                poll_count += 1
                
            except Exception as e:
                logger.error(f"Error polling session: {e}")
                await asyncio.sleep(1)
                poll_count += 1
        
        # Timeout
        return OpenHandsResult(
            success=False,
            task_id=session_id,
            agent_type=self.config.agent_type.value,
            iterations=iterations,
            final_state="timeout",
            outputs=outputs,
            files_modified=files_modified,
            commands_executed=commands_executed,
            error_message="Session execution timeout"
        )
    
    def _find_openhands_installation(self) -> Optional[Path]:
        """Find OpenHands installation."""
        # Check if we have the cloned OpenHands repo
        openhands_paths = [
            Path("/workspace/OpenHands"),
            Path("./OpenHands"),
            Path("../OpenHands")
        ]
        
        for path in openhands_paths:
            if path.exists() and (path / "openhands").exists():
                return path
        
        # Check if OpenHands is installed as package
        try:
            import openhands
            return Path(openhands.__file__).parent.parent
        except ImportError:
            pass
        
        return None
    
    def _prepare_environment(self) -> Dict[str, str]:
        """Prepare environment variables for OpenHands."""
        import os
        env = os.environ.copy()
        
        # Set required environment variables
        env.update({
            "WORKSPACE_DIR": str(self.workspace_dir),
            "SANDBOX_RUNTIME_CONTAINER_IMAGE": self.config.sandbox_container_image,
            "LOG_ALL_EVENTS": "true",
            "PYTHONPATH": str(self._find_openhands_installation())
        })
        
        if self.config.github_token:
            env["GITHUB_TOKEN"] = self.config.github_token
        
        return env
    
    async def _wait_for_server(self, timeout: int = 60) -> bool:
        """Wait for OpenHands server to be ready."""
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            try:
                response = await self.client.get(f"{self.server_url}/api/health")
                if response.status_code == 200:
                    return True
            except:
                pass
            
            await asyncio.sleep(2)
        
        return False
    
    async def health_check(self) -> bool:
        """Check if OpenHands integration is healthy."""
        if not self.is_running:
            return False
        
        try:
            response = await self.client.get(f"{self.server_url}/api/health")
            return response.status_code == 200
        except:
            return False
    
    async def get_available_agents(self) -> List[str]:
        """Get list of available OpenHands agents."""
        try:
            response = await self.client.get(f"{self.server_url}/api/agents")
            response.raise_for_status()
            return response.json().get("agents", [])
        except:
            return [agent.value for agent in OpenHandsAgentType]
    
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a session."""
        try:
            response = await self.client.get(
                f"{self.server_url}/api/sessions/{session_id}"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting session info: {e}")
            return None
    
    async def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions."""
        try:
            response = await self.client.get(f"{self.server_url}/api/sessions")
            response.raise_for_status()
            return response.json().get("sessions", [])
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        try:
            response = await self.client.delete(
                f"{self.server_url}/api/sessions/{session_id}"
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False
    
    def get_workspace_files(self) -> List[str]:
        """Get list of files in workspace."""
        files = []
        for file_path in self.workspace_dir.rglob("*"):
            if file_path.is_file():
                files.append(str(file_path.relative_to(self.workspace_dir)))
        return files
    
    async def create_code_generation_task(self, 
                                        instruction: str,
                                        files: Optional[List[str]] = None,
                                        context: Optional[str] = None) -> OpenHandsTask:
        """Create a code generation task."""
        task_context = {"type": "code_generation"}
        if context:
            task_context["additional_context"] = context
        
        return OpenHandsTask(
            instruction=instruction,
            task_type="code_generation",
            files=files,
            context=task_context
        )
    
    async def create_debugging_task(self,
                                  instruction: str,
                                  error_logs: Optional[str] = None,
                                  files: Optional[List[str]] = None) -> OpenHandsTask:
        """Create a debugging task."""
        task_context = {"type": "debugging"}
        if error_logs:
            task_context["error_logs"] = error_logs
        
        return OpenHandsTask(
            instruction=instruction,
            task_type="debugging",
            files=files,
            context=task_context
        )
    
    async def create_testing_task(self,
                                code_files: List[str],
                                test_framework: str = "pytest") -> OpenHandsTask:
        """Create a testing task."""
        instruction = f"Create comprehensive tests for the provided code files using {test_framework}"
        
        task_context = {
            "type": "testing",
            "test_framework": test_framework,
            "code_files": code_files
        }
        
        return OpenHandsTask(
            instruction=instruction,
            task_type="testing",
            files=code_files,
            context=task_context
        )
    
    async def create_repository_task(self,
                                   repository_url: str,
                                   instruction: str,
                                   issue_number: Optional[int] = None) -> OpenHandsTask:
        """Create a repository-based task."""
        task_context = {"type": "repository", "repository_url": repository_url}
        if issue_number:
            task_context["issue_number"] = issue_number
        
        return OpenHandsTask(
            instruction=instruction,
            task_type="repository",
            repository_url=repository_url,
            issue_number=issue_number,
            context=task_context
        )
    
    async def shutdown(self):
        """Shutdown the OpenHands integration."""
        await self.stop_server()
        logger.info("OpenHands integration shutdown complete")