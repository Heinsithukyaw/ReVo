"""
Unified WebSocket Service for reVoAgent
Consolidates all WebSocket functionality into a single robust service
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Set, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
import structlog

logger = structlog.get_logger(__name__)

class MessageType(Enum):
    """WebSocket message types"""
    # Connection management
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    HEARTBEAT = "heartbeat"
    
    # Chat and communication
    CHAT_MESSAGE = "chat_message"
    AGENT_RESPONSE = "agent_response"
    SYSTEM_MESSAGE = "system_message"
    
    # Agent coordination
    AGENT_STATUS = "agent_status"
    AGENT_COLLABORATION = "agent_collaboration"
    TASK_UPDATE = "task_update"
    
    # Memory and context
    MEMORY_UPDATE = "memory_update"
    CONTEXT_SYNC = "context_sync"
    
    # Real-time updates
    PROGRESS_UPDATE = "progress_update"
    ERROR_NOTIFICATION = "error_notification"
    
    # Room management
    JOIN_ROOM = "join_room"
    LEAVE_ROOM = "leave_room"
    ROOM_UPDATE = "room_update"

@dataclass
class WebSocketMessage:
    """Standardized WebSocket message format"""
    type: MessageType
    data: Dict[str, Any]
    timestamp: float
    message_id: str
    user_id: Optional[str] = None
    room_id: Optional[str] = None
    agent_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp,
            "message_id": self.message_id,
            "user_id": self.user_id,
            "room_id": self.room_id,
            "agent_id": self.agent_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebSocketMessage':
        return cls(
            type=MessageType(data["type"]),
            data=data["data"],
            timestamp=data["timestamp"],
            message_id=data["message_id"],
            user_id=data.get("user_id"),
            room_id=data.get("room_id"),
            agent_id=data.get("agent_id")
        )

@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection"""
    websocket: WebSocket
    user_id: str
    session_id: str
    rooms: Set[str]
    connected_at: float
    last_heartbeat: float
    metadata: Dict[str, Any]

class WebSocketRoom:
    """Manages a WebSocket room for group communication"""
    
    def __init__(self, room_id: str, name: str = None):
        self.room_id = room_id
        self.name = name or room_id
        self.connections: Set[str] = set()
        self.created_at = time.time()
        self.metadata: Dict[str, Any] = {}
    
    def add_connection(self, connection_id: str):
        self.connections.add(connection_id)
    
    def remove_connection(self, connection_id: str):
        self.connections.discard(connection_id)
    
    def is_empty(self) -> bool:
        return len(self.connections) == 0

