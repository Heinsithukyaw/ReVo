#!/usr/bin/env python3
"""
Test script to verify all 9 agents are properly integrated
"""

import sys
import asyncio
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent))

from packages.agents.realtime_executor import realtime_executor

async def test_all_agents():
    """Test that all 9 agents can be executed"""
    
    print("🧪 Testing All 9 Agents Integration")
    print("=" * 50)
    
    # List of all 9 agents
    agents_to_test = [
        "code_generator",
        "debug_agent", 
        "testing_agent",
        "security_agent",
        "deploy_agent",
        "browser_agent",
        "documentation_agent",
        "performance_optimizer",
        "architecture_advisor"
    ]
    
    results = {}
    
    for agent_type in agents_to_test:
        print(f"\n🤖 Testing {agent_type}...")
        
        try:
            # Test if agent is configured
            if agent_type in realtime_executor.agent_configs:
                config = realtime_executor.agent_configs[agent_type]
                print(f"  ✅ Configuration found: {config['name']}")
                
                # Test task execution (without actually running it)
                task_id = await realtime_executor.execute_agent_task(
                    agent_type,
                    f"Test task for {agent_type}",
                    {"test": True}
                )
                print(f"  ✅ Task created with ID: {task_id}")
                
                # Wait a moment for task to start
                await asyncio.sleep(0.5)
                
                # Check task status
                task_status = await realtime_executor.get_task_status(task_id)
                if task_status:
                    print(f"  ✅ Task status: {task_status['status']}")
                    results[agent_type] = "SUCCESS"
                else:
                    print(f"  ❌ Could not retrieve task status")
                    results[agent_type] = "FAILED"
                    
            else:
                print(f"  ❌ Configuration not found")
                results[agent_type] = "NOT_CONFIGURED"
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            results[agent_type] = f"ERROR: {str(e)}"
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 INTEGRATION TEST RESULTS")
    print("=" * 50)
    
    success_count = 0
    for agent_type, result in results.items():
        status_icon = "✅" if result == "SUCCESS" else "❌"
        print(f"{status_icon} {agent_type}: {result}")
        if result == "SUCCESS":
            success_count += 1
    
    print(f"\n🎯 Success Rate: {success_count}/{len(agents_to_test)} ({success_count/len(agents_to_test)*100:.1f}%)")
    
    if success_count == len(agents_to_test):
        print("🎉 ALL AGENTS SUCCESSFULLY INTEGRATED!")
        return True
    else:
        print("⚠️  Some agents need attention")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_all_agents())
    sys.exit(0 if result else 1)