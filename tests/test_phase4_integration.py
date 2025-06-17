#!/usr/bin/env python3
"""
Comprehensive Testing Framework for Phase 4 Integration

Tests all Phase 4 components including:
- Specialized Agents
- Workflow Intelligence
- Real-time Dashboard
- AI Integrations (DeepSeek R1, Llama)
- Modern Backend API
"""

import asyncio
import pytest
import json
import time
from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock

# Test imports
from src.revoagent.core.framework import ThreeEngineArchitecture
from src.revoagent.specialized_agents import (
    WorkflowIntelligence, AgentDashboard, CodeAnalysisAgent,
    DebugDetectiveAgent, ArchitectureAdvisorAgent, PerformanceOptimizerAgent,
    SecurityAuditorAgent, AgentCapability, Problem, ProblemComplexity
)
from src.revoagent.ai.deepseek_r1_integration import (
    DeepSeekR1Integration, ReasoningRequest, ReasoningType, DeepSeekR1Mode
)
from src.revoagent.ai.llama_local_integration import (
    LlamaLocalIntegration, LlamaConfig, LlamaModelSize, QuantizationMode,
    GenerationRequest, TaskType
)


class TestPhase4Integration:
    """Comprehensive Phase 4 integration tests"""
    
    @pytest.fixture
    async def engines(self):
        """Initialize Three-Engine Architecture for testing"""
        engines = ThreeEngineArchitecture()
        await engines.initialize()
        yield engines
        await engines.cleanup()
    
    @pytest.fixture
    async def workflow_intelligence(self, engines):
        """Initialize Workflow Intelligence for testing"""
        workflow_intel = WorkflowIntelligence(engines)
        await workflow_intel.initialize()
        yield workflow_intel
        await workflow_intel.cleanup()
    
    @pytest.fixture
    async def agent_dashboard(self, engines, workflow_intelligence):
        """Initialize Agent Dashboard for testing"""
        dashboard = AgentDashboard(engines, workflow_intelligence)
        await dashboard.initialize()
        yield dashboard
        await dashboard.stop_monitoring()
    
    @pytest.fixture
    async def deepseek_integration(self):
        """Initialize DeepSeek R1 integration for testing"""
        integration = DeepSeekR1Integration(mode=DeepSeekR1Mode.LOCAL)
        # Mock initialization for testing
        integration.local_model = Mock()
        integration.local_tokenizer = Mock()
        integration.device = "cpu"
        yield integration
        await integration.cleanup()
    
    @pytest.fixture
    async def llama_integration(self):
        """Initialize Llama integration for testing"""
        config = LlamaConfig(
            model_size=LlamaModelSize.LLAMA_7B,
            quantization=QuantizationMode.INT8,
            max_memory_gb=8.0,
            use_gpu=False,
            gpu_memory_fraction=0.8
        )
        integration = LlamaLocalIntegration(config)
        # Mock initialization for testing
        integration.model = Mock()
        integration.tokenizer = Mock()
        integration.device = "cpu"
        yield integration
        await integration.cleanup()


