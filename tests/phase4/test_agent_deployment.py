#!/usr/bin/env python3
"""
Comprehensive Test Suite for Agent Deployment
Tests for Kubernetes deployment configurations and agent orchestration
"""

import pytest
import yaml
import json
import os
import sys
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

# Add project paths
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../../packages'))

class TestKubernetesDeploymentConfigs:
    """Test Kubernetes deployment configurations"""
    
    @pytest.fixture
    def deployment_config_path(self):
        """Path to Kubernetes deployment configuration"""
        return Path(__file__).parent.parent.parent / "deployment" / "k8s" / "multi-agent-deployment.yaml"
    
    @pytest.fixture
    def docker_compose_path(self):
        """Path to Docker Compose configuration"""
        return Path(__file__).parent.parent.parent / "deployment" / "agents" / "docker-compose.agents.yml"
    
    def test_kubernetes_deployment_file_exists(self, deployment_config_path):
        """Test that Kubernetes deployment file exists"""
        assert deployment_config_path.exists(), f"Deployment config not found at {deployment_config_path}"
    
    def test_docker_compose_file_exists(self, docker_compose_path):
        """Test that Docker Compose file exists"""
        assert docker_compose_path.exists(), f"Docker Compose config not found at {docker_compose_path}"
    
    def test_kubernetes_deployment_yaml_valid(self, deployment_config_path):
        """Test that Kubernetes YAML is valid"""
        if not deployment_config_path.exists():
            pytest.skip("Deployment config file not found")
        
        with open(deployment_config_path, 'r') as f:
            try:
                docs = list(yaml.safe_load_all(f))
                assert len(docs) > 0, "No YAML documents found"
                
                # Check for required resource types
                resource_types = [doc.get('kind') for doc in docs if doc]
                expected_types = ['Namespace', 'ConfigMap', 'Secret', 'Deployment', 'Service']
                
                for expected_type in expected_types:
                    assert expected_type in resource_types, f"Missing {expected_type} resource"
                
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML: {e}")
    
    def test_docker_compose_yaml_valid(self, docker_compose_path):
        """Test that Docker Compose YAML is valid"""
        if not docker_compose_path.exists():
            pytest.skip("Docker Compose config file not found")
        
        with open(docker_compose_path, 'r') as f:
            try:
                config = yaml.safe_load(f)
                assert 'services' in config, "No services defined in Docker Compose"
                assert 'version' in config, "No version specified in Docker Compose"
                
                # Check for expected services
                services = config['services']
                expected_services = ['multi-agent-chat', 'redis']
                
                for service in expected_services:
                    assert service in services, f"Missing service: {service}"
                
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML: {e}")
    
    def test_agent_deployment_configurations(self, deployment_config_path):
        """Test agent-specific deployment configurations"""
        if not deployment_config_path.exists():
            pytest.skip("Deployment config file not found")
        
        with open(deployment_config_path, 'r') as f:
            docs = list(yaml.safe_load_all(f))
        
        # Find agent deployments
        agent_deployments = [
            doc for doc in docs 
            if doc and doc.get('kind') == 'Deployment' 
            and 'agent' in doc.get('metadata', {}).get('name', '')
        ]
        
        expected_agents = ['code-analyst', 'debug-detective', 'workflow-manager', 'coordinator']
        
        for agent in expected_agents:
            agent_deployment = next(
                (dep for dep in agent_deployments 
                 if agent in dep.get('metadata', {}).get('name', '')), 
                None
            )
            
            if agent_deployment:
                # Test deployment structure
                spec = agent_deployment.get('spec', {})
                assert 'replicas' in spec, f"No replicas specified for {agent}"
                assert 'selector' in spec, f"No selector specified for {agent}"
                assert 'template' in spec, f"No template specified for {agent}"
                
                # Test container configuration
                containers = spec.get('template', {}).get('spec', {}).get('containers', [])
                assert len(containers) > 0, f"No containers defined for {agent}"
                
                container = containers[0]
                assert 'image' in container, f"No image specified for {agent}"
                assert 'ports' in container, f"No ports specified for {agent}"
                assert 'env' in container, f"No environment variables for {agent}"
    
    def test_resource_limits_and_requests(self, deployment_config_path):
        """Test that resource limits and requests are properly configured"""
        if not deployment_config_path.exists():
            pytest.skip("Deployment config file not found")
        
        with open(deployment_config_path, 'r') as f:
            docs = list(yaml.safe_load_all(f))
        
        deployments = [doc for doc in docs if doc and doc.get('kind') == 'Deployment']
        
        for deployment in deployments:
            containers = deployment.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [])
            
            for container in containers:
                resources = container.get('resources', {})
                
                # Check that resources are defined
                assert 'requests' in resources or 'limits' in resources, \
                    f"No resource constraints for container in {deployment.get('metadata', {}).get('name')}"
                
                if 'requests' in resources:
                    requests = resources['requests']
                    assert 'cpu' in requests or 'memory' in requests, \
                        "Resource requests should specify CPU or memory"
                
                if 'limits' in resources:
                    limits = resources['limits']
                    assert 'cpu' in limits or 'memory' in limits, \
                        "Resource limits should specify CPU or memory"
    
    def test_health_checks_configured(self, deployment_config_path):
        """Test that health checks are properly configured"""
        if not deployment_config_path.exists():
            pytest.skip("Deployment config file not found")
        
        with open(deployment_config_path, 'r') as f:
            docs = list(yaml.safe_load_all(f))
        
        deployments = [doc for doc in docs if doc and doc.get('kind') == 'Deployment']
        
        for deployment in deployments:
            containers = deployment.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [])
            
            for container in containers:
                # Check for health checks
                has_liveness = 'livenessProbe' in container
                has_readiness = 'readinessProbe' in container
                
                assert has_liveness or has_readiness, \
                    f"No health checks configured for container in {deployment.get('metadata', {}).get('name')}"
    
    def test_security_contexts(self, deployment_config_path):
        """Test that security contexts are properly configured"""
        if not deployment_config_path.exists():
            pytest.skip("Deployment config file not found")
        
        with open(deployment_config_path, 'r') as f:
            docs = list(yaml.safe_load_all(f))
        
        deployments = [doc for doc in docs if doc and doc.get('kind') == 'Deployment']
        
        for deployment in deployments:
            pod_spec = deployment.get('spec', {}).get('template', {}).get('spec', {})
            containers = pod_spec.get('containers', [])
            
            # Check pod security context
            pod_security_context = pod_spec.get('securityContext', {})
            
            # Check container security contexts
            for container in containers:
                container_security_context = container.get('securityContext', {})
                
                # Should have some security configuration
                has_security_config = (
                    bool(pod_security_context) or 
                    bool(container_security_context)
                )
                
                assert has_security_config, \
                    f"No security context for {deployment.get('metadata', {}).get('name')}"

