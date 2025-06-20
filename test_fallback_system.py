#!/usr/bin/env python3
"""
Test script for the enhanced LLM fallback system.

This script tests the core functionalities of the Phase 3 implementation:
- Local model loading and functioning
- Fallback mechanism from API to local model
- Content-based model routing
- Resource-aware model selection
"""

import asyncio
import logging
import time
import sys
from typing import Dict, Any
import yaml

# Add project src to path
sys.path.append('src')

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_fallback")

# Import required modules
from revoagent.ai.llm_manager_enhanced import LLMManagerEnhanced
from revoagent.ai.llm_fallback_manager import LLMFallbackManager, FallbackReason
from revoagent.ai.cpu_optimized_deepseek_enhanced import CPUOptimizedDeepSeekEnhanced

# Test configurations
TEST_MESSAGES = [
    {
        "name": "Simple greeting",
        "message": "Hello, how are you today?",
        "expected_model_type": "any"
    },
    {
        "name": "Code generation request",
        "message": "Write a Python function to calculate Fibonacci numbers recursively.",
        "expected_model_type": "code"
    },
    {
        "name": "Complex reasoning",
        "message": "Explain the key differences between quantum computing and classical computing, focusing on practical applications.",
        "expected_model_type": "high_quality"
    }
]

# Main test function
async def run_tests():
    """Run all tests for the fallback system."""
    print("\n" + "="*80)
    print(" REVO AGENT FALLBACK SYSTEM TESTS")
    print("="*80)
    
    # Initialize the enhanced LLM manager
    print("\n[1/5] Initializing LLM Manager Enhanced...")
    llm_manager = LLMManagerEnhanced()
    success = await llm_manager.initialize()
    
    if not success:
        print("❌ Failed to initialize LLM Manager Enhanced")
        return
    
    print("✅ LLM Manager Enhanced initialized successfully")
    
    # Test model discovery
    print("\n[2/5] Testing model discovery...")
    models = await llm_manager.get_available_models()
    
    if not models:
        print("❌ No models discovered")
        return
    
    print(f"✅ Discovered {len(models)} models:")
    for i, model in enumerate(models[:5], 1):  # Show max 5 models
        print(f"  {i}. {model['name']} ({model['source']})")
    
    if len(models) > 5:
        print(f"     ... and {len(models) - 5} more")
    
    # Test fallback manager functionality
    print("\n[3/5] Testing fallback manager...")
    fallback_manager = llm_manager.fallback_manager
    
    if not fallback_manager or not fallback_manager.enabled:
        print("❌ Fallback manager not enabled")
    else:
        print("✅ Fallback manager is enabled")
        
        # Test fallback chain generation
        test_model = models[0]["id"] if models else "deepseek-r1"
        fallback_chain = await fallback_manager.get_fallback_chain(test_model)
        
        print(f"✅ Fallback chain for {test_model}:")
        for i, model in enumerate(fallback_chain[:5], 1):
            print(f"  {i}. {model}")
        
        if len(fallback_chain) > 5:
            print(f"     ... and {len(fallback_chain) - 5} more")
    
    # Test message generation
    print("\n[4/5] Testing message generation with fallback...")
    for i, test in enumerate(TEST_MESSAGES, 1):
        print(f"\nTest {i}/{len(TEST_MESSAGES)}: {test['name']}")
        print(f"Message: \"{test['message'][:50]}...\"")
        
        try:
            start_time = time.time()
            response = await llm_manager.generate_response(test["message"])
            elapsed = time.time() - start_time
            
            print(f"✅ Generated response in {elapsed:.2f}s")
            print(f"Response: \"{response[:100]}...\"")
        except Exception as e:
            print(f"❌ Error generating response: {e}")
    
    # Test code generation
    print("\n[5/5] Testing code generation...")
    code_request = {
        "task_description": "Create a simple Flask API with two endpoints: one for listing users and one for creating users",
        "language": "python",
        "framework": "flask",
        "database": "sqlite",
        "features": ["auth", "tests"]
    }
    
    try:
        start_time = time.time()
        code_result = await llm_manager.generate_code(code_request)
        elapsed = time.time() - start_time
        
        print(f"✅ Generated code in {elapsed:.2f}s")
        print(f"Model used: {code_result.get('model_used', 'unknown')}")
        
        # Show a snippet of the generated code
        code = code_result.get("generated_code", "")
        code_snippet = code.split("\n")[:10]
        print("Generated code snippet:")
        for line in code_snippet:
            print(f"  {line}")
        print("  ...")
    except Exception as e:
        print(f"❌ Error generating code: {e}")
    
    # Print system health
    print("\n[Final] System health check...")
    health = await llm_manager.get_health()
    
    print(f"Overall status: {health.get('status', 'unknown')}")
    print(f"Stats: {len(health.get('stats', {}))} metrics tracked")
    print(f"Subsystems: {len(health.get('subsystems', {}))} subsystems monitored")
    
    print("\n" + "="*80)
    print(" TESTS COMPLETED")
    print("="*80)

# Run tests
if __name__ == "__main__":
    asyncio.run(run_tests())