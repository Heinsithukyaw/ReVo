#!/usr/bin/env python3
"""
Enhanced Integration Test Script for reVoAgent LLM Integration
Tests all aspects of the enhanced platform
"""

import asyncio
import aiohttp
import json
import time
import sys
import os
from typing import Dict, Any, List
from datetime import datetime

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

class EnhancedIntegrationTester:
    def __init__(self, base_url: str = "http://localhost:12001"):
        self.base_url = base_url
        self.session = None
        self.test_results = []
        self.start_time = time.time()
    
    def log_info(self, message: str):
        print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")
    
    def log_success(self, message: str):
        print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")
    
    def log_warning(self, message: str):
        print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")
    
    def log_error(self, message: str):
        print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")
    
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        status = f"{Colors.GREEN}✅ PASS{Colors.NC}" if passed else f"{Colors.RED}❌ FAIL{Colors.NC}"
        print(f"{status} {test_name}")
        if details:
            print(f"   {Colors.CYAN}ℹ️  {details}{Colors.NC}")
    
    async def setup(self):
        """Initialize test session"""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        self.log_info("Test session initialized")
    
    async def cleanup(self):
        """Cleanup test session"""
        if self.session:
            await self.session.close()
        self.log_info("Test session cleaned up")
    
    async def test_basic_health(self) -> Dict[str, Any]:
        """Test basic health endpoint"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                data = await response.json()
                passed = response.status == 200 and data.get("status") == "healthy"
                details = f"Status: {data.get('status')}, Uptime: {data.get('uptime', 0):.2f}s"
                
                self.log_test("Basic Health Check", passed, details)
                
                return {
                    "test": "basic_health",
                    "passed": passed,
                    "status_code": response.status,
                    "data": data,
                    "response_time": time.time() - self.start_time
                }
        except Exception as e:
            self.log_test("Basic Health Check", False, f"Error: {str(e)}")
            return {
                "test": "basic_health",
                "passed": False,
                "error": str(e)
            }
    
    async def test_enhanced_health(self) -> Dict[str, Any]:
        """Test enhanced health with LLM status"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                data = await response.json()
                has_llm_status = "llm_status" in data
                llm_data = data.get("llm_status", {})
                
                passed = (response.status == 200 and 
                         has_llm_status and 
                         llm_data.get("status") in ["active", "no_providers"])
                
                details = f"LLM Status: {llm_data.get('status')}, Providers: {llm_data.get('providers', 0)}"
                
                self.log_test("Enhanced Health Check", passed, details)
                
                return {
                    "test": "enhanced_health",
                    "passed": passed,
                    "llm_status": llm_data,
                    "data": data
                }
        except Exception as e:
            self.log_test("Enhanced Health Check", False, f"Error: {str(e)}")
            return {
                "test": "enhanced_health",
                "passed": False,
                "error": str(e)
            }
    
    async def test_models_endpoint(self) -> Dict[str, Any]:
        """Test models endpoint"""
        try:
            async with self.session.get(f"{self.base_url}/api/models") as response:
                data = await response.json()
                has_models = "models" in data and isinstance(data["models"], list)
                model_count = len(data.get("models", []))
                
                passed = response.status == 200 and has_models
                details = f"Found {model_count} models"
                
                if model_count > 0:
                    model_names = [m.get("name", m.get("id", "Unknown")) for m in data["models"]]
                    details += f": {', '.join(model_names[:3])}"
                    if model_count > 3:
                        details += f" (+{model_count - 3} more)"
                
                self.log_test("Models Endpoint", passed, details)
                
                return {
                    "test": "models_endpoint",
                    "passed": passed,
                    "model_count": model_count,
                    "models": data.get("models", [])
                }
        except Exception as e:
            self.log_test("Models Endpoint", False, f"Error: {str(e)}")
            return {
                "test": "models_endpoint",
                "passed": False,
                "error": str(e)
            }
    
    async def test_chat_endpoint(self) -> Dict[str, Any]:
        """Test basic chat endpoint"""
        try:
            chat_request = {
                "message": "Hello, this is a test message. Please respond briefly.",
                "model": "deepseek-r1",
                "temperature": 0.7,
                "max_tokens": 100
            }
            
            start_time = time.time()
            async with self.session.post(
                f"{self.base_url}/api/chat",
                json=chat_request
            ) as response:
                response_time = time.time() - start_time
                data = await response.json()
                
                has_response = "response" in data and len(data["response"]) > 0
                has_metadata = all(key in data for key in ["model", "timestamp", "tokens_used"])
                
                passed = response.status == 200 and has_response and has_metadata
                details = f"Response length: {len(data.get('response', ''))}, Time: {response_time:.2f}s"
                
                self.log_test("Chat Endpoint", passed, details)
                
                return {
                    "test": "chat_endpoint",
                    "passed": passed,
                    "response_time": response_time,
                    "response_length": len(data.get("response", "")),
                    "data": data
                }
        except Exception as e:
            self.log_test("Chat Endpoint", False, f"Error: {str(e)}")
            return {
                "test": "chat_endpoint",
                "passed": False,
                "error": str(e)
            }
    
    async def test_multi_agent_chat(self) -> Dict[str, Any]:
        """Test multi-agent endpoint"""
        try:
            chat_request = {
                "message": "Analyze this simple Python code: print('Hello World')",
                "model": "deepseek-r1",
                "temperature": 0.7,
                "max_tokens": 200
            }
            
            start_time = time.time()
            async with self.session.post(
                f"{self.base_url}/api/chat/multi-agent",
                json=chat_request
            ) as response:
                response_time = time.time() - start_time
                data = await response.json()
                
                has_responses = "responses" in data and isinstance(data["responses"], list)
                response_count = len(data.get("responses", []))
                
                expected_agents = ["code_analyst", "debug_detective", "workflow_manager"]
                agent_names = [r.get("agent") for r in data.get("responses", [])]
                has_expected_agents = all(agent in agent_names for agent in expected_agents)
                
                passed = (response.status == 200 and 
                         has_responses and 
                         response_count >= 3 and 
                         has_expected_agents)
                
                details = f"Agents: {response_count}, Time: {response_time:.2f}s"
                
                self.log_test("Multi-Agent Chat", passed, details)
                
                return {
                    "test": "multi_agent_chat",
                    "passed": passed,
                    "response_time": response_time,
                    "agent_count": response_count,
                    "agents": agent_names,
                    "data": data
                }
        except Exception as e:
            self.log_test("Multi-Agent Chat", False, f"Error: {str(e)}")
            return {
                "test": "multi_agent_chat",
                "passed": False,
                "error": str(e)
            }
    
    async def test_llm_config_endpoint(self) -> Dict[str, Any]:
        """Test LLM configuration endpoint"""
        try:
            async with self.session.get(f"{self.base_url}/api/config/llm") as response:
                data = await response.json()
                
                has_config = all(key in data for key in ["default_model", "available_providers", "status"])
                providers_count = len(data.get("available_providers", []))
                
                passed = response.status == 200 and has_config
                details = f"Default: {data.get('default_model')}, Providers: {providers_count}"
                
                self.log_test("LLM Config Endpoint", passed, details)
                
                return {
                    "test": "llm_config_endpoint",
                    "passed": passed,
                    "config": data
                }
        except Exception as e:
            self.log_test("LLM Config Endpoint", False, f"Error: {str(e)}")
            return {
                "test": "llm_config_endpoint",
                "passed": False,
                "error": str(e)
            }
    
    async def test_websocket_connection(self) -> Dict[str, Any]:
        """Test WebSocket connection"""
        try:
            import websockets
            
            ws_url = self.base_url.replace('http', 'ws') + '/ws/chat'
            
            async with websockets.connect(ws_url) as websocket:
                # Send test message
                test_message = {
                    "message": "WebSocket test message",
                    "model": "deepseek-r1",
                    "temperature": 0.7,
                    "max_tokens": 50
                }
                
                await websocket.send(json.dumps(test_message))
                
                # Wait for response (with timeout)
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(response)
                
                is_valid_response = data.get("type") in ["response", "typing", "error"]
                
                passed = is_valid_response
                details = f"Response type: {data.get('type')}"
                
                self.log_test("WebSocket Connection", passed, details)
                
                return {
                    "test": "websocket_connection",
                    "passed": passed,
                    "response_type": data.get("type"),
                    "data": data
                }
                
        except ImportError:
            self.log_test("WebSocket Connection", False, "websockets library not available")
            return {
                "test": "websocket_connection",
                "passed": False,
                "error": "websockets library not installed"
            }
        except Exception as e:
            self.log_test("WebSocket Connection", False, f"Error: {str(e)}")
            return {
                "test": "websocket_connection",
                "passed": False,
                "error": str(e)
            }
    
    async def test_cors_headers(self) -> Dict[str, Any]:
        """Test CORS headers"""
        try:
            async with self.session.options(f"{self.base_url}/api/chat") as response:
                cors_headers = {
                    "access-control-allow-origin": response.headers.get("access-control-allow-origin"),
                    "access-control-allow-methods": response.headers.get("access-control-allow-methods"),
                    "access-control-allow-headers": response.headers.get("access-control-allow-headers"),
                }
                
                has_cors = any(cors_headers.values())
                passed = response.status in [200, 204] and has_cors
                
                details = f"Origin: {cors_headers['access-control-allow-origin'] or 'Not set'}"
                
                self.log_test("CORS Headers", passed, details)
                
                return {
                    "test": "cors_headers",
                    "passed": passed,
                    "cors_headers": cors_headers
                }
        except Exception as e:
            self.log_test("CORS Headers", False, f"Error: {str(e)}")
            return {
                "test": "cors_headers",
                "passed": False,
                "error": str(e)
            }
    
    async def run_all_tests(self):
        """Run all integration tests"""
        print(f"{Colors.PURPLE}🧪 Running Enhanced LLM Integration Tests{Colors.NC}")
        print("=" * 60)
        
        await self.setup()
        
        # Define test suite
        tests = [
            ("Basic Health Check", self.test_basic_health),
            ("Enhanced Health Check", self.test_enhanced_health),
            ("Models Endpoint", self.test_models_endpoint),
            ("Chat Endpoint", self.test_chat_endpoint),
            ("Multi-Agent Chat", self.test_multi_agent_chat),
            ("LLM Config Endpoint", self.test_llm_config_endpoint),
            ("WebSocket Connection", self.test_websocket_connection),
            ("CORS Headers", self.test_cors_headers),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            try:
                self.log_info(f"Running {test_name}...")
                result = await test_func()
                results.append(result)
            except Exception as e:
                self.log_error(f"Test {test_name} failed with exception: {e}")
                results.append({
                    "test": test_name.lower().replace(" ", "_"),
                    "passed": False,
                    "error": str(e)
                })
        
        await self.cleanup()
        
        # Generate summary
        passed_tests = [r for r in results if r.get("passed", False)]
        failed_tests = [r for r in results if not r.get("passed", False)]
        
        total_time = time.time() - self.start_time
        
        print("\n" + "=" * 60)
        print(f"{Colors.PURPLE}📊 Test Summary{Colors.NC}")
        print(f"Total Tests: {len(results)}")
        print(f"{Colors.GREEN}Passed: {len(passed_tests)}{Colors.NC}")
        print(f"{Colors.RED}Failed: {len(failed_tests)}{Colors.NC}")
        print(f"Total Time: {total_time:.2f}s")
        
        if len(passed_tests) == len(results):
            print(f"\n{Colors.GREEN}🎉 All tests passed! Enhanced LLM integration is working correctly.{Colors.NC}")
        else:
            print(f"\n{Colors.YELLOW}⚠️ {len(failed_tests)} test(s) failed. Check the issues above.{Colors.NC}")
            
            if failed_tests:
                print(f"\n{Colors.RED}Failed Tests:{Colors.NC}")
                for test in failed_tests:
                    print(f"  - {test.get('test', 'Unknown')}: {test.get('error', 'Unknown error')}")
        
        # Save detailed results
        detailed_results = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": len(results),
                "passed": len(passed_tests),
                "failed": len(failed_tests),
                "duration": total_time
            },
            "tests": results
        }
        
        with open("enhanced_integration_test_results.json", "w") as f:
            json.dump(detailed_results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: enhanced_integration_test_results.json")
        
        # System recommendations
        if failed_tests:
            print(f"\n{Colors.CYAN}💡 Troubleshooting Tips:{Colors.NC}")
            print("1. Ensure the enhanced backend is running: python3 enhanced_backend_main.py")
            print("2. Check API keys in .env file")
            print("3. Verify port 12001 is not blocked")
            print("4. Check logs: tail -f logs/revoagent.log")
            print("5. Test manually: curl http://localhost:12001/health")
        
        return results

async def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced reVoAgent Integration Tests")
    parser.add_argument("--url", default="http://localhost:12001", 
                       help="Backend URL (default: http://localhost:12001)")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        print(f"Testing against: {args.url}")
        print(f"Current time: {datetime.now().isoformat()}")
        print(f"Python version: {sys.version}")
    
    tester = EnhancedIntegrationTester(args.url)
    results = await tester.run_all_tests()
    
    # Exit with appropriate code
    failed_count = len([r for r in results if not r.get("passed", False)])
    sys.exit(failed_count)

if __name__ == "__main__":
    asyncio.run(main())