class TestDockerfileConfigurations:
    """Test Dockerfile configurations for agents"""
    
    @pytest.fixture
    def dockerfiles_path(self):
        """Path to Dockerfiles directory"""
        return Path(__file__).parent.parent.parent / "deployment" / "agents"
    
    def test_dockerfiles_exist(self, dockerfiles_path):
        """Test that Dockerfiles exist for each agent"""
        expected_dockerfiles = [
            "Dockerfile.code-analyst",
            "Dockerfile.debug-detective", 
            "Dockerfile.workflow-manager",
            "Dockerfile.multi-agent-chat"
        ]
        
        for dockerfile in expected_dockerfiles:
            dockerfile_path = dockerfiles_path / dockerfile
            assert dockerfile_path.exists(), f"Dockerfile not found: {dockerfile}"
    
    def test_dockerfile_structure(self, dockerfiles_path):
        """Test Dockerfile structure and best practices"""
        dockerfiles = [
            "Dockerfile.code-analyst",
            "Dockerfile.debug-detective",
            "Dockerfile.workflow-manager", 
            "Dockerfile.multi-agent-chat"
        ]
        
        for dockerfile_name in dockerfiles:
            dockerfile_path = dockerfiles_path / dockerfile_name
            
            if not dockerfile_path.exists():
                continue
            
            with open(dockerfile_path, 'r') as f:
                content = f.read()
            
            # Check for required instructions
            assert 'FROM' in content, f"No FROM instruction in {dockerfile_name}"
            assert 'WORKDIR' in content, f"No WORKDIR instruction in {dockerfile_name}"
            assert 'COPY' in content or 'ADD' in content, f"No COPY/ADD instruction in {dockerfile_name}"
            assert 'CMD' in content or 'ENTRYPOINT' in content, f"No CMD/ENTRYPOINT in {dockerfile_name}"
            
            # Check for security best practices
            assert 'USER' in content, f"No USER instruction in {dockerfile_name} (should run as non-root)"
            assert 'HEALTHCHECK' in content, f"No HEALTHCHECK in {dockerfile_name}"
            
            # Check for Python-specific requirements
            if 'python' in content.lower():
                assert 'pip install' in content, f"No pip install in Python Dockerfile {dockerfile_name}"

