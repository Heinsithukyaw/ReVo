"""
Staging Environment Smoke Tests
Quick validation tests for staging deployment
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SmokeTestResult:
    test_name: str
    status: str  # PASS, FAIL, SKIP
    duration: float
    error_message: str = ""
    response_data: Dict[str, Any] = None

class StagingSmokeTest:
    def __init__(self, base_url: str = "https://staging.revoagent.com"):
        self.base_url = base_url
        self.results: List[SmokeTestResult] = []
        
    async def test_health_endpoint(self) -> SmokeTestResult:
        """Test basic health endpoint"""
        logger.info("🏥 Testing health endpoint...")
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health", timeout=10) as response:
                    duration = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        return SmokeTestResult(
                            test_name="Health Endpoint",
                            status="PASS",
                            duration=duration,
                            response_data=data
                        )
                    else:
                        return SmokeTestResult(
                            test_name="Health Endpoint",
                            status="FAIL",
                            duration=duration,
                            error_message=f"HTTP {response.status}"
                        )
        except Exception as e:
            return SmokeTestResult(
                test_name="Health Endpoint",
                status="FAIL",
                duration=time.time() - start_time,
                error_message=str(e)
            )
    
    async def test_api_endpoints(self) -> SmokeTestResult:
        """Test critical API endpoints"""
        logger.info("🔌 Testing API endpoints...")
        start_time = time.time()
        
        endpoints = [
            "/api/agents/status",
            "/api/system/metrics",
            "/api/models/list",
            "/api/health/detailed"
        ]
        
        try:
            async with aiohttp.ClientSession() as session:
                for endpoint in endpoints:
                    async with session.get(f"{self.base_url}{endpoint}", timeout=10) as response:
                        if response.status not in [200, 401, 403]:  # 401/403 are acceptable for protected endpoints
                            return SmokeTestResult(
                                test_name="API Endpoints",
                                status="FAIL",
                                duration=time.time() - start_time,
                                error_message=f"Endpoint {endpoint} returned HTTP {response.status}"
                            )
                
                return SmokeTestResult(
                    test_name="API Endpoints",
                    status="PASS",
                    duration=time.time() - start_time
                )
                
        except Exception as e:
            return SmokeTestResult(
                test_name="API Endpoints",
                status="FAIL",
                duration=time.time() - start_time,
                error_message=str(e)
            )
    
    async def test_websocket_connection(self) -> SmokeTestResult:
        """Test WebSocket connectivity"""
        logger.info("🔌 Testing WebSocket connection...")
        start_time = time.time()
        
        try:
            import websockets
            
            ws_url = self.base_url.replace("https://", "wss://").replace("http://", "ws://") + "/ws"
            
            async with websockets.connect(ws_url, timeout=10) as websocket:
                # Send test message
                test_message = {
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send(json.dumps(test_message))
                
                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                
                return SmokeTestResult(
                    test_name="WebSocket Connection",
                    status="PASS",
                    duration=time.time() - start_time,
                    response_data={"response": response}
                )
                
        except Exception as e:
            return SmokeTestResult(
                test_name="WebSocket Connection",
                status="FAIL",
                duration=time.time() - start_time,
                error_message=str(e)
            )
    
    async def test_database_connectivity(self) -> SmokeTestResult:
        """Test database connectivity through API"""
        logger.info("💾 Testing database connectivity...")
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test endpoint that requires database
                async with session.get(f"{self.base_url}/api/system/status", timeout=10) as response:
                    duration = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        if "database" in data and data["database"].get("status") == "connected":
                            return SmokeTestResult(
                                test_name="Database Connectivity",
                                status="PASS",
                                duration=duration,
                                response_data=data
                            )
                        else:
                            return SmokeTestResult(
                                test_name="Database Connectivity",
                                status="FAIL",
                                duration=duration,
                                error_message="Database not connected"
                            )
                    else:
                        return SmokeTestResult(
                            test_name="Database Connectivity",
                            status="FAIL",
                            duration=duration,
                            error_message=f"HTTP {response.status}"
                        )
                        
        except Exception as e:
            return SmokeTestResult(
                test_name="Database Connectivity",
                status="FAIL",
                duration=time.time() - start_time,
                error_message=str(e)
            )
    
    async def test_ai_model_availability(self) -> SmokeTestResult:
        """Test AI model availability"""
        logger.info("🤖 Testing AI model availability...")
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test model list endpoint
                async with session.get(f"{self.base_url}/api/models/status", timeout=15) as response:
                    duration = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        available_models = [m for m in data.get("models", []) if m.get("status") == "available"]
                        
                        if available_models:
                            return SmokeTestResult(
                                test_name="AI Model Availability",
                                status="PASS",
                                duration=duration,
                                response_data={"available_models": len(available_models)}
                            )
                        else:
                            return SmokeTestResult(
                                test_name="AI Model Availability",
                                status="FAIL",
                                duration=duration,
                                error_message="No AI models available"
                            )
                    else:
                        return SmokeTestResult(
                            test_name="AI Model Availability",
                            status="FAIL",
                            duration=duration,
                            error_message=f"HTTP {response.status}"
                        )
                        
        except Exception as e:
            return SmokeTestResult(
                test_name="AI Model Availability",
                status="FAIL",
                duration=time.time() - start_time,
                error_message=str(e)
            )
    
    async def test_agent_coordination(self) -> SmokeTestResult:
        """Test basic agent coordination"""
        logger.info("👥 Testing agent coordination...")
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test simple agent task
                task_data = {
                    "task_type": "health_check",
                    "priority": "low",
                    "timeout": 30
                }
                
                async with session.post(
                    f"{self.base_url}/api/agents/simple-task",
                    json=task_data,
                    timeout=30
                ) as response:
                    duration = time.time() - start_time
                    
                    if response.status in [200, 202]:  # 202 for async tasks
                        data = await response.json()
                        return SmokeTestResult(
                            test_name="Agent Coordination",
                            status="PASS",
                            duration=duration,
                            response_data=data
                        )
                    else:
                        return SmokeTestResult(
                            test_name="Agent Coordination",
                            status="FAIL",
                            duration=duration,
                            error_message=f"HTTP {response.status}"
                        )
                        
        except Exception as e:
            return SmokeTestResult(
                test_name="Agent Coordination",
                status="FAIL",
                duration=time.time() - start_time,
                error_message=str(e)
            )
    
    async def test_monitoring_metrics(self) -> SmokeTestResult:
        """Test monitoring and metrics endpoints"""
        logger.info("📊 Testing monitoring metrics...")
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test metrics endpoint
                async with session.get(f"{self.base_url}/metrics", timeout=10) as response:
                    duration = time.time() - start_time
                    
                    if response.status == 200:
                        metrics_data = await response.text()
                        
                        # Check for essential metrics
                        essential_metrics = [
                            "revoagent_requests_total",
                            "revoagent_response_time",
                            "revoagent_system_health"
                        ]
                        
                        missing_metrics = [m for m in essential_metrics if m not in metrics_data]
                        
                        if not missing_metrics:
                            return SmokeTestResult(
                                test_name="Monitoring Metrics",
                                status="PASS",
                                duration=duration,
                                response_data={"metrics_count": len(metrics_data.split('\n'))}
                            )
                        else:
                            return SmokeTestResult(
                                test_name="Monitoring Metrics",
                                status="FAIL",
                                duration=duration,
                                error_message=f"Missing metrics: {missing_metrics}"
                            )
                    else:
                        return SmokeTestResult(
                            test_name="Monitoring Metrics",
                            status="FAIL",
                            duration=duration,
                            error_message=f"HTTP {response.status}"
                        )
                        
        except Exception as e:
            return SmokeTestResult(
                test_name="Monitoring Metrics",
                status="FAIL",
                duration=time.time() - start_time,
                error_message=str(e)
            )
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all smoke tests"""
        logger.info("🚀 Starting Staging Smoke Tests...")
        
        start_time = time.time()
        
        # Run all tests
        tests = [
            self.test_health_endpoint(),
            self.test_api_endpoints(),
            self.test_websocket_connection(),
            self.test_database_connectivity(),
            self.test_ai_model_availability(),
            self.test_agent_coordination(),
            self.test_monitoring_metrics()
        ]
        
        self.results = await asyncio.gather(*tests)
        
        # Calculate metrics
        total_duration = time.time() - start_time
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == "PASS"])
        failed_tests = len([r for r in self.results if r.status == "FAIL"])
        skipped_tests = len([r for r in self.results if r.status == "SKIP"])
        
        success_rate = (passed_tests / total_tests) * 100
        overall_status = "PASS" if failed_tests == 0 else "FAIL"
        
        # Generate summary
        summary = {
            "test_suite": "Staging Smoke Tests",
            "environment": "staging",
            "timestamp": datetime.now().isoformat(),
            "duration": total_duration,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "skipped_tests": skipped_tests,
            "success_rate": success_rate,
            "overall_status": overall_status,
            "results": [asdict(result) for result in self.results]
        }
        
        # Save results
        with open("staging_smoke_test_results.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        # Print summary
        print("\n" + "="*80)
        print("🧪 STAGING SMOKE TEST SUMMARY")
        print("="*80)
        print(f"🌐 Environment: staging.revoagent.com")
        print(f"⏱️  Duration: {total_duration:.2f} seconds")
        print(f"🧪 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⏭️  Skipped: {skipped_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print(f"🎉 Overall Status: {overall_status}")
        print("="*80)
        
        for result in self.results:
            status_icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️"}[result.status]
            print(f"{status_icon} {result.test_name} ({result.duration:.2f}s)")
            if result.error_message:
                print(f"   Error: {result.error_message}")
            if result.response_data:
                print(f"   Data: {result.response_data}")
        
        return summary

async def main():
    """Main function to run staging smoke tests"""
    import sys
    
    # Get base URL from command line or use default
    base_url = sys.argv[1] if len(sys.argv) > 1 else "https://staging.revoagent.com"
    
    tester = StagingSmokeTest(base_url)
    
    try:
        results = await tester.run_all_tests()
        
        # Exit with appropriate code
        if results["overall_status"] == "PASS":
            print("🎉 All staging smoke tests passed!")
            exit(0)
        else:
            print("❌ Some staging smoke tests failed!")
            exit(1)
            
    except Exception as e:
        logger.error(f"Staging smoke testing failed: {e}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())