class UnifiedWebSocketService:
    """
    Unified WebSocket service that consolidates all WebSocket functionality
    """
    
    def __init__(self):
        self.connections: Dict[str, ConnectionInfo] = {}
        self.rooms: Dict[str, WebSocketRoom] = {}
        self.message_handlers: Dict[MessageType, List[Callable]] = {}
        self.heartbeat_interval = 30  # seconds
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "rooms_created": 0
        }
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default message handlers"""
        self.register_handler(MessageType.HEARTBEAT, self._handle_heartbeat)
        self.register_handler(MessageType.JOIN_ROOM, self._handle_join_room)
        self.register_handler(MessageType.LEAVE_ROOM, self._handle_leave_room)
    
    def register_handler(self, message_type: MessageType, handler: Callable):
        """Register a message handler for a specific message type"""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)
        logger.info(f"Registered handler for {message_type.value}")
    
    async def connect(self, websocket: WebSocket, user_id: str, session_id: str = None) -> str:
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        connection_id = str(uuid.uuid4())
        session_id = session_id or str(uuid.uuid4())
        
        connection_info = ConnectionInfo(
            websocket=websocket,
            user_id=user_id,
            session_id=session_id,
            rooms=set(),
            connected_at=time.time(),
            last_heartbeat=time.time(),
            metadata={}
        )
        
        self.connections[connection_id] = connection_info
        self.stats["total_connections"] += 1
        self.stats["active_connections"] += 1
        
        # Start heartbeat task if not running
        if self.heartbeat_task is None or self.heartbeat_task.done():
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        logger.info(f"WebSocket connected: {connection_id} (user: {user_id})")
        
        # Send connection confirmation
        await self.send_to_connection(connection_id, WebSocketMessage(
            type=MessageType.CONNECT,
            data={"connection_id": connection_id, "session_id": session_id},
            timestamp=time.time(),
            message_id=str(uuid.uuid4()),
            user_id=user_id
        ))
        
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """Handle WebSocket disconnection"""
        if connection_id not in self.connections:
            return
        
        connection_info = self.connections[connection_id]
        
        # Leave all rooms
        for room_id in list(connection_info.rooms):
            await self._leave_room(connection_id, room_id)
        
        # Remove connection
        del self.connections[connection_id]
        self.stats["active_connections"] -= 1
        
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_to_connection(self, connection_id: str, message: WebSocketMessage):
        """Send a message to a specific connection"""
        if connection_id not in self.connections:
            logger.warning(f"Connection not found: {connection_id}")
            return False
        
        connection_info = self.connections[connection_id]
        
        try:
            if connection_info.websocket.client_state == WebSocketState.CONNECTED:
                await connection_info.websocket.send_text(json.dumps(message.to_dict()))
                self.stats["messages_sent"] += 1
                return True
            else:
                logger.warning(f"Connection not in connected state: {connection_id}")
                await self.disconnect(connection_id)
                return False
        except Exception as e:
            logger.error(f"Error sending message to {connection_id}: {e}")
            await self.disconnect(connection_id)
            return False
    
    async def send_to_user(self, user_id: str, message: WebSocketMessage):
        """Send a message to all connections of a specific user"""
        sent_count = 0
        for connection_id, connection_info in self.connections.items():
            if connection_info.user_id == user_id:
                if await self.send_to_connection(connection_id, message):
                    sent_count += 1
        return sent_count
    
    async def send_to_room(self, room_id: str, message: WebSocketMessage, exclude_connection: str = None):
        """Send a message to all connections in a room"""
        if room_id not in self.rooms:
            logger.warning(f"Room not found: {room_id}")
            return 0
        
        room = self.rooms[room_id]
        sent_count = 0
        
        for connection_id in list(room.connections):
            if connection_id != exclude_connection:
                if await self.send_to_connection(connection_id, message):
                    sent_count += 1
        
        return sent_count
    
    async def broadcast(self, message: WebSocketMessage, exclude_connection: str = None):
        """Broadcast a message to all connections"""
        sent_count = 0
        for connection_id in list(self.connections.keys()):
            if connection_id != exclude_connection:
                if await self.send_to_connection(connection_id, message):
                    sent_count += 1
        return sent_count
    
    async def handle_message(self, connection_id: str, raw_message: str):
        """Handle incoming WebSocket message"""
        try:
            message_data = json.loads(raw_message)
            message = WebSocketMessage.from_dict(message_data)
            self.stats["messages_received"] += 1
            
            # Update last heartbeat
            if connection_id in self.connections:
                self.connections[connection_id].last_heartbeat = time.time()
            
            # Call registered handlers
            if message.type in self.message_handlers:
                for handler in self.message_handlers[message.type]:
                    try:
                        await handler(connection_id, message)
                    except Exception as e:
                        logger.error(f"Error in message handler: {e}")
            else:
                logger.warning(f"No handler for message type: {message.type.value}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON message from {connection_id}: {e}")
            await self.send_error(connection_id, "Invalid JSON format")
        except Exception as e:
            logger.error(f"Error handling message from {connection_id}: {e}")
            await self.send_error(connection_id, "Message processing error")
    
    async def send_error(self, connection_id: str, error_message: str):
        """Send an error message to a connection"""
        error_msg = WebSocketMessage(
            type=MessageType.ERROR_NOTIFICATION,
            data={"error": error_message},
            timestamp=time.time(),
            message_id=str(uuid.uuid4())
        )
        await self.send_to_connection(connection_id, error_msg)
    
    async def create_room(self, room_id: str, name: str = None) -> WebSocketRoom:
        """Create a new room"""
        if room_id in self.rooms:
            return self.rooms[room_id]
        
        room = WebSocketRoom(room_id, name)
        self.rooms[room_id] = room
        self.stats["rooms_created"] += 1
        
        logger.info(f"Created room: {room_id}")
        return room
    
    async def _join_room(self, connection_id: str, room_id: str):
        """Internal method to join a room"""
        if connection_id not in self.connections:
            return False
        
        # Create room if it doesn't exist
        if room_id not in self.rooms:
            await self.create_room(room_id)
        
        room = self.rooms[room_id]
        connection_info = self.connections[connection_id]
        
        room.add_connection(connection_id)
        connection_info.rooms.add(room_id)
        
        logger.info(f"Connection {connection_id} joined room {room_id}")
        
        # Notify room members
        notification = WebSocketMessage(
            type=MessageType.ROOM_UPDATE,
            data={
                "action": "user_joined",
                "room_id": room_id,
                "user_id": connection_info.user_id,
                "connection_count": len(room.connections)
            },
            timestamp=time.time(),
            message_id=str(uuid.uuid4()),
            room_id=room_id
        )
        await self.send_to_room(room_id, notification, exclude_connection=connection_id)
        
        return True
    
    async def _leave_room(self, connection_id: str, room_id: str):
        """Internal method to leave a room"""
        if connection_id not in self.connections or room_id not in self.rooms:
            return False
        
        room = self.rooms[room_id]
        connection_info = self.connections[connection_id]
        
        room.remove_connection(connection_id)
        connection_info.rooms.discard(room_id)
        
        logger.info(f"Connection {connection_id} left room {room_id}")
        
        # Notify room members
        notification = WebSocketMessage(
            type=MessageType.ROOM_UPDATE,
            data={
                "action": "user_left",
                "room_id": room_id,
                "user_id": connection_info.user_id,
                "connection_count": len(room.connections)
            },
            timestamp=time.time(),
            message_id=str(uuid.uuid4()),
            room_id=room_id
        )
        await self.send_to_room(room_id, notification)
        
        # Clean up empty room
        if room.is_empty():
            del self.rooms[room_id]
            logger.info(f"Deleted empty room: {room_id}")
        
        return True
    
    async def _handle_heartbeat(self, connection_id: str, message: WebSocketMessage):
        """Handle heartbeat message"""
        response = WebSocketMessage(
            type=MessageType.HEARTBEAT,
            data={"pong": True, "server_time": time.time()},
            timestamp=time.time(),
            message_id=str(uuid.uuid4())
        )
        await self.send_to_connection(connection_id, response)
    
    async def _handle_join_room(self, connection_id: str, message: WebSocketMessage):
        """Handle join room message"""
        room_id = message.data.get("room_id")
        if room_id:
            success = await self._join_room(connection_id, room_id)
            response = WebSocketMessage(
                type=MessageType.JOIN_ROOM,
                data={"success": success, "room_id": room_id},
                timestamp=time.time(),
                message_id=str(uuid.uuid4()),
                room_id=room_id if success else None
            )
            await self.send_to_connection(connection_id, response)
    
    async def _handle_leave_room(self, connection_id: str, message: WebSocketMessage):
        """Handle leave room message"""
        room_id = message.data.get("room_id")
        if room_id:
            success = await self._leave_room(connection_id, room_id)
            response = WebSocketMessage(
                type=MessageType.LEAVE_ROOM,
                data={"success": success, "room_id": room_id},
                timestamp=time.time(),
                message_id=str(uuid.uuid4())
            )
            await self.send_to_connection(connection_id, response)
    
    async def _heartbeat_loop(self):
        """Background task to check connection health"""
        while True:
            try:
                current_time = time.time()
                dead_connections = []
                
                for connection_id, connection_info in self.connections.items():
                    if current_time - connection_info.last_heartbeat > self.heartbeat_interval * 2:
                        dead_connections.append(connection_id)
                
                # Clean up dead connections
                for connection_id in dead_connections:
                    logger.info(f"Removing dead connection: {connection_id}")
                    await self.disconnect(connection_id)
                
                await asyncio.sleep(self.heartbeat_interval)
                
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(5)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            **self.stats,
            "active_rooms": len(self.rooms),
            "handlers_registered": sum(len(handlers) for handlers in self.message_handlers.values())
        }
    
    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a connection"""
        if connection_id not in self.connections:
            return None
        
        connection_info = self.connections[connection_id]
        return {
            "connection_id": connection_id,
            "user_id": connection_info.user_id,
            "session_id": connection_info.session_id,
            "rooms": list(connection_info.rooms),
            "connected_at": connection_info.connected_at,
            "last_heartbeat": connection_info.last_heartbeat,
            "metadata": connection_info.metadata
        }
    
    def get_room_info(self, room_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a room"""
        if room_id not in self.rooms:
            return None
        
        room = self.rooms[room_id]
        return {
            "room_id": room.room_id,
            "name": room.name,
            "connection_count": len(room.connections),
            "connections": list(room.connections),
            "created_at": room.created_at,
            "metadata": room.metadata
        }

# Global WebSocket service instance
websocket_service = UnifiedWebSocketService()

# Convenience functions for external use
async def connect_websocket(websocket: WebSocket, user_id: str, session_id: str = None) -> str:
    """Connect a WebSocket"""
    return await websocket_service.connect(websocket, user_id, session_id)

async def disconnect_websocket(connection_id: str):
    """Disconnect a WebSocket"""
    await websocket_service.disconnect(connection_id)

async def handle_websocket_message(connection_id: str, message: str):
    """Handle a WebSocket message"""
    await websocket_service.handle_message(connection_id, message)

def register_message_handler(message_type: MessageType, handler: Callable):
    """Register a message handler"""
    websocket_service.register_handler(message_type, handler)

async def send_to_user(user_id: str, message_type: MessageType, data: Dict[str, Any]):
    """Send a message to a user"""
    message = WebSocketMessage(
        type=message_type,
        data=data,
        timestamp=time.time(),
        message_id=str(uuid.uuid4()),
        user_id=user_id
    )
    return await websocket_service.send_to_user(user_id, message)

async def send_to_room(room_id: str, message_type: MessageType, data: Dict[str, Any]):
    """Send a message to a room"""
    message = WebSocketMessage(
        type=message_type,
        data=data,
        timestamp=time.time(),
        message_id=str(uuid.uuid4()),
        room_id=room_id
    )
    return await websocket_service.send_to_room(room_id, message)

async def broadcast_message(message_type: MessageType, data: Dict[str, Any]):
    """Broadcast a message to all connections"""
    message = WebSocketMessage(
        type=message_type,
        data=data,
        timestamp=time.time(),
        message_id=str(uuid.uuid4())
    )
    return await websocket_service.broadcast(message)