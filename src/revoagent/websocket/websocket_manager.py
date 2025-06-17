"""
🔄 WebSocket Manager for Real-Time Communication

Manages WebSocket connections for real-time engine monitoring,
task execution updates, and live dashboard communication.
"""

import asyncio
import json
import time
import uuid
from typing import Dict, List, Set, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from fastapi import WebSocket, WebSocketDisconnect
from enum import Enum

from .engine_monitor import EngineMonitor, EngineType, EngineStatus

logger = logging.getLogger(__name__)

class MessageType(Enum):
    # Client to server
    SUBSCRIBE_ENGINE = "subscribe_engine"
    UNSUBSCRIBE_ENGINE = "unsubscribe_engine"
    REQUEST_METRICS = "request_metrics"
    EXECUTE_TASK = "execute_task"
    
    # Server to client
    ENGINE_STATUS = "engine_status"
    ENGINE_METRICS = "engine_metrics"
    TASK_UPDATE = "task_update"
    SYSTEM_ALERT = "system_alert"
    ERROR = "error"

@dataclass
class WebSocketMessage:
    """Structured WebSocket message"""
    type: MessageType
    data: Dict[str, Any]
    timestamp: datetime
    client_id: Optional[str] = None
    message_id: Optional[str] = None

@dataclass
class ClientConnection:
    """WebSocket client connection info"""
    client_id: str
    websocket: WebSocket
    connected_at: datetime
    subscriptions: Set[EngineType]
    last_activity: datetime

