"""
reVo Chat Package
Advanced conversational AI with multi-agent collaboration
"""

from .multi_agent_chat import (
    AdvancedMultiAgentChat,
    ChatMessage,
    ChatMessageType,
    AgentRole,
    CollaborationMode,
    ConflictResolutionStrategy,
    AgentCollaborationSession,
    multi_agent_chat
)

__all__ = [
    'AdvancedMultiAgentChat',
    'ChatMessage', 
    'ChatMessageType',
    'AgentRole',
    'CollaborationMode',
    'ConflictResolutionStrategy',
    'AgentCollaborationSession',
    'multi_agent_chat'
]