"""
🔄 Enterprise Real-time Manager - Complete WebSocket Infrastructure
Provides comprehensive real-time communication with WebSocket, events, and live updates.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, asdict
from collections import defaultdict

import websockets
from websockets.server import WebSocketServerProtocol
import structlog

logger = structlog.get_logger(__name__)

@dataclass
class WebSocketConnection:
    """WebSocket connection information"""
    connection_id: str
    websocket: WebSocketServerProtocol
    user_id: Optional[str] = None
    subscriptions: Set[str] = None
    connected_at: datetime = None
    last_activity: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.subscriptions is None:
            self.subscriptions = set()
        if self.connected_at is None:
            self.connected_at = datetime.utcnow()
        if self.last_activity is None:
            self.last_activity = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class RealtimeEvent:
    """Real-time event data"""
    event_id: str
    event_type: str
    channel: str
    data: Dict[str, Any]
    timestamp: datetime
    sender_id: Optional[str] = None
    target_users: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.target_users is None:
            self.target_users = []
        if self.metadata is None:
            self.metadata = {}

class EventBus:
    """Event bus for real-time event distribution"""
    
    def __init__(self):
        self.subscribers = defaultdict(list)
        self.event_history = []
        self.max_history = 1000
    
    def subscribe(self, channel: str, callback: Callable):
        """Subscribe to a channel"""
        self.subscribers[channel].append(callback)
        logger.debug(f"Subscribed to channel: {channel}")
    
    def unsubscribe(self, channel: str, callback: Callable):
        """Unsubscribe from a channel"""
        if callback in self.subscribers[channel]:
            self.subscribers[channel].remove(callback)
            logger.debug(f"Unsubscribed from channel: {channel}")
    
    async def publish(self, event: RealtimeEvent):
        """Publish an event to subscribers"""
        # Add to history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
        
        # Notify subscribers
        for callback in self.subscribers[event.channel]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")
        
        # Also notify wildcard subscribers
        for callback in self.subscribers["*"]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Error in wildcard event callback: {e}")
    
    def get_recent_events(self, channel: str = None, limit: int = 50) -> List[RealtimeEvent]:
        """Get recent events"""
        events = self.event_history
        
        if channel:
            events = [e for e in events if e.channel == channel]
        
        return events[-limit:]

class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.user_connections: Dict[str, Set[str]] = defaultdict(set)
        self.channel_subscriptions: Dict[str, Set[str]] = defaultdict(set)
    
    async def connect(self, websocket: WebSocketServerProtocol, user_id: str = None) -> str:
        """Register a new WebSocket connection"""
        connection_id = str(uuid.uuid4())
        
        connection = WebSocketConnection(
            connection_id=connection_id,
            websocket=websocket,
            user_id=user_id
        )
        
        self.connections[connection_id] = connection
        
        if user_id:
            self.user_connections[user_id].add(connection_id)
        
        logger.info(f"🔗 WebSocket connected: {connection_id} (user: {user_id})")
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """Unregister a WebSocket connection"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            
            # Remove from user connections
            if connection.user_id:
                self.user_connections[connection.user_id].discard(connection_id)
                if not self.user_connections[connection.user_id]:
                    del self.user_connections[connection.user_id]
            
            # Remove from channel subscriptions
            for channel in connection.subscriptions:
                self.channel_subscriptions[channel].discard(connection_id)
                if not self.channel_subscriptions[channel]:
                    del self.channel_subscriptions[channel]
            
            del self.connections[connection_id]
            
            logger.info(f"🔗 WebSocket disconnected: {connection_id}")
    
    async def subscribe_to_channel(self, connection_id: str, channel: str):
        """Subscribe connection to a channel"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            connection.subscriptions.add(channel)
            self.channel_subscriptions[channel].add(connection_id)
            
            logger.debug(f"📡 Connection {connection_id} subscribed to {channel}")
    
    async def unsubscribe_from_channel(self, connection_id: str, channel: str):
        """Unsubscribe connection from a channel"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            connection.subscriptions.discard(channel)
            self.channel_subscriptions[channel].discard(connection_id)
            
            if not self.channel_subscriptions[channel]:
                del self.channel_subscriptions[channel]
            
            logger.debug(f"📡 Connection {connection_id} unsubscribed from {channel}")
    
    async def send_to_connection(self, connection_id: str, message: Dict[str, Any]):
        """Send message to specific connection"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            try:
                await connection.websocket.send(json.dumps(message))
                connection.last_activity = datetime.utcnow()
                return True
            except Exception as e:
                logger.error(f"Failed to send to connection {connection_id}: {e}")
                await self.disconnect(connection_id)
                return False
        return False
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send message to all connections of a user"""
        if user_id in self.user_connections:
            connection_ids = list(self.user_connections[user_id])
            results = []
            
            for connection_id in connection_ids:
                result = await self.send_to_connection(connection_id, message)
                results.append(result)
            
            return any(results)
        return False
    
    async def send_to_channel(self, channel: str, message: Dict[str, Any], exclude_connection: str = None):
        """Send message to all connections subscribed to a channel"""
        if channel in self.channel_subscriptions:
            connection_ids = list(self.channel_subscriptions[channel])
            
            if exclude_connection:
                connection_ids = [cid for cid in connection_ids if cid != exclude_connection]
            
            results = []
            for connection_id in connection_ids:
                result = await self.send_to_connection(connection_id, message)
                results.append(result)
            
            return any(results)
        return False
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "total_connections": len(self.connections),
            "authenticated_connections": len([c for c in self.connections.values() if c.user_id]),
            "unique_users": len(self.user_connections),
            "active_channels": len(self.channel_subscriptions),
            "connections_by_channel": {
                channel: len(connections) 
                for channel, connections in self.channel_subscriptions.items()
            }
        }

