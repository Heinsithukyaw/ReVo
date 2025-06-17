#!/usr/bin/env python3
"""
reVoAgent Platform Demo

This script demonstrates the core capabilities of the reVoAgent platform.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from revoagent.core.framework import AgentFramework, TaskRequest
from revoagent.core.config import Config


async def demo_platform():
    """Demonstrate reVoAgent platform capabilities."""
    
    print("🚀 reVoAgent Platform Demo")
    print("=" * 50)
    
    # Load configuration
    try:
        config = Config.load_from_file("config/config.yaml")
        print("✅ Configuration loaded from config/config.yaml")
    except FileNotFoundError:
        config = Config.load_default()
        print("⚠️  Using default configuration (config file not found)")
    
    print(f"Platform: {config.platform.name} v{config.platform.version}")
    print(f"Available models: {len(config.models)}")
    print(f"Available agents: {len(config.agents)}")
    print()
    
    # Initialize framework
    print("🔧 Initializing Agent Framework...")
    framework = AgentFramework(config)
    
    # Show framework status
    status = framework.get_framework_status()
    print(f"Framework Status: {status['status']}")
    print(f"Agents Created: {len(status['agents'])}")
    print()
    
    # Demonstrate agent capabilities
    print("🤖 Agent Capabilities Demo")
    print("-" * 30)
    
    for agent_id, agent_info in status['agents'].items():
        print(f"Agent: {agent_id}")
        print(f"  Type: {agent_info['type']}")
        print(f"  State: {agent_info['state']}")
        
        # Get agent instance
        agent = framework.get_agent(agent_id)
        if agent:
            print(f"  Capabilities: {agent.get_capabilities()}")
            print(f"  Available Tools: {', '.join(agent.get_available_tools())}")
        print()
    
    # Demonstrate tool manager
    print("🛠️  Tool Manager Demo")
    print("-" * 20)
    
    tools = framework.tool_manager.get_available_tools()
    print(f"Available Tools: {len(tools)}")
    
    for tool_name in tools:
        tool_info = framework.tool_manager.get_tool_info(tool_name)
        if tool_info:
            print(f"  - {tool_name}: {tool_info['description'][:60]}...")
    print()
    
    # Demonstrate model manager
    print("🧠 Model Manager Demo")
    print("-" * 20)
    
    models = framework.model_manager.get_available_models()
    print(f"Available Models: {len(models)}")
    
    for model_name in models:
        status = framework.model_manager.get_model_status(model_name)
        print(f"  - {model_name}: {status}")
    print()
    
    # Demonstrate memory manager
    print("💾 Memory Manager Demo")
    print("-" * 20)
    
    # Get memory stats for each agent
    for agent_id in framework.list_agents():
        stats = framework.memory_manager.get_memory_stats(agent_id)
        print(f"Agent {agent_id} Memory:")
        print(f"  Total memories: {stats['total_memories']}")
        print(f"  Average importance: {stats['average_importance']:.2f}")
    print()
    
    # Demonstrate simple task execution (simulated)
    print("📋 Task Execution Demo")
    print("-" * 20)
    
    # Create a simple task for the code generator
    if 'code_generator' in framework.list_agents():
        print("Creating a simple code generation task...")
        
        task_request = TaskRequest(
            id="demo_task_001",
            type="demo",
            description="Create a simple Python function that calculates the factorial of a number",
            agent_type="code_generator",
            parameters={"language": "python", "function_name": "factorial"}
        )
        
        print(f"Task: {task_request.description}")
        print("Note: This is a demo - actual execution would require model loading")
        print("In a real scenario, the agent would generate the requested code.")
    
    print()
    
    # Show final status
    print("📊 Final Platform Status")
    print("-" * 25)
    
    final_status = framework.get_framework_status()
    print(f"Framework Status: {final_status['status']}")
    print(f"Active Tasks: {final_status['active_tasks']}")
    print(f"Queue Size: {final_status['queue_size']}")
    print()
    
    # Cleanup
    print("🧹 Cleaning up...")
    await framework.shutdown()
    
    print("✅ Demo completed successfully!")
    print()
    print("Next Steps:")
    print("1. Download AI models (e.g., DeepSeek Coder, Llama 3.2)")
    print("2. Configure API keys if using cloud models")
    print("3. Run: python main.py")
    print("4. Try: python src/revoagent/cli.py start")


if __name__ == "__main__":
    asyncio.run(demo_platform())