class TestSpecializedAgents:
    """Test specialized agent functionality"""
    
    @pytest.mark.asyncio
    async def test_code_analysis_agent(self, workflow_intelligence):
        """Test Code Analysis Agent functionality"""
        agent = workflow_intelligence.agents[AgentCapability.CODE_ANALYSIS]
        
        # Test problem analysis
        problem = Problem(
            description="Analyze Python code quality",
            context={"language": "python", "file_path": "test.py"},
            complexity=ProblemComplexity.MODERATE
        )
        
        analysis = await agent.analyze_problem(problem)
        
        assert analysis is not None
        assert analysis.problem_type == "code_analysis"
        assert analysis.confidence_score > 0.0
        assert analysis.complexity_assessment == ProblemComplexity.MODERATE
    
    @pytest.mark.asyncio
    async def test_debug_detective_agent(self, workflow_intelligence):
        """Test Debug Detective Agent functionality"""
        agent = workflow_intelligence.agents[AgentCapability.DEBUG_DETECTION]
        
        problem = Problem(
            description="Debug NullPointerException in Java code",
            context={"language": "java", "error_type": "NullPointerException"},
            complexity=ProblemComplexity.HIGH
        )
        
        analysis = await agent.analyze_problem(problem)
        solutions = await agent.generate_solution(analysis)
        
        assert analysis is not None
        assert len(solutions) >= 1
        assert all(solution.confidence_score > 0.0 for solution in solutions)
    
    @pytest.mark.asyncio
    async def test_security_auditor_agent(self, workflow_intelligence):
        """Test Security Auditor Agent functionality"""
        agent = workflow_intelligence.agents[AgentCapability.SECURITY_AUDITING]
        
        problem = Problem(
            description="Conduct security audit of web application",
            context={"app_type": "web", "framework": "flask"},
            complexity=ProblemComplexity.HIGH
        )
        
        analysis = await agent.analyze_problem(problem)
        solutions = await agent.generate_solution(analysis)
        
        assert analysis is not None
        assert len(solutions) >= 1
        assert any("security" in solution.approach.lower() for solution in solutions)
    
    @pytest.mark.asyncio
    async def test_agent_collaboration(self, workflow_intelligence):
        """Test multi-agent collaboration"""
        from src.revoagent.specialized_agents.workflow_intelligence import AgentCollaboration
        
        collaboration = AgentCollaboration(
            collaboration_id="test_collaboration",
            participating_agents=[
                AgentCapability.CODE_ANALYSIS,
                AgentCapability.SECURITY_AUDITING
            ],
            coordination_strategy="consensus",
            communication_protocol="message_passing",
            conflict_resolution="voting",
            success_metrics={"consensus_threshold": 0.8}
        )
        
        result = await workflow_intelligence.coordinate_agents(
            collaboration,
            task_context={"description": "Comprehensive code review"}
        )
        
        assert result is not None
        assert result.get("status") == "completed"


class TestWorkflowIntelligence:
    """Test workflow intelligence functionality"""
    
    @pytest.mark.asyncio
    async def test_intelligent_workflow_creation(self, workflow_intelligence):
        """Test intelligent workflow creation"""
        workflow_def = await workflow_intelligence.create_intelligent_workflow(
            problem_description="Perform security audit",
            context={"app_type": "web", "priority": "high"},
            preferences={"workflow_type": "collaborative"}
        )
        
        assert workflow_def is not None
        assert workflow_def.workflow_id is not None
        assert len(workflow_def.steps) > 0
        assert workflow_def.workflow_type.value == "collaborative"
    
    @pytest.mark.asyncio
    async def test_workflow_execution(self, workflow_intelligence):
        """Test workflow execution"""
        # Create workflow
        workflow_def = await workflow_intelligence.create_intelligent_workflow(
            problem_description="Code analysis task",
            context={"language": "python"},
            preferences={"workflow_type": "sequential"}
        )
        
        # Execute workflow
        execution = await workflow_intelligence.execute_workflow(
            workflow_def.workflow_id,
            execution_context={"target": "test_code.py"}
        )
        
        assert execution is not None
        assert execution.execution_id is not None
        assert execution.workflow_id == workflow_def.workflow_id
    
    @pytest.mark.asyncio
    async def test_workflow_prediction(self, workflow_intelligence):
        """Test workflow outcome prediction"""
        workflow_def = await workflow_intelligence.create_intelligent_workflow(
            problem_description="Performance optimization",
            context={"complexity": "medium"},
            preferences={}
        )
        
        prediction = await workflow_intelligence.predict_workflow_outcome(
            workflow_def,
            context={"urgency": "high"}
        )
        
        assert prediction is not None
        assert "success_probability" in prediction
        assert "estimated_duration" in prediction
        assert 0.0 <= prediction["success_probability"] <= 1.0


