# test_realtime_integration.py
"""
Comprehensive Testing System for reVoAgent Real-Time AI Integration
Tests all components: AI providers, agents, WebSocket, error handling
"""

import asyncio
import json
import time
import websockets
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import sys
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent))

from packages.ai.real_model_manager import real_model_manager
from packages.agents.realtime_executor import realtime_executor
from packages.core.error_handling import error_handler, safe_ai_call

class TestResults:
    """Store and track test results"""
    
    def __init__(self):
        self.tests: List[Dict[str, Any]] = []
        self.passed = 0
        self.failed = 0
        self.start_time = time.time()
    
    def add_test(self, name: str, passed: bool, duration: float, details: Optional[Dict] = None):
        """Add test result"""
        self.tests.append({
            "name": name,
            "passed": passed,
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        })
        
        if passed:
            self.passed += 1
            print(f"✅ PASS: {name} ({duration:.2f}s)")
        else:
            self.failed += 1
            print(f"❌ FAIL: {name} ({duration:.2f}s)")
            if details and "error" in details:
                print(f"   Error: {details['error']}")
    
    def print_summary(self):
        """Print test summary"""
        total_time = time.time() - self.start_time
        total_tests = self.passed + self.failed
        success_rate = (self.passed / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "="*60)
        print("🧪 TEST SUMMARY")
        print("="*60)
        print(f"Total tests: {total_tests}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success rate: {success_rate:.1f}%")
        print(f"Total time: {total_time:.2f}s")
        
        if self.failed == 0:
            print("\n🎉 ALL TESTS PASSED! System is ready for production.")
        else:
            print(f"\n⚠️  {self.failed} test(s) failed. Check issues before deployment.")
        
        return self.failed == 0

