#!/usr/bin/env python3
"""
Comprehensive Test Suite for Multi-Agent Chat System
Phase 4 - Advanced Multi-Agent Capabilities Testing
"""

import pytest
import asyncio
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch

# Import the components to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src'))

from packages.chat.multi_agent_chat import (
    AdvancedMultiAgentChat,
    ChatMessage,
    ChatMessageType,
    AgentRole,
    CollaborationMode,
    ConflictResolutionStrategy,
    AgentCollaborationSession
)

class TestAdvancedMultiAgentChat:
    """Test suite for Advanced Multi-Agent Chat System"""
    
    @pytest.fixture
    def chat_system(self):
        """Create a chat system instance for testing"""
        return AdvancedMultiAgentChat()
    
    @pytest.fixture
    def sample_agents(self):
        """Sample agent roles for testing"""
        return [
            AgentRole.CODE_ANALYST,
            AgentRole.DEBUG_DETECTIVE,
            AgentRole.WORKFLOW_MANAGER
        ]
    
    @pytest.mark.asyncio
    async def test_create_collaboration_session(self, chat_system, sample_agents):
        """Test creating a collaboration session"""
        task_description = "Analyze code quality issues"
        
        session_id = await chat_system.create_collaboration_session(
            task_description=task_description,
            participants=sample_agents,
            mode=CollaborationMode.CONSENSUS
        )
        
        assert session_id is not None
        assert session_id in chat_system.active_sessions
        
        session = chat_system.active_sessions[session_id]
        assert session.task_description == task_description
        assert session.participants == sample_agents
        assert session.mode == CollaborationMode.CONSENSUS
        assert len(session.messages) == 1  # System message
        assert session.messages[0].type == ChatMessageType.SYSTEM
    
    @pytest.mark.asyncio
    async def test_process_user_message_sequential(self, chat_system, sample_agents):
        """Test processing user message in sequential mode"""
        session_id = await chat_system.create_collaboration_session(
            task_description="Test sequential processing",
            participants=sample_agents,
            mode=CollaborationMode.SEQUENTIAL
        )
        
        with patch.object(chat_system, '_get_agent_response') as mock_get_response:
            # Mock agent responses
            mock_responses = [
                ChatMessage(
                    id=str(uuid.uuid4()),
                    type=ChatMessageType.AGENT,
                    content=f"Response from {agent.value}",
                    agent_role=agent,
                    confidence_score=0.8
                )
                for agent in sample_agents
            ]
            mock_get_response.side_effect = mock_responses
            
            result = await chat_system.process_user_message(
                session_id=session_id,
                message="Test message",
                user_id="test_user"
            )
            
            assert result["session_id"] == session_id
            assert len(result["agent_responses"]) == len(sample_agents)
            assert mock_get_response.call_count == len(sample_agents)
    
    def test_response_similarity_calculation(self, chat_system):
        """Test response similarity calculation"""
        content1 = "The code quality is good with minor issues"
        content2 = "The code quality is excellent with no issues"
        content3 = "This is completely different content about databases"
        
        # Similar content should have high similarity
        similarity1 = chat_system._calculate_response_similarity(content1, content2)
        assert similarity1 > 0.3
        
        # Different content should have low similarity
        similarity2 = chat_system._calculate_response_similarity(content1, content3)
        assert similarity2 < 0.5

if __name__ == "__main__":
    pytest.main([__file__, "-v"])