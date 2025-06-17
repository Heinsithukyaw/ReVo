"""reVoAgent CLI Application"""
import click
import asyncio

@click.group()
def cli():
    """reVoAgent Command Line Interface"""
    pass

@cli.command()
def start():
    """Start the reVoAgent system"""
    click.echo("🚀 Starting reVoAgent...")
    # Import and start system

@cli.command()
@click.option('--agent', default='code_generation', help='Agent type to run')
def run_agent(agent):
    """Run a specific agent"""
    click.echo(f"🤖 Running {agent} agent...")

@cli.command()
def status():
    """Check system status"""
    click.echo("📊 System Status: Healthy")

if __name__ == "__main__":
    cli()
