"""Terminal tool for reVoAgent platform."""

import asyncio
import shlex
from typing import Dict, Any, List
from pathlib import Path

from .base import BaseTool


class TerminalTool(BaseTool):
    """
    Terminal/shell command execution tool for reVoAgent platform.
    
    Capabilities:
    - Command execution
    - Environment variable management
    - Working directory control
    - Process management
    - Output capture
    """
    
    def get_description(self) -> str:
        """Get tool description."""
        return "Terminal command execution with environment control and output capture"
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get parameter schema."""
        return {
            "required": ["command"],
            "optional": ["cwd", "env", "timeout", "shell", "capture_output"],
            "examples": [
                "ls -la",
                "python --version",
                "git status",
                "npm install"
            ]
        }
    
    def get_capabilities(self) -> List[str]:
        """Get tool capabilities."""
        return [
            "command_execution",
            "process_management",
            "environment_control",
            "output_capture",
            "shell_operations"
        ]
    
    def get_dependencies(self) -> List[str]:
        """Get tool dependencies."""
        return []  # No external dependencies
    
    async def execute(self, parameters: Dict[str, Any]) -> Any:
        """Execute terminal commands."""
        # Apply sandbox restrictions
        safe_params = self._apply_sandbox_restrictions(parameters)
        
        # Validate parameters
        if not self.validate_parameters(safe_params):
            raise ValueError("Invalid parameters for terminal tool")
        
        command = safe_params["command"]
        
        # Additional security checks for dangerous commands
        if self.sandbox_enabled and self._is_command_dangerous(command):
            raise ValueError(f"Command not allowed in sandbox mode: {command}")
        
        return await self._execute_command(safe_params)
    
    def _is_command_dangerous(self, command: str) -> bool:
        """Check if a command is dangerous in sandbox mode."""
        dangerous_commands = [
            "rm -rf", "sudo", "su", "chmod 777", "chown", "dd",
            "mkfs", "fdisk", "format", "del /f", "rmdir /s",
            "shutdown", "reboot", "halt", "poweroff",
            "iptables", "ufw", "firewall-cmd",
            "passwd", "useradd", "userdel", "usermod"
        ]
        
        command_lower = command.lower()
        return any(dangerous in command_lower for dangerous in dangerous_commands)
    
    async def _execute_command(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a shell command."""
        command = parameters["command"]
        cwd = parameters.get("cwd", ".")
        timeout = parameters.get("timeout", 30)
        shell = parameters.get("shell", True)
        capture_output = parameters.get("capture_output", True)
        env = parameters.get("env", {})
        
        try:
            # Prepare working directory
            work_dir = Path(cwd).resolve()
            if not work_dir.exists():
                return {
                    "success": False,
                    "command": command,
                    "error": f"Working directory does not exist: {cwd}"
                }
            
            # Prepare environment variables
            import os
            process_env = os.environ.copy()
            process_env.update(env)
            
            # Execute command
            if shell:
                # Execute as shell command
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE if capture_output else None,
                    stderr=asyncio.subprocess.PIPE if capture_output else None,
                    cwd=str(work_dir),
                    env=process_env
                )
            else:
                # Execute as separate arguments
                args = shlex.split(command)
                process = await asyncio.create_subprocess_exec(
                    *args,
                    stdout=asyncio.subprocess.PIPE if capture_output else None,
                    stderr=asyncio.subprocess.PIPE if capture_output else None,
                    cwd=str(work_dir),
                    env=process_env
                )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                # Kill the process if it times out
                process.kill()
                await process.wait()
                return {
                    "success": False,
                    "command": command,
                    "error": f"Command timed out after {timeout} seconds",
                    "timeout": True
                }
            
            # Decode output
            stdout_text = stdout.decode('utf-8', errors='ignore') if stdout else ""
            stderr_text = stderr.decode('utf-8', errors='ignore') if stderr else ""
            
            return {
                "success": process.returncode == 0,
                "command": command,
                "returncode": process.returncode,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "cwd": str(work_dir),
                "timeout": timeout,
                "execution_time": None  # Could add timing if needed
            }
            
        except Exception as e:
            return {
                "success": False,
                "command": command,
                "error": str(e)
            }
    
    async def run_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """Convenience method to run a command."""
        parameters = {"command": command, **kwargs}
        return await self.execute(parameters)
    
    async def run_python_script(self, script_content: str, **kwargs) -> Dict[str, Any]:
        """Run Python code."""
        # Create temporary script file
        import tempfile
        import os
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(script_content)
                script_path = f.name
            
            # Execute the script
            result = await self.run_command(f"python {script_path}", **kwargs)
            
            # Clean up
            os.unlink(script_path)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "command": "python script execution",
                "error": str(e)
            }
    
    async def check_command_exists(self, command: str) -> bool:
        """Check if a command exists in the system."""
        try:
            result = await self.run_command(f"which {command}")
            return result["success"]
        except:
            return False
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        info = {}
        
        # Get OS information
        try:
            os_result = await self.run_command("uname -a")
            if os_result["success"]:
                info["os"] = os_result["stdout"].strip()
        except:
            pass
        
        # Get Python version
        try:
            python_result = await self.run_command("python --version")
            if python_result["success"]:
                info["python"] = python_result["stdout"].strip()
        except:
            pass
        
        # Get current directory
        try:
            pwd_result = await self.run_command("pwd")
            if pwd_result["success"]:
                info["current_directory"] = pwd_result["stdout"].strip()
        except:
            pass
        
        # Get environment variables (limited for security)
        try:
            env_result = await self.run_command("env | grep -E '^(PATH|HOME|USER|SHELL)='")
            if env_result["success"]:
                env_vars = {}
                for line in env_result["stdout"].split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key] = value
                info["environment"] = env_vars
        except:
            pass
        
        return info
    
    async def install_package(self, package_name: str, package_manager: str = "pip") -> Dict[str, Any]:
        """Install a package using the specified package manager."""
        if package_manager == "pip":
            command = f"pip install {package_name}"
        elif package_manager == "npm":
            command = f"npm install {package_name}"
        elif package_manager == "apt":
            command = f"apt-get install -y {package_name}"
        elif package_manager == "yum":
            command = f"yum install -y {package_name}"
        else:
            return {
                "success": False,
                "error": f"Unsupported package manager: {package_manager}"
            }
        
        return await self.run_command(command, timeout=300)  # 5 minute timeout for installations
    
    async def create_virtual_environment(self, env_name: str, python_version: str = None) -> Dict[str, Any]:
        """Create a Python virtual environment."""
        if python_version:
            command = f"python{python_version} -m venv {env_name}"
        else:
            command = f"python -m venv {env_name}"
        
        return await self.run_command(command)
    
    async def activate_virtual_environment(self, env_name: str) -> Dict[str, str]:
        """Get environment variables to activate a virtual environment."""
        # Return environment variables that would activate the venv
        import os
        
        venv_path = Path(env_name).resolve()
        
        if os.name == 'nt':  # Windows
            scripts_dir = venv_path / "Scripts"
            python_exe = scripts_dir / "python.exe"
        else:  # Unix-like
            scripts_dir = venv_path / "bin"
            python_exe = scripts_dir / "python"
        
        if not python_exe.exists():
            raise ValueError(f"Virtual environment not found: {env_name}")
        
        # Prepare environment variables
        env_vars = {
            "VIRTUAL_ENV": str(venv_path),
            "PATH": f"{scripts_dir}{os.pathsep}{os.environ.get('PATH', '')}",
            "PYTHONPATH": ""  # Clear PYTHONPATH to avoid conflicts
        }
        
        return env_vars
    
    async def _tool_specific_health_check(self) -> bool:
        """Check if terminal tool is healthy."""
        try:
            # Test basic command execution
            result = await self.run_command("echo 'health check'", timeout=5)
            return result["success"] and "health check" in result["stdout"]
        except Exception:
            return False
    
    def _apply_sandbox_restrictions(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Apply sandbox restrictions to terminal parameters."""
        restricted_params = super()._apply_sandbox_restrictions(parameters)
        
        if self.sandbox_enabled:
            # Restrict working directory to safe locations
            cwd = restricted_params.get("cwd", ".")
            safe_cwd = self._get_safe_working_directory(cwd)
            restricted_params["cwd"] = safe_cwd
            
            # Limit timeout in sandbox mode
            timeout = restricted_params.get("timeout", 30)
            restricted_params["timeout"] = min(timeout, 60)  # Max 1 minute
        
        return restricted_params
    
    def _get_safe_working_directory(self, cwd: str) -> str:
        """Get a safe working directory for sandbox mode."""
        if not self.sandbox_enabled:
            return cwd
        
        # Restrict to safe directories
        safe_dirs = [
            self.config.platform.data_dir,
            self.config.platform.temp_dir,
            ".",
            "./src",
            "./tests",
            "./docs"
        ]
        
        cwd_path = Path(cwd).resolve()
        
        # Check if the directory is within safe boundaries
        for safe_dir in safe_dirs:
            safe_path = Path(safe_dir).resolve()
            try:
                cwd_path.relative_to(safe_path)
                return cwd  # Directory is safe
            except ValueError:
                continue
        
        # Default to temp directory if not safe
        return self.config.platform.temp_dir