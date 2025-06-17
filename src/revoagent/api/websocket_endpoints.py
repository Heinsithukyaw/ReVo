"""
🔌 FastAPI WebSocket Endpoints

Real-time WebSocket endpoints for Three-Engine Architecture monitoring,
providing live engine status, metrics, and task execution updates.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import HTMLResponse
import asyncio
import json
from typing import Dict, Any, Optional
import logging

from ..websocket import WebSocketManager, EngineMonitor, EngineEventStream
from ..engines.engine_coordinator import EngineCoordinator
from ..engines.perfect_recall import PerfectRecallEngine
from ..engines.parallel_mind.worker_manager import WorkerManager
from ..engines.creative_engine import CreativeEngine

logger = logging.getLogger(__name__)

# Global instances (would be properly injected in production)
websocket_manager: Optional[WebSocketManager] = None
engine_monitor: Optional[EngineMonitor] = None
event_stream: Optional[EngineEventStream] = None

router = APIRouter(prefix="/ws", tags=["websocket"])

async def get_websocket_manager() -> WebSocketManager:
    """Dependency to get WebSocket manager"""
    global websocket_manager
    if not websocket_manager:
        raise HTTPException(status_code=503, detail="WebSocket manager not initialized")
    return websocket_manager

async def get_engine_monitor() -> EngineMonitor:
    """Dependency to get engine monitor"""
    global engine_monitor
    if not engine_monitor:
        raise HTTPException(status_code=503, detail="Engine monitor not initialized")
    return engine_monitor

async def initialize_websocket_system(engines: Dict[str, Any]):
    """Initialize the WebSocket system with engines"""
    global websocket_manager, engine_monitor, event_stream
    
    try:
        # Initialize engine monitor
        from ..websocket.engine_monitor import EngineType
        engine_mapping = {
            EngineType.PERFECT_RECALL: engines.get('perfect_recall'),
            EngineType.PARALLEL_MIND: engines.get('parallel_mind'),
            EngineType.CREATIVE: engines.get('creative'),
            EngineType.COORDINATOR: engines.get('coordinator')
        }
        
        engine_monitor = EngineMonitor(engine_mapping)
        
        # Initialize event stream
        event_stream = EngineEventStream()
        
        # Initialize WebSocket manager
        websocket_manager = WebSocketManager(engine_monitor)
        
        # Start monitoring and broadcasting
        await engine_monitor.start_monitoring()
        await event_stream.start_processing()
        await websocket_manager.start_broadcasting()
        
        logger.info("🔌 WebSocket system initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize WebSocket system: {e}")
        raise

@router.websocket("/engines")
async def websocket_engines_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for engine monitoring"""
    ws_manager = await get_websocket_manager()
    await ws_manager.handle_websocket_connection(websocket)

