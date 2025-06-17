"""Command-line interface for reVoAgent platform."""

import asyncio
import logging
import uuid
from typing import Optional, Dict, Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.live import Live
from rich.layout import Layout

from ..core.framework import AgentFramework, TaskRequest


class CLI:
    """
    Command-line interface for reVoAgent platform.
    
    Provides an interactive terminal interface for:
    - Agent management
    - Task execution
    - System monitoring
    - Configuration
    """
    
    def __init__(self, framework: AgentFramework):
        """Initialize CLI."""
        self.framework = framework
        self.console = Console()
        self.logger = logging.getLogger(__name__)
        
        # CLI state
        self.running = False
        self.current_agent = None
        
        # Commands
        self.commands = {
            "help": self.show_help,
            "status": self.show_status,
            "agents": self.list_agents,
            "models": self.list_models,
            "tools": self.list_tools,
            "create": self.create_agent,
            "use": self.use_agent,
            "task": self.execute_task,
            "chat": self.start_chat,
            "config": self.show_config,
            "quit": self.quit,
            "exit": self.quit,
        }
    
    async def start(self) -> None:
        """Start the CLI interface."""
        self.running = True
        
        # Show welcome message
        self._show_welcome()
        
        # Start task processor
        task_processor = asyncio.create_task(self.framework.start_task_processor())
        
        try:
            # Main CLI loop
            while self.running:
                try:
                    # Get user input
                    command_line = await self._get_input()
                    
                    if not command_line.strip():
                        continue
                    
                    # Parse and execute command
                    await self._execute_command(command_line)
                    
                except KeyboardInterrupt:
                    if Confirm.ask("\nDo you want to quit?"):
                        break
                except Exception as e:
                    self.console.print(f"[red]Error: {e}[/red]")
        
        finally:
            # Stop task processor
            await self.framework.stop_task_processor()
            task_processor.cancel()
    
    def _show_welcome(self) -> None:
        """Show welcome message."""
        welcome_text = Text()
        welcome_text.append("🚀 Welcome to ", style="bold blue")
        welcome_text.append("reVoAgent", style="bold green")
        welcome_text.append(" - Revolutionary Agentic Coding System Platform", style="bold blue")
        
        welcome_panel = Panel(
            welcome_text,
            title="reVoAgent v1.0.0",
            border_style="green"
        )
        
        self.console.print(welcome_panel)
        self.console.print("\nType 'help' for available commands or 'chat' to start chatting with an agent.\n")
    
    async def _get_input(self) -> str:
        """Get user input asynchronously."""
        prompt_text = "reVoAgent"
        if self.current_agent:
            prompt_text += f" ({self.current_agent})"
        prompt_text += " > "
        
        # Use asyncio to make input non-blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: input(prompt_text))
    
    async def _execute_command(self, command_line: str) -> None:
        """Execute a command."""
        parts = command_line.strip().split()
        if not parts:
            return
        
        command = parts[0].lower()
        args = parts[1:]
        
        if command in self.commands:
            await self.commands[command](args)
        else:
            self.console.print(f"[red]Unknown command: {command}[/red]")
            self.console.print("Type 'help' for available commands.")
    
    async def show_help(self, args: list) -> None:
        """Show help information."""
        help_table = Table(title="Available Commands")
        help_table.add_column("Command", style="cyan", no_wrap=True)
        help_table.add_column("Description", style="white")
        help_table.add_column("Usage", style="yellow")
        
        commands_info = [
            ("help", "Show this help message", "help"),
            ("status", "Show system status", "status"),
            ("agents", "List available agents", "agents"),
            ("models", "List available models", "models"),
            ("tools", "List available tools", "tools"),
            ("create", "Create a new agent", "create <agent_type> <agent_id>"),
            ("use", "Select an agent to use", "use <agent_id>"),
            ("task", "Execute a task", "task <description>"),
            ("chat", "Start interactive chat", "chat [agent_id]"),
            ("config", "Show configuration", "config"),
            ("quit/exit", "Exit the application", "quit"),
        ]
        
        for cmd, desc, usage in commands_info:
            help_table.add_row(cmd, desc, usage)
        
        self.console.print(help_table)
    
    async def show_status(self, args: list) -> None:
        """Show system status."""
        status = self.framework.get_framework_status()
        
        # Create status panel
        status_text = Text()
        status_text.append(f"Framework Status: ", style="bold")
        status_text.append(f"{status['status']}\n", style="green" if status['status'] == 'running' else "yellow")
        status_text.append(f"Active Tasks: {status['active_tasks']}\n")
        status_text.append(f"Queue Size: {status['queue_size']}\n")
        status_text.append(f"Total Agents: {len(status['agents'])}\n")
        
        status_panel = Panel(status_text, title="System Status", border_style="blue")
        self.console.print(status_panel)
        
        # Show agent status
        if status['agents']:
            agent_table = Table(title="Agent Status")
            agent_table.add_column("Agent ID", style="cyan")
            agent_table.add_column("Type", style="white")
            agent_table.add_column("State", style="yellow")
            
            for agent_id, agent_info in status['agents'].items():
                agent_table.add_row(
                    agent_id,
                    agent_info['type'],
                    agent_info['state']
                )
            
            self.console.print(agent_table)
    
    async def list_agents(self, args: list) -> None:
        """List available agents."""
        agents = self.framework.list_agents()
        
        if not agents:
            self.console.print("[yellow]No agents available.[/yellow]")
            return
        
        agent_table = Table(title="Available Agents")
        agent_table.add_column("Agent ID", style="cyan")
        agent_table.add_column("Type", style="white")
        agent_table.add_column("Model", style="green")
        agent_table.add_column("Tools", style="yellow")
        
        for agent_id in agents:
            agent = self.framework.get_agent(agent_id)
            if agent:
                agent_table.add_row(
                    agent_id,
                    agent.__class__.__name__,
                    agent.config.model,
                    ", ".join(agent.config.tools[:3]) + ("..." if len(agent.config.tools) > 3 else "")
                )
        
        self.console.print(agent_table)
    
    async def list_models(self, args: list) -> None:
        """List available models."""
        models = self.framework.model_manager.get_available_models()
        loaded_models = self.framework.model_manager.get_loaded_models()
        
        model_table = Table(title="Available Models")
        model_table.add_column("Model Name", style="cyan")
        model_table.add_column("Type", style="white")
        model_table.add_column("Status", style="yellow")
        model_table.add_column("Path/URL", style="green")
        
        for model_name in models:
            model_config = self.framework.config.get_model_config(model_name)
            status = "loaded" if model_name in loaded_models else "unloaded"
            
            model_table.add_row(
                model_name,
                model_config.type,
                status,
                model_config.path or model_config.base_url or "N/A"
            )
        
        self.console.print(model_table)
    
    async def list_tools(self, args: list) -> None:
        """List available tools."""
        tools = self.framework.tool_manager.get_available_tools()
        
        tool_table = Table(title="Available Tools")
        tool_table.add_column("Tool Name", style="cyan")
        tool_table.add_column("Description", style="white")
        tool_table.add_column("Capabilities", style="yellow")
        
        for tool_name in tools:
            tool_info = self.framework.tool_manager.get_tool_info(tool_name)
            if tool_info:
                tool_table.add_row(
                    tool_name,
                    tool_info['description'][:50] + "..." if len(tool_info['description']) > 50 else tool_info['description'],
                    ", ".join(tool_info['capabilities'][:2]) + ("..." if len(tool_info['capabilities']) > 2 else "")
                )
        
        self.console.print(tool_table)
    
    async def create_agent(self, args: list) -> None:
        """Create a new agent."""
        if len(args) < 2:
            self.console.print("[red]Usage: create <agent_type> <agent_id>[/red]")
            return
        
        agent_type = args[0]
        agent_id = args[1]
        
        try:
            agent = self.framework.create_agent(agent_id, agent_type)
            self.console.print(f"[green]Created agent '{agent_id}' of type '{agent_type}'[/green]")
        except Exception as e:
            self.console.print(f"[red]Failed to create agent: {e}[/red]")
    
    async def use_agent(self, args: list) -> None:
        """Select an agent to use."""
        if len(args) < 1:
            self.console.print("[red]Usage: use <agent_id>[/red]")
            return
        
        agent_id = args[0]
        agent = self.framework.get_agent(agent_id)
        
        if not agent:
            self.console.print(f"[red]Agent '{agent_id}' not found[/red]")
            return
        
        self.current_agent = agent_id
        self.console.print(f"[green]Now using agent '{agent_id}'[/green]")
    
    async def execute_task(self, args: list) -> None:
        """Execute a task."""
        if not args:
            self.console.print("[red]Usage: task <description>[/red]")
            return
        
        if not self.current_agent:
            self.console.print("[red]No agent selected. Use 'use <agent_id>' first.[/red]")
            return
        
        task_description = " ".join(args)
        task_id = str(uuid.uuid4())
        
        # Create task request
        task_request = TaskRequest(
            id=task_id,
            type="user_task",
            description=task_description,
            agent_type=self.current_agent,
            parameters={}
        )
        
        self.console.print(f"[blue]Executing task: {task_description}[/blue]")
        
        try:
            # Execute task
            result = await self.framework.execute_task(task_request)
            
            if result.success:
                self.console.print(f"[green]Task completed successfully![/green]")
                self.console.print(f"Result: {result.result}")
            else:
                self.console.print(f"[red]Task failed: {result.error}[/red]")
                
        except Exception as e:
            self.console.print(f"[red]Error executing task: {e}[/red]")
    
    async def start_chat(self, args: list) -> None:
        """Start interactive chat with an agent."""
        agent_id = args[0] if args else self.current_agent
        
        if not agent_id:
            self.console.print("[red]No agent specified. Use 'chat <agent_id>' or select an agent with 'use <agent_id>'[/red]")
            return
        
        agent = self.framework.get_agent(agent_id)
        if not agent:
            self.console.print(f"[red]Agent '{agent_id}' not found[/red]")
            return
        
        self.console.print(f"[green]Starting chat with {agent_id}. Type 'exit' to end chat.[/green]")
        
        while True:
            try:
                user_input = await self._get_input_with_prompt(f"You: ")
                
                if user_input.lower() in ['exit', 'quit']:
                    break
                
                if not user_input.strip():
                    continue
                
                # Get agent response
                self.console.print("[blue]Agent is thinking...[/blue]")
                response = await agent.process_message(user_input)
                
                self.console.print(f"[green]{agent_id}:[/green] {response}")
                
            except KeyboardInterrupt:
                break
        
        self.console.print("[blue]Chat ended.[/blue]")
    
    async def _get_input_with_prompt(self, prompt: str) -> str:
        """Get user input with custom prompt."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: input(prompt))
    
    async def show_config(self, args: list) -> None:
        """Show configuration."""
        config = self.framework.config
        
        config_text = Text()
        config_text.append(f"Platform: {config.platform.name} v{config.platform.version}\n", style="bold")
        config_text.append(f"Data Directory: {config.platform.data_dir}\n")
        config_text.append(f"Models Directory: {config.platform.models_dir}\n")
        config_text.append(f"Debug Mode: {config.platform.debug}\n")
        config_text.append(f"Log Level: {config.platform.log_level}\n")
        config_text.append(f"Sandbox Enabled: {config.security.sandbox_enabled}\n")
        config_text.append(f"GPU Enabled: {config.resources.gpu_enabled}\n")
        
        config_panel = Panel(config_text, title="Configuration", border_style="blue")
        self.console.print(config_panel)
    
    async def quit(self, args: list) -> None:
        """Quit the application."""
        self.console.print("[blue]Goodbye![/blue]")
        self.running = False