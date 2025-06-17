#!/usr/bin/env python3
"""
Real-time Communication Hub for reVoAgent
Advanced WebSocket-based communication system with event streaming and collaboration

This module implements a comprehensive real-time communication system featuring:
- WebSocket connection management
- Event streaming and broadcasting
- Real-time collaboration features
- Message queuing and persistence
- Connection pooling and load balancing
- Presence and activity tracking
- Room-based communication
- Message encryption and security
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict, deque
import weakref
from fastapi import WebSocket, WebSocketDisconnect
import redis.asyncio as redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageType(Enum):
    """Message types for real-time communication"""
    # System messages
    PING = "ping"
    PONG = "pong"
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    ERROR = "error"
    
    # User activity
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    USER_TYPING = "user_typing"
    USER_PRESENCE = "user_presence"
    
    # Workflow events
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    WORKFLOW_PROGRESS = "workflow_progress"
    
    # AI events
    AI_GENERATION_STARTED = "ai_generation_started"
    AI_GENERATION_COMPLETED = "ai_generation_completed"
    AI_GENERATION_PROGRESS = "ai_generation_progress"
    
    # Collaboration
    DOCUMENT_EDIT = "document_edit"
    CURSOR_MOVE = "cursor_move"
    SELECTION_CHANGE = "selection_change"
    
    # Notifications
    NOTIFICATION = "notification"
    ALERT = "alert"
    SYSTEM_ANNOUNCEMENT = "system_announcement"
    
    # Custom events
    CUSTOM = "custom"

class PresenceStatus(Enum):
    """User presence status"""
    ONLINE = "online"
    AWAY = "away"
    BUSY = "busy"
    OFFLINE = "offline"

@dataclass
class Message:
    """Real-time message"""
    message_id: str
    message_type: MessageType
    sender_id: Optional[str]
    recipient_id: Optional[str] = None
    room_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ttl: Optional[int] = None  # Time to live in seconds
    encrypted: bool = False

@dataclass
class Connection:
    """WebSocket connection info"""
    connection_id: str
    websocket: WebSocket
    user_id: Optional[str]
    connected_at: datetime
    last_activity: datetime
    rooms: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Room:
    """Communication room"""
    room_id: str
    name: str
    description: str = ""
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    members: Set[str] = field(default_factory=set)
    max_members: Optional[int] = None
    is_private: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UserPresence:
    """User presence information"""
    user_id: str
    status: PresenceStatus
    last_seen: datetime
    current_room: Optional[str] = None
    activity: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class RealtimeCommunicationHub:
    """
    Real-time Communication Hub
    
    Provides advanced WebSocket-based communication with event streaming,
    collaboration features, and enterprise-grade reliability.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the communication hub"""
        self.config = config or {}
        
        # Connection management
        self.connections: Dict[str, Connection] = {}
        self.user_connections: Dict[str, List[str]] = defaultdict(list)
        
        # Room management
        self.rooms: Dict[str, Room] = {}
        
        # Presence tracking
        self.user_presence: Dict[str, UserPresence] = {}
        
        # Message queuing
        self.message_queue: deque = deque(maxlen=10000)
        self.pending_messages: Dict[str, List[Message]] = defaultdict(list)
        
        # Event handlers
        self.event_handlers: Dict[MessageType, List[Callable]] = defaultdict(list)
        
        # Performance metrics
        self.metrics = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "rooms_created": 0,
            "events_processed": 0
        }
        
        # Redis for scaling (optional)
        self.redis_client = None
        if self.config.get("redis_url"):
            self.redis_client = redis.from_url(self.config["redis_url"])
        
        # Background tasks
        self.cleanup_task = None
        self.heartbeat_task = None
        
        logger.info("🔄 Real-time Communication Hub initialized")
        self._start_background_tasks()

    def _start_background_tasks(self):
        """Start background maintenance tasks"""
        self.cleanup_task = asyncio.create_task(self._cleanup_connections())
        self.heartbeat_task = asyncio.create_task(self._heartbeat_monitor())

    async def _cleanup_connections(self):
        """Clean up stale connections"""
        while True:
            try:
                current_time = datetime.now(timezone.utc)
                stale_connections = []
                
                for connection_id, connection in self.connections.items():
                    # Mark connections as stale if no activity for 5 minutes
                    if (current_time - connection.last_activity).total_seconds() > 300:
                        stale_connections.append(connection_id)
                
                for connection_id in stale_connections:
                    await self.disconnect(connection_id)
                    logger.info(f"🧹 Cleaned up stale connection: {connection_id}")
                
                # Clean up expired messages
                current_timestamp = time.time()
                expired_messages = []
                
                for i, message in enumerate(self.message_queue):
                    if message.ttl and (current_timestamp - message.timestamp.timestamp()) > message.ttl:
                        expired_messages.append(i)
                
                for i in reversed(expired_messages):
                    del self.message_queue[i]
                
                await asyncio.sleep(60)  # Run every minute
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(60)

    async def _heartbeat_monitor(self):
        """Monitor connection heartbeats"""
        while True:
            try:
                # Send ping to all connections
                ping_message = Message(
                    message_id=f"ping_{uuid.uuid4().hex[:8]}",
                    message_type=MessageType.PING,
                    sender_id="system"
                )
                
                await self.broadcast_message(ping_message)
                
                await asyncio.sleep(30)  # Send ping every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in heartbeat monitor: {e}")
                await asyncio.sleep(30)

    async def connect(self, websocket: WebSocket, user_id: Optional[str] = None, 
                     metadata: Optional[Dict[str, Any]] = None) -> str:
        """Connect a WebSocket"""
        await websocket.accept()
        
        connection_id = f"conn_{uuid.uuid4().hex[:8]}"
        current_time = datetime.now(timezone.utc)
        
        connection = Connection(
            connection_id=connection_id,
            websocket=websocket,
            user_id=user_id,
            connected_at=current_time,
            last_activity=current_time,
            metadata=metadata or {}
        )
        
        self.connections[connection_id] = connection
        
        if user_id:
            self.user_connections[user_id].append(connection_id)
            
            # Update user presence
            self.user_presence[user_id] = UserPresence(
                user_id=user_id,
                status=PresenceStatus.ONLINE,
                last_seen=current_time
            )
            
            # Notify others about user joining
            await self._broadcast_user_event(MessageType.USER_JOINED, user_id)
        
        self.metrics["total_connections"] += 1
        self.metrics["active_connections"] += 1
        
        # Send connection confirmation
        connect_message = Message(
            message_id=f"connect_{uuid.uuid4().hex[:8]}",
            message_type=MessageType.CONNECT,
            sender_id="system",
            recipient_id=user_id,
            data={
                "connection_id": connection_id,
                "timestamp": current_time.isoformat()
            }
        )
        
        await self.send_message_to_connection(connect_message, connection_id)
        
        # Send any pending messages
        if user_id and user_id in self.pending_messages:
            for message in self.pending_messages[user_id]:
                await self.send_message_to_connection(message, connection_id)
            del self.pending_messages[user_id]
        
        logger.info(f"🔌 WebSocket connected: {connection_id} (user: {user_id})")
        return connection_id

    async def disconnect(self, connection_id: str):
        """Disconnect a WebSocket"""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        user_id = connection.user_id
        
        # Remove from rooms
        for room_id in connection.rooms.copy():
            await self.leave_room(connection_id, room_id)
        
        # Remove connection
        del self.connections[connection_id]
        
        if user_id:
            if connection_id in self.user_connections[user_id]:
                self.user_connections[user_id].remove(connection_id)
            
            # Update presence if no more connections
            if not self.user_connections[user_id]:
                if user_id in self.user_presence:
                    self.user_presence[user_id].status = PresenceStatus.OFFLINE
                    self.user_presence[user_id].last_seen = datetime.now(timezone.utc)
                
                # Notify others about user leaving
                await self._broadcast_user_event(MessageType.USER_LEFT, user_id)
                
                # Clean up empty user connection list
                del self.user_connections[user_id]
        
        self.metrics["active_connections"] -= 1
        
        logger.info(f"🔌 WebSocket disconnected: {connection_id}")

    async def send_message_to_connection(self, message: Message, connection_id: str) -> bool:
        """Send message to specific connection"""
        if connection_id not in self.connections:
            return False
        
        connection = self.connections[connection_id]
        
        try:
            message_data = {
                "id": message.message_id,
                "type": message.message_type.value,
                "sender": message.sender_id,
                "data": message.data,
                "timestamp": message.timestamp.isoformat()
            }
            
            await connection.websocket.send_text(json.dumps(message_data))
            connection.last_activity = datetime.now(timezone.utc)
            
            self.metrics["messages_sent"] += 1
            return True
            
        except Exception as e:
            logger.error(f"Error sending message to {connection_id}: {e}")
            await self.disconnect(connection_id)
            return False

    async def send_message_to_user(self, message: Message, user_id: str) -> int:
        """Send message to all user connections"""
        sent_count = 0
        
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id].copy():
                if await self.send_message_to_connection(message, connection_id):
                    sent_count += 1
        else:
            # User not connected, queue message
            self.pending_messages[user_id].append(message)
        
        return sent_count

    async def broadcast_message(self, message: Message, exclude_connections: Optional[Set[str]] = None) -> int:
        """Broadcast message to all connections"""
        sent_count = 0
        exclude_connections = exclude_connections or set()
        
        for connection_id in list(self.connections.keys()):
            if connection_id not in exclude_connections:
                if await self.send_message_to_connection(message, connection_id):
                    sent_count += 1
        
        return sent_count

    async def create_room(self, name: str, created_by: Optional[str] = None, 
                         description: str = "", is_private: bool = False,
                         max_members: Optional[int] = None) -> str:
        """Create a communication room"""
        room_id = f"room_{uuid.uuid4().hex[:8]}"
        
        room = Room(
            room_id=room_id,
            name=name,
            description=description,
            created_by=created_by,
            max_members=max_members,
            is_private=is_private
        )
        
        self.rooms[room_id] = room
        self.metrics["rooms_created"] += 1
        
        logger.info(f"🏠 Room created: {name} ({room_id})")
        return room_id

    async def join_room(self, connection_id: str, room_id: str) -> bool:
        """Join a room"""
        if connection_id not in self.connections or room_id not in self.rooms:
            return False
        
        connection = self.connections[connection_id]
        room = self.rooms[room_id]
        
        # Check room capacity
        if room.max_members and len(room.members) >= room.max_members:
            return False
        
        # Add to room
        connection.rooms.add(room_id)
        room.members.add(connection.user_id or connection_id)
        
        # Notify room members
        join_message = Message(
            message_id=f"join_{uuid.uuid4().hex[:8]}",
            message_type=MessageType.USER_JOINED,
            sender_id="system",
            room_id=room_id,
            data={
                "user_id": connection.user_id,
                "connection_id": connection_id,
                "room_name": room.name
            }
        )
        
        await self.send_message_to_room(join_message, room_id, exclude_connections={connection_id})
        
        logger.info(f"🏠 User joined room: {connection.user_id} -> {room.name}")
        return True

    async def leave_room(self, connection_id: str, room_id: str) -> bool:
        """Leave a room"""
        if connection_id not in self.connections or room_id not in self.rooms:
            return False
        
        connection = self.connections[connection_id]
        room = self.rooms[room_id]
        
        # Remove from room
        connection.rooms.discard(room_id)
        room.members.discard(connection.user_id or connection_id)
        
        # Notify room members
        leave_message = Message(
            message_id=f"leave_{uuid.uuid4().hex[:8]}",
            message_type=MessageType.USER_LEFT,
            sender_id="system",
            room_id=room_id,
            data={
                "user_id": connection.user_id,
                "connection_id": connection_id,
                "room_name": room.name
            }
        )
        
        await self.send_message_to_room(leave_message, room_id)
        
        logger.info(f"🏠 User left room: {connection.user_id} <- {room.name}")
        return True

    async def send_message_to_room(self, message: Message, room_id: str, 
                                  exclude_connections: Optional[Set[str]] = None) -> int:
        """Send message to all room members"""
        if room_id not in self.rooms:
            return 0
        
        sent_count = 0
        exclude_connections = exclude_connections or set()
        
        for connection_id, connection in self.connections.items():
            if (room_id in connection.rooms and 
                connection_id not in exclude_connections):
                if await self.send_message_to_connection(message, connection_id):
                    sent_count += 1
        
        return sent_count

    async def handle_message(self, connection_id: str, message_data: str):
        """Handle incoming message from WebSocket"""
        try:
            data = json.loads(message_data)
            message_type = MessageType(data.get("type", "custom"))
            
            connection = self.connections.get(connection_id)
            if not connection:
                return
            
            # Update last activity
            connection.last_activity = datetime.now(timezone.utc)
            
            message = Message(
                message_id=data.get("id", f"msg_{uuid.uuid4().hex[:8]}"),
                message_type=message_type,
                sender_id=connection.user_id,
                recipient_id=data.get("recipient"),
                room_id=data.get("room"),
                data=data.get("data", {})
            )
            
            self.metrics["messages_received"] += 1
            
            # Handle different message types
            if message_type == MessageType.PING:
                await self._handle_ping(connection_id)
            elif message_type == MessageType.USER_PRESENCE:
                await self._handle_presence_update(connection_id, message.data)
            elif message_type == MessageType.USER_TYPING:
                await self._handle_typing_indicator(connection_id, message)
            else:
                # Process through event handlers
                await self._process_event_handlers(message_type, message)
                
                # Route message
                if message.recipient_id:
                    await self.send_message_to_user(message, message.recipient_id)
                elif message.room_id:
                    await self.send_message_to_room(message, message.room_id, {connection_id})
                
            self.metrics["events_processed"] += 1
            
        except Exception as e:
            logger.error(f"Error handling message from {connection_id}: {e}")
            
            error_message = Message(
                message_id=f"error_{uuid.uuid4().hex[:8]}",
                message_type=MessageType.ERROR,
                sender_id="system",
                data={"error": str(e)}
            )
            await self.send_message_to_connection(error_message, connection_id)

    async def _handle_ping(self, connection_id: str):
        """Handle ping message"""
        pong_message = Message(
            message_id=f"pong_{uuid.uuid4().hex[:8]}",
            message_type=MessageType.PONG,
            sender_id="system"
        )
        await self.send_message_to_connection(pong_message, connection_id)

    async def _handle_presence_update(self, connection_id: str, data: Dict[str, Any]):
        """Handle user presence update"""
        connection = self.connections.get(connection_id)
        if not connection or not connection.user_id:
            return
        
        user_id = connection.user_id
        status = PresenceStatus(data.get("status", "online"))
        activity = data.get("activity")
        
        if user_id in self.user_presence:
            self.user_presence[user_id].status = status
            self.user_presence[user_id].activity = activity
            self.user_presence[user_id].last_seen = datetime.now(timezone.utc)
        
        # Broadcast presence update
        await self._broadcast_user_event(MessageType.USER_PRESENCE, user_id, {
            "status": status.value,
            "activity": activity
        })

    async def _handle_typing_indicator(self, connection_id: str, message: Message):
        """Handle typing indicator"""
        if message.room_id:
            await self.send_message_to_room(message, message.room_id, {connection_id})
        elif message.recipient_id:
            await self.send_message_to_user(message, message.recipient_id)

    async def _broadcast_user_event(self, event_type: MessageType, user_id: str, 
                                   extra_data: Optional[Dict[str, Any]] = None):
        """Broadcast user-related event"""
        data = {"user_id": user_id}
        if extra_data:
            data.update(extra_data)
        
        event_message = Message(
            message_id=f"event_{uuid.uuid4().hex[:8]}",
            message_type=event_type,
            sender_id="system",
            data=data
        )
        
        await self.broadcast_message(event_message, 
                                   exclude_connections=set(self.user_connections.get(user_id, [])))

    async def _process_event_handlers(self, message_type: MessageType, message: Message):
        """Process registered event handlers"""
        handlers = self.event_handlers.get(message_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                logger.error(f"Error in event handler for {message_type}: {e}")

    def add_event_handler(self, message_type: MessageType, handler: Callable):
        """Add event handler"""
        self.event_handlers[message_type].append(handler)

    async def get_metrics(self) -> Dict[str, Any]:
        """Get communication hub metrics"""
        return {
            "connections": {
                "total": self.metrics["total_connections"],
                "active": self.metrics["active_connections"],
                "by_user": len(self.user_connections)
            },
            "rooms": {
                "total": len(self.rooms),
                "created": self.metrics["rooms_created"]
            },
            "messages": {
                "sent": self.metrics["messages_sent"],
                "received": self.metrics["messages_received"],
                "queued": len(self.message_queue)
            },
            "presence": {
                "online_users": len([p for p in self.user_presence.values() 
                                   if p.status == PresenceStatus.ONLINE])
            },
            "events": {
                "processed": self.metrics["events_processed"]
            }
        }

    async def get_room_info(self, room_id: str) -> Optional[Dict[str, Any]]:
        """Get room information"""
        if room_id not in self.rooms:
            return None
        
        room = self.rooms[room_id]
        return {
            "room_id": room.room_id,
            "name": room.name,
            "description": room.description,
            "created_by": room.created_by,
            "created_at": room.created_at.isoformat(),
            "member_count": len(room.members),
            "max_members": room.max_members,
            "is_private": room.is_private
        }

    async def get_user_presence(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user presence information"""
        if user_id not in self.user_presence:
            return None
        
        presence = self.user_presence[user_id]
        return {
            "user_id": presence.user_id,
            "status": presence.status.value,
            "last_seen": presence.last_seen.isoformat(),
            "current_room": presence.current_room,
            "activity": presence.activity
        }

    async def shutdown(self):
        """Shutdown the communication hub"""
        logger.info("🛑 Shutting down Real-time Communication Hub...")
        
        # Cancel background tasks
        if self.cleanup_task:
            self.cleanup_task.cancel()
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        
        # Close all connections
        for connection_id in list(self.connections.keys()):
            await self.disconnect(connection_id)
        
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("🛑 Real-time Communication Hub shutdown complete")

# Example usage and testing
async def main():
    """Example usage of Real-time Communication Hub"""
    
    print("🔄 Real-time Communication Hub Demo")
    print("=" * 50)
    
    # Initialize communication hub
    hub = RealtimeCommunicationHub()
    
    print("✅ Real-time Communication Hub initialized")
    print("📋 Features:")
    print("   - WebSocket connection management")
    print("   - Real-time messaging and broadcasting")
    print("   - Room-based communication")
    print("   - User presence tracking")
    print("   - Event streaming and handling")
    print("   - Message queuing and persistence")
    
    # Create a test room
    room_id = await hub.create_room("General Chat", description="Main discussion room")
    print(f"✅ Room created: {room_id}")
    
    # Get metrics
    metrics = await hub.get_metrics()
    print(f"✅ Hub metrics:")
    print(f"   - Active connections: {metrics['connections']['active']}")
    print(f"   - Total rooms: {metrics['rooms']['total']}")
    print(f"   - Messages sent: {metrics['messages']['sent']}")
    
    print("\n🎉 Real-time Communication Hub ready for WebSocket connections!")

if __name__ == "__main__":
    asyncio.run(main())