@router.websocket("/events")
async def websocket_events_endpoint(websocket: WebSocket):
    """WebSocket endpoint for event stream monitoring"""
    await websocket.accept()
    client_id = f"events_client_{id(websocket)}"
    
    try:
        # Subscribe to all events for this client
        def event_callback(event):
            # Send event to WebSocket client
            asyncio.create_task(websocket.send_text(json.dumps({
                "type": "event",
                "event_type": event.event_type.value,
                "source_engine": event.source_engine,
                "target_engine": event.target_engine,
                "timestamp": event.timestamp.isoformat(),
                "data": event.data
            })))
        
        if event_stream:
            from ..websocket.event_stream import EventType
            event_stream.subscribe(
                subscriber_id=client_id,
                event_types=list(EventType),
                callback=event_callback
            )
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            # Handle client messages if needed
            logger.debug(f"Received from events client: {data}")
            
    except WebSocketDisconnect:
        if event_stream:
            event_stream.unsubscribe(client_id)
        logger.info(f"Events WebSocket client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"Events WebSocket error: {e}")
        if event_stream:
            event_stream.unsubscribe(client_id)

@router.get("/status")
async def websocket_status():
    """Get WebSocket system status"""
    try:
        status = {
            "websocket_manager": {
                "initialized": websocket_manager is not None,
                "stats": websocket_manager.get_stats() if websocket_manager else None
            },
            "engine_monitor": {
                "initialized": engine_monitor is not None,
                "monitoring_active": engine_monitor.monitoring_active if engine_monitor else False
            },
            "event_stream": {
                "initialized": event_stream is not None,
                "metrics": event_stream.get_metrics() if event_stream else None
            }
        }
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting WebSocket status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_realtime_metrics():
    """Get current real-time metrics for all engines"""
    monitor = await get_engine_monitor()
    
    try:
        current_metrics = monitor.get_current_metrics()
        system_health = monitor.get_system_health()
        
        return {
            "system_health": system_health,
            "engine_metrics": {
                engine_type.value: {
                    "status": metrics.status.value if metrics else "offline",
                    "metrics": {
                        "uptime_seconds": metrics.uptime_seconds if metrics else 0,
                        "cpu_usage_percent": metrics.cpu_usage_percent if metrics else 0,
                        "memory_usage_mb": metrics.memory_usage_mb if metrics else 0,
                        "requests_per_second": metrics.requests_per_second if metrics else 0,
                        "error_rate": metrics.error_rate if metrics else 0,
                        **metrics.engine_specific if metrics else {}
                    }
                }
                for engine_type, metrics in current_metrics.items()
            },
            "timestamp": monitor.get_current_metrics(list(current_metrics.keys())[0]).last_activity.isoformat() if current_metrics else None
        }
        
    except Exception as e:
        logger.error(f"Error getting real-time metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/{engine_name}")
async def get_engine_metrics(engine_name: str):
    """Get metrics for a specific engine"""
    monitor = await get_engine_monitor()
    
    try:
        from ..websocket.engine_monitor import EngineType
        engine_type = EngineType(engine_name)
        
        current_metrics = monitor.get_current_metrics(engine_type)
        history = monitor.get_metrics_history(engine_type, minutes=5)
        
        return {
            "engine": engine_name,
            "current_metrics": {
                "status": current_metrics.status.value if current_metrics else "offline",
                "uptime_seconds": current_metrics.uptime_seconds if current_metrics else 0,
                "cpu_usage_percent": current_metrics.cpu_usage_percent if current_metrics else 0,
                "memory_usage_mb": current_metrics.memory_usage_mb if current_metrics else 0,
                "requests_per_second": current_metrics.requests_per_second if current_metrics else 0,
                "error_rate": current_metrics.error_rate if current_metrics else 0,
                "engine_specific": current_metrics.engine_specific if current_metrics else {}
            },
            "history_count": len(history),
            "timestamp": current_metrics.last_activity.isoformat() if current_metrics else None
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid engine name: {engine_name}")
    except Exception as e:
        logger.error(f"Error getting engine metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events/history")
async def get_event_history(limit: int = 100, event_type: Optional[str] = None):
    """Get event history"""
    if not event_stream:
        raise HTTPException(status_code=503, detail="Event stream not initialized")
    
    try:
        from ..websocket.event_stream import EventType
        
        event_types = None
        if event_type:
            try:
                event_types = [EventType(event_type)]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid event type: {event_type}")
        
        events = event_stream.get_event_history(event_types=event_types, limit=limit)
        
        return {
            "events": [
                {
                    "event_id": event.event_id,
                    "event_type": event.event_type.value,
                    "source_engine": event.source_engine,
                    "target_engine": event.target_engine,
                    "timestamp": event.timestamp.isoformat(),
                    "data": event.data,
                    "correlation_id": event.correlation_id,
                    "priority": event.priority
                }
                for event in events
            ],
            "total_events": len(events),
            "metrics": event_stream.get_metrics()
        }
        
    except Exception as e:
        logger.error(f"Error getting event history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-event")
async def publish_test_event(event_data: Dict[str, Any]):
    """Publish a test event (for development/testing)"""
    if not event_stream:
        raise HTTPException(status_code=503, detail="Event stream not initialized")
    
    try:
        from ..websocket.event_stream import EventType
        
        event_type = EventType(event_data.get("event_type", "SYSTEM_ALERT"))
        source_engine = event_data.get("source_engine", "test")
        data = event_data.get("data", {"message": "Test event"})
        
        event_id = await event_stream.publish_simple_event(
            event_type=event_type,
            source_engine=source_engine,
            data=data
        )
        
        return {
            "success": True,
            "event_id": event_id,
            "message": "Test event published successfully"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid event data: {e}")
    except Exception as e:
        logger.error(f"Error publishing test event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard")
async def websocket_dashboard():
    """Serve a simple WebSocket dashboard for testing"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🎯 reVoAgent Three-Engine Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #fff; }
            .engine { border: 2px solid #333; margin: 10px; padding: 15px; border-radius: 8px; }
            .perfect-recall { border-color: #3b82f6; background: rgba(59, 130, 246, 0.1); }
            .parallel-mind { border-color: #8b5cf6; background: rgba(139, 92, 246, 0.1); }
            .creative { border-color: #ec4899; background: rgba(236, 72, 153, 0.1); }
            .coordinator { border-color: #10b981; background: rgba(16, 185, 129, 0.1); }
            .status { font-weight: bold; padding: 5px 10px; border-radius: 4px; }
            .active { background: #10b981; }
            .idle { background: #6b7280; }
            .error { background: #ef4444; }
            .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin-top: 10px; }
            .metric { background: rgba(255,255,255,0.1); padding: 10px; border-radius: 4px; }
            #events { height: 200px; overflow-y: auto; background: #111; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 12px; }
        </style>
    </head>
    <body>
        <h1>🎯 reVoAgent Three-Engine Architecture Dashboard</h1>
        <div id="connection-status">Connecting...</div>
        
        <div id="engines">
            <div id="perfect-recall" class="engine perfect-recall">
                <h3>🔵 Perfect Recall Engine</h3>
                <div class="status" id="pr-status">Offline</div>
                <div class="metrics" id="pr-metrics"></div>
            </div>
            
            <div id="parallel-mind" class="engine parallel-mind">
                <h3>🟣 Parallel Mind Engine</h3>
                <div class="status" id="pm-status">Offline</div>
                <div class="metrics" id="pm-metrics"></div>
            </div>
            
            <div id="creative" class="engine creative">
                <h3>🩷 Creative Engine</h3>
                <div class="status" id="ce-status">Offline</div>
                <div class="metrics" id="ce-metrics"></div>
            </div>
            
            <div id="coordinator" class="engine coordinator">
                <h3>🔄 Engine Coordinator</h3>
                <div class="status" id="coord-status">Offline</div>
                <div class="metrics" id="coord-metrics"></div>
            </div>
        </div>
        
        <h3>📡 Live Events</h3>
        <div id="events"></div>
        
        <script>
            const ws = new WebSocket('ws://localhost:8000/ws/engines');
            const eventsWs = new WebSocket('ws://localhost:8000/ws/events');
            
            ws.onopen = function(event) {
                document.getElementById('connection-status').innerHTML = '✅ Connected to Engine Monitor';
                // Subscribe to all engines
                ws.send(JSON.stringify({type: 'subscribe_engine', data: {engine: 'perfect_recall'}}));
                ws.send(JSON.stringify({type: 'subscribe_engine', data: {engine: 'parallel_mind'}}));
                ws.send(JSON.stringify({type: 'subscribe_engine', data: {engine: 'creative'}}));
                ws.send(JSON.stringify({type: 'subscribe_engine', data: {engine: 'coordinator'}}));
            };
            
            ws.onmessage = function(event) {
                const message = JSON.parse(event.data);
                if (message.type === 'engine_metrics') {
                    updateEngineMetrics(message.data);
                }
            };
            
            eventsWs.onmessage = function(event) {
                const message = JSON.parse(event.data);
                if (message.type === 'event') {
                    addEvent(message);
                }
            };
            
            function updateEngineMetrics(data) {
                const engine = data.engine;
                const metrics = data.metrics;
                
                // Update status
                const statusElement = document.getElementById(getStatusId(engine));
                if (statusElement) {
                    statusElement.textContent = metrics.status;
                    statusElement.className = 'status ' + metrics.status;
                }
                
                // Update metrics
                const metricsElement = document.getElementById(getMetricsId(engine));
                if (metricsElement) {
                    metricsElement.innerHTML = formatMetrics(metrics);
                }
            }
            
            function getStatusId(engine) {
                const mapping = {
                    'perfect_recall': 'pr-status',
                    'parallel_mind': 'pm-status',
                    'creative': 'ce-status',
                    'coordinator': 'coord-status'
                };
                return mapping[engine];
            }
            
            function getMetricsId(engine) {
                const mapping = {
                    'perfect_recall': 'pr-metrics',
                    'parallel_mind': 'pm-metrics',
                    'creative': 'ce-metrics',
                    'coordinator': 'coord-metrics'
                };
                return mapping[engine];
            }
            
            function formatMetrics(metrics) {
                let html = '';
                html += `<div class="metric">CPU: ${metrics.cpu_usage_percent.toFixed(1)}%</div>`;
                html += `<div class="metric">Memory: ${metrics.memory_usage_mb.toFixed(0)} MB</div>`;
                html += `<div class="metric">RPS: ${metrics.requests_per_second.toFixed(1)}</div>`;
                
                // Engine-specific metrics
                for (const [key, value] of Object.entries(metrics.engine_specific)) {
                    if (typeof value === 'number') {
                        html += `<div class="metric">${key}: ${value.toFixed(2)}</div>`;
                    } else {
                        html += `<div class="metric">${key}: ${value}</div>`;
                    }
                }
                
                return html;
            }
            
            function addEvent(event) {
                const eventsDiv = document.getElementById('events');
                const eventDiv = document.createElement('div');
                eventDiv.innerHTML = `[${new Date(event.timestamp).toLocaleTimeString()}] ${event.event_type} from ${event.source_engine}`;
                eventsDiv.appendChild(eventDiv);
                eventsDiv.scrollTop = eventsDiv.scrollHeight;
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# Shutdown handler
async def shutdown_websocket_system():
    """Shutdown WebSocket system"""
    global websocket_manager, engine_monitor, event_stream
    
    try:
        if websocket_manager:
            await websocket_manager.stop_broadcasting()
        
        if engine_monitor:
            await engine_monitor.stop_monitoring()
        
        if event_stream:
            await event_stream.stop_processing()
        
        logger.info("🔌 WebSocket system shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during WebSocket system shutdown: {e}")