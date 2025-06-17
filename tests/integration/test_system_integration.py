#!/usr/bin/env python3
"""
Comprehensive System Integration Test

Tests all major components before Phase 5:
- Backend API and routing
- Frontend build and connectivity
- Three-Engine Architecture
- Agent Framework
- MCP Integration
- Configuration System
"""

import asyncio
import pytest
import sys
import pytest
import subprocess
import pytest
import time
import pytest
import requests
import pytest
import json
import pytest
from pathlib import Path
from typing import Dict, Any, List

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class SystemIntegrationTester:
    """Comprehensive system integration tester"""
    
    def __init__(self):
        self.test_results = {}
        self.backend_process = None
        self.frontend_process = None
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all system integration tests"""
        
        print("🧪 COMPREHENSIVE SYSTEM INTEGRATION TEST")
        print("="*60)
        print("Testing all components before Phase 5 implementation")
        print()
        
        # Test 1: Backend API and Routing
        print("🔧 Testing Backend API and Routing...")
        backend_result = await self.test_backend_api()
        self.test_results["backend_api"] = backend_result
        
        # Test 2: Package Structure and Imports
        print("\n📦 Testing Package Structure and Imports...")
        package_result = await self.test_package_imports()
        self.test_results["package_imports"] = package_result
        
        # Test 3: Three-Engine Architecture
        print("\n🧠 Testing Three-Engine Architecture...")
        engine_result = await self.test_three_engines()
        self.test_results["three_engines"] = engine_result
        
        # Test 4: Agent Framework
        print("\n🤖 Testing Agent Framework...")
        agent_result = await self.test_agent_framework()
        self.test_results["agent_framework"] = agent_result
        
        # Test 5: MCP Integration
        print("\n🌐 Testing MCP Integration...")
        mcp_result = await self.test_mcp_integration()
        self.test_results["mcp_integration"] = mcp_result
        
        # Test 6: Configuration System
        print("\n⚙️ Testing Configuration System...")
        config_result = await self.test_configuration_system()
        self.test_results["configuration"] = config_result
        
        # Test 7: Frontend Build
        print("\n🎨 Testing Frontend Build...")
        frontend_result = await self.test_frontend_build()
        self.test_results["frontend_build"] = frontend_result
        
        # Generate summary
        await self.generate_test_summary()
        
        return self.test_results
    
    async def test_backend_api(self) -> Dict[str, Any]:
        """Test backend API functionality"""
        try:
            # Start backend server
            print("   🚀 Starting backend server...")
            self.backend_process = subprocess.Popen([
                sys.executable, "apps/backend/main.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for server to start
            time.sleep(3)
            
            # Test health endpoint
            print("   🔍 Testing health endpoint...")
            health_response = requests.get("http://localhost:8000/health", timeout=5)
            health_data = health_response.json()
            
            # Test API status endpoint
            print("   🔍 Testing API status endpoint...")
            status_response = requests.get("http://localhost:8000/api/status", timeout=5)
            status_data = status_response.json()
            
            # Test root endpoint
            print("   🔍 Testing root endpoint...")
            root_response = requests.get("http://localhost:8000/", timeout=5)
            root_data = root_response.json()
            
            success = (
                health_response.status_code == 200 and
                status_response.status_code == 200 and
                root_response.status_code == 200 and
                health_data.get("status") == "healthy" and
                status_data.get("status") == "operational"
            )
            
            return {
                "success": success,
                "health_check": health_data,
                "api_status": status_data,
                "root_response": root_data,
                "message": "Backend API working correctly" if success else "Backend API issues detected"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Backend API test failed"
            }
        finally:
            # Clean up backend process
            if self.backend_process:
                self.backend_process.terminate()
                self.backend_process.wait()
    
    async def test_package_imports(self) -> Dict[str, Any]:
        """Test package structure and imports"""
        try:
            import_results = {}
            
            # Test core package
            print("   📦 Testing core package...")
            try:
                from core.config import ConfigLoader
                from core.framework import CoreFramework
                import_results["core"] = "success"
            except Exception as e:
                import_results["core"] = f"error: {e}"
            
            # Test engines package
            print("   🧠 Testing engines package...")
            try:
                from engines.perfect_recall_engine import PerfectRecallEngine
                from engines.parallel_mind_engine import ParallelMindEngine
                from engines.creative_engine import CreativeEngine
                from engines.engine_coordinator import EngineCoordinator
                import_results["engines"] = "success"
            except Exception as e:
                import_results["engines"] = f"error: {e}"
            
            # Test agents package
            print("   🤖 Testing agents package...")
            try:
                from agents.base_intelligent_agent import BaseIntelligentAgent
                from agents.code_generator import CodeGenerationAgent
                import_results["agents"] = "success"
            except Exception as e:
                import_results["agents"] = f"error: {e}"
            
            # Test AI package
            print("   🤖 Testing AI package...")
            try:
                from packages.ai.model_loader import ModelLoader
                from packages.ai.deepseek_integration import DeepSeekIntegration
                import_results["ai"] = "success"
            except Exception as e:
                import_results["ai"] = f"error: {e}"
            
            # Test MCP integration
            print("   🌐 Testing MCP package...")
            try:
                from integrations.mcp import MCPClient, MCPServerRegistry
                import_results["mcp"] = "success"
            except Exception as e:
                import_results["mcp"] = f"error: {e}"
            
            success = all(result == "success" for result in import_results.values())
            
            return {
                "success": success,
                "import_results": import_results,
                "message": "All packages imported successfully" if success else "Some package imports failed"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Package import test failed"
            }
    
    async def test_three_engines(self) -> Dict[str, Any]:
        """Test Three-Engine Architecture"""
        try:
            from engines.engine_coordinator import EngineCoordinator
            from engines.perfect_recall_engine import PerfectRecallEngine
            from engines.parallel_mind_engine import ParallelMindEngine
            from engines.creative_engine import CreativeEngine
            
            print("   🔵 Testing Perfect Recall Engine...")
            perfect_recall = PerfectRecallEngine()
            await perfect_recall.initialize()
            
            print("   🟣 Testing Parallel Mind Engine...")
            parallel_mind = ParallelMindEngine()
            await parallel_mind.initialize()
            
            print("   🩷 Testing Creative Engine...")
            creative = CreativeEngine()
            await creative.initialize()
            
            print("   🎛️ Testing Engine Coordinator...")
            coordinator = EngineCoordinator()
            await coordinator.initialize()
            
            # Test basic functionality
            test_query = "Test query for engine integration"
            
            # Test Perfect Recall
            recall_result = await perfect_recall.process_query(test_query)
            
            # Test Parallel Mind
            parallel_result = await parallel_mind.process_query(test_query)
            
            # Test Creative Engine
            creative_result = await creative.process_query(test_query)
            
            # Test Coordinator
            coordinator_result = await coordinator.process_query(test_query)
            
            return {
                "success": True,
                "engines": {
                    "perfect_recall": "operational",
                    "parallel_mind": "operational", 
                    "creative": "operational",
                    "coordinator": "operational"
                },
                "test_results": {
                    "recall_result": str(recall_result)[:100],
                    "parallel_result": str(parallel_result)[:100],
                    "creative_result": str(creative_result)[:100],
                    "coordinator_result": str(coordinator_result)[:100]
                },
                "message": "Three-Engine Architecture working correctly"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Three-Engine Architecture test failed"
            }
    
    async def test_agent_framework(self) -> Dict[str, Any]:
        """Test Agent Framework"""
        try:
            from agents.base_intelligent_agent import BaseIntelligentAgent
            from agents.code_generator import CodeGenerationAgent
            from agents.browser_agent import BrowserAgent
            
            print("   🏗️ Testing Base Agent...")
            base_agent = BaseIntelligentAgent({
                "name": "test_agent",
                "type": "test",
                "tenant_id": "test_tenant"
            })
            await base_agent.initialize()
            
            print("   💻 Testing Code Generation Agent...")
            code_agent = CodeGenerationAgent({
                "name": "code_test",
                "tenant_id": "test_tenant"
            })
            await code_agent.initialize()
            
            print("   🌐 Testing Browser Agent...")
            browser_agent = BrowserAgent({
                "name": "browser_test",
                "tenant_id": "test_tenant"
            })
            await browser_agent.initialize()
            
            # Test basic agent functionality
            test_task = "Generate a simple Python function"
            code_result = await code_agent.process_task(test_task)
            
            return {
                "success": True,
                "agents": {
                    "base_agent": "operational",
                    "code_agent": "operational",
                    "browser_agent": "operational"
                },
                "test_result": str(code_result)[:200],
                "message": "Agent Framework working correctly"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Agent Framework test failed"
            }
    
    async def test_mcp_integration(self) -> Dict[str, Any]:
        """Test MCP Integration"""
        try:
            from integrations.mcp import MCPClient, MCPServerRegistry
            from integrations.mcp.client import MCPServerConfig, MCPTransportType
            
            print("   🌐 Testing MCP Client...")
            client = MCPClient(tenant_id="test_tenant")
            
            print("   📋 Testing MCP Registry...")
            from integrations.mcp.registry import mcp_registry
            
            # Test server discovery
            servers = await mcp_registry.discover_servers()
            
            # Test security manager
            print("   🔒 Testing MCP Security...")
            from integrations.mcp.security import MCPSecurityManager
            security = MCPSecurityManager("test_tenant")
            summary = await security.get_security_summary()
            
            return {
                "success": True,
                "mcp_components": {
                    "client": "operational",
                    "registry": "operational",
                    "security": "operational"
                },
                "discovered_servers": len(servers),
                "security_summary": summary,
                "message": "MCP Integration working correctly"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "MCP Integration test failed"
            }
    
    async def test_configuration_system(self) -> Dict[str, Any]:
        """Test Configuration System"""
        try:
            from core.config import ConfigLoader
            
            print("   ⚙️ Testing Configuration Loader...")
            config_loader = ConfigLoader()
            
            # Test environment config
            env_config = config_loader.load_environment_config()
            
            # Test agent config
            agent_config = config_loader.load_agent_config()
            
            # Test engine config
            engine_config = config_loader.load_engine_config()
            
            return {
                "success": True,
                "configurations": {
                    "environment": "loaded",
                    "agents": "loaded",
                    "engines": "loaded"
                },
                "config_details": {
                    "environment": env_config.get("environment", "unknown"),
                    "agent_count": len(agent_config.get("agents", [])),
                    "engine_count": len(engine_config.get("engines", []))
                },
                "message": "Configuration System working correctly"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Configuration System test failed"
            }
    
    async def test_frontend_build(self) -> Dict[str, Any]:
        """Test Frontend Build"""
        try:
            print("   🎨 Testing frontend build process...")
            
            # Change to frontend directory and run build
            result = subprocess.run([
                "npm", "run", "build"
            ], cwd="frontend", capture_output=True, text=True, timeout=60)
            
            build_success = result.returncode == 0
            
            # Check if dist directory was created
            dist_exists = Path("frontend/dist").exists()
            
            return {
                "success": build_success and dist_exists,
                "build_output": result.stdout[-500:] if result.stdout else "",
                "build_errors": result.stderr[-500:] if result.stderr else "",
                "dist_created": dist_exists,
                "message": "Frontend build successful" if build_success else "Frontend build failed"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Frontend build test failed"
            }
    
    async def generate_test_summary(self):
        """Generate comprehensive test summary"""
        
        print("\n" + "="*60)
        print("📊 SYSTEM INTEGRATION TEST SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result.get("success", False))
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Detailed results
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
            message = result.get("message", "No message")
            print(f"{status} {test_name.replace('_', ' ').title()}: {message}")
            
            if not result.get("success", False) and "error" in result:
                print(f"      Error: {result['error']}")
        
        print()
        
        # Phase 5 readiness assessment
        critical_tests = ["backend_api", "package_imports", "three_engines"]
        critical_passed = sum(1 for test in critical_tests if self.test_results.get(test, {}).get("success", False))
        
        if critical_passed == len(critical_tests):
            print("🚀 PHASE 5 READINESS: ✅ READY")
            print("   All critical systems operational. Ready to begin Phase 5 implementation.")
        else:
            print("⚠️ PHASE 5 READINESS: ❌ NOT READY")
            print("   Critical systems need attention before Phase 5.")
        
        print("="*60)

async def main():
    """Main test execution"""
    tester = SystemIntegrationTester()
    
    print("🌟 reVoAgent System Integration Test")
    print("   Comprehensive testing before Phase 5 implementation")
    print()
    
    try:
        results = await tester.run_all_tests()
        
        # Save results to file
        with open("system_integration_test_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📄 Test results saved to: system_integration_test_results.json")
        
        # Return appropriate exit code
        all_passed = all(result.get("success", False) for result in results.values())
        return 0 if all_passed else 1
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))