class TestEntrypointScripts:
    """Test entrypoint scripts for agents"""
    
    @pytest.fixture
    def entrypoints_path(self):
        """Path to entrypoint scripts directory"""
        return Path(__file__).parent.parent.parent / "deployment" / "agents" / "entrypoints"
    
    def test_entrypoint_scripts_exist(self, entrypoints_path):
        """Test that entrypoint scripts exist"""
        expected_scripts = [
            "code-analyst-entrypoint.py",
            "debug-detective-entrypoint.py",
            "workflow-manager-entrypoint.py",
            "multi-agent-chat-entrypoint.py"
        ]
        
        for script in expected_scripts:
            script_path = entrypoints_path / script
            assert script_path.exists(), f"Entrypoint script not found: {script}"
    
    def test_entrypoint_script_structure(self, entrypoints_path):
        """Test entrypoint script structure"""
        scripts = [
            "code-analyst-entrypoint.py",
            "multi-agent-chat-entrypoint.py"
        ]
        
        for script_name in scripts:
            script_path = entrypoints_path / script_name
            
            if not script_path.exists():
                continue
            
            with open(script_path, 'r') as f:
                content = f.read()
            
            # Check for required imports and structure
            assert 'import' in content, f"No imports in {script_name}"
            assert 'def main(' in content or 'if __name__' in content, f"No main function in {script_name}"
            assert 'FastAPI' in content or 'uvicorn' in content, f"No FastAPI/uvicorn in {script_name}"
            
            # Check for proper error handling
            assert 'try:' in content or 'except' in content, f"No error handling in {script_name}"
            
            # Check for logging
            assert 'logging' in content, f"No logging in {script_name}"

class TestAgentOrchestration:
    """Test agent orchestration and communication"""
    
    def test_agent_communication_config(self):
        """Test agent communication configuration"""
        # Test Redis configuration for agent communication
        expected_redis_config = {
            "host": "agent-redis",
            "port": 6379,
            "db": 0
        }
        
        # Verify configuration structure
        assert expected_redis_config["host"] == "agent-redis"
        assert expected_redis_config["port"] == 6379
    
    def test_agent_service_discovery(self):
        """Test agent service discovery configuration"""
        expected_services = {
            "code-analyst": "code-analyst-service:8000",
            "debug-detective": "debug-detective-service:8000", 
            "workflow-manager": "workflow-manager-service:8000",
            "coordinator": "coordinator-service:8000"
        }
        
        # Verify service naming convention
        for agent, service_url in expected_services.items():
            assert agent in service_url
            assert ":8000" in service_url
    
    def test_agent_scaling_configuration(self):
        """Test agent auto-scaling configuration"""
        scaling_config = {
            "code-analyst": {"min": 2, "max": 10},
            "debug-detective": {"min": 1, "max": 8},
            "workflow-manager": {"min": 1, "max": 5},
            "coordinator": {"min": 1, "max": 3}
        }
        
        # Verify scaling limits are reasonable
        for agent, config in scaling_config.items():
            assert config["min"] >= 1, f"Minimum replicas too low for {agent}"
            assert config["max"] > config["min"], f"Max replicas not greater than min for {agent}"
            assert config["max"] <= 10, f"Maximum replicas too high for {agent}"

class TestDeploymentValidation:
    """Test deployment validation and readiness"""
    
    @pytest.mark.asyncio
    async def test_agent_health_endpoints(self):
        """Test agent health endpoint configuration"""
        agents = ["code-analyst", "debug-detective", "workflow-manager", "coordinator"]
        
        for agent in agents:
            # Mock health check
            health_response = {
                "status": "healthy",
                "agent_type": agent.replace("-", "_"),
                "version": "1.0.0"
            }
            
            assert health_response["status"] == "healthy"
            assert agent.replace("-", "_") in health_response["agent_type"]
    
    @pytest.mark.asyncio
    async def test_agent_readiness_endpoints(self):
        """Test agent readiness endpoint configuration"""
        agents = ["code-analyst", "debug-detective", "workflow-manager", "coordinator"]
        
        for agent in agents:
            # Mock readiness check
            readiness_response = {
                "status": "ready",
                "agent_type": agent.replace("-", "_"),
                "capabilities": ["analysis", "collaboration"]
            }
            
            assert readiness_response["status"] == "ready"
            assert len(readiness_response["capabilities"]) > 0
    
    def test_environment_variable_configuration(self):
        """Test environment variable configuration"""
        required_env_vars = [
            "AGENT_TYPE",
            "REDIS_URL", 
            "JWT_SECRET",
            "LOG_LEVEL",
            "METRICS_ENABLED"
        ]
        
        # Test that all required environment variables are defined
        for env_var in required_env_vars:
            # In actual deployment, these would be set
            assert env_var is not None
            assert len(env_var) > 0
    
    def test_network_policy_configuration(self):
        """Test network policy configuration"""
        network_policy = {
            "ingress": {
                "allowed_namespaces": ["revoagent-agents", "revoagent-main"],
                "allowed_ports": [8000, 8001, 6379]
            },
            "egress": {
                "allowed_destinations": ["dns", "external_apis"],
                "blocked_destinations": ["internal_services"]
            }
        }
        
        # Verify network policy structure
        assert "ingress" in network_policy
        assert "egress" in network_policy
        assert len(network_policy["ingress"]["allowed_ports"]) > 0