class RealTimeIntegrationTester:
    """Comprehensive testing system for real-time AI integration"""
    
    def __init__(self):
        self.results = TestResults()
        self.backend_url = "http://localhost:12001"
        self.websocket_url = "ws://localhost:12001"
        
    async def run_all_tests(self):
        """Run comprehensive test suite"""
        
        print("🚀 Starting reVoAgent Real-Time Integration Tests")
        print("="*60)
        
        # Test categories
        await self.test_backend_health()
        await self.test_ai_providers()
        await self.test_agent_execution()
        await self.test_websocket_integration()
        await self.test_error_handling()
        await self.test_performance()
        
        return self.results.print_summary()
    
    async def test_backend_health(self):
        """Test backend API health and endpoints"""
        
        print("\n📡 Testing Backend Health...")
        
        # Test 1: Basic health endpoint
        start_time = time.time()
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            data = response.json()
            
            self.results.add_test(
                "Backend Health Endpoint",
                response.status_code == 200 and data.get("status") == "healthy",
                time.time() - start_time,
                {"response": data}
            )
        except Exception as e:
            self.results.add_test(
                "Backend Health Endpoint",
                False,
                time.time() - start_time,
                {"error": str(e)}
            )
        
        # Test 2: API status endpoint
        start_time = time.time()
        try:
            response = requests.get(f"{self.backend_url}/api/ai/status", timeout=10)
            data = response.json()
            
            self.results.add_test(
                "AI Status Endpoint",
                response.status_code == 200 and "available_providers" in data,
                time.time() - start_time,
                {"providers": data.get("available_providers", [])}
            )
        except Exception as e:
            self.results.add_test(
                "AI Status Endpoint",
                False,
                time.time() - start_time,
                {"error": str(e)}
            )
        
        # Test 3: Dashboard stats endpoint
        start_time = time.time()
        try:
            response = requests.get(f"{self.backend_url}/api/dashboard/stats", timeout=10)
            data = response.json()
            
            self.results.add_test(
                "Dashboard Stats Endpoint",
                response.status_code == 200 and "system" in data,
                time.time() - start_time,
                {"has_ai_data": "ai" in data, "has_agents_data": "agents" in data}
            )
        except Exception as e:
            self.results.add_test(
                "Dashboard Stats Endpoint",
                False,
                time.time() - start_time,
                {"error": str(e)}
            )
    
    async def test_ai_providers(self):
        """Test AI provider integrations"""
        
        print("\n🤖 Testing AI Providers...")
        
        # Test 1: AI provider detection
        start_time = time.time()
        try:
            provider_status = real_model_manager.get_provider_status()
            has_providers = len(provider_status["available_providers"]) > 0
            
            self.results.add_test(
                "AI Provider Detection",
                has_providers,
                time.time() - start_time,
                {"providers": provider_status["available_providers"]}
            )
        except Exception as e:
            self.results.add_test(
                "AI Provider Detection",
                False,
                time.time() - start_time,
                {"error": str(e)}
            )
        
        # Test 2: Simple AI generation
        start_time = time.time()
        try:
            response = await real_model_manager.generate_response(
                "Generate a simple Python function that adds two numbers",
                "code_generation"
            )
            
            success = (
                response.get("content") and 
                len(response["content"]) > 50 and
                "def" in response["content"]
            )
            
            self.results.add_test(
                "AI Generation Test",
                success,
                time.time() - start_time,
                {
                    "provider": response.get("provider"),
                    "response_time": response.get("response_time"),
                    "content_length": len(response.get("content", ""))
                }
            )
        except Exception as e:
            self.results.add_test(
                "AI Generation Test",
                False,
                time.time() - start_time,
                {"error": str(e)}
            )
        
        # Test 3: AI test endpoint
        start_time = time.time()
        try:
            test_data = {
                "prompt": "Write a Python function that calculates factorial",
                "task_type": "code_generation"
            }
            
            response = requests.post(
                f"{self.backend_url}/api/ai/test",
                json=test_data,
                timeout=30
            )
            
            data = response.json()
            success = (
                response.status_code == 200 and
                data.get("success") == True and
                "response" in data
            )
            
            self.results.add_test(
                "AI Test Endpoint",
                success,
                time.time() - start_time,
                {
                    "provider_used": data.get("provider_used"),
                    "response_time": data.get("response_time")
                }
            )
        except Exception as e:
            self.results.add_test(
                "AI Test Endpoint",
                False,
                time.time() - start_time,
                {"error": str(e)}
            )
    
    async def test_agent_execution(self):
        """Test real-time agent execution"""
        
        print("\n🎯 Testing Agent Execution...")
        
        # Test each agent type
        agent_types = ["code-generator", "debug-agent", "testing-agent", "security-agent"]
        
        for agent_type in agent_types:
            start_time = time.time()
            try:
                # Submit task
                task_data = {
                    "description": f"Test task for {agent_type}",
                    "parameters": {"language": "python", "test_mode": True}
                }
                
                response = requests.post(
                    f"{self.backend_url}/api/agents/{agent_type}/execute",
                    json=task_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    task_id = data.get("task_id")
                    
                    # Wait for completion (with timeout)
                    completion_start = time.time()
                    completed = False
                    final_status = None
                    
                    while time.time() - completion_start < 30:  # 30 second timeout
                        await asyncio.sleep(1)
                        
                        status_response = requests.get(
                            f"{self.backend_url}/api/agents/tasks/{task_id}",
                            timeout=5
                        )
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            if status_data.get("status") in ["completed", "failed"]:
                                completed = True
                                final_status = status_data
                                break
                    
                    success = (
                        completed and 
                        final_status and 
                        final_status.get("status") == "completed" and
                        final_status.get("result") is not None
                    )
                    
                    self.results.add_test(
                        f"{agent_type.title()} Execution",
                        success,
                        time.time() - start_time,
                        {
                            "task_id": task_id,
                            "completed": completed,
                            "final_status": final_status.get("status") if final_status else None,
                            "has_result": bool(final_status.get("result") if final_status else False)
                        }
                    )
                else:
                    self.results.add_test(
                        f"{agent_type.title()} Execution",
                        False,
                        time.time() - start_time,
                        {"http_status": response.status_code, "response": response.text}
                    )
                
            except Exception as e:
                self.results.add_test(
                    f"{agent_type.title()} Execution",
                    False,
                    time.time() - start_time,
                    {"error": str(e)}
                )
    
    async def test_websocket_integration(self):
        """Test WebSocket real-time updates"""
        
        print("\n🔌 Testing WebSocket Integration...")
        
        # Test 1: Dashboard WebSocket connection
        start_time = time.time()
        try:
            messages_received = []
            
            async with websockets.connect(f"{self.websocket_url}/ws/dashboard") as websocket:
                # Wait for messages for 5 seconds
                try:
                    for _ in range(3):  # Try to receive 3 messages
                        message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        data = json.loads(message)
                        messages_received.append(data)
                except asyncio.TimeoutError:
                    pass  # Expected after timeout
            
            success = len(messages_received) > 0
            
            self.results.add_test(
                "Dashboard WebSocket Connection",
                success,
                time.time() - start_time,
                {
                    "messages_received": len(messages_received),
                    "message_types": [msg.get("type") for msg in messages_received]
                }
            )
            
        except Exception as e:
            self.results.add_test(
                "Dashboard WebSocket Connection",
                False,
                time.time() - start_time,
                {"error": str(e)}
            )
        
        # Test 2: Agent-specific WebSocket
        start_time = time.time()
        try:
            messages_received = []
            
            async with websockets.connect(f"{self.websocket_url}/ws/agents/code-generator") as websocket:
                # Wait for messages for 3 seconds
                try:
                    for _ in range(2):
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.5)
                        data = json.loads(message)
                        messages_received.append(data)
                except asyncio.TimeoutError:
                    pass
            
            success = len(messages_received) > 0
            
            self.results.add_test(
                "Agent WebSocket Connection",
                success,
                time.time() - start_time,
                {"messages_received": len(messages_received)}
            )
            
        except Exception as e:
            self.results.add_test(
                "Agent WebSocket Connection",
                False,
                time.time() - start_time,
                {"error": str(e)}
            )
    
    async def test_error_handling(self):
        """Test error handling and recovery"""
        
        print("\n🛡️ Testing Error Handling...")
        
        # Test 1: Invalid API request
        start_time = time.time()
        try:
            response = requests.post(
                f"{self.backend_url}/api/agents/invalid-agent/execute",
                json={"description": "test"},
                timeout=10
            )
            
            # Should return 400 or 404 error
            success = response.status_code in [400, 404]
            
            self.results.add_test(
                "Invalid Agent Request Handling",
                success,
                time.time() - start_time,
                {"status_code": response.status_code}
            )
            
        except Exception as e:
            self.results.add_test(
                "Invalid Agent Request Handling",
                False,
                time.time() - start_time,
                {"error": str(e)}
            )
        
        # Test 2: Error statistics endpoint
        start_time = time.time()
        try:
            error_stats = error_handler.get_error_stats()
            success = isinstance(error_stats, dict) and "total_errors" in error_stats
            
            self.results.add_test(
                "Error Statistics Collection",
                success,
                time.time() - start_time,
                {"total_errors": error_stats.get("total_errors", 0)}
            )
            
        except Exception as e:
            self.results.add_test(
                "Error Statistics Collection",
                False,
                time.time() - start_time,
                {"error": str(e)}
            )
        
        # Test 3: Safe AI call with fallback
        start_time = time.time()
        try:
            async def failing_ai_function():
                raise Exception("Simulated AI failure")
            
            async def fallback_function():
                return {"content": "Fallback response", "provider": "fallback"}
            
            result = await safe_ai_call(
                failing_ai_function,
                fallback_function,
                {"component": "test"}
            )
            
            success = result and result.get("provider") == "fallback"
            
            self.results.add_test(
                "AI Fallback Mechanism",
                success,
                time.time() - start_time,
                {"fallback_triggered": True}
            )
            
        except Exception as e:
            self.results.add_test(
                "AI Fallback Mechanism",
                False,
                time.time() - start_time,
                {"error": str(e)}
            )
    
    async def test_performance(self):
        """Test system performance metrics"""
        
        print("\n⚡ Testing Performance...")
        
        # Test 1: API response time
        start_time = time.time()
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            response_time = time.time() - start_time
            
            # Should respond within 1 second
            success = response.status_code == 200 and response_time < 1.0
            
            self.results.add_test(
                "API Response Time",
                success,
                response_time,
                {"response_time_ms": response_time * 1000}
            )
            
        except Exception as e:
            self.results.add_test(
                "API Response Time",
                False,
                time.time() - start_time,
                {"error": str(e)}
            )
        
        # Test 2: Concurrent requests
        start_time = time.time()
        try:
            async def make_request():
                response = requests.get(f"{self.backend_url}/health", timeout=10)
                return response.status_code == 200
            
            # Make 5 concurrent requests
            tasks = [make_request() for _ in range(5)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful = sum(1 for result in results if result is True)
            success = successful >= 4  # At least 4 out of 5 should succeed
            
            self.results.add_test(
                "Concurrent Request Handling",
                success,
                time.time() - start_time,
                {"successful_requests": successful, "total_requests": 5}
            )
            
        except Exception as e:
            self.results.add_test(
                "Concurrent Request Handling",
                False,
                time.time() - start_time,
                {"error": str(e)}
            )

async def main():
    """Run the comprehensive test suite"""
    
    print("🧪 reVoAgent Real-Time Integration Test Suite")
    print("Verifying all components are working correctly...")
    print()
    
    tester = RealTimeIntegrationTester()
    
    try:
        success = await tester.run_all_tests()
        
        if success:
            print("\n🎉 All tests passed! Your reVoAgent integration is ready.")
            print("\nNext steps:")
            print("1. Configure your AI API keys in .env")
            print("2. Start the frontend with: cd frontend && npm run dev")
            print("3. Access the dashboard at: http://localhost:12000")
            return 0
        else:
            print("\n⚠️  Some tests failed. Please check the issues above.")
            print("\nTroubleshooting:")
            print("1. Ensure backend is running: python apps/backend/main_realtime.py")
            print("2. Check your API keys are set correctly")
            print("3. Verify all dependencies are installed")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n💥 Test suite failed with error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
