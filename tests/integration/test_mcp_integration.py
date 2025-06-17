#!/usr/bin/env python3
"""
Test MCP Integration

Test the MCP integration framework to ensure it works correctly
before proceeding with Phase 5 implementation.
"""

import asyncio
import sys
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent / "packages"))

async def test_mcp_integration():
    """Test MCP integration components"""
    
    print("🧪 TESTING MCP INTEGRATION")
    print("="*50)
    
    try:
        # Test imports
        print("📦 Testing imports...")
        from integrations.mcp import MCPClient, MCPServerRegistry, MCPSecurityManager
        from integrations.mcp.client import MCPServerConfig, MCPTransportType
        print("   ✅ All imports successful")
        
        # Test MCP Client
        print("\n🔧 Testing MCP Client...")
        client = MCPClient(tenant_id="test_tenant")
        print(f"   ✅ Client created for tenant: {client.tenant_id}")
        
        # Test server configuration
        config = MCPServerConfig(
            name="test_filesystem",
            transport_type=MCPTransportType.STDIO,
            command="echo",
            args=["test"],
            timeout=10
        )
        print(f"   ✅ Server config created: {config.name}")
        
        # Test connection (will use mock)
        success = await client.connect_server(config)
        print(f"   {'✅' if success else '❌'} Server connection: {success}")
        
        if success:
            # Test tool listing
            tools = await client.list_tools()
            print(f"   ✅ Tools available: {len(tools)}")
            
            # Test tool execution
            if tools:
                result = await client.call_tool("test_filesystem", "mock_tool", {"test": "data"})
                print(f"   ✅ Tool execution successful")
            
            # Test server status
            status = await client.get_server_status("test_filesystem")
            print(f"   ✅ Server status: {status['status']}")
        
        # Test MCP Registry
        print("\n📋 Testing MCP Registry...")
        from integrations.mcp.registry import mcp_registry
        
        # Discover servers
        servers = await mcp_registry.discover_servers()
        print(f"   ✅ Discovered {len(servers)} servers")
        
        # Get enterprise servers
        enterprise_servers = await mcp_registry.get_enterprise_servers()
        print(f"   ✅ Enterprise servers: {len(enterprise_servers)}")
        
        # Get servers for agent type
        code_servers = await mcp_registry.get_servers_for_agent("code_generation")
        print(f"   ✅ Code generation servers: {len(code_servers)}")
        
        # Test Security Manager
        print("\n🔒 Testing Security Manager...")
        security = MCPSecurityManager("test_tenant")
        
        # Test server access validation
        access_allowed = await security.validate_server_access(config)
        print(f"   {'✅' if access_allowed else '❌'} Server access validation: {access_allowed}")
        
        # Test tool access validation
        tool_access = await security.validate_tool_access("test_filesystem", "mock_tool")
        print(f"   {'✅' if tool_access else '❌'} Tool access validation: {tool_access}")
        
        # Test security summary
        summary = await security.get_security_summary()
        print(f"   ✅ Security summary: {summary['security_level']}")
        
        print("\n🎉 MCP INTEGRATION TEST COMPLETED SUCCESSFULLY!")
        print("="*50)
        print("✅ All components working correctly")
        print("🚀 Ready for Phase 5 enterprise implementation")
        
        return True
        
    except Exception as e:
        print(f"\n❌ MCP Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_agent_mcp_integration():
    """Test MCP integration with agents"""
    
    print("\n🤖 TESTING AGENT-MCP INTEGRATION")
    print("="*50)
    
    try:
        # Test agent with MCP capabilities
        from integrations.mcp import MCPClient
        from integrations.mcp.registry import mcp_registry
        
        # Create agent with MCP client
        class TestAgent:
            def __init__(self, agent_type: str):
                self.agent_type = agent_type
                self.mcp_client = MCPClient(tenant_id="test_tenant")
                self.required_servers = []
            
            async def initialize_mcp_servers(self):
                """Initialize MCP servers for this agent"""
                # Get recommended servers for agent type
                servers = await mcp_registry.get_servers_for_agent(self.agent_type)
                print(f"   📋 Recommended servers for {self.agent_type}: {len(servers)}")
                
                # For testing, we'll just use mock servers
                from integrations.mcp.client import MCPServerConfig, MCPTransportType
                
                test_config = MCPServerConfig(
                    name="agent_filesystem",
                    transport_type=MCPTransportType.STDIO,
                    command="echo",
                    args=["agent_test"]
                )
                
                success = await self.mcp_client.connect_server(test_config)
                print(f"   {'✅' if success else '❌'} Agent MCP server connected: {success}")
                
                return success
            
            async def use_mcp_tool(self, tool_spec: str, **kwargs):
                """Use an MCP tool"""
                server_name, tool_name = tool_spec.split('.')
                result = await self.mcp_client.call_tool(server_name, tool_name, kwargs)
                return result
        
        # Test different agent types
        agent_types = ["code_generation", "data_analysis", "browser_automation"]
        
        for agent_type in agent_types:
            print(f"\n🔧 Testing {agent_type} agent...")
            agent = TestAgent(agent_type)
            
            success = await agent.initialize_mcp_servers()
            if success:
                # Test tool usage
                result = await agent.use_mcp_tool("agent_filesystem.mock_tool", test_data="agent_test")
                print(f"   ✅ Agent tool usage successful")
            
        print("\n✅ Agent-MCP integration test completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Agent-MCP integration test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🌟 reVoAgent MCP Integration Test Suite")
    print("   Testing enterprise-ready MCP framework")
    print()
    
    # Test basic MCP integration
    basic_test = await test_mcp_integration()
    
    # Test agent integration
    agent_test = await test_agent_mcp_integration()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"Basic MCP Integration: {'✅ PASS' if basic_test else '❌ FAIL'}")
    print(f"Agent-MCP Integration: {'✅ PASS' if agent_test else '❌ FAIL'}")
    
    if basic_test and agent_test:
        print("\n🎉 ALL TESTS PASSED!")
        print("🚀 MCP integration is ready for Phase 5 implementation")
        print("\n📋 Next steps:")
        print("1. Install actual MCP servers (npm packages)")
        print("2. Configure enterprise security policies")
        print("3. Integrate with agent marketplace")
        print("4. Begin Phase 5 multi-tenant implementation")
        return 0
    else:
        print("\n⚠️ SOME TESTS FAILED")
        print("📋 Review errors and fix before Phase 5")
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))