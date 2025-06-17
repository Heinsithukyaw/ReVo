"""Communication management for reVoAgent platform."""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class MessageType(Enum):
    """Message type enumeration."""
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    AGENT_STATUS = "agent_status"
    SYSTEM_EVENT = "system_event"
    COLLABORATION = "collaboration"
    NOTIFICATION = "notification"


class MessagePriority(Enum):
    """Message priority enumeration."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Message:
    """Message structure for inter-agent communication."""
    id: str
    type: MessageType
    sender: str
    recipient: str
    content: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = None
    correlation_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class CommunicationManager:
    """
    Manages communication between agents and system components.
    
    Features:
    - Asynchronous message passing
    - Message routing and delivery
    - Pub/Sub pattern support
    - Message persistence (optional)
    - Communication monitoring
    """
    
    def __init__(self):
        """Initialize communication manager."""
        self.logger = logging.getLogger(__name__)
        
        # Message queues for each agent/component
        self.message_queues: Dict[str, asyncio.Queue] = {}
        
        # Subscribers for different message types
        self.subscribers: Dict[MessageType, List[str]] = {
            message_type: [] for message_type in MessageType
        }
        
        # Message handlers
        self.message_handlers: Dict[str, Callable] = {}
        
        # Message history (limited to prevent memory growth)
        self.message_history: List[Message] = []
        self.max_history_size = 1000
        
        # Active connections
        self.active_connections: Dict[str, bool] = {}
        
        # Communication statistics
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "messages_failed": 0,
            "active_queues": 0
        }
    
    def register_agent(self, agent_id: str) -> None:
        """Register an agent for communication."""
        if agent_id not in self.message_queues:
            self.message_queues[agent_id] = asyncio.Queue()
            self.active_connections[agent_id] = True
            self.stats["active_queues"] += 1
            self.logger.debug(f"Registered agent for communication: {agent_id}")
    
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent from communication."""
        if agent_id in self.message_queues:
            del self.message_queues[agent_id]
            self.active_connections[agent_id] = False
            self.stats["active_queues"] -= 1
            self.logger.debug(f"Unregistered agent from communication: {agent_id}")
    
    def register_message_handler(self, agent_id: str, handler: Callable) -> None:
        """Register a message handler for an agent."""
        self.message_handlers[agent_id] = handler
    
    def subscribe(self, agent_id: str, message_type: MessageType) -> None:
        """Subscribe an agent to a specific message type."""
        if agent_id not in self.subscribers[message_type]:
            self.subscribers[message_type].append(agent_id)
            self.logger.debug(f"Agent {agent_id} subscribed to {message_type.value}")
    
    def unsubscribe(self, agent_id: str, message_type: MessageType) -> None:
        """Unsubscribe an agent from a specific message type."""
        if agent_id in self.subscribers[message_type]:
            self.subscribers[message_type].remove(agent_id)
            self.logger.debug(f"Agent {agent_id} unsubscribed from {message_type.value}")
    
    async def send_message(self, message: Message) -> bool:
        """Send a message to a specific recipient."""
        try:
            # Check if recipient is registered
            if message.recipient not in self.message_queues:
                self.logger.warning(f"Recipient not found: {message.recipient}")
                self.stats["messages_failed"] += 1
                return False
            
            # Add to recipient's queue
            await self.message_queues[message.recipient].put(message)
            
            # Add to history
            self._add_to_history(message)
            
            # Update statistics
            self.stats["messages_sent"] += 1
            
            self.logger.debug(
                f"Message sent from {message.sender} to {message.recipient}: {message.type.value}"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            self.stats["messages_failed"] += 1
            return False
    
    async def broadcast_message(self, message: Message) -> int:
        """Broadcast a message to all subscribers of its type."""
        subscribers = self.subscribers.get(message.type, [])
        successful_sends = 0
        
        for subscriber in subscribers:
            if subscriber != message.sender:  # Don't send to sender
                message_copy = Message(
                    id=f"{message.id}_{subscriber}",
                    type=message.type,
                    sender=message.sender,
                    recipient=subscriber,
                    content=message.content,
                    priority=message.priority,
                    timestamp=message.timestamp,
                    correlation_id=message.correlation_id
                )
                
                if await self.send_message(message_copy):
                    successful_sends += 1
        
        return successful_sends
    
    async def receive_message(self, agent_id: str, timeout: Optional[float] = None) -> Optional[Message]:
        """Receive a message for a specific agent."""
        if agent_id not in self.message_queues:
            return None
        
        try:
            if timeout:
                message = await asyncio.wait_for(
                    self.message_queues[agent_id].get(),
                    timeout=timeout
                )
            else:
                message = await self.message_queues[agent_id].get()
            
            self.stats["messages_received"] += 1
            
            # Call message handler if registered
            if agent_id in self.message_handlers:
                try:
                    await self.message_handlers[agent_id](message)
                except Exception as e:
                    self.logger.error(f"Error in message handler for {agent_id}: {e}")
            
            return message
            
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            self.logger.error(f"Failed to receive message for {agent_id}: {e}")
            return None
    
    def get_queue_size(self, agent_id: str) -> int:
        """Get the size of an agent's message queue."""
        if agent_id in self.message_queues:
            return self.message_queues[agent_id].qsize()
        return 0
    
    def get_pending_messages(self, agent_id: str) -> int:
        """Get the number of pending messages for an agent."""
        return self.get_queue_size(agent_id)
    
    async def send_task_request(
        self,
        sender: str,
        recipient: str,
        task_description: str,
        parameters: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> str:
        """Send a task request message."""
        message_id = f"task_req_{datetime.now().timestamp()}"
        
        message = Message(
            id=message_id,
            type=MessageType.TASK_REQUEST,
            sender=sender,
            recipient=recipient,
            content={
                "task_description": task_description,
                "parameters": parameters
            },
            priority=MessagePriority.HIGH,
            correlation_id=correlation_id
        )
        
        await self.send_message(message)
        return message_id
    
    async def send_task_response(
        self,
        sender: str,
        recipient: str,
        task_result: Any,
        success: bool,
        correlation_id: Optional[str] = None
    ) -> str:
        """Send a task response message."""
        message_id = f"task_resp_{datetime.now().timestamp()}"
        
        message = Message(
            id=message_id,
            type=MessageType.TASK_RESPONSE,
            sender=sender,
            recipient=recipient,
            content={
                "result": task_result,
                "success": success
            },
            priority=MessagePriority.HIGH,
            correlation_id=correlation_id
        )
        
        await self.send_message(message)
        return message_id
    
    async def send_agent_status(
        self,
        sender: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Send agent status update."""
        message = Message(
            id=f"status_{datetime.now().timestamp()}",
            type=MessageType.AGENT_STATUS,
            sender=sender,
            recipient="system",
            content={
                "status": status,
                "metadata": metadata or {}
            },
            priority=MessagePriority.NORMAL
        )
        
        await self.broadcast_message(message)
    
    async def send_system_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        sender: str = "system"
    ) -> None:
        """Send system event notification."""
        message = Message(
            id=f"event_{datetime.now().timestamp()}",
            type=MessageType.SYSTEM_EVENT,
            sender=sender,
            recipient="all",
            content={
                "event_type": event_type,
                "event_data": event_data
            },
            priority=MessagePriority.NORMAL
        )
        
        await self.broadcast_message(message)
    
    def get_message_history(
        self,
        agent_id: Optional[str] = None,
        message_type: Optional[MessageType] = None,
        limit: int = 100
    ) -> List[Message]:
        """Get message history with optional filtering."""
        filtered_messages = self.message_history
        
        if agent_id:
            filtered_messages = [
                msg for msg in filtered_messages
                if msg.sender == agent_id or msg.recipient == agent_id
            ]
        
        if message_type:
            filtered_messages = [
                msg for msg in filtered_messages
                if msg.type == message_type
            ]
        
        # Return most recent messages
        return filtered_messages[-limit:]
    
    def get_communication_stats(self) -> Dict[str, Any]:
        """Get communication statistics."""
        return {
            **self.stats,
            "active_agents": len([
                agent_id for agent_id, active in self.active_connections.items()
                if active
            ]),
            "total_subscribers": sum(len(subs) for subs in self.subscribers.values()),
            "message_history_size": len(self.message_history)
        }
    
    def _add_to_history(self, message: Message) -> None:
        """Add message to history with size limit."""
        self.message_history.append(message)
        
        # Limit history size
        if len(self.message_history) > self.max_history_size:
            self.message_history = self.message_history[-self.max_history_size:]
    
    async def start_message_processor(self, agent_id: str) -> None:
        """Start message processing loop for an agent."""
        self.logger.info(f"Starting message processor for {agent_id}")
        
        while self.active_connections.get(agent_id, False):
            try:
                message = await self.receive_message(agent_id, timeout=1.0)
                if message:
                    self.logger.debug(f"Processed message for {agent_id}: {message.type.value}")
            except Exception as e:
                self.logger.error(f"Error in message processor for {agent_id}: {e}")
                await asyncio.sleep(1.0)
    
    async def stop_message_processor(self, agent_id: str) -> None:
        """Stop message processing for an agent."""
        self.active_connections[agent_id] = False
        self.logger.info(f"Stopped message processor for {agent_id}")
    
    def cleanup(self) -> None:
        """Cleanup communication manager resources."""
        for agent_id in list(self.active_connections.keys()):
            self.unregister_agent(agent_id)
        
        self.message_history.clear()
        self.logger.info("Communication manager cleanup complete")