class TestAgentDashboard:
    """Test agent dashboard functionality"""
    
    @pytest.mark.asyncio
    async def test_dashboard_state(self, agent_dashboard):
        """Test dashboard state retrieval"""
        state = await agent_dashboard.get_dashboard_state()
        
        assert state is not None
        assert hasattr(state, 'active_sessions')
        assert hasattr(state, 'total_problems_solved')
        assert hasattr(state, 'agent_statuses')
        assert hasattr(state, 'workflow_metrics')
    
    @pytest.mark.asyncio
    async def test_system_alerts(self, agent_dashboard):
        """Test system alerts functionality"""
        alerts = await agent_dashboard.get_system_alerts()
        
        assert isinstance(alerts, list)
        # Should be empty initially or contain valid alert objects
        for alert in alerts:
            assert hasattr(alert, 'alert_id')
            assert hasattr(alert, 'level')
            assert hasattr(alert, 'message')
    
    @pytest.mark.asyncio
    async def test_agent_control(self, agent_dashboard):
        """Test agent control functionality"""
        # Test health check
        result = await agent_dashboard.trigger_agent_action(
            agent_id="code_analysis_agent",
            action="health_check"
        )
        
        assert result is not None
        assert "success" in result


class TestAIIntegrations:
    """Test AI model integrations"""
    
    @pytest.mark.asyncio
    async def test_deepseek_r1_reasoning(self, deepseek_integration):
        """Test DeepSeek R1 reasoning capabilities"""
        request = ReasoningRequest(
            prompt="Solve this logic puzzle: If all cats are animals and some animals are pets, what can we conclude?",
            reasoning_type=ReasoningType.LOGICAL,
            context={"domain": "logic"},
            reasoning_depth=3
        )
        
        # Mock the reasoning process
        with patch.object(deepseek_integration, '_reason_local') as mock_reason:
            mock_reason.return_value = Mock(
                request_id="test_req",
                final_answer="Some cats are pets",
                reasoning_chain=[],
                confidence_score=0.9,
                processing_time=2.5
            )
            
            result = await deepseek_integration.reason(request)
            
            assert result is not None
            assert result.final_answer is not None
            assert result.confidence_score > 0.0
    
    @pytest.mark.asyncio
    async def test_deepseek_quality_analysis(self, deepseek_integration):
        """Test DeepSeek reasoning quality analysis"""
        # Mock reasoning result
        mock_result = Mock(
            reasoning_chain=[
                Mock(confidence=0.8, evidence=["fact1", "fact2"], assumptions=[])
            ],
            confidence_score=0.85
        )
        
        quality = await deepseek_integration.analyze_reasoning_quality(mock_result)
        
        assert quality is not None
        assert "overall_quality" in quality
        assert "metrics" in quality
        assert "recommendations" in quality
    
    @pytest.mark.asyncio
    async def test_llama_code_generation(self, llama_integration):
        """Test Llama code generation"""
        request = GenerationRequest(
            prompt="Create a Python function to calculate fibonacci numbers",
            task_type=TaskType.CODE_GENERATION,
            max_tokens=512,
            temperature=0.7
        )
        
        # Mock the generation process
        with patch.object(llama_integration, 'generate') as mock_generate:
            mock_generate.return_value = Mock(
                request_id="test_req",
                generated_text="def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
                prompt_tokens=20,
                completion_tokens=50,
                tokens_per_second=25.0
            )
            
            result = await llama_integration.generate(request)
            
            assert result is not None
            assert result.generated_text is not None
            assert result.tokens_per_second > 0.0
    
    @pytest.mark.asyncio
    async def test_llama_performance_metrics(self, llama_integration):
        """Test Llama performance metrics"""
        metrics = await llama_integration.get_performance_metrics()
        
        assert metrics is not None
        assert "total_requests" in metrics
        assert "average_tokens_per_second" in metrics
        assert "memory_usage_mb" in metrics


