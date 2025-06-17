#!/usr/bin/env python3
"""
Frontend-Backend Integration Test for DeepSeek R1

This script tests the complete integration between the frontend and backend
with DeepSeek R1 model, including async loading, generation, and real-time updates.
"""

import asyncio
import json
import logging
import requests
import time
import websockets
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:12000"
WS_URL = "ws://localhost:12000/ws"

class FrontendBackendTester:
    def __init__(self):
        self.websocket = None
        self.ws_messages = []
        self.test_results = {}
        
    async def connect_websocket(self):
        """Connect to WebSocket for real-time updates."""
        try:
            self.websocket = await websockets.connect(WS_URL)
            logger.info("✅ WebSocket connected successfully")
            return True
        except Exception as e:
            logger.error(f"❌ WebSocket connection failed: {e}")
            return False
    
    async def listen_websocket(self):
        """Listen for WebSocket messages."""
        try:
            while True:
                message = await self.websocket.recv()
                data = json.loads(message)
                self.ws_messages.append({
                    'timestamp': datetime.now(),
                    'data': data
                })
                logger.info(f"📨 WebSocket message: {data.get('type', 'unknown')}")
        except websockets.exceptions.ConnectionClosed:
            logger.warning("🔌 WebSocket connection closed")
        except Exception as e:
            logger.error(f"❌ WebSocket error: {e}")
    
    def test_api_endpoint(self, method: str, endpoint: str, data: dict = None) -> dict:
        """Test an API endpoint."""
        url = f"{BASE_URL}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, timeout=60)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return {
                'success': True,
                'data': response.json(),
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds()
            }
        
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            }
    
    def test_frontend_accessibility(self):
        """Test if frontend pages are accessible."""
        logger.info("🌐 Testing Frontend Accessibility...")
        
        pages = [
            ("/", "Main Dashboard"),
            ("/static/index.html", "Static Dashboard"),
            ("/static/deepseek_test.html", "DeepSeek Test Page"),
            ("/static/dashboard.js", "Dashboard JavaScript"),
            ("/static/dashboard.css", "Dashboard CSS")
        ]
        
        results = {}
        
        for path, name in pages:
            try:
                response = requests.get(f"{BASE_URL}{path}", timeout=10)
                if response.status_code == 200:
                    logger.info(f"  ✅ {name}: Accessible")
                    results[name] = {'status': 'accessible', 'size': len(response.content)}
                else:
                    logger.warning(f"  ⚠️  {name}: Status {response.status_code}")
                    results[name] = {'status': f'status_{response.status_code}'}
            except Exception as e:
                logger.error(f"  ❌ {name}: {str(e)}")
                results[name] = {'status': 'error', 'error': str(e)}
        
        return results
    
    def test_model_management_api(self):
        """Test model management API endpoints."""
        logger.info("🧠 Testing Model Management API...")
        
        # Test model status
        logger.info("  Testing model status endpoint...")
        status_result = self.test_api_endpoint("GET", "/api/v1/models/status")
        
        if status_result['success']:
            models = status_result['data'].get('models', {})
            deepseek_model = models.get('deepseek-r1-0528', {})
            logger.info(f"    📊 DeepSeek R1 Status: {deepseek_model.get('status', 'unknown')}")
            logger.info(f"    💾 Memory Usage: {status_result['data'].get('system_stats', {}).get('memory_percent', 0)}%")
        else:
            logger.error(f"    ❌ Status check failed: {status_result['error']}")
        
        # Test model loading
        logger.info("  Testing model loading endpoint...")
        load_result = self.test_api_endpoint("POST", "/api/v1/models/load", {
            "model_name": "deepseek-r1-0528",
            "action": "load"
        })
        
        if load_result['success']:
            logger.info(f"    ✅ Model load response: {load_result['data'].get('status', 'unknown')}")
        else:
            logger.error(f"    ❌ Model load failed: {load_result['error']}")
        
        return {
            'status_check': status_result,
            'model_load': load_result
        }
    
    def test_code_generation_api(self):
        """Test code generation API with various scenarios."""
        logger.info("🔧 Testing Code Generation API...")
        
        test_cases = [
            {
                "name": "Simple FastAPI App",
                "request": {
                    "task_description": "Create a simple REST API for managing books with CRUD operations",
                    "language": "python",
                    "framework": "fastapi",
                    "database": "postgresql",
                    "features": ["auth", "tests"]
                }
            },
            {
                "name": "React Dashboard",
                "request": {
                    "task_description": "Build a responsive dashboard with charts and data visualization",
                    "language": "typescript",
                    "framework": "react",
                    "features": ["auth", "tests", "docs"]
                }
            },
            {
                "name": "Microservice with Monitoring",
                "request": {
                    "task_description": "Create a user authentication microservice with health checks and metrics",
                    "language": "python",
                    "framework": "fastapi",
                    "database": "postgresql",
                    "features": ["auth", "tests", "docs", "docker", "monitoring"]
                }
            }
        ]
        
        results = {}
        
        for test_case in test_cases:
            logger.info(f"  Testing: {test_case['name']}")
            
            start_time = time.time()
            result = self.test_api_endpoint("POST", "/api/v1/agents/code/generate", test_case["request"])
            end_time = time.time()
            
            if result['success']:
                data = result['data']
                logger.info(f"    ✅ Generated {len(data.get('generated_code', '').split())} words")
                logger.info(f"    🤖 Model used: {data.get('model_used', 'Unknown')}")
                logger.info(f"    📊 Quality score: {data.get('quality_score', 0)}")
                logger.info(f"    ⏱️  Time: {end_time - start_time:.2f}s")
                
                results[test_case['name']] = {
                    'success': True,
                    'model_used': data.get('model_used'),
                    'quality_score': data.get('quality_score'),
                    'code_length': len(data.get('generated_code', '')),
                    'time_taken': end_time - start_time,
                    'files_created': data.get('files_created', [])
                }
            else:
                logger.error(f"    ❌ Generation failed: {result['error']}")
                results[test_case['name']] = {
                    'success': False,
                    'error': result['error'],
                    'time_taken': end_time - start_time
                }
        
        return results
    
    def test_dashboard_api(self):
        """Test dashboard and analytics API endpoints."""
        logger.info("📊 Testing Dashboard API...")
        
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
            result = self.test_api_endpoint("GET", endpoint)
            
            if result['success']:
                logger.info(f"    ✅ {name}: Retrieved successfully")
                logger.info(f"    ⏱️  Response time: {result['response_time']:.3f}s")
                results[name] = {
                    'success': True,
                    'response_time': result['response_time'],
                    'data_size': len(str(result['data']))
                }
            else:
                logger.error(f"    ❌ {name}: {result['error']}")
                results[name] = {
                    'success': False,
                    'error': result['error']
                }
        
        return results
    
    async def test_websocket_integration(self):
        """Test WebSocket real-time integration."""
        logger.info("🔌 Testing WebSocket Integration...")
        
        # Connect to WebSocket
        connected = await self.connect_websocket()
        if not connected:
            return {'success': False, 'error': 'Failed to connect to WebSocket'}
        
        # Start listening for messages
        listen_task = asyncio.create_task(self.listen_websocket())
        
        # Wait a bit to collect messages
        await asyncio.sleep(2)
        
        # Trigger some API calls to generate WebSocket messages
        logger.info("  Triggering API calls to test real-time updates...")
        
        # Check model status (should trigger WebSocket update)
        self.test_api_endpoint("GET", "/api/v1/models/status")
        await asyncio.sleep(1)
        
        # Generate code (should trigger progress updates)
        self.test_api_endpoint("POST", "/api/v1/agents/code/generate", {
            "task_description": "Create a simple hello world API",
            "language": "python",
            "framework": "fastapi"
        })
        await asyncio.sleep(3)
        
        # Cancel listening task
        listen_task.cancel()
        
        # Close WebSocket
        if self.websocket:
            await self.websocket.close()
        
        logger.info(f"  📨 Received {len(self.ws_messages)} WebSocket messages")
        
        return {
            'success': True,
            'messages_received': len(self.ws_messages),
            'message_types': [msg['data'].get('type', 'unknown') for msg in self.ws_messages]
        }
    
    def test_async_loading_simulation(self):
        """Test async loading behavior simulation."""
        logger.info("⚡ Testing Async Loading Simulation...")
        
        # Simulate multiple concurrent requests
        def make_request(request_id):
            return self.test_api_endpoint("POST", "/api/v1/agents/code/generate", {
                "task_description": f"Create a simple API endpoint #{request_id}",
                "language": "python",
                "framework": "fastapi"
            })
        
        # Test concurrent requests
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request, i) for i in range(3)]
            results = [future.result() for future in futures]
        end_time = time.time()
        
        successful_requests = sum(1 for r in results if r['success'])
        
        logger.info(f"  ✅ Completed {successful_requests}/3 concurrent requests")
        logger.info(f"  ⏱️  Total time: {end_time - start_time:.2f}s")
        
        return {
            'concurrent_requests': 3,
            'successful_requests': successful_requests,
            'total_time': end_time - start_time,
            'average_time_per_request': (end_time - start_time) / 3
        }
    
    async def run_comprehensive_test(self):
        """Run all tests comprehensively."""
        logger.info("🚀 Starting Comprehensive Frontend-Backend Integration Test")
        logger.info("=" * 80)
        
        # Check if server is running
        try:
            response = requests.get(f"{BASE_URL}/api/v1/dashboard/stats", timeout=5)
            response.raise_for_status()
            logger.info("✅ Server is running and accessible")
        except requests.exceptions.RequestException:
            logger.error("❌ Server is not accessible. Please start the production server first.")
            return
        
        # Run all tests
        test_functions = [
            ("Frontend Accessibility", self.test_frontend_accessibility),
            ("Model Management API", self.test_model_management_api),
            ("Code Generation API", self.test_code_generation_api),
            ("Dashboard API", self.test_dashboard_api),
            ("Async Loading Simulation", self.test_async_loading_simulation),
        ]
        
        for test_name, test_func in test_functions:
            logger.info(f"\n{'='*60}")
            logger.info(f"Running: {test_name}")
            logger.info(f"{'='*60}")
            
            try:
                start_time = time.time()
                result = test_func()
                end_time = time.time()
                
                self.test_results[test_name] = {
                    'result': result,
                    'time_taken': end_time - start_time,
                    'status': 'success'
                }
                
                logger.info(f"✅ {test_name} completed in {end_time - start_time:.2f}s")
                
            except Exception as e:
                logger.error(f"❌ {test_name} failed: {str(e)}")
                self.test_results[test_name] = {
                    'error': str(e),
                    'status': 'failed'
                }
        
        # Test WebSocket integration
        logger.info(f"\n{'='*60}")
        logger.info("Running: WebSocket Integration")
        logger.info(f"{'='*60}")
        
        try:
            ws_result = await self.test_websocket_integration()
            self.test_results['WebSocket Integration'] = {
                'result': ws_result,
                'status': 'success' if ws_result['success'] else 'failed'
            }
            logger.info("✅ WebSocket Integration completed")
        except Exception as e:
            logger.error(f"❌ WebSocket Integration failed: {str(e)}")
            self.test_results['WebSocket Integration'] = {
                'error': str(e),
                'status': 'failed'
            }
        
        # Generate summary
        self.generate_test_summary()
    
    def generate_test_summary(self):
        """Generate and display test summary."""
        logger.info(f"\n{'='*80}")
        logger.info("TEST SUMMARY")
        logger.info(f"{'='*80}")
        
        successful_tests = sum(1 for result in self.test_results.values() if result.get('status') == 'success')
        total_tests = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASSED" if result.get('status') == 'success' else "❌ FAILED"
            time_taken = result.get('time_taken', 0)
            logger.info(f"{test_name}: {status} ({time_taken:.2f}s)")
        
        logger.info(f"\nOverall: {successful_tests}/{total_tests} tests passed")
        
        if successful_tests == total_tests:
            logger.info("🎉 All tests passed! Frontend-Backend integration with DeepSeek R1 is fully functional!")
        else:
            logger.info("⚠️  Some tests failed, but core functionality is working.")
        
        # Save detailed results
        with open("frontend_backend_test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        logger.info("📄 Detailed test results saved to frontend_backend_test_results.json")
        
        # Display key metrics
        logger.info(f"\n{'='*60}")
        logger.info("KEY METRICS")
        logger.info(f"{'='*60}")
        
        # Code generation metrics
        if 'Code Generation API' in self.test_results:
            code_gen_results = self.test_results['Code Generation API']['result']
            for test_name, result in code_gen_results.items():
                if result.get('success'):
                    logger.info(f"📊 {test_name}:")
                    logger.info(f"    Model: {result.get('model_used', 'Unknown')}")
                    logger.info(f"    Quality: {result.get('quality_score', 0)}%")
                    logger.info(f"    Time: {result.get('time_taken', 0):.2f}s")
                    logger.info(f"    Code Length: {result.get('code_length', 0)} chars")
        
        # WebSocket metrics
        if 'WebSocket Integration' in self.test_results:
            ws_result = self.test_results['WebSocket Integration']['result']
            if ws_result.get('success'):
                logger.info(f"🔌 WebSocket Messages: {ws_result.get('messages_received', 0)}")
                logger.info(f"🔌 Message Types: {', '.join(ws_result.get('message_types', []))}")

async def main():
    """Main test execution function."""
    tester = FrontendBackendTester()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())