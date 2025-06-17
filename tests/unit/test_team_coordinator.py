#!/usr/bin/env python3
"""
Unit tests for AI Team Coordinator
Tests the 100-agent coordination system with task assignment and load balancing
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from apps.backend.services.ai_team_coordinator import AITeamCoordinator, DevelopmentTask, TaskType, TaskPriority, TaskStatus


class TestAITeamCoordinator:
    """Test suite for AITeamCoordinator"""
    
    @pytest.fixture
    def mock_ai_service(self):
        """Create mock AI service for testing"""
        mock_service = Mock()
        mock_service.generate_with_cost_optimization = AsyncMock()
        return mock_service
    
    @pytest.fixture
    def team_coordinator(self, mock_ai_service):
        """Create team coordinator instance for testing"""
        coordinator = AITeamCoordinator(mock_ai_service)
        return coordinator
    
    @pytest.mark.unit
    def test_team_coordinator_initialization(self, team_coordinator):
        """Test team coordinator initializes with correct agent distribution"""
        # Check agent counts
        assert len(team_coordinator.claude_agents) == 30
        assert len(team_coordinator.gemini_agents) == 40
        assert len(team_coordinator.openhands_agents) == 30
        
        # Check total agents
        total_agents = (len(team_coordinator.claude_agents) + 
                       len(team_coordinator.gemini_agents) + 
                       len(team_coordinator.openhands_agents))
        assert total_agents == 100
        
        # Check agent specializations
        claude_agent = team_coordinator.claude_agents[0]
        assert "code_generation" in claude_agent.specialties
        
        gemini_agent = team_coordinator.gemini_agents[0]
        assert "analysis" in gemini_agent.specialties
        
        openhands_agent = team_coordinator.openhands_agents[0]
        assert "testing" in openhands_agent.specialties
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_epic_coordination_basic(self, team_coordinator):
        """Test basic epic coordination and task breakdown"""
        epic = Epic(
            title="Build User Authentication System",
            description="Create secure user authentication with JWT tokens and password hashing"
        )
        
        # Mock AI decomposition
        with patch.object(team_coordinator.ai_service, 'generate_with_cost_optimization', new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = {
                "content": "Task breakdown: 1. Design auth API, 2. Implement JWT, 3. Add password hashing, 4. Create tests",
                "success": True
            }
            
            tasks = await team_coordinator.coordinate_development_task(epic)
            
            # Verify tasks were created
            assert len(tasks) >= 3  # Should break into multiple tasks
            
            # Verify task assignment
            for task in tasks:
                assert task.assigned_agent is not None
                assert task.task_type in ["analysis", "implementation", "testing"]
                assert task.epic_id == epic.id
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_intelligent_agent_assignment(self, team_coordinator):
        """Test intelligent assignment of tasks to appropriate agents"""
        # Create different types of tasks
        analysis_epic = Epic(
            title="Performance Analysis",
            description="Analyze system performance and identify bottlenecks"
        )
        
        coding_epic = Epic(
            title="API Implementation", 
            description="Implement REST API endpoints for user management"
        )
        
        testing_epic = Epic(
            title="Test Automation",
            description="Create automated test suite for the application"
        )
        
        with patch.object(team_coordinator.ai_service, 'generate_with_cost_optimization', new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = {"content": "Task breakdown", "success": True}
            
            # Process different epic types
            analysis_tasks = await team_coordinator.coordinate_development_task(analysis_epic)
            coding_tasks = await team_coordinator.coordinate_development_task(coding_epic)
            testing_tasks = await team_coordinator.coordinate_development_task(testing_epic)
            
            # Verify appropriate agent assignment
            # Analysis tasks should prefer Gemini agents
            analysis_agents = [task.assigned_agent for task in analysis_tasks]
            assert any("gemini" in agent for agent in analysis_agents)
            
            # Coding tasks should prefer Claude agents
            coding_agents = [task.assigned_agent for task in coding_tasks]
            assert any("claude" in agent for agent in coding_agents)
            
            # Testing tasks should prefer OpenHands agents
            testing_agents = [task.assigned_agent for task in testing_tasks]
            assert any("openhands" in agent for agent in testing_agents)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_load_balancing(self, team_coordinator):
        """Test load balancing across agents"""
        # Create multiple similar tasks
        epics = [
            Epic(title=f"Task {i}", description=f"Implementation task {i}")
            for i in range(10)
        ]
        
        with patch.object(team_coordinator.ai_service, 'generate_with_cost_optimization', new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = {"content": "Single task", "success": True}
            
            all_tasks = []
            for epic in epics:
                tasks = await team_coordinator.coordinate_development_task(epic)
                all_tasks.extend(tasks)
            
            # Verify load distribution
            agent_assignments = {}
            for task in all_tasks:
                agent = task.assigned_agent
                agent_assignments[agent] = agent_assignments.get(agent, 0) + 1
            
            # Check that tasks are distributed (not all to same agent)
            assert len(agent_assignments) > 1
            
            # Check that no single agent is overloaded
            max_tasks_per_agent = max(agent_assignments.values())
            min_tasks_per_agent = min(agent_assignments.values())
            assert max_tasks_per_agent - min_tasks_per_agent <= 2  # Reasonable distribution
    
    @pytest.mark.unit
    def test_agent_capacity_management(self, team_coordinator):
        """Test agent capacity and availability tracking"""
        # Get initial capacity
        initial_capacity = team_coordinator.get_team_capacity()
        
        # Assign some tasks
        claude_agent = team_coordinator.claude_agents[0]
        team_coordinator._assign_task_to_agent(claude_agent, "test_task")
        
        # Check capacity updated
        updated_capacity = team_coordinator.get_team_capacity()
        assert updated_capacity["claude"]["available"] == initial_capacity["claude"]["available"] - 1
        assert updated_capacity["claude"]["busy"] == initial_capacity["claude"]["busy"] + 1
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_task_execution_tracking(self, team_coordinator):
        """Test task execution and progress tracking"""
        epic = Epic(title="Test Epic", description="Test description")
        
        with patch.object(team_coordinator.ai_service, 'generate_with_cost_optimization', new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = {"content": "Task result", "success": True}
            
            tasks = await team_coordinator.coordinate_development_task(epic)
            
            # Verify task tracking
            for task in tasks:
                assert task.status in ["pending", "in_progress", "completed"]
                assert task.created_at is not None
                assert task.assigned_agent is not None
    
    @pytest.mark.unit
    def test_team_status_reporting(self, team_coordinator):
        """Test team status and metrics reporting"""
        status = team_coordinator.get_team_status()
        
        # Check required status fields
        required_fields = [
            "total_agents",
            "active_agents", 
            "busy_agents",
            "idle_agents",
            "tasks_completed_today",
            "average_response_time",
            "success_rate"
        ]
        
        for field in required_fields:
            assert field in status
        
        # Check agent breakdown
        assert "agent_breakdown" in status
        breakdown = status["agent_breakdown"]
        assert "claude_agents" in breakdown
        assert "gemini_agents" in breakdown
        assert "openhands_agents" in breakdown
        
        # Verify totals add up
        total_from_breakdown = (
            breakdown["claude_agents"]["total"] +
            breakdown["gemini_agents"]["total"] +
            breakdown["openhands_agents"]["total"]
        )
        assert total_from_breakdown == 100
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_error_handling_in_coordination(self, team_coordinator):
        """Test error handling during task coordination"""
        epic = Epic(title="Test Epic", description="Test description")
        
        # Mock AI service failure
        with patch.object(team_coordinator.ai_service, 'generate_with_cost_optimization', new_callable=AsyncMock) as mock_ai:
            mock_ai.side_effect = Exception("AI service unavailable")
            
            tasks = await team_coordinator.coordinate_development_task(epic)
            
            # Should still return tasks (fallback mechanism)
            assert len(tasks) > 0
            
            # Tasks should have error status or fallback assignment
            for task in tasks:
                assert task.assigned_agent is not None  # Fallback assignment should work
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_concurrent_epic_coordination(self, team_coordinator):
        """Test handling multiple concurrent epics"""
        epics = [
            Epic(title=f"Concurrent Epic {i}", description=f"Description {i}")
            for i in range(5)
        ]
        
        with patch.object(team_coordinator.ai_service, 'generate_with_cost_optimization', new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = {"content": "Task breakdown", "success": True}
            
            # Process epics concurrently
            tasks_lists = await asyncio.gather(*[
                team_coordinator.coordinate_development_task(epic)
                for epic in epics
            ])
            
            # Verify all epics were processed
            assert len(tasks_lists) == 5
            
            # Verify no conflicts in agent assignment
            all_tasks = [task for tasks in tasks_lists for task in tasks]
            agent_assignments = [task.assigned_agent for task in all_tasks]
            
            # Should have reasonable distribution
            unique_agents = set(agent_assignments)
            assert len(unique_agents) > 1  # Multiple agents used
    
    @pytest.mark.unit
    def test_agent_specialization_matching(self, team_coordinator):
        """Test matching tasks to agent specializations"""
        # Test different task types
        code_task = Task(
            title="Implement Function",
            description="Write Python function",
            task_type="implementation",
            epic_id="test"
        )
        
        analysis_task = Task(
            title="Performance Analysis", 
            description="Analyze system performance",
            task_type="analysis",
            epic_id="test"
        )
        
        test_task = Task(
            title="Create Tests",
            description="Write unit tests",
            task_type="testing", 
            epic_id="test"
        )
        
        # Test agent selection
        code_agent = team_coordinator._select_best_agent(code_task)
        analysis_agent = team_coordinator._select_best_agent(analysis_task)
        test_agent = team_coordinator._select_best_agent(test_task)
        
        # Verify appropriate agent types selected
        assert "claude" in code_agent.agent_id  # Claude for coding
        assert "gemini" in analysis_agent.agent_id  # Gemini for analysis
        assert "openhands" in test_agent.agent_id  # OpenHands for testing


class TestEpic:
    """Test suite for Epic model"""
    
    @pytest.mark.unit
    def test_epic_creation(self):
        """Test Epic can be created with required fields"""
        epic = Epic(
            title="Test Epic",
            description="Test description",
            priority="high"
        )
        
        assert epic.title == "Test Epic"
        assert epic.description == "Test description"
        assert epic.priority == "high"
        assert epic.id is not None
        assert epic.created_at is not None
    
    @pytest.mark.unit
    def test_epic_defaults(self):
        """Test Epic has sensible defaults"""
        epic = Epic(title="Test", description="Test")
        
        assert epic.priority == "medium"
        assert epic.status == "pending"
        assert epic.estimated_hours is None


class TestTask:
    """Test suite for Task model"""
    
    @pytest.mark.unit
    def test_task_creation(self):
        """Test Task can be created with required fields"""
        task = Task(
            title="Test Task",
            description="Test description",
            task_type="implementation",
            epic_id="epic_123"
        )
        
        assert task.title == "Test Task"
        assert task.description == "Test description"
        assert task.task_type == "implementation"
        assert task.epic_id == "epic_123"
        assert task.id is not None
        assert task.created_at is not None
    
    @pytest.mark.unit
    def test_task_defaults(self):
        """Test Task has sensible defaults"""
        task = Task(
            title="Test",
            description="Test",
            task_type="implementation",
            epic_id="epic_123"
        )
        
        assert task.status == "pending"
        assert task.priority == "medium"
        assert task.assigned_agent is None
        assert task.result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])