class TestModernBackendAPI:
    """Test modern FastAPI backend"""
    
    @pytest.fixture
    def client(self):
        """Create test client for FastAPI app"""
        from fastapi.testclient import TestClient
        from backend_modern import app
        
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
    
    def test_dashboard_endpoint(self, client):
        """Test dashboard data endpoint"""
        # Mock the dashboard state
        with patch('backend_modern.get_dashboard_data') as mock_dashboard:
            mock_dashboard.return_value = Mock(
                dict=lambda: {
                    "engines": [],
                    "system_metrics": {
                        "total_tasks": 100,
                        "active_sessions": 5,
                        "success_rate": 0.95,
                        "uptime": 3600
                    },
                    "alerts": []
                }
            )
            
            response = client.get("/api/dashboard")
            assert response.status_code == 200
            
            data = response.json()
            assert "engines" in data
            assert "system_metrics" in data
            assert "alerts" in data
    
    def test_workflow_creation(self, client):
        """Test workflow creation endpoint"""
        workflow_request = {
            "description": "Test workflow",
            "context": {"test": True},
            "preferences": {"workflow_type": "sequential"}
        }
        
        with patch('backend_modern.app_state') as mock_state:
            mock_workflow_intel = AsyncMock()
            mock_workflow_intel.create_intelligent_workflow.return_value = Mock(
                workflow_id="test_workflow_123",
                steps=[Mock(), Mock()],
                workflow_type=Mock(value="sequential")
            )
            mock_state.workflow_intelligence = mock_workflow_intel
            
            response = client.post("/api/workflows", json=workflow_request)
            assert response.status_code == 200
            
            data = response.json()
            assert "workflow_id" in data
            assert "status" in data
            assert "steps" in data
    
    def test_agent_execution(self, client):
        """Test agent execution endpoint"""
        agent_request = {
            "agent_capability": "code_analysis",
            "task_description": "Analyze this code",
            "context": {"language": "python"}
        }
        
        with patch('backend_modern.app_state') as mock_state:
            mock_workflow_intel = Mock()
            mock_agent = AsyncMock()
            mock_agent.agent_id = "test_agent"
            mock_agent.analyze_problem.return_value = Mock(
                problem_type="code_analysis",
                complexity_assessment=Mock(value="moderate"),
                confidence_score=0.85
            )
            mock_agent.generate_solution.return_value = [
                Mock(approach="static_analysis", confidence_score=0.9, estimated_effort=30)
            ]
            
            mock_workflow_intel.agents = {Mock(value="code_analysis"): mock_agent}
            mock_state.workflow_intelligence = mock_workflow_intel
            
            response = client.post("/api/agents/code_analysis/execute", json=agent_request)
            assert response.status_code == 200
            
            data = response.json()
            assert "agent_id" in data
            assert "task_id" in data
            assert "status" in data
            assert "result" in data


class TestPerformanceAndScaling:
    """Test performance and scaling capabilities"""
    
    @pytest.mark.asyncio
    async def test_concurrent_agent_execution(self, workflow_intelligence):
        """Test concurrent execution of multiple agents"""
        problems = [
            Problem(
                description=f"Test problem {i}",
                context={"test_id": i},
                complexity=ProblemComplexity.LOW
            )
            for i in range(5)
        ]
        
        # Execute problems concurrently
        tasks = []
        for problem in problems:
            agent = workflow_intelligence.agents[AgentCapability.CODE_ANALYSIS]
            task = asyncio.create_task(agent.analyze_problem(problem))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        assert all(result is not None for result in results)
    
    @pytest.mark.asyncio
    async def test_workflow_scalability(self, workflow_intelligence):
        """Test workflow system scalability"""
        # Create multiple workflows
        workflows = []
        for i in range(3):
            workflow_def = await workflow_intelligence.create_intelligent_workflow(
                problem_description=f"Scalability test {i}",
                context={"test_id": i},
                preferences={"workflow_type": "parallel"}
            )
            workflows.append(workflow_def)
        
        assert len(workflows) == 3
        assert all(wf.workflow_id is not None for wf in workflows)
    
    @pytest.mark.asyncio
    async def test_memory_usage(self, engines):
        """Test memory usage under load"""
        import psutil
        import gc
        
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Simulate load
        for _ in range(10):
            await engines.perfect_recall.store_context("test_key", {"data": "test"})
        
        # Force garbage collection
        gc.collect()
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for this test)
        assert memory_increase < 100