class EnterpriseRealtimeManager:
    """
    🔄 Enterprise Real-time Manager
    
    Provides comprehensive real-time communication with:
    - WebSocket server and connection management
    - Event bus for real-time event distribution
    - Channel-based subscriptions and broadcasting
    - User-specific messaging and notifications
    - Real-time collaboration features
    - Live system monitoring and updates
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.host = self.config.get("host", "localhost")
        self.port = self.config.get("port", 8001)
        
        self.connection_manager = ConnectionManager()
        self.event_bus = EventBus()
        self.server = None
        self.running = False
        
        # Set up event handlers
        self._setup_event_handlers()
        
        logger.info("🔄 Enterprise Real-time Manager initializing...")
    
    async def initialize(self):
        """Initialize real-time system"""
        try:
            # Start WebSocket server
            await self.start_server()
            
            logger.info("✅ Enterprise Real-time Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize real-time manager: {e}")
            raise
    
    def _setup_event_handlers(self):
        """Set up default event handlers"""
        
        async def handle_system_event(event: RealtimeEvent):
            """Handle system events"""
            await self.connection_manager.send_to_channel("system", {
                "type": "system_event",
                "event": {
                    "id": event.event_id,
                    "type": event.event_type,
                    "data": event.data,
                    "timestamp": event.timestamp.isoformat()
                }
            })
        
        async def handle_user_event(event: RealtimeEvent):
            """Handle user-specific events"""
            if event.target_users:
                for user_id in event.target_users:
                    await self.connection_manager.send_to_user(user_id, {
                        "type": "user_event",
                        "event": {
                            "id": event.event_id,
                            "type": event.event_type,
                            "data": event.data,
                            "timestamp": event.timestamp.isoformat()
                        }
                    })
        
        # Subscribe to event channels
        self.event_bus.subscribe("system", handle_system_event)
        self.event_bus.subscribe("user", handle_user_event)
    
    async def start_server(self):
        """Start WebSocket server"""
        try:
            self.server = await websockets.serve(
                self._handle_websocket_connection,
                self.host,
                self.port
            )
            self.running = True
            
            logger.info(f"🔄 WebSocket server started on {self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            raise
    
    async def stop_server(self):
        """Stop WebSocket server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.running = False
            
            logger.info("🔄 WebSocket server stopped")
    
    async def _handle_websocket_connection(self, websocket: WebSocketServerProtocol, path: str):
        """Handle new WebSocket connection"""
        connection_id = None
        
        try:
            # Register connection
            connection_id = await self.connection_manager.connect(websocket)
            
            # Send welcome message
            await self.connection_manager.send_to_connection(connection_id, {
                "type": "welcome",
                "connection_id": connection_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Handle messages
            async for message in websocket:
                try:
                    await self._handle_websocket_message(connection_id, json.loads(message))
                except json.JSONDecodeError:
                    await self.connection_manager.send_to_connection(connection_id, {
                        "type": "error",
                        "message": "Invalid JSON format"
                    })
                except Exception as e:
                    logger.error(f"Error handling WebSocket message: {e}")
                    await self.connection_manager.send_to_connection(connection_id, {
                        "type": "error",
                        "message": "Internal server error"
                    })
        
        except websockets.exceptions.ConnectionClosed:
            logger.debug(f"WebSocket connection closed: {connection_id}")
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
        finally:
            if connection_id:
                await self.connection_manager.disconnect(connection_id)
    
    async def _handle_websocket_message(self, connection_id: str, message: Dict[str, Any]):
        """Handle WebSocket message"""
        message_type = message.get("type")
        
        if message_type == "authenticate":
            await self._handle_authenticate(connection_id, message)
        elif message_type == "subscribe":
            await self._handle_subscribe(connection_id, message)
        elif message_type == "unsubscribe":
            await self._handle_unsubscribe(connection_id, message)
        elif message_type == "send_message":
            await self._handle_send_message(connection_id, message)
        elif message_type == "ping":
            await self._handle_ping(connection_id, message)
        else:
            await self.connection_manager.send_to_connection(connection_id, {
                "type": "error",
                "message": f"Unknown message type: {message_type}"
            })
    
    async def _handle_authenticate(self, connection_id: str, message: Dict[str, Any]):
        """Handle authentication message"""
        user_id = message.get("user_id")
        token = message.get("token")
        
        # TODO: Verify token with security manager
        # For now, accept any user_id
        
        if connection_id in self.connection_manager.connections:
            connection = self.connection_manager.connections[connection_id]
            connection.user_id = user_id
            
            if user_id:
                self.connection_manager.user_connections[user_id].add(connection_id)
            
            await self.connection_manager.send_to_connection(connection_id, {
                "type": "authenticated",
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(f"🔐 WebSocket authenticated: {connection_id} as {user_id}")
    
    async def _handle_subscribe(self, connection_id: str, message: Dict[str, Any]):
        """Handle channel subscription"""
        channel = message.get("channel")
        
        if channel:
            await self.connection_manager.subscribe_to_channel(connection_id, channel)
            
            await self.connection_manager.send_to_connection(connection_id, {
                "type": "subscribed",
                "channel": channel,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def _handle_unsubscribe(self, connection_id: str, message: Dict[str, Any]):
        """Handle channel unsubscription"""
        channel = message.get("channel")
        
        if channel:
            await self.connection_manager.unsubscribe_from_channel(connection_id, channel)
            
            await self.connection_manager.send_to_connection(connection_id, {
                "type": "unsubscribed",
                "channel": channel,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def _handle_send_message(self, connection_id: str, message: Dict[str, Any]):
        """Handle message sending"""
        channel = message.get("channel")
        data = message.get("data", {})
        
        if channel:
            # Create and publish event
            event = RealtimeEvent(
                event_id=str(uuid.uuid4()),
                event_type="message",
                channel=channel,
                data=data,
                timestamp=datetime.utcnow(),
                sender_id=self.connection_manager.connections[connection_id].user_id
            )
            
            await self.event_bus.publish(event)
            
            # Send to channel (excluding sender)
            await self.connection_manager.send_to_channel(channel, {
                "type": "message",
                "channel": channel,
                "data": data,
                "sender_id": event.sender_id,
                "timestamp": event.timestamp.isoformat()
            }, exclude_connection=connection_id)
    
    async def _handle_ping(self, connection_id: str, message: Dict[str, Any]):
        """Handle ping message"""
        await self.connection_manager.send_to_connection(connection_id, {
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    # Public API methods
    async def publish_event(self, event_type: str, channel: str, data: Dict[str, Any], 
                           sender_id: str = None, target_users: List[str] = None):
        """Publish an event to the event bus"""
        event = RealtimeEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            channel=channel,
            data=data,
            timestamp=datetime.utcnow(),
            sender_id=sender_id,
            target_users=target_users or []
        )
        
        await self.event_bus.publish(event)
        return event.event_id
    
    async def send_notification(self, user_id: str, notification: Dict[str, Any]):
        """Send notification to specific user"""
        await self.connection_manager.send_to_user(user_id, {
            "type": "notification",
            "notification": notification,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def broadcast_system_message(self, message: str, level: str = "info"):
        """Broadcast system message to all connected users"""
        await self.connection_manager.send_to_channel("system", {
            "type": "system_message",
            "message": message,
            "level": level,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def send_workflow_update(self, workflow_id: str, status: str, data: Dict[str, Any] = None):
        """Send workflow status update"""
        await self.publish_event(
            event_type="workflow_update",
            channel="workflows",
            data={
                "workflow_id": workflow_id,
                "status": status,
                "data": data or {}
            }
        )
    
    async def send_ai_generation_update(self, generation_id: str, status: str, 
                                       content: str = None, user_id: str = None):
        """Send AI generation update"""
        event_data = {
            "generation_id": generation_id,
            "status": status
        }
        
        if content:
            event_data["content"] = content
        
        if user_id:
            await self.publish_event(
                event_type="ai_generation_update",
                channel="user",
                data=event_data,
                target_users=[user_id]
            )
        else:
            await self.publish_event(
                event_type="ai_generation_update",
                channel="ai_generations",
                data=event_data
            )
    
    def get_realtime_stats(self) -> Dict[str, Any]:
        """Get real-time system statistics"""
        connection_stats = self.connection_manager.get_connection_stats()
        
        return {
            "server_running": self.running,
            "server_address": f"{self.host}:{self.port}",
            "connections": connection_stats,
            "recent_events": len(self.event_bus.get_recent_events()),
            "event_channels": len(self.event_bus.subscribers),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific connection"""
        if connection_id in self.connection_manager.connections:
            connection = self.connection_manager.connections[connection_id]
            return {
                "connection_id": connection.connection_id,
                "user_id": connection.user_id,
                "connected_at": connection.connected_at.isoformat(),
                "last_activity": connection.last_activity.isoformat(),
                "subscriptions": list(connection.subscriptions),
                "metadata": connection.metadata
            }
        return None

# Example usage
async def main():
    """Example usage of Enterprise Real-time Manager"""
    realtime_manager = EnterpriseRealtimeManager({
        "host": "localhost",
        "port": 8001
    })
    
    await realtime_manager.initialize()
    
    # Simulate some events
    await asyncio.sleep(1)
    
    await realtime_manager.publish_event(
        event_type="test_event",
        channel="system",
        data={"message": "Hello, real-time world!"}
    )
    
    await realtime_manager.broadcast_system_message("System is running smoothly")
    
    # Get stats
    stats = realtime_manager.get_realtime_stats()
    print(f"Real-time stats: {json.dumps(stats, indent=2)}")
    
    # Keep running for a while
    print("Real-time server running... Press Ctrl+C to stop")
    try:
        await asyncio.sleep(60)
    except KeyboardInterrupt:
        pass
    finally:
        await realtime_manager.stop_server()

if __name__ == "__main__":
    asyncio.run(main())