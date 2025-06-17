"""
Test AI Integration for ReVo Chat Interface
Tests the LLM client with multiple providers and function calling
"""

import asyncio
import json
import os
import sys
import pytest
from pathlib import Path

# Add packages to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # Go to repo root

@pytest.mark.asyncio
async def test_llm_client():
    """Test the LLM client with different providers."""
    print("🧪 Testing ReVo AI LLM Integration")
    print("=" * 50)
    
    try:
        from packages.ai.llm_config import create_llm_client_from_env, LLMConfigManager
        from packages.ai.llm_client import LLMProvider
        
        # Create LLM client
        print("📋 Creating LLM client...")
        llm_client = create_llm_client_from_env()
        
        # Get configuration summary
        configs = LLMConfigManager.get_default_configs()
        summary = LLMConfigManager.get_config_summary(configs)
        
        print("\n🔧 Configuration Summary:")
        for provider, info in summary.items():
            status = "✅" if info["enabled"] else "❌"
            cost = "Free" if info["cost_per_token"] == 0 else f"${info['cost_per_token']}/token"
            print(f"  {status} {provider}: {info['model']} ({cost})")
        
        # Test 1: Simple chat completion
        print("\n🗣️  Test 1: Simple Chat Completion")
        print("-" * 30)
        
        messages = [
            {"role": "user", "content": "Hello! Please introduce yourself as ReVo AI and tell me you're ready to help with development tasks."}
        ]
        
        response = await llm_client.chat_completion(messages)
        
        print(f"Provider: {response.provider.value}")
        print(f"Model: {response.model}")
        print(f"Response: {response.content}")
        print(f"Tokens: {response.tokens_used}")
        print(f"Cost: ${response.cost:.6f}")
        print(f"Time: {response.response_time:.2f}s")
        
        if response.error:
            print(f"Error: {response.error}")
        
        # Test 2: Function calling
        print("\n🔧 Test 2: Function Calling")
        print("-" * 30)
        
        function_messages = [
            {"role": "user", "content": "Please run the command 'ls -la' to list all files in the current directory"}
        ]
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "run_terminal_command",
                    "description": "Execute a shell command on the local machine",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "The command to execute"}
                        },
                        "required": ["command"]
                    }
                }
            }
        ]
        
        function_response = await llm_client.chat_completion(function_messages, tools)
        
        print(f"Provider: {function_response.provider.value}")
        print(f"Model: {function_response.model}")
        print(f"Response: {function_response.content}")
        
        if function_response.function_calls:
            print("Function Calls:")
            for call in function_response.function_calls:
                print(f"  - {call['name']}: {call['arguments']}")
        else:
            print("No function calls detected")
        
        print(f"Tokens: {function_response.tokens_used}")
        print(f"Cost: ${function_response.cost:.6f}")
        print(f"Time: {function_response.response_time:.2f}s")
        
        # Test 3: Provider health check
        print("\n🏥 Test 3: Provider Health Check")
        print("-" * 30)
        
        health_results = await llm_client.health_check()
        
        for provider, health in health_results.items():
            if health["status"] == "healthy":
                print(f"  ✅ {provider}: {health['status']} ({health.get('response_time', 0):.2f}s)")
            elif health["status"] == "not_configured":
                print(f"  ⚪ {provider}: not configured")
            else:
                print(f"  ❌ {provider}: {health['status']} - {health.get('error', 'Unknown error')}")
        
        # Test 4: Usage statistics
        print("\n📊 Test 4: Usage Statistics")
        print("-" * 30)
        
        stats = llm_client.get_usage_stats()
        
        print(f"Total Calls: {stats['total_calls']}")
        print(f"Total Tokens: {stats['total_tokens']}")
        print(f"Total Cost: ${stats['total_cost']:.6f}")
        
        print("\nPer Provider:")
        for provider, provider_stats in stats['providers'].items():
            if provider_stats['calls'] > 0:
                print(f"  {provider}: {provider_stats['calls']} calls, {provider_stats['tokens']} tokens, ${provider_stats['cost']:.6f}")
        
        # Test 5: Optimal provider selection
        print("\n🎯 Test 5: Optimal Provider Selection")
        print("-" * 30)
        
        optimal = llm_client.get_optimal_provider()
        print(f"Optimal Provider: {optimal.value}")
        print(f"Fallback Order: {[p.value for p in llm_client.fallback_order]}")
        
        print("\n✅ All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_orchestrator_integration():
    """Test the ReVo Orchestrator with LLM integration."""
    print("\n🎭 Testing ReVo Orchestrator Integration")
    print("=" * 50)
    
    try:
        from core.revo_orchestrator import ReVoOrchestrator
        from ai.llm_config import create_llm_client_from_env
        
        # Create LLM client
        llm_client = create_llm_client_from_env()
        
        # Create orchestrator
        orchestrator = ReVoOrchestrator(llm_client=llm_client)
        
        # Test message handling
        test_messages = [
            "Hello, can you help me with development tasks?",
            "/help",
            "/run ls -la",
            "Create a Python function to calculate fibonacci numbers"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n📝 Test Message {i}: {message}")
            print("-" * 40)
            
            # Simulate WebSocket callback
            responses = []
            
            async def mock_callback(response):
                responses.append(response)
                print(f"Response: {response}")
            
            orchestrator.set_websocket_callback(mock_callback)
            
            # Handle the message
            await orchestrator.handle_message({"content": message}, "test_session")
            
            # Wait a moment for processing
            await asyncio.sleep(0.5)
            
            print(f"Received {len(responses)} responses")
        
        print("\n✅ Orchestrator integration test completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Orchestrator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def setup_test_environment():
    """Setup test environment variables."""
    print("🔧 Setting up test environment...")
    
    # Set default endpoints for local testing
    os.environ.setdefault("DEEPSEEK_ENDPOINT", "http://localhost:8001")
    os.environ.setdefault("LLAMA_ENDPOINT", "http://localhost:11434")
    
    # Disable paid providers by default for testing
    os.environ.setdefault("OPENAI_ENABLED", "false")
    os.environ.setdefault("ANTHROPIC_ENABLED", "false")
    
    print("  ✅ Environment configured for local testing")

async def main():
    """Main test function."""
    print("🚀 ReVo AI Integration Test Suite")
    print("=" * 60)
    
    setup_test_environment()
    
    # Test LLM client
    llm_success = await test_llm_client()
    
    # Test orchestrator integration
    orchestrator_success = await test_orchestrator_integration()
    
    # Summary
    print("\n📋 Test Summary")
    print("=" * 30)
    print(f"LLM Client: {'✅ PASS' if llm_success else '❌ FAIL'}")
    print(f"Orchestrator: {'✅ PASS' if orchestrator_success else '❌ FAIL'}")
    
    if llm_success and orchestrator_success:
        print("\n🎉 All tests passed! ReVo AI is ready for action.")
        print("\n🚀 Next steps:")
        print("  1. Start local LLM servers (if not running)")
        print("  2. Run: python test_revo_ai_server.py")
        print("  3. Open: http://localhost:8000/test")
    else:
        print("\n⚠️  Some tests failed. Please check the setup:")
        print("  1. Ensure local LLM servers are running")
        print("  2. Check network connectivity")
        print("  3. Verify environment variables")

if __name__ == "__main__":
    asyncio.run(main())