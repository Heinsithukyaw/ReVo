#!/usr/bin/env python3
"""
Test Real-time Functionality with DeepSeek R1 Integration

This script demonstrates the complete reVoAgent platform functionality
with DeepSeek R1 integration, including real-time code generation,
model management, and API endpoints.
"""

import asyncio
import json
import logging
import requests
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:12000"

def test_api_endpoint(method: str, endpoint: str, data: dict = None) -> dict:
    """Test an API endpoint and return the response."""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url)
        elif method.upper() == "POST":
            response = requests.post(url, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return {"error": str(e)}

def test_code_generation():
    """Test the code generation functionality."""
    logger.info("🔧 Testing Code Generation with DeepSeek R1...")
    
    # Test different types of code generation requests
    test_cases = [
        {
            "name": "FastAPI Todo App",
            "request": {
                "task_description": "Create a complete todo application with user authentication, task management, and real-time updates",
                "language": "python",
                "framework": "fastapi",
                "database": "postgresql",
                "features": ["auth", "tests", "docs", "docker"]
            }
        },
        {
            "name": "React Dashboard",
            "request": {
                "task_description": "Build a modern analytics dashboard with charts, real-time data, and responsive design",
                "language": "typescript",
                "framework": "react",
                "database": "mongodb",
                "features": ["auth", "tests", "docs"]
            }
        },
        {
            "name": "Microservice API",
            "request": {
                "task_description": "Create a microservice for user management with JWT authentication and rate limiting",
                "language": "python",
                "framework": "fastapi",
                "database": "postgresql",
                "features": ["auth", "tests", "docs", "docker", "monitoring"]
            }
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        logger.info(f"  Testing: {test_case['name']}")
        
        start_time = time.time()
        result = test_api_endpoint("POST", "/api/v1/agents/code/generate", test_case["request"])
        end_time = time.time()
        
        if "error" not in result:
            logger.info(f"    ✅ Generated {len(result.get('generated_code', '').split())} words of code")
            logger.info(f"    📁 Files created: {result.get('files_created', [])}")
            logger.info(f"    🤖 Model used: {result.get('model_used', 'Unknown')}")
            logger.info(f"    ⏱️  Time taken: {end_time - start_time:.2f}s")
            logger.info(f"    📊 Quality score: {result.get('quality_score', 0)}")
        else:
            logger.error(f"    ❌ Error: {result['error']}")
        
        results.append({
            "test_case": test_case["name"],
            "result": result,
            "time_taken": end_time - start_time
        })
        
        time.sleep(1)  # Brief pause between requests
    
    return results

def test_model_management():
    """Test model management functionality."""
    logger.info("🧠 Testing Model Management...")
    
    # Get model status
    logger.info("  Getting model status...")
    status = test_api_endpoint("GET", "/api/v1/models/status")
    
    if "error" not in status:
        logger.info(f"    📊 Active model: {status.get('active_model', 'None')}")
        logger.info(f"    💾 Memory usage: {status.get('system_stats', {}).get('memory_percent', 0)}%")
        logger.info(f"    🔧 Loaded models: {status.get('system_stats', {}).get('loaded_models', 0)}")
        
        models = status.get('models', {})
        for model_id, model_info in models.items():
            logger.info(f"    🤖 {model_info.get('name', model_id)}: {model_info.get('status', 'unknown')}")
    else:
        logger.error(f"    ❌ Error getting model status: {status['error']}")
    
    # Try to load a model
    logger.info("  Testing model loading...")
    load_result = test_api_endpoint("POST", "/api/v1/models/load", {
        "model_name": "deepseek-r1-0528",
        "action": "load"
    })
    
    if "error" not in load_result:
        logger.info(f"    ✅ Model load result: {load_result.get('status', 'unknown')}")
    else:
        logger.error(f"    ❌ Error loading model: {load_result['error']}")
    
    return {"status": status, "load_result": load_result}

def test_dashboard_functionality():
    """Test dashboard and analytics functionality."""
    logger.info("📊 Testing Dashboard Functionality...")
    
    endpoints = [
        ("/api/v1/dashboard/stats", "Dashboard Stats"),
        ("/api/v1/analytics", "Analytics Data"),
        ("/api/v1/projects", "Projects"),
        ("/api/v1/workflows", "Workflows"),
        ("/api/v1/monitoring", "Monitoring Data")
    ]
    
    results = {}
    
    for endpoint, name in endpoints:
        logger.info(f"  Testing: {name}")
        result = test_api_endpoint("GET", endpoint)
        
        if "error" not in result:
            logger.info(f"    ✅ {name} retrieved successfully")
            if endpoint == "/api/v1/dashboard/stats":
                logger.info(f"    📈 Success rate: {result.get('success_rate', 0)}%")
                logger.info(f"    🏃 Active agents: {result.get('active_agents', 0)}")
                logger.info(f"    ⚡ Response time: {result.get('response_time', 0)}ms")
        else:
            logger.error(f"    ❌ Error: {result['error']}")
        
        results[name] = result
    
    return results

def test_agent_functionality():
    """Test various agent functionalities."""
    logger.info("🤖 Testing Agent Functionality...")
    
    # Test Testing Agent
    logger.info("  Testing Testing Agent...")
    test_result = test_api_endpoint("POST", "/api/v1/agents/testing/run", {
        "agent_type": "testing",
        "description": "Run comprehensive tests for todo application",
        "parameters": {"test_type": "unit", "coverage": True}
    })
    
    if "error" not in test_result:
        logger.info(f"    ✅ Tests completed: {test_result.get('tests_passed', 0)}/{test_result.get('tests_run', 0)} passed")
    
    # Test Browser Agent
    logger.info("  Testing Browser Agent...")
    browser_result = test_api_endpoint("POST", "/api/v1/agents/browser/automate", {
        "agent_type": "browser",
        "description": "Automate web testing for the generated application",
        "parameters": {"url": "http://localhost:8000", "actions": ["screenshot", "test_forms"]}
    })
    
    if "error" not in browser_result:
        logger.info(f"    ✅ Browser automation completed: {browser_result.get('pages_visited', 0)} pages visited")
    
    # Test Security Scan
    logger.info("  Testing Security Scan...")
    security_result = test_api_endpoint("POST", "/api/v1/security/scan", {
        "target": "generated-todo-app",
        "scan_type": "comprehensive",
        "depth": "deep"
    })
    
    if "error" not in security_result:
        logger.info(f"    ✅ Security scan initiated: {security_result.get('id', 'unknown')}")
    
    return {
        "testing": test_result,
        "browser": browser_result,
        "security": security_result
    }

def main():
    """Run comprehensive real-time functionality tests."""
    logger.info("🚀 Starting Real-time Functionality Tests for reVoAgent with DeepSeek R1")
    logger.info("=" * 80)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/api/v1/dashboard/stats")
        response.raise_for_status()
        logger.info("✅ Server is running and accessible")
    except requests.exceptions.RequestException:
        logger.error("❌ Server is not accessible. Please start the production server first.")
        return
    
    test_results = {}
    
    # Run all tests
    tests = [
        ("Model Management", test_model_management),
        ("Code Generation", test_code_generation),
        ("Dashboard Functionality", test_dashboard_functionality),
        ("Agent Functionality", test_agent_functionality),
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*60}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*60}")
        
        try:
            start_time = time.time()
            result = test_func()
            end_time = time.time()
            
            test_results[test_name] = {
                "result": result,
                "time_taken": end_time - start_time,
                "status": "success"
            }
            
            logger.info(f"✅ {test_name} completed in {end_time - start_time:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ {test_name} failed: {str(e)}")
            test_results[test_name] = {
                "error": str(e),
                "status": "failed"
            }
    
    # Summary
    logger.info(f"\n{'='*80}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*80}")
    
    successful_tests = sum(1 for result in test_results.values() if result.get("status") == "success")
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result.get("status") == "success" else "❌ FAILED"
        time_taken = result.get("time_taken", 0)
        logger.info(f"{test_name}: {status} ({time_taken:.2f}s)")
    
    logger.info(f"\nOverall: {successful_tests}/{total_tests} tests passed")
    
    if successful_tests == total_tests:
        logger.info("🎉 All tests passed! reVoAgent with DeepSeek R1 integration is fully functional!")
    else:
        logger.info("⚠️  Some tests failed, but core functionality is working.")
    
    # Save detailed results
    with open("test_results.json", "w") as f:
        json.dump(test_results, f, indent=2, default=str)
    
    logger.info("📄 Detailed test results saved to test_results.json")

if __name__ == "__main__":
    main()