class ConnectionManager:
    """Manages WebSocket connections and message routing"""
    
    def __init__(self):
        self.active_connections: Dict[str, ClientConnection] = {}
        self.engine_subscribers: Dict[EngineType, Set[str]] = {
            engine_type: set() for engine_type in EngineType
        }
        self.message_handlers: Dict[MessageType, Callable] = {}
        self._setup_message_handlers()
    
    def _setup_message_handlers(self):
        """Setup message handlers for different message types"""
        self.message_handlers = {
            MessageType.SUBSCRIBE_ENGINE: self._handle_subscribe_engine,
            MessageType.UNSUBSCRIBE_ENGINE: self._handle_unsubscribe_engine,
            MessageType.REQUEST_METRICS: self._handle_request_metrics,
            MessageType.EXECUTE_TASK: self._handle_execute_task,
        }
    
    async def connect(self, websocket: WebSocket) -> str:
        """Accept new WebSocket connection"""
        await websocket.accept()
        
        client_id = str(uuid.uuid4())
        connection = ClientConnection(
            client_id=client_id,
            websocket=websocket,
            connected_at=datetime.now(),
            subscriptions=set(),
            last_activity=datetime.now()
        )
        
        self.active_connections[client_id] = connection
        logger.info(f"🔗 WebSocket client connected: {client_id}")
        
        # Send welcome message
        await self.send_to_client(client_id, WebSocketMessage(
            type=MessageType.ENGINE_STATUS,
            data={
                "message": "Connected to reVoAgent Three-Engine Architecture",
                "client_id": client_id,
                "available_engines": [engine.value for engine in EngineType]
            },
            timestamp=datetime.now()
        ))
        
        return client_id
    
    async def disconnect(self, client_id: str):
        """Handle client disconnection"""
        if client_id in self.active_connections:
            connection = self.active_connections[client_id]
            
            # Remove from all subscriptions
            for engine_type in connection.subscriptions:
                self.engine_subscribers[engine_type].discard(client_id)
            
            # Remove connection
            del self.active_connections[client_id]
            logger.info(f"🔌 WebSocket client disconnected: {client_id}")
    
    async def send_to_client(self, client_id: str, message: WebSocketMessage):
        """Send message to specific client"""
        if client_id not in self.active_connections:
            return False
        
        connection = self.active_connections[client_id]
        
        try:
            message_data = {
                "type": message.type.value,
                "data": message.data,
                "timestamp": message.timestamp.isoformat(),
                "message_id": message.message_id or str(uuid.uuid4())
            }
            
            await connection.websocket.send_text(json.dumps(message_data))
            connection.last_activity = datetime.now()
            return True
            
        except Exception as e:
            logger.error(f"Error sending message to client {client_id}: {e}")
            await self.disconnect(client_id)
            return False
    
    async def broadcast_to_subscribers(self, engine_type: EngineType, message: WebSocketMessage):
        """Broadcast message to all subscribers of an engine"""
        subscribers = self.engine_subscribers[engine_type].copy()
        
        for client_id in subscribers:
            success = await self.send_to_client(client_id, message)
            if not success:
                # Remove failed client from subscribers
                self.engine_subscribers[engine_type].discard(client_id)
    
    async def broadcast_to_all(self, message: WebSocketMessage):
        """Broadcast message to all connected clients"""
        client_ids = list(self.active_connections.keys())
        
        for client_id in client_ids:
            await self.send_to_client(client_id, message)
    
    async def handle_message(self, client_id: str, message_data: str):
        """Handle incoming message from client"""
        try:
            data = json.loads(message_data)
            message_type = MessageType(data.get("type"))
            
            message = WebSocketMessage(
                type=message_type,
                data=data.get("data", {}),
                timestamp=datetime.now(),
                client_id=client_id,
                message_id=data.get("message_id")
            )
            
            # Update client activity
            if client_id in self.active_connections:
                self.active_connections[client_id].last_activity = datetime.now()
            
            # Route to appropriate handler
            handler = self.message_handlers.get(message_type)
            if handler:
                await handler(client_id, message)
            else:
                await self.send_error(client_id, f"Unknown message type: {message_type.value}")
                
        except Exception as e:
            logger.error(f"Error handling message from client {client_id}: {e}")
            await self.send_error(client_id, f"Message handling error: {str(e)}")
    
    async def _handle_subscribe_engine(self, client_id: str, message: WebSocketMessage):
        """Handle engine subscription request"""
        engine_name = message.data.get("engine")
        
        try:
            engine_type = EngineType(engine_name)
            
            # Add to subscriptions
            if client_id in self.active_connections:
                self.active_connections[client_id].subscriptions.add(engine_type)
                self.engine_subscribers[engine_type].add(client_id)
                
                await self.send_to_client(client_id, WebSocketMessage(
                    type=MessageType.ENGINE_STATUS,
                    data={
                        "message": f"Subscribed to {engine_name} engine",
                        "engine": engine_name,
                        "subscribed": True
                    },
                    timestamp=datetime.now()
                ))
                
                logger.info(f"Client {client_id} subscribed to {engine_name}")
                
        except ValueError:
            await self.send_error(client_id, f"Invalid engine name: {engine_name}")
    
    async def _handle_unsubscribe_engine(self, client_id: str, message: WebSocketMessage):
        """Handle engine unsubscription request"""
        engine_name = message.data.get("engine")
        
        try:
            engine_type = EngineType(engine_name)
            
            # Remove from subscriptions
            if client_id in self.active_connections:
                self.active_connections[client_id].subscriptions.discard(engine_type)
                self.engine_subscribers[engine_type].discard(client_id)
                
                await self.send_to_client(client_id, WebSocketMessage(
                    type=MessageType.ENGINE_STATUS,
                    data={
                        "message": f"Unsubscribed from {engine_name} engine",
                        "engine": engine_name,
                        "subscribed": False
                    },
                    timestamp=datetime.now()
                ))
                
                logger.info(f"Client {client_id} unsubscribed from {engine_name}")
                
        except ValueError:
            await self.send_error(client_id, f"Invalid engine name: {engine_name}")
    
    async def _handle_request_metrics(self, client_id: str, message: WebSocketMessage):
        """Handle metrics request"""
        engine_name = message.data.get("engine")
        
        if engine_name:
            try:
                engine_type = EngineType(engine_name)
                # This would be handled by WebSocketManager which has access to EngineMonitor
                await self.send_to_client(client_id, WebSocketMessage(
                    type=MessageType.ENGINE_METRICS,
                    data={
                        "message": f"Metrics request for {engine_name} received",
                        "engine": engine_name
                    },
                    timestamp=datetime.now()
                ))
            except ValueError:
                await self.send_error(client_id, f"Invalid engine name: {engine_name}")
        else:
            # Request all metrics
            await self.send_to_client(client_id, WebSocketMessage(
                type=MessageType.ENGINE_METRICS,
                data={"message": "All metrics request received"},
                timestamp=datetime.now()
            ))
    
    async def _handle_execute_task(self, client_id: str, message: WebSocketMessage):
        """Handle task execution request"""
        task_data = message.data.get("task", {})
        engine_name = task_data.get("engine")
        
        if not engine_name:
            await self.send_error(client_id, "Engine name required for task execution")
            return
        
        try:
            engine_type = EngineType(engine_name)
            
            # Send task received confirmation
            await self.send_to_client(client_id, WebSocketMessage(
                type=MessageType.TASK_UPDATE,
                data={
                    "status": "received",
                    "engine": engine_name,
                    "task_id": task_data.get("task_id", str(uuid.uuid4())),
                    "message": f"Task received for {engine_name} engine"
                },
                timestamp=datetime.now()
            ))
            
        except ValueError:
            await self.send_error(client_id, f"Invalid engine name: {engine_name}")
    
    async def send_error(self, client_id: str, error_message: str):
        """Send error message to client"""
        await self.send_to_client(client_id, WebSocketMessage(
            type=MessageType.ERROR,
            data={"error": error_message},
            timestamp=datetime.now()
        ))
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "total_connections": len(self.active_connections),
            "engine_subscribers": {
                engine.value: len(subscribers) 
                for engine, subscribers in self.engine_subscribers.items()
            },
            "connections": [
                {
                    "client_id": conn.client_id,
                    "connected_at": conn.connected_at.isoformat(),
                    "subscriptions": [engine.value for engine in conn.subscriptions],
                    "last_activity": conn.last_activity.isoformat()
                }
                for conn in self.active_connections.values()
            ]
        }

