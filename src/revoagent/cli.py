#!/usr/bin/env python3
"""
Command-line interface for reVoAgent platform.
"""

import asyncio
import click
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from revoagent.core.framework import AgentFramework, TaskRequest
from revoagent.core.config import get_config, Config
from revoagent.ui.cli import CLI


@click.group()
@click.option('--config', '-c', default='config/config.yaml', help='Configuration file path')
@click.option('--debug', '-d', is_flag=True, help='Enable debug mode')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def main(ctx, config, debug, verbose):
    """reVoAgent - Revolutionary Agentic Coding System Platform"""
    
    # Setup logging
    log_level = logging.DEBUG if debug or verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Store config path in context
    ctx.ensure_object(dict)
    ctx.obj['config_path'] = config
    ctx.obj['debug'] = debug


@main.command()
@click.pass_context
def start(ctx):
    """Start the reVoAgent platform with interactive CLI."""
    asyncio.run(_start_interactive(ctx.obj['config_path']))


@main.command()
@click.option('--agent', '-a', required=True, help='Agent type to use')
@click.option('--task', '-t', required=True, help='Task description')
@click.option('--output', '-o', help='Output file for results')
@click.pass_context
def run(ctx, agent, task, output):
    """Run a single task with specified agent."""
    asyncio.run(_run_single_task(ctx.obj['config_path'], agent, task, output))


@main.command()
@click.pass_context
def status(ctx):
    """Show platform status."""
    asyncio.run(_show_status(ctx.obj['config_path']))


@main.command()
@click.pass_context
def agents(ctx):
    """List available agents."""
    asyncio.run(_list_agents(ctx.obj['config_path']))


@main.command()
@click.pass_context
def models(ctx):
    """List available models."""
    asyncio.run(_list_models(ctx.obj['config_path']))


@main.command()
@click.pass_context
def tools(ctx):
    """List available tools."""
    asyncio.run(_list_tools(ctx.obj['config_path']))


@main.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=8000, help='Port to bind to')
@click.pass_context
def server(ctx, host, port):
    """Start the web server."""
    asyncio.run(_start_server(ctx.obj['config_path'], host, port))


@main.command()
@click.option('--output', '-o', default='config/config.yaml', help='Output configuration file')
@click.pass_context
def init(ctx, output):
    """Initialize a new configuration file."""
    _init_config(output)


async def _start_interactive(config_path: str):
    """Start interactive CLI."""
    try:
        # Load configuration
        if Path(config_path).exists():
            config = Config.load_from_file(config_path)
        else:
            click.echo(f"Configuration file not found: {config_path}")
            click.echo("Using default configuration. Run 'revoagent init' to create a config file.")
            config = Config.load_default()
        
        # Initialize framework
        framework = AgentFramework(config)
        
        # Start CLI
        cli = CLI(framework)
        await cli.start()
        
    except KeyboardInterrupt:
        click.echo("\nShutting down...")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


async def _run_single_task(config_path: str, agent_type: str, task_description: str, output_file: str):
    """Run a single task."""
    try:
        # Load configuration
        if Path(config_path).exists():
            config = Config.load_from_file(config_path)
        else:
            config = Config.load_default()
        
        # Initialize framework
        framework = AgentFramework(config)
        
        # Create task request
        task_request = TaskRequest(
            id=f"cli_task_{asyncio.get_event_loop().time()}",
            type="cli_task",
            description=task_description,
            agent_type=agent_type,
            parameters={}
        )
        
        click.echo(f"Executing task with {agent_type}: {task_description}")
        
        # Execute task
        result = await framework.execute_task(task_request)
        
        if result.success:
            click.echo("Task completed successfully!")
            click.echo(f"Result: {result.result}")
            
            # Save to output file if specified
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(str(result.result))
                click.echo(f"Result saved to: {output_file}")
        else:
            click.echo(f"Task failed: {result.error}", err=True)
            sys.exit(1)
        
        # Cleanup
        await framework.shutdown()
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


async def _show_status(config_path: str):
    """Show platform status."""
    try:
        # Load configuration
        if Path(config_path).exists():
            config = Config.load_from_file(config_path)
        else:
            config = Config.load_default()
        
        # Initialize framework
        framework = AgentFramework(config)
        
        # Get status
        status = framework.get_framework_status()
        
        click.echo("=== reVoAgent Platform Status ===")
        click.echo(f"Framework Status: {status['status']}")
        click.echo(f"Active Tasks: {status['active_tasks']}")
        click.echo(f"Queue Size: {status['queue_size']}")
        click.echo(f"Total Agents: {len(status['agents'])}")
        
        if status['agents']:
            click.echo("\nAgents:")
            for agent_id, agent_info in status['agents'].items():
                click.echo(f"  - {agent_id}: {agent_info['type']} ({agent_info['state']})")
        
        # Cleanup
        await framework.shutdown()
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


async def _list_agents(config_path: str):
    """List available agents."""
    try:
        # Load configuration
        if Path(config_path).exists():
            config = Config.load_from_file(config_path)
        else:
            config = Config.load_default()
        
        click.echo("=== Available Agents ===")
        for agent_name, agent_config in config.agents.items():
            status = "enabled" if agent_config.enabled else "disabled"
            click.echo(f"  - {agent_name}: {agent_config.model} ({status})")
            click.echo(f"    Tools: {', '.join(agent_config.tools)}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


async def _list_models(config_path: str):
    """List available models."""
    try:
        # Load configuration
        if Path(config_path).exists():
            config = Config.load_from_file(config_path)
        else:
            config = Config.load_default()
        
        click.echo("=== Available Models ===")
        for model_name, model_config in config.models.items():
            click.echo(f"  - {model_name}: {model_config.type}")
            if model_config.path:
                click.echo(f"    Path: {model_config.path}")
            if model_config.base_url:
                click.echo(f"    URL: {model_config.base_url}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


async def _list_tools(config_path: str):
    """List available tools."""
    try:
        # Load configuration
        if Path(config_path).exists():
            config = Config.load_from_file(config_path)
        else:
            config = Config.load_default()
        
        # Initialize framework to get tool manager
        framework = AgentFramework(config)
        tools = framework.tool_manager.get_available_tools()
        
        click.echo("=== Available Tools ===")
        for tool_name in tools:
            tool_info = framework.tool_manager.get_tool_info(tool_name)
            if tool_info:
                click.echo(f"  - {tool_name}: {tool_info['description']}")
                click.echo(f"    Capabilities: {', '.join(tool_info['capabilities'])}")
        
        # Cleanup
        await framework.shutdown()
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


async def _start_server(config_path: str, host: str, port: int):
    """Start web server."""
    try:
        click.echo(f"Starting web server on {host}:{port}")
        click.echo("Web server functionality not yet implemented.")
        click.echo("Use 'revoagent start' for interactive CLI instead.")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _init_config(output_path: str):
    """Initialize configuration file."""
    try:
        output_file = Path(output_path)
        
        if output_file.exists():
            if not click.confirm(f"Configuration file {output_path} already exists. Overwrite?"):
                click.echo("Aborted.")
                return
        
        # Create default configuration
        config = Config.load_default()
        
        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save configuration
        config.save_to_file(output_path)
        
        click.echo(f"Configuration file created: {output_path}")
        click.echo("Please edit the configuration file to customize your setup.")
        
    except Exception as e:
        click.echo(f"Error creating configuration: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()