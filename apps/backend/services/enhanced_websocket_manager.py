"""
Enhanced WebSocket Manager
Part of reVoAgent Next Phase Implementation
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Set, Any, Optional, List
from fastapi import WebSocket, WebSocketDisconnect
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class MessageType(Enum):
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    HEARTBEAT = "heartbeat"
    HEARTBEAT_RESPONSE = "heartbeat_response"
    GET_AGENT_STATUS = "get_agent_status"
    GET_SYSTEM_METRICS = "get_system_metrics"
    GET_ENGINE_STATUS = "get_engine_status"
    AGENT_TASK = "agent_task"
    ERROR = "error"

@dataclass
class WebSocketConnection:
    websocket: WebSocket
    connection_id: str
    connected_at: datetime
    last_heartbeat: datetime
    subscriptions: Set[str]
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class EnhancedWebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocketConnection] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # channel -> set of connection_ids
        self.message_handlers: Dict[str, callable] = {}
        self.heartbeat_interval = 30  # seconds
        self.heartbeat_timeout = 60  # seconds
        self.running = False
        
        # Register default message handlers
        self._register_default_handlers()
        
    def _register_default_handlers(self):
        """Register default message handlers"""
        self.message_handlers.update({
            MessageType.SUBSCRIBE.value: self._handle_subscribe,
            MessageType.UNSUBSCRIBE.value: self._handle_unsubscribe,
            MessageType.HEARTBEAT.value: self._handle_heartbeat,
            MessageType.GET_AGENT_STATUS.value: self._handle_get_agent_status,
            MessageType.GET_SYSTEM_METRICS.value: self._handle_get_system_metrics,
            MessageType.GET_ENGINE_STATUS.value: self._handle_get_engine_status,
            MessageType.AGENT_TASK.value: self._handle_agent_task,
        })

    async def connect(self, websocket: WebSocket, connection_id: str, user_id: Optional[str] = None) -> bool:
        """Accept a new WebSocket connection"""
        try:
            await websocket.accept()
            
            connection = WebSocketConnection(
                websocket=websocket,
                connection_id=connection_id,
                connected_at=datetime.now(),
                last_heartbeat=datetime.now(),
                subscriptions=set(),
                user_id=user_id
            )
            
            self.active_connections[connection_id] = connection
            
            logger.info(f"WebSocket connected: {connection_id} (user: {user_id})")
            
            # Send welcome message
            await self.send_personal_message(connection_id, {
                "type": "welcome",
                "payload": {
                    "connection_id": connection_id,
                    "server_time": datetime.now().isoformat(),
                    "heartbeat_interval": self.heartbeat_interval
                }
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to accept WebSocket connection {connection_id}: {e}")
            return False

    async def disconnect(self, connection_id: str):
        """Disconnect a WebSocket connection"""
        if connection_id not in self.active_connections:
            return
            
        connection = self.active_connections[connection_id]
        
        # Remove from all subscriptions
        for channel in connection.subscriptions:
            if channel in self.subscriptions:
                self.subscriptions[channel].discard(connection_id)
                if not self.subscriptions[channel]:
                    del self.subscriptions[channel]
        
        # Remove connection
        del self.active_connections[connection_id]
        
        logger.info(f"WebSocket disconnected: {connection_id}")

    async def send_personal_message(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """Send a message to a specific connection"""
        if connection_id not in self.active_connections:
            return False
            
        connection = self.active_connections[connection_id]
        
        try:
            message_with_timestamp = {
                **message,
                "timestamp": datetime.now().isoformat()
            }
            await connection.websocket.send_text(json.dumps(message_with_timestamp))
            return True
        except Exception as e:
            logger.error(f"Failed to send message to {connection_id}: {e}")
            await self.disconnect(connection_id)
            return False

    async def broadcast(self, message: Dict[str, Any]) -> int:
        """Broadcast a message to all connected clients"""
        if not self.active_connections:
            return 0
            
        disconnected = []
        sent_count = 0
        
        message_with_timestamp = {
            **message,
            "timestamp": datetime.now().isoformat()
        }
        
        for connection_id, connection in self.active_connections.items():
            try:
                await connection.websocket.send_text(json.dumps(message_with_timestamp))
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to broadcast to {connection_id}: {e}")
                disconnected.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected:
            await self.disconnect(connection_id)
            
        return sent_count

    async def broadcast_to_channel(self, channel: str, message: Dict[str, Any]) -> int:
        """Broadcast a message to all subscribers of a specific channel"""
        if channel not in self.subscriptions:
            return 0
            
        disconnected = []
        sent_count = 0
        
        message_with_timestamp = {
            **message,
            "timestamp": datetime.now().isoformat()
        }
        
        for connection_id in self.subscriptions[channel].copy():
            if connection_id in self.active_connections:
                try:
                    connection = self.active_connections[connection_id]
                    await connection.websocket.send_text(json.dumps(message_with_timestamp))
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to send to {connection_id} on channel {channel}: {e}")
                    disconnected.append(connection_id)
            else:
                # Connection no longer exists, remove from subscription
                disconnected.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected:
            await self.disconnect(connection_id)
            
        return sent_count

    def subscribe(self, connection_id: str, channel: str) -> bool:
        """Subscribe a connection to a channel"""
        if connection_id not in self.active_connections:
            return False
            
        if channel not in self.subscriptions:
            self.subscriptions[channel] = set()
            
        self.subscriptions[channel].add(connection_id)
        self.active_connections[connection_id].subscriptions.add(channel)
        
        logger.debug(f"Connection {connection_id} subscribed to channel {channel}")
        return True

    def unsubscribe(self, connection_id: str, channel: str) -> bool:
        """Unsubscribe a connection from a channel"""
        if connection_id not in self.active_connections:
            return False
            
        if channel in self.subscriptions:
            self.subscriptions[channel].discard(connection_id)
            if not self.subscriptions[channel]:
                del self.subscriptions[channel]
                
        self.active_connections[connection_id].subscriptions.discard(channel)
        
        logger.debug(f"Connection {connection_id} unsubscribed from channel {channel}")
        return True

    async def handle_message(self, connection_id: str, message: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            payload = data.get("payload", {})
            
            if message_type in self.message_handlers:
                await self.message_handlers[message_type](connection_id, payload)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                await self.send_personal_message(connection_id, {
                    "type": MessageType.ERROR.value,
                    "payload": {
                        "error": f"Unknown message type: {message_type}",
                        "original_message": data
                    }
                })
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from {connection_id}: {e}")
            await self.send_personal_message(connection_id, {
                "type": MessageType.ERROR.value,
                "payload": {
                    "error": "Invalid JSON format",
                    "details": str(e)
                }
            })
        except Exception as e:
            logger.error(f"Error handling message from {connection_id}: {e}")
            await self.send_personal_message(connection_id, {
                "type": MessageType.ERROR.value,
                "payload": {
                    "error": "Internal server error",
                    "details": str(e)
                }
            })

    # Message Handlers
    async def _handle_subscribe(self, connection_id: str, payload: Dict[str, Any]):
        """Handle subscription request"""
        channel = payload.get("channel")
        if channel:
            success = self.subscribe(connection_id, channel)
            await self.send_personal_message(connection_id, {
                "type": "subscription_confirmed",
                "payload": {
                    "channel": channel,
                    "success": success
                }
            })

    async def _handle_unsubscribe(self, connection_id: str, payload: Dict[str, Any]):
        """Handle unsubscription request"""
        channel = payload.get("channel")
        if channel:
            success = self.unsubscribe(connection_id, channel)
            await self.send_personal_message(connection_id, {
                "type": "unsubscription_confirmed",
                "payload": {
                    "channel": channel,
                    "success": success
                }
            })

    async def _handle_heartbeat(self, connection_id: str, payload: Dict[str, Any]):
        """Handle heartbeat message"""
        if connection_id in self.active_connections:
            self.active_connections[connection_id].last_heartbeat = datetime.now()
            
        await self.send_personal_message(connection_id, {
            "type": MessageType.HEARTBEAT_RESPONSE.value,
            "payload": {
                "server_time": datetime.now().isoformat(),
                "client_timestamp": payload.get("timestamp")
            }
        })

    async def _handle_get_agent_status(self, connection_id: str, payload: Dict[str, Any]):
        """Handle agent status request"""
        # This would typically interface with your agent coordinator
        # For now, we'll send a placeholder response
        agent_id = payload.get("agent_id")
        all_agents = payload.get("all", False)
        
        if all_agents:
            # Send system overview
            await self.send_personal_message(connection_id, {
                "channel": "system_overview",
                "payload": {
                    "total_agents": 0,
                    "active_agents": 0,
                    "processing_agents": 0,
                    "system_metrics": {
                        "average_response_time": 0,
                        "average_success_rate": 0,
                        "total_tasks_completed": 0
                    }
                }
            })
        else:
            # Send specific agent status
            await self.send_personal_message(connection_id, {
                "channel": "agent_status",
                "payload": {
                    "id": agent_id or "unknown",
                    "status": "idle",
                    "message": "Agent status requested"
                }
            })

    async def _handle_get_system_metrics(self, connection_id: str, payload: Dict[str, Any]):
        """Handle system metrics request"""
        # This would typically interface with your monitoring service
        await self.send_personal_message(connection_id, {
            "channel": "system_metrics",
            "payload": {
                "cpu_usage": 0,
                "memory_usage": 0,
                "disk_usage": 0,
                "network_io": {
                    "bytes_sent": 0,
                    "bytes_received": 0
                },
                "response_times": [],
                "error_rates": [],
                "throughput": 0
            }
        })

    async def _handle_get_engine_status(self, connection_id: str, payload: Dict[str, Any]):
        """Handle engine status request"""
        # This would typically interface with your engine coordinator
        await self.send_personal_message(connection_id, {
            "channel": "engine_status",
            "payload": {
                "engines": {
                    "perfect_recall": {
                        "status": "idle",
                        "current_tasks": 0,
                        "queue_size": 0,
                        "performance_metrics": {
                            "avg_response_time": 0,
                            "success_rate": 100,
                            "throughput": 0
                        }
                    },
                    "parallel_mind": {
                        "status": "idle",
                        "current_tasks": 0,
                        "queue_size": 0,
                        "performance_metrics": {
                            "avg_response_time": 0,
                            "success_rate": 100,
                            "throughput": 0
                        }
                    },
                    "creative": {
                        "status": "idle",
                        "current_tasks": 0,
                        "queue_size": 0,
                        "performance_metrics": {
                            "avg_response_time": 0,
                            "success_rate": 100,
                            "throughput": 0
                        }
                    }
                }
            }
        })

    async def _handle_agent_task(self, connection_id: str, payload: Dict[str, Any]):
        """Handle agent task submission"""
        agent_id = payload.get("agent_id")
        task = payload.get("task")
        parameters = payload.get("parameters", {})
        
        if not agent_id or not task:
            await self.send_personal_message(connection_id, {
                "type": MessageType.ERROR.value,
                "payload": {
                    "error": "Missing agent_id or task in request"
                }
            })
            return
        
        # This would typically interface with your agent coordinator
        task_id = str(uuid.uuid4())
        
        await self.send_personal_message(connection_id, {
            "type": "task_submitted",
            "payload": {
                "task_id": task_id,
                "agent_id": agent_id,
                "task": task,
                "status": "queued"
            }
        })

    # Utility methods
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        now = datetime.now()
        
        return {
            "total_connections": len(self.active_connections),
            "total_subscriptions": sum(len(subs) for subs in self.subscriptions.values()),
            "channels": list(self.subscriptions.keys()),
            "connections": [
                {
                    "connection_id": conn.connection_id,
                    "user_id": conn.user_id,
                    "connected_at": conn.connected_at.isoformat(),
                    "last_heartbeat": conn.last_heartbeat.isoformat(),
                    "subscriptions": list(conn.subscriptions),
                    "connected_duration": (now - conn.connected_at).total_seconds()
                }
                for conn in self.active_connections.values()
            ]
        }

    async def start_heartbeat_monitor(self):
        """Start monitoring heartbeats and clean up stale connections"""
        self.running = True
        
        while self.running:
            try:
                now = datetime.now()
                stale_connections = []
                
                for connection_id, connection in self.active_connections.items():
                    time_since_heartbeat = (now - connection.last_heartbeat).total_seconds()
                    
                    if time_since_heartbeat > self.heartbeat_timeout:
                        stale_connections.append(connection_id)
                        logger.warning(f"Connection {connection_id} timed out (no heartbeat for {time_since_heartbeat}s)")
                
                # Clean up stale connections
                for connection_id in stale_connections:
                    await self.disconnect(connection_id)
                
                await asyncio.sleep(self.heartbeat_interval)
                
            except Exception as e:
                logger.error(f"Error in heartbeat monitor: {e}")
                await asyncio.sleep(5)

    async def stop_heartbeat_monitor(self):
        """Stop the heartbeat monitor"""
        self.running = False

    def register_message_handler(self, message_type: str, handler: callable):
        """Register a custom message handler"""
        self.message_handlers[message_type] = handler

    async def cleanup(self):
        """Clean up all connections and resources"""
        logger.info("Cleaning up WebSocket manager...")
        
        # Disconnect all connections
        connection_ids = list(self.active_connections.keys())
        for connection_id in connection_ids:
            await self.disconnect(connection_id)
        
        # Stop monitoring
        await self.stop_heartbeat_monitor()
        
        logger.info("WebSocket manager cleanup complete")

# Global instance
enhanced_websocket_manager = EnhancedWebSocketManager()