class WebSocketManager:
    """Main WebSocket manager integrating with engine monitoring"""
    
    def __init__(self, engine_monitor: EngineMonitor):
        self.engine_monitor = engine_monitor
        self.connection_manager = ConnectionManager()
        self.broadcasting_active = False
        self.broadcast_interval = 1.0  # 1 second
    
    async def start_broadcasting(self):
        """Start broadcasting engine metrics to subscribers"""
        self.broadcasting_active = True
        logger.info("📡 Starting WebSocket broadcasting")
        
        # Start broadcasting task
        asyncio.create_task(self._broadcast_metrics_loop())
    
    async def stop_broadcasting(self):
        """Stop broadcasting"""
        self.broadcasting_active = False
        logger.info("📡 Stopping WebSocket broadcasting")
    
    async def _broadcast_metrics_loop(self):
        """Continuously broadcast metrics to subscribers"""
        while self.broadcasting_active:
            try:
                # Get current metrics for all engines
                current_metrics = self.engine_monitor.get_current_metrics()
                
                # Broadcast to subscribers of each engine
                for engine_type, metrics in current_metrics.items():
                    if metrics and self.connection_manager.engine_subscribers[engine_type]:
                        message = WebSocketMessage(
                            type=MessageType.ENGINE_METRICS,
                            data={
                                "engine": engine_type.value,
                                "metrics": asdict(metrics),
                                "timestamp": datetime.now().isoformat()
                            },
                            timestamp=datetime.now()
                        )
                        
                        await self.connection_manager.broadcast_to_subscribers(engine_type, message)
                
                # Broadcast system health to all clients
                system_health = self.engine_monitor.get_system_health()
                if system_health.get('alerts'):
                    alert_message = WebSocketMessage(
                        type=MessageType.SYSTEM_ALERT,
                        data=system_health,
                        timestamp=datetime.now()
                    )
                    await self.connection_manager.broadcast_to_all(alert_message)
                
                await asyncio.sleep(self.broadcast_interval)
                
            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}")
                await asyncio.sleep(self.broadcast_interval * 2)
    
    async def handle_websocket_connection(self, websocket: WebSocket):
        """Handle new WebSocket connection"""
        client_id = await self.connection_manager.connect(websocket)
        
        try:
            while True:
                # Wait for message from client
                data = await websocket.receive_text()
                await self.connection_manager.handle_message(client_id, data)
                
        except WebSocketDisconnect:
            await self.connection_manager.disconnect(client_id)
        except Exception as e:
            logger.error(f"WebSocket error for client {client_id}: {e}")
            await self.connection_manager.disconnect(client_id)
    
    async def send_task_update(self, task_id: str, engine_type: EngineType, 
                              status: str, data: Dict[str, Any]):
        """Send task execution update to relevant subscribers"""
        message = WebSocketMessage(
            type=MessageType.TASK_UPDATE,
            data={
                "task_id": task_id,
                "engine": engine_type.value,
                "status": status,
                **data
            },
            timestamp=datetime.now()
        )
        
        await self.connection_manager.broadcast_to_subscribers(engine_type, message)
    
    async def send_system_alert(self, alert_type: str, message: str, severity: str = "warning"):
        """Send system-wide alert"""
        alert_message = WebSocketMessage(
            type=MessageType.SYSTEM_ALERT,
            data={
                "alert_type": alert_type,
                "message": message,
                "severity": severity,
                "timestamp": datetime.now().isoformat()
            },
            timestamp=datetime.now()
        )
        
        await self.connection_manager.broadcast_to_all(alert_message)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket manager statistics"""
        return {
            "broadcasting_active": self.broadcasting_active,
            "broadcast_interval": self.broadcast_interval,
            "connection_stats": self.connection_manager.get_connection_stats()
        }