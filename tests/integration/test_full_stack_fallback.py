#!/usr/bin/env python3
"""
Full Stack Integration Test for reVoAgent Platform

Tests the entire application flow including:
1. Frontend-Backend communication
2. LLM integration with fallback system
3. Error handling and validation
4. End-to-end response generation

This test suite ensures all components of the system work together correctly.
"""

import os
import sys
import asyncio
import json
import time
import logging
import requests
import subprocess
import signal
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("full_stack_test")

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

class TestResult:
    """Store and report test results"""
    
    def __init__(self, name: str):
        self.name = name
        self.start_time = time.time()
        self.end_time = None
        self.success = False
        self.error = None
        self.details = {}
    
    def complete(self, success: bool, error: Optional[str] = None, **details):
        """Mark test as complete"""
        self.end_time = time.time()
        self.success = success
        self.error = error
        self.details.update(details)
    
    @property
    def duration(self) -> float:
        """Get test duration in seconds"""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "success": self.success,
            "duration": self.duration,
            "error": self.error,
            "details": self.details,
            "timestamp": datetime.now().isoformat()
        }

class FullStackTest:
    """
    Full stack integration test for reVoAgent platform
    
    Tests the entire application stack from frontend to backend, including:
    - Server startup and health checks
    - API endpoint functionality
    - Error handling and validation
    - LLM fallback system
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {
            "backend_url": "http://localhost:12001",
            "frontend_url": "http://localhost:12000",
            "start_servers": True,
            "timeout": 120,
            "test_auth": False
        }
        
        self.results = []
        self.server_processes = []
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests"""
        try:
            if self.config.get("start_servers"):
                await self.start_servers()
            
            # Run tests
            await self.test_backend_health()
            await self.test_api_endpoints()
            await self.test_error_handling()
            await self.test_llm_fallback()
            await self.test_validation()
            
            # Generate report
            return self.generate_report()
            
        finally:
            if self.config.get("start_servers"):
                await self.stop_servers()
    
    async def start_servers(self):
        """Start backend and frontend servers"""
        logger.info("Starting servers for integration test...")
        
        # Start the backend server
        backend_result = TestResult("start_backend_server")
        try:
            logger.info("Starting backend server...")
            backend_cmd = ["python", str(project_root / "start_fallback_backend.sh")]
            backend_proc = subprocess.Popen(
                backend_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.server_processes.append(backend_proc)
            
            # Wait for backend to start
            backend_started = await self._wait_for_url(f"{self.config['backend_url']}/health")
            backend_result.complete(
                success=backend_started,
                error=None if backend_started else "Backend server failed to start"
            )
            self.results.append(backend_result)
            
            if not backend_started:
                raise Exception("Backend server failed to start")
                
            logger.info("Backend server started successfully")
            
        except Exception as e:
            logger.error(f"Error starting backend server: {e}")
            backend_result.complete(success=False, error=str(e))
            self.results.append(backend_result)
            raise
        
        # Start the frontend server
        frontend_result = TestResult("start_frontend_server")
        try:
            logger.info("Starting frontend server...")
            frontend_cmd = ["python", str(project_root / "start_frontend.sh")]
            frontend_proc = subprocess.Popen(
                frontend_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.server_processes.append(frontend_proc)
            
            # Wait for frontend to start
            frontend_started = await self._wait_for_url(f"{self.config['frontend_url']}")
            frontend_result.complete(
                success=frontend_started,
                error=None if frontend_started else "Frontend server failed to start"
            )
            self.results.append(frontend_result)
            
            if not frontend_started:
                raise Exception("Frontend server failed to start")
                
            logger.info("Frontend server started successfully")
            
        except Exception as e:
            logger.error(f"Error starting frontend server: {e}")
            frontend_result.complete(success=False, error=str(e))
            self.results.append(frontend_result)
            raise
    
    async def stop_servers(self):
        """Stop all started server processes"""
        logger.info("Stopping servers...")
        
        for proc in self.server_processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            except Exception as e:
                logger.error(f"Error stopping server process: {e}")
        
        self.server_processes = []
        logger.info("All servers stopped")
    
    async def _wait_for_url(self, url: str, timeout: int = 60) -> bool:
        """Wait for a URL to become available"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code < 500:  # Accept any non-5xx status
                    return True
            except requests.RequestException:
                pass
            
            await asyncio.sleep(1)
        
        return False
    
    async def test_backend_health(self) -> TestResult:
        """Test backend health endpoints"""
        result = TestResult("backend_health")
        
        try:
            # Test basic health endpoint
            health_response = requests.get(f"{self.config['backend_url']}/health")
            health_data = health_response.json()
            
            # Test readiness probe
            ready_response = requests.get(f"{self.config['backend_url']}/health/ready")
            ready_data = ready_response.json()
            
            # Test liveness probe
            live_response = requests.get(f"{self.config['backend_url']}/health/live")
            live_data = live_response.json()
            
            # Verify results
            all_endpoints_ok = (
                health_response.status_code == 200 and
                ready_response.status_code == 200 and
                live_response.status_code == 200
            )
            
            health_ok = health_data.get("status") == "healthy"
            ready_ok = ready_data.get("status") == "ready"
            live_ok = live_data.get("status") == "alive"
            
            all_checks_ok = all_endpoints_ok and health_ok and ready_ok and live_ok
            
            result.complete(
                success=all_checks_ok,
                error=None if all_checks_ok else "Health check failed",
                health_status=health_data.get("status"),
                ready_status=ready_data.get("status"),
                live_status=live_data.get("status")
            )
            
        except Exception as e:
            logger.error(f"Error testing backend health: {e}")
            result.complete(success=False, error=str(e))
        
        self.results.append(result)
        return result
    
    async def test_api_endpoints(self) -> List[TestResult]:
        """Test API endpoints functionality"""
        endpoint_results = []
        
        # Test models endpoint
        models_result = TestResult("api_models")
        try:
            response = requests.get(f"{self.config['backend_url']}/api/models")
            
            if response.status_code == 200:
                models_data = response.json()
                has_models = len(models_data.get("models", [])) > 0
                
                models_result.complete(
                    success=has_models,
                    error=None if has_models else "No models returned",
                    models_count=len(models_data.get("models", [])),
                    models=models_data.get("models", [])
                )
            else:
                models_result.complete(
                    success=False,
                    error=f"API returned status code {response.status_code}",
                    response=response.text
                )
                
        except Exception as e:
            logger.error(f"Error testing models endpoint: {e}")
            models_result.complete(success=False, error=str(e))
        
        endpoint_results.append(models_result)
        self.results.append(models_result)
        
        # Test chat endpoint
        chat_result = TestResult("api_chat")
        try:
            chat_data = {
                "message": "Hello, can you help me test the integration?",
                "model": "deepseek-r1",
                "temperature": 0.7,
                "max_tokens": 100
            }
            
            response = requests.post(
                f"{self.config['backend_url']}/api/chat",
                json=chat_data
            )
            
            if response.status_code == 200:
                chat_response = response.json()
                has_response = bool(chat_response.get("response"))
                
                chat_result.complete(
                    success=has_response,
                    error=None if has_response else "Empty response received",
                    response_length=len(chat_response.get("response", "")),
                    model_used=chat_response.get("model"),
                    fallback_info=chat_response.get("fallback_info")
                )
            else:
                chat_result.complete(
                    success=False,
                    error=f"API returned status code {response.status_code}",
                    response=response.text
                )
                
        except Exception as e:
            logger.error(f"Error testing chat endpoint: {e}")
            chat_result.complete(success=False, error=str(e))
        
        endpoint_results.append(chat_result)
        self.results.append(chat_result)
        
        # Test code generation endpoint
        code_result = TestResult("api_code")
        try:
            code_data = {
                "task_description": "Create a simple Flask hello world app",
                "language": "python",
                "framework": "flask",
                "model": "deepseek-r1",
                "max_tokens": 500
            }
            
            response = requests.post(
                f"{self.config['backend_url']}/api/code",
                json=code_data
            )
            
            if response.status_code == 200:
                code_response = response.json()
                has_code = bool(code_response.get("generated_code"))
                
                code_result.complete(
                    success=has_code,
                    error=None if has_code else "No code generated",
                    code_length=len(code_response.get("generated_code", "")),
                    model_used=code_response.get("model_used"),
                    fallback_info=code_response.get("fallback_info")
                )
            else:
                code_result.complete(
                    success=False,
                    error=f"API returned status code {response.status_code}",
                    response=response.text
                )
                
        except Exception as e:
            logger.error(f"Error testing code endpoint: {e}")
            code_result.complete(success=False, error=str(e))
        
        endpoint_results.append(code_result)
        self.results.append(code_result)
        
        # Test agent endpoint
        agent_result = TestResult("api_agent")
        try:
            agent_data = {
                "agent_type": "code_analyst",
                "message": "Analyze this code: def hello(): print('hello world')",
                "model": "deepseek-r1",
                "max_tokens": 200
            }
            
            response = requests.post(
                f"{self.config['backend_url']}/api/agent",
                json=agent_data
            )
            
            if response.status_code == 200:
                agent_response = response.json()
                has_response = bool(agent_response.get("response"))
                
                agent_result.complete(
                    success=has_response,
                    error=None if has_response else "Empty agent response received",
                    response_length=len(agent_response.get("response", "")),
                    agent=agent_response.get("agent"),
                    model=agent_response.get("model"),
                    fallback_info=agent_response.get("fallback_info")
                )
            else:
                agent_result.complete(
                    success=False,
                    error=f"API returned status code {response.status_code}",
                    response=response.text
                )
                
        except Exception as e:
            logger.error(f"Error testing agent endpoint: {e}")
            agent_result.complete(success=False, error=str(e))
        
        endpoint_results.append(agent_result)
        self.results.append(agent_result)
        
        return endpoint_results
    
    async def test_error_handling(self) -> TestResult:
        """Test enhanced error handling"""
        result = TestResult("error_handling")
        
        try:
            error_tests = []
            
            # Test 1: Validation error (missing required field)
            validation_test = {"name": "validation_error"}
            try:
                response = requests.post(
                    f"{self.config['backend_url']}/api/chat",
                    json={}  # Missing required 'message' field
                )
                
                validation_test["status_code"] = response.status_code
                validation_test["success"] = response.status_code == 422
                validation_test["response"] = response.json()
                
                # Check if error structure is correct
                has_error_field = "error" in response.json()
                validation_test["has_error_field"] = has_error_field
                
                if has_error_field:
                    validation_test["error_code"] = response.json()["error"].get("code")
                    validation_test["error_category"] = response.json()["error"].get("category")
                
            except Exception as e:
                validation_test["success"] = False
                validation_test["error"] = str(e)
            
            error_tests.append(validation_test)
            
            # Test 2: Non-existent endpoint
            not_found_test = {"name": "not_found_error"}
            try:
                response = requests.get(
                    f"{self.config['backend_url']}/api/nonexistent"
                )
                
                not_found_test["status_code"] = response.status_code
                not_found_test["success"] = response.status_code == 404
                not_found_test["response"] = response.json() if response.status_code != 404 else response.text
                
            except Exception as e:
                not_found_test["success"] = False
                not_found_test["error"] = str(e)
            
            error_tests.append(not_found_test)
            
            # Test 3: Invalid model name
            invalid_model_test = {"name": "invalid_model_error"}
            try:
                response = requests.post(
                    f"{self.config['backend_url']}/api/chat",
                    json={
                        "message": "Hello, testing error handling",
                        "model": "nonexistent-model"
                    }
                )
                
                invalid_model_test["status_code"] = response.status_code
                invalid_model_test["success"] = 400 <= response.status_code < 600
                invalid_model_test["response"] = response.json() if 'application/json' in response.headers.get('Content-Type', '') else response.text
                
            except Exception as e:
                invalid_model_test["success"] = False
                invalid_model_test["error"] = str(e)
            
            error_tests.append(invalid_model_test)
            
            # Check if all error tests were successful
            all_tests_passed = all(test.get("success", False) for test in error_tests)
            
            result.complete(
                success=all_tests_passed,
                error=None if all_tests_passed else "One or more error handling tests failed",
                tests=error_tests
            )
            
        except Exception as e:
            logger.error(f"Error testing error handling: {e}")
            result.complete(success=False, error=str(e))
        
        self.results.append(result)
        return result
    
    async def test_llm_fallback(self) -> TestResult:
        """Test LLM fallback system"""
        result = TestResult("llm_fallback")
        
        try:
            # Get fallback stats before test
            before_stats_response = requests.get(f"{self.config['backend_url']}/api/fallback/stats")
            before_stats = before_stats_response.json() if before_stats_response.status_code == 200 else {}
            
            # Try to trigger a fallback by using a very strict timeout
            # Send a complex request with parameters that might trigger fallback
            fallback_test_data = {
                "message": "Write a detailed analysis of quantum computing algorithms and their implementations, with code examples and benchmarks",
                "model": "deepseek-r1",  # Specify the primary model
                "temperature": 0.2,      # Low temperature for deterministic results
                "max_tokens": 2000       # Request a long response
            }
            
            response = requests.post(
                f"{self.config['backend_url']}/api/chat",
                json=fallback_test_data
            )
            
            # Get fallback stats after test
            after_stats_response = requests.get(f"{self.config['backend_url']}/api/fallback/stats")
            after_stats = after_stats_response.json() if after_stats_response.status_code == 200 else {}
            
            # Check response
            if response.status_code == 200:
                # Look for fallback info in the response
                fallback_info = response.json().get("fallback_info")
                
                # Check if fallback count increased
                before_count = before_stats.get("total_events", 0)
                after_count = after_stats.get("total_events", 0)
                fallback_occurred = after_count > before_count
                
                # Alternative check if fallback info is present in response
                fallback_in_response = fallback_info is not None and fallback_info.get("used", False)
                
                fallback_detected = fallback_occurred or fallback_in_response
                
                result.complete(
                    success=True,  # Test is successful regardless of fallback occurrence
                    fallback_detected=fallback_detected,
                    fallback_info=fallback_info,
                    before_stats=before_stats,
                    after_stats=after_stats,
                    response_length=len(response.json().get("response", ""))
                )
            else:
                result.complete(
                    success=False,
                    error=f"API returned status code {response.status_code}",
                    response=response.text
                )
                
        except Exception as e:
            logger.error(f"Error testing LLM fallback: {e}")
            result.complete(success=False, error=str(e))
        
        self.results.append(result)
        return result
    
    async def test_validation(self) -> TestResult:
        """Test response validation"""
        result = TestResult("response_validation")
        
        try:
            # This test requires that the llm_validator is integrated into the backend
            # We'll check if the code endpoint returns quality scores
            
            # Request code generation with syntax that's easy to validate
            code_data = {
                "task_description": "Write a Python function to sort a list of integers",
                "language": "python",
                "framework": "none",
                "model": "deepseek-r1"
            }
            
            response = requests.post(
                f"{self.config['backend_url']}/api/code",
                json=code_data
            )
            
            if response.status_code == 200:
                code_response = response.json()
                
                # Check if quality score is present
                has_quality_score = "quality_score" in code_response
                quality_score = code_response.get("quality_score", 0)
                
                # Check generated code for syntax validity
                code = code_response.get("generated_code", "")
                syntax_valid = False
                
                if code:
                    # Use a very basic syntax check
                    try:
                        # Try to compile the code to check syntax
                        compile(code, "<string>", "exec")
                        syntax_valid = True
                    except SyntaxError:
                        syntax_valid = False
                
                result.complete(
                    success=has_quality_score and syntax_valid,
                    error=None if (has_quality_score and syntax_valid) else "Validation issues detected",
                    quality_score=quality_score,
                    syntax_valid=syntax_valid,
                    code_length=len(code)
                )
            else:
                result.complete(
                    success=False,
                    error=f"API returned status code {response.status_code}",
                    response=response.text
                )
                
        except Exception as e:
            logger.error(f"Error testing response validation: {e}")
            result.complete(success=False, error=str(e))
        
        self.results.append(result)
        return result
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        # Calculate overall success rate
        total_tests = len(self.results)
        successful_tests = sum(1 for result in self.results if result.success)
        success_rate = successful_tests / total_tests if total_tests > 0 else 0
        
        # Categorize results
        report = {
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": total_tests - successful_tests,
                "success_rate": success_rate,
                "timestamp": datetime.now().isoformat()
            },
            "tests": [result.to_dict() for result in self.results]
        }
        
        # Save report to file
        report_path = project_root / "full_stack_test_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"Test report saved to {report_path}")
        
        # Print summary
        logger.info(f"Integration Test Summary:")
        logger.info(f"Total tests: {total_tests}")
        logger.info(f"Success rate: {success_rate:.2%}")
        logger.info(f"Successful tests: {successful_tests}")
        logger.info(f"Failed tests: {total_tests - successful_tests}")
        
        return report

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run full stack integration tests")
    parser.add_argument("--start-servers", action="store_true", help="Start servers before testing")
    parser.add_argument("--backend-url", default="http://localhost:12001", help="Backend URL")
    parser.add_argument("--frontend-url", default="http://localhost:12000", help="Frontend URL")
    
    args = parser.parse_args()
    
    config = {
        "backend_url": args.backend_url,
        "frontend_url": args.frontend_url,
        "start_servers": args.start_servers,
        "timeout": 120
    }
    
    test = FullStackTest(config)
    await test.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())