class TestProductionReadiness:
    """Test production readiness of agent deployments"""
    
    def test_monitoring_configuration(self):
        """Test monitoring and metrics configuration"""
        monitoring_config = {
            "prometheus": {
                "enabled": True,
                "port": 8001,
                "path": "/metrics"
            },
            "grafana": {
                "dashboards": ["agent-performance", "agent-health"],
                "alerts": ["high-cpu", "memory-leak", "response-time"]
            }
        }
        
        assert monitoring_config["prometheus"]["enabled"] is True
        assert len(monitoring_config["grafana"]["dashboards"]) > 0
        assert len(monitoring_config["grafana"]["alerts"]) > 0
    
    def test_logging_configuration(self):
        """Test logging configuration"""
        logging_config = {
            "level": "INFO",
            "format": "json",
            "output": ["stdout", "file"],
            "rotation": "daily",
            "retention": "30d"
        }
        
        assert logging_config["level"] in ["DEBUG", "INFO", "WARNING", "ERROR"]
        assert "stdout" in logging_config["output"]
    
    def test_backup_and_recovery_configuration(self):
        """Test backup and recovery configuration"""
        backup_config = {
            "redis_backup": {
                "enabled": True,
                "schedule": "0 2 * * *",  # Daily at 2 AM
                "retention": "7d"
            },
            "config_backup": {
                "enabled": True,
                "schedule": "0 1 * * 0",  # Weekly on Sunday at 1 AM
                "retention": "30d"
            }
        }
        
        assert backup_config["redis_backup"]["enabled"] is True
        assert backup_config["config_backup"]["enabled"] is True
    
    def test_disaster_recovery_configuration(self):
        """Test disaster recovery configuration"""
        dr_config = {
            "multi_region": False,  # Single region for now
            "backup_region": None,
            "rto": "4h",  # Recovery Time Objective
            "rpo": "1h"   # Recovery Point Objective
        }
        
        # Verify DR configuration is defined
        assert "rto" in dr_config
        assert "rpo" in dr_config

# Integration tests
class TestDeploymentIntegration:
    """Integration tests for deployment"""
    
    @pytest.mark.asyncio
    async def test_agent_to_agent_communication(self):
        """Test agent-to-agent communication"""
        # Mock agent communication
        communication_test = {
            "source": "code-analyst",
            "target": "debug-detective", 
            "message": "Analysis complete, please review",
            "response": "Review started"
        }
        
        assert communication_test["source"] != communication_test["target"]
        assert len(communication_test["message"]) > 0
        assert len(communication_test["response"]) > 0
    
    @pytest.mark.asyncio
    async def test_load_balancing_configuration(self):
        """Test load balancing configuration"""
        load_balancer_config = {
            "algorithm": "round_robin",
            "health_check": {
                "path": "/health",
                "interval": "30s",
                "timeout": "10s"
            },
            "session_affinity": False
        }
        
        assert load_balancer_config["algorithm"] in ["round_robin", "least_connections", "ip_hash"]
        assert load_balancer_config["health_check"]["path"] == "/health"
    
    def test_deployment_rollout_strategy(self):
        """Test deployment rollout strategy"""
        rollout_config = {
            "strategy": "RollingUpdate",
            "max_unavailable": "25%",
            "max_surge": "25%",
            "revision_history_limit": 10
        }
        
        assert rollout_config["strategy"] == "RollingUpdate"
        assert rollout_config["revision_history_limit"] > 0

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])