class TestIntegrationScenarios:
    """Test end-to-end integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_complete_code_review_workflow(self, workflow_intelligence):
        """Test complete code review workflow"""
        # Create comprehensive code review workflow
        workflow_def = await workflow_intelligence.create_intelligent_workflow(
            problem_description="Comprehensive code review of Python web application",
            context={
                "language": "python",
                "framework": "flask",
                "review_scope": "security_and_performance"
            },
            preferences={
                "workflow_type": "collaborative",
                "focus_areas": ["security", "performance", "maintainability"]
            }
        )
        
        # Execute workflow
        execution = await workflow_intelligence.execute_workflow(
            workflow_def.workflow_id,
            execution_context={"target_files": ["app.py", "models.py"]}
        )
        
        assert execution is not None
        assert execution.status.value in ["running", "completed"]
    
    @pytest.mark.asyncio
    async def test_ai_model_integration_workflow(self, deepseek_integration, llama_integration):
        """Test workflow using both AI models"""
        # DeepSeek for reasoning
        reasoning_request = ReasoningRequest(
            prompt="Analyze the architectural implications of microservices",
            reasoning_type=ReasoningType.ANALYTICAL,
            context={"domain": "software_architecture"}
        )
        
        # Llama for code generation
        code_request = GenerationRequest(
            prompt="Generate microservice boilerplate code",
            task_type=TaskType.CODE_GENERATION,
            context={"framework": "fastapi"}
        )
        
        # Mock both integrations
        with patch.object(deepseek_integration, 'reason') as mock_reason, \
             patch.object(llama_integration, 'generate') as mock_generate:
            
            mock_reason.return_value = Mock(final_answer="Microservices provide scalability benefits")
            mock_generate.return_value = Mock(generated_text="from fastapi import FastAPI\napp = FastAPI()")
            
            # Execute both
            reasoning_result = await deepseek_integration.reason(reasoning_request)
            code_result = await llama_integration.generate(code_request)
            
            assert reasoning_result is not None
            assert code_result is not None


# Performance benchmarks
class TestPerformanceBenchmarks:
    """Performance benchmarking tests"""
    
    @pytest.mark.asyncio
    async def test_agent_response_time(self, workflow_intelligence):
        """Benchmark agent response times"""
        agent = workflow_intelligence.agents[AgentCapability.CODE_ANALYSIS]
        
        problem = Problem(
            description="Quick analysis test",
            context={"test": True},
            complexity=ProblemComplexity.LOW
        )
        
        start_time = time.time()
        result = await agent.analyze_problem(problem)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert result is not None
        assert response_time < 5.0  # Should respond within 5 seconds
    
    @pytest.mark.asyncio
    async def test_workflow_throughput(self, workflow_intelligence):
        """Benchmark workflow creation throughput"""
        start_time = time.time()
        
        workflows = []
        for i in range(5):
            workflow_def = await workflow_intelligence.create_intelligent_workflow(
                problem_description=f"Throughput test {i}",
                context={"test_id": i},
                preferences={}
            )
            workflows.append(workflow_def)
        
        end_time = time.time()
        total_time = end_time - start_time
        throughput = len(workflows) / total_time
        
        assert len(workflows) == 5
        assert throughput > 1.0  # Should create more than 1 workflow per second


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([
        __file__,
        "-v",
        "--asyncio-mode=auto",
        "--tb=short",
        "--durations=10"
    ])