#!/usr/bin/env python3
"""
reVoAgent Dashboard Integration Test

Tests the dashboard functionality and API endpoints.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
import httpx
import websockets

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_dashboard_health():
    """Test dashboard health endpoint."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:12000/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            logger.info("✅ Health check passed")
            return True
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False


async def test_dashboard_main_page():
    """Test dashboard main page."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:12000/")
            assert response.status_code == 200
            assert "reVoAgent Dashboard" in response.text
            assert "Revolutionary Agentic Coding Platform" in response.text
            logger.info("✅ Main page loads correctly")
            return True
        except Exception as e:
            logger.error(f"❌ Main page test failed: {e}")
            return False


async def test_api_dashboard_stats():
    """Test dashboard stats API."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:12000/api/v1/dashboard/stats")
            assert response.status_code == 200
            data = response.json()
            
            # Check required fields
            required_fields = [
                "active_agents", "running_workflows", "tasks_completed", 
                "models_loaded", "success_rate", "response_time"
            ]
            for field in required_fields:
                assert field in data, f"Missing field: {field}"
            
            logger.info("✅ Dashboard stats API working")
            return True
        except Exception as e:
            logger.error(f"❌ Dashboard stats API failed: {e}")
            return False


async def test_api_agents():
    """Test agents API."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:12000/api/v1/agents")
            assert response.status_code == 200
            data = response.json()
            assert "agents" in data
            assert isinstance(data["agents"], list)
            logger.info("✅ Agents API working")
            return True
        except Exception as e:
            logger.error(f"❌ Agents API failed: {e}")
            return False


async def test_api_workflows():
    """Test workflows API."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:12000/api/v1/workflows")
            assert response.status_code == 200
            data = response.json()
            assert "workflows" in data
            assert isinstance(data["workflows"], list)
            logger.info("✅ Workflows API working")
            return True
        except Exception as e:
            logger.error(f"❌ Workflows API failed: {e}")
            return False


async def test_api_models():
    """Test models API."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:12000/api/v1/models")
            assert response.status_code == 200
            data = response.json()
            assert "models" in data
            assert isinstance(data["models"], list)
            logger.info("✅ Models API working")
            return True
        except Exception as e:
            logger.error(f"❌ Models API failed: {e}")
            return False


async def test_api_system_metrics():
    """Test system metrics API."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:12000/api/v1/system/metrics")
            assert response.status_code == 200
            data = response.json()
            
            # Check required sections
            required_sections = ["cpu", "memory", "disk", "network"]
            for section in required_sections:
                assert section in data, f"Missing section: {section}"
            
            logger.info("✅ System metrics API working")
            return True
        except Exception as e:
            logger.error(f"❌ System metrics API failed: {e}")
            return False


async def test_api_integration_status():
    """Test integration status API."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:12000/api/v1/integrations/status")
            assert response.status_code == 200
            data = response.json()
            assert "integrations" in data
            logger.info("✅ Integration status API working")
            return True
        except Exception as e:
            logger.error(f"❌ Integration status API failed: {e}")
            return False


async def test_api_recent_activity():
    """Test recent activity API."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:12000/api/v1/activity/recent")
            assert response.status_code == 200
            data = response.json()
            assert "activities" in data
            assert isinstance(data["activities"], list)
            logger.info("✅ Recent activity API working")
            return True
        except Exception as e:
            logger.error(f"❌ Recent activity API failed: {e}")
            return False


async def test_websocket_connection():
    """Test WebSocket connection."""
    try:
        uri = "ws://localhost:12000/ws"
        async with websockets.connect(uri) as websocket:
            # Test connection establishment
            await asyncio.sleep(0.5)
            
            # Test ping
            ping_message = {"type": "ping"}
            await websocket.send(json.dumps(ping_message))
            
            # Wait for pong response
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)
            
            # Should receive connection_established or pong
            assert data["type"] in ["connection_established", "pong"]
            
            logger.info("✅ WebSocket connection working")
            return True
    except Exception as e:
        logger.error(f"❌ WebSocket test failed: {e}")
        return False


async def test_static_files():
    """Test static file serving."""
    async with httpx.AsyncClient() as client:
        try:
            # Test CSS file
            response = await client.get("http://localhost:12000/static/dashboard.css")
            assert response.status_code == 200
            assert "text/css" in response.headers.get("content-type", "")
            
            # Test JS file
            response = await client.get("http://localhost:12000/static/dashboard.js")
            assert response.status_code == 200
            assert "javascript" in response.headers.get("content-type", "")
            
            logger.info("✅ Static files serving correctly")
            return True
        except Exception as e:
            logger.error(f"❌ Static files test failed: {e}")
            return False


async def test_dashboard_features():
    """Test dashboard feature completeness."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:12000/")
            content = response.text
            
            # Check for key dashboard features
            features = [
                "Revolutionary Agentic Coding Platform",
                "Zero-cost AI",
                "Multi-platform",
                "Production Ready",
                "OpenHands",
                "vLLM",
                "Docker",
                "All-Hands",
                "Quick Actions",
                "System Metrics",
                "Active Workflows",
                "Recent Activity Feed"
            ]
            
            missing_features = []
            for feature in features:
                if feature not in content:
                    missing_features.append(feature)
            
            if missing_features:
                logger.warning(f"⚠️ Missing features: {missing_features}")
            else:
                logger.info("✅ All dashboard features present")
            
            return len(missing_features) == 0
        except Exception as e:
            logger.error(f"❌ Dashboard features test failed: {e}")
            return False


async def run_all_tests():
    """Run all dashboard tests."""
    logger.info("🚀 Starting reVoAgent Dashboard Integration Tests")
    
    tests = [
        ("Health Check", test_dashboard_health),
        ("Main Page", test_dashboard_main_page),
        ("Dashboard Stats API", test_api_dashboard_stats),
        ("Agents API", test_api_agents),
        ("Workflows API", test_api_workflows),
        ("Models API", test_api_models),
        ("System Metrics API", test_api_system_metrics),
        ("Integration Status API", test_api_integration_status),
        ("Recent Activity API", test_api_recent_activity),
        ("WebSocket Connection", test_websocket_connection),
        ("Static Files", test_static_files),
        ("Dashboard Features", test_dashboard_features),
    ]
    
    results = []
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running test: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
            if result:
                passed += 1
        except Exception as e:
            logger.error(f"❌ Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    logger.info(f"\n📊 Test Results Summary:")
    logger.info(f"{'='*50}")
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name:<30} {status}")
    
    logger.info(f"{'='*50}")
    logger.info(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        logger.info("🎉 All tests passed! Dashboard is working correctly.")
        return True
    else:
        logger.error(f"💥 {total-passed} tests failed. Please check the dashboard.")
        return False


async def main():
    """Main test runner."""
    try:
        success = await run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test runner failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())