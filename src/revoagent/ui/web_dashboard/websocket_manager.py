"""
WebSocket Manager for reVoAgent Dashboard

Handles real-time communication between the dashboard and clients.
"""

import asyncio
import json
import logging
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and real-time communication."""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.connection_info: Dict[WebSocket, Dict] = {}
        self.subscriptions: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.connection_info[websocket] = {
            "connected_at": datetime.now(),
            "subscriptions": set()
        }
        
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
        # Send welcome message
        await self.send_personal_message(websocket, {
            "type": "connection_established",
            "message": "Connected to reVoAgent Dashboard",
            "timestamp": datetime.now().isoformat()
        })
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            
            # Remove from subscriptions
            if websocket in self.connection_info:
                for subscription in self.connection_info[websocket]["subscriptions"]:
                    if subscription in self.subscriptions:
                        self.subscriptions[subscription].discard(websocket)
                del self.connection_info[websocket]
            
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, websocket: WebSocket, message: Dict):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict):
        """Broadcast a message to all connected clients."""
        if not self.active_connections:
            return
        
        message["timestamp"] = datetime.now().isoformat()
        message_text = json.dumps(message)
        
        # Send to all connections
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(message_text)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_to_subscription(self, subscription: str, message: Dict):
        """Broadcast a message to clients subscribed to a specific topic."""
        if subscription not in self.subscriptions:
            return
        
        message["timestamp"] = datetime.now().isoformat()
        message_text = json.dumps(message)
        
        disconnected = set()
        for connection in self.subscriptions[subscription]:
            try:
                await connection.send_text(message_text)
            except Exception as e:
                logger.error(f"Error broadcasting to subscription {subscription}: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def handle_message(self, websocket: WebSocket, message: Dict):
        """Handle incoming WebSocket messages."""
        try:
            message_type = message.get("type")
            
            if message_type == "subscribe":
                await self._handle_subscribe(websocket, message)
            elif message_type == "unsubscribe":
                await self._handle_unsubscribe(websocket, message)
            elif message_type == "ping":
                await self._handle_ping(websocket, message)
            elif message_type == "get_status":
                await self._handle_get_status(websocket, message)
            else:
                await self.send_personal_message(websocket, {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })
        
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            await self.send_personal_message(websocket, {
                "type": "error",
                "message": "Error processing message"
            })
    
    async def _handle_subscribe(self, websocket: WebSocket, message: Dict):
        """Handle subscription requests."""
        topic = message.get("topic")
        if not topic:
            await self.send_personal_message(websocket, {
                "type": "error",
                "message": "Topic is required for subscription"
            })
            return
        
        # Add to subscription
        if topic not in self.subscriptions:
            self.subscriptions[topic] = set()
        
        self.subscriptions[topic].add(websocket)
        self.connection_info[websocket]["subscriptions"].add(topic)
        
        await self.send_personal_message(websocket, {
            "type": "subscribed",
            "topic": topic,
            "message": f"Subscribed to {topic}"
        })
        
        logger.info(f"WebSocket subscribed to {topic}")
    
    async def _handle_unsubscribe(self, websocket: WebSocket, message: Dict):
        """Handle unsubscription requests."""
        topic = message.get("topic")
        if not topic:
            await self.send_personal_message(websocket, {
                "type": "error",
                "message": "Topic is required for unsubscription"
            })
            return
        
        # Remove from subscription
        if topic in self.subscriptions:
            self.subscriptions[topic].discard(websocket)
        
        if websocket in self.connection_info:
            self.connection_info[websocket]["subscriptions"].discard(topic)
        
        await self.send_personal_message(websocket, {
            "type": "unsubscribed",
            "topic": topic,
            "message": f"Unsubscribed from {topic}"
        })
        
        logger.info(f"WebSocket unsubscribed from {topic}")
    
    async def _handle_ping(self, websocket: WebSocket, message: Dict):
        """Handle ping messages."""
        await self.send_personal_message(websocket, {
            "type": "pong",
            "timestamp": datetime.now().isoformat()
        })
    
    async def _handle_get_status(self, websocket: WebSocket, message: Dict):
        """Handle status requests."""
        status = {
            "type": "status",
            "connections": len(self.active_connections),
            "subscriptions": {topic: len(connections) for topic, connections in self.subscriptions.items()},
            "uptime": datetime.now().isoformat()
        }
        
        await self.send_personal_message(websocket, status)
    
    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)
    
    def get_subscription_count(self, topic: str) -> int:
        """Get the number of subscribers for a topic."""
        return len(self.subscriptions.get(topic, set()))
    
    async def send_system_update(self, update_type: str, data: Dict):
        """Send system updates to all connected clients."""
        message = {
            "type": "system_update",
            "update_type": update_type,
            "data": data
        }
        await self.broadcast(message)
    
    async def send_agent_update(self, agent_id: str, status: str, data: Dict = None):
        """Send agent status updates."""
        message = {
            "type": "agent_update",
            "agent_id": agent_id,
            "status": status,
            "data": data or {}
        }
        await self.broadcast_to_subscription("agents", message)
        await self.broadcast(message)  # Also broadcast to all
    
    async def send_workflow_update(self, workflow_id: str, status: str, progress: float = None, data: Dict = None):
        """Send workflow updates."""
        message = {
            "type": "workflow_update",
            "workflow_id": workflow_id,
            "status": status,
            "data": data or {}
        }
        
        if progress is not None:
            message["progress"] = progress
        
        await self.broadcast_to_subscription("workflows", message)
        await self.broadcast(message)  # Also broadcast to all
    
    async def send_model_update(self, model_name: str, status: str, data: Dict = None):
        """Send model status updates."""
        message = {
            "type": "model_update",
            "model_name": model_name,
            "status": status,
            "data": data or {}
        }
        await self.broadcast_to_subscription("models", message)
        await self.broadcast(message)  # Also broadcast to all
    
    async def send_metrics_update(self, metrics: Dict):
        """Send real-time metrics updates."""
        message = {
            "type": "metrics_update",
            "metrics": metrics
        }
        await self.broadcast_to_subscription("metrics", message)
    
    async def send_activity_update(self, activity: Dict):
        """Send new activity updates."""
        message = {
            "type": "activity_update",
            "activity": activity
        }
        await self.broadcast_to_subscription("activity", message)
        await self.broadcast(message)  # Also broadcast to all
    
    async def start_periodic_updates(self):
        """Start periodic system updates."""
        asyncio.create_task(self._periodic_metrics_update())
    
    async def _periodic_metrics_update(self):
        """Send periodic metrics updates."""
        while True:
            try:
                if self.active_connections:
                    # This would normally get real metrics
                    # For now, we'll send mock data
                    import psutil
                    
                    metrics = {
                        "cpu_usage": psutil.cpu_percent(interval=1),
                        "memory_usage": psutil.virtual_memory().percent,
                        "disk_usage": psutil.disk_usage('/').percent,
                        "active_connections": len(self.active_connections),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    await self.send_metrics_update(metrics)
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in periodic metrics update: {e}")
                await asyncio.sleep(10)  # Wait longer on error