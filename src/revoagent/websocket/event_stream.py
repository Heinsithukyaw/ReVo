"""
🌊 Engine Event Stream System

Event-driven communication system for inter-engine coordination,
inspired by OpenHands EventStream pattern for the Three-Engine Architecture.
"""

import asyncio
import json
import time
from typing import Dict, List, Set, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import uuid
import logging

logger = logging.getLogger(__name__)

class EventType(Enum):
    # Engine lifecycle events
    ENGINE_STARTED = "engine_started"
    ENGINE_STOPPED = "engine_stopped"
    ENGINE_ERROR = "engine_error"
    
    # Perfect Recall events
    CONTEXT_STORED = "context_stored"
    CONTEXT_RETRIEVED = "context_retrieved"
    MEMORY_OPTIMIZED = "memory_optimized"
    
    # Parallel Mind events
    WORKER_SCALED = "worker_scaled"
    TASK_QUEUED = "task_queued"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    
    # Creative Engine events
    SOLUTION_GENERATED = "solution_generated"
    INNOVATION_SCORED = "innovation_scored"
    LEARNING_UPDATED = "learning_updated"
    
    # Coordination events
    COORDINATION_STARTED = "coordination_started"
    COORDINATION_COMPLETED = "coordination_completed"
    INTER_ENGINE_MESSAGE = "inter_engine_message"
    
    # System events
    SYSTEM_ALERT = "system_alert"
    PERFORMANCE_THRESHOLD = "performance_threshold"
    HEALTH_CHECK = "health_check"

@dataclass
class EngineEvent:
    """Structured event for engine communication"""
    event_id: str
    event_type: EventType
    source_engine: str
    target_engine: Optional[str]  # None for broadcast
    timestamp: datetime
    data: Dict[str, Any]
    correlation_id: Optional[str] = None  # For tracking related events
    priority: int = 5  # 1-10, higher = more priority

@dataclass
class EventSubscription:
    """Event subscription configuration"""
    subscriber_id: str
    event_types: Set[EventType]
    source_engines: Set[str]  # Empty set means all engines
    callback: Callable[[EngineEvent], None]
    active: bool = True

class EngineEventStream:
    """Central event stream for Three-Engine Architecture"""
    
    def __init__(self, max_history: int = 1000):
        self.subscriptions: Dict[str, EventSubscription] = {}
        self.event_history: List[EngineEvent] = []
        self.max_history = max_history
        self.processing_queue = asyncio.Queue()
        self.processing_active = False
        
        # Performance metrics
        self.events_processed = 0
        self.events_per_second = 0.0
        self.last_metrics_update = time.time()
        
        # Event routing patterns
        self.routing_patterns: Dict[EventType, List[str]] = {
            # Perfect Recall events that other engines might need
            EventType.CONTEXT_STORED: ["parallel_mind", "creative"],
            EventType.CONTEXT_RETRIEVED: ["coordinator"],
            
            # Parallel Mind events
            EventType.TASK_COMPLETED: ["coordinator", "perfect_recall"],
            EventType.WORKER_SCALED: ["coordinator"],
            
            # Creative Engine events
            EventType.SOLUTION_GENERATED: ["coordinator", "perfect_recall"],
            EventType.INNOVATION_SCORED: ["coordinator"],
            
            # System-wide events
            EventType.SYSTEM_ALERT: ["all"],
            EventType.PERFORMANCE_THRESHOLD: ["coordinator"],
        }
    
    async def start_processing(self):
        """Start event processing loop"""
        self.processing_active = True
        logger.info("🌊 Starting Engine Event Stream processing")
        
        # Start processing tasks
        asyncio.create_task(self._process_events_loop())
        asyncio.create_task(self._update_metrics_loop())
    
    async def stop_processing(self):
        """Stop event processing"""
        self.processing_active = False
        logger.info("🌊 Stopping Engine Event Stream processing")
    
    async def publish_event(self, event: EngineEvent):
        """Publish event to the stream"""
        # Add to processing queue
        await self.processing_queue.put(event)
        
        # Add to history
        self.event_history.append(event)
        
        # Limit history size
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]
        
        logger.debug(f"📤 Event published: {event.event_type.value} from {event.source_engine}")
    
    async def publish_simple_event(self, event_type: EventType, source_engine: str, 
                                  data: Dict[str, Any], target_engine: Optional[str] = None,
                                  correlation_id: Optional[str] = None, priority: int = 5):
        """Publish a simple event with automatic ID generation"""
        event = EngineEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            source_engine=source_engine,
            target_engine=target_engine,
            timestamp=datetime.now(),
            data=data,
            correlation_id=correlation_id,
            priority=priority
        )
        
        await self.publish_event(event)
        return event.event_id
    
    def subscribe(self, subscriber_id: str, event_types: List[EventType], 
                 callback: Callable[[EngineEvent], None], 
                 source_engines: Optional[List[str]] = None) -> str:
        """Subscribe to specific event types"""
        subscription = EventSubscription(
            subscriber_id=subscriber_id,
            event_types=set(event_types),
            source_engines=set(source_engines) if source_engines else set(),
            callback=callback
        )
        
        self.subscriptions[subscriber_id] = subscription
        logger.info(f"📥 Subscription created: {subscriber_id} for {len(event_types)} event types")
        
        return subscriber_id
    
    def unsubscribe(self, subscriber_id: str):
        """Unsubscribe from events"""
        if subscriber_id in self.subscriptions:
            del self.subscriptions[subscriber_id]
            logger.info(f"📤 Subscription removed: {subscriber_id}")
    
    async def _process_events_loop(self):
        """Main event processing loop"""
        while self.processing_active:
            try:
                # Get event from queue with timeout
                event = await asyncio.wait_for(self.processing_queue.get(), timeout=1.0)
                
                # Process the event
                await self._process_event(event)
                
                # Update metrics
                self.events_processed += 1
                
            except asyncio.TimeoutError:
                # No events to process, continue
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")
    
    async def _process_event(self, event: EngineEvent):
        """Process a single event"""
        # Route to appropriate subscribers
        matching_subscriptions = self._find_matching_subscriptions(event)
        
        # Execute callbacks
        for subscription in matching_subscriptions:
            try:
                # Execute callback (could be async or sync)
                if asyncio.iscoroutinefunction(subscription.callback):
                    await subscription.callback(event)
                else:
                    subscription.callback(event)
                    
            except Exception as e:
                logger.error(f"Error in event callback for {subscription.subscriber_id}: {e}")
        
        # Auto-route based on patterns
        await self._auto_route_event(event)
        
        logger.debug(f"📨 Event processed: {event.event_type.value} -> {len(matching_subscriptions)} subscribers")
    
    def _find_matching_subscriptions(self, event: EngineEvent) -> List[EventSubscription]:
        """Find subscriptions that match the event"""
        matching = []
        
        for subscription in self.subscriptions.values():
            if not subscription.active:
                continue
            
            # Check event type
            if event.event_type not in subscription.event_types:
                continue
            
            # Check source engine filter
            if subscription.source_engines and event.source_engine not in subscription.source_engines:
                continue
            
            # Check target engine (if specified)
            if event.target_engine and subscription.subscriber_id != event.target_engine:
                continue
            
            matching.append(subscription)
        
        return matching
    
    async def _auto_route_event(self, event: EngineEvent):
        """Auto-route events based on predefined patterns"""
        routing_targets = self.routing_patterns.get(event.event_type, [])
        
        for target in routing_targets:
            if target == "all":
                # Broadcast to all engines
                await self._broadcast_to_all_engines(event)
            elif target != event.source_engine:  # Don't route back to source
                # Route to specific engine
                await self._route_to_engine(event, target)
    
    async def _broadcast_to_all_engines(self, event: EngineEvent):
        """Broadcast event to all engines"""
        # This would integrate with the actual engine instances
        logger.debug(f"🌐 Broadcasting event {event.event_type.value} to all engines")
    
    async def _route_to_engine(self, event: EngineEvent, target_engine: str):
        """Route event to specific engine"""
        # This would integrate with the actual engine instances
        logger.debug(f"🎯 Routing event {event.event_type.value} to {target_engine}")
    
    async def _update_metrics_loop(self):
        """Update performance metrics"""
        while self.processing_active:
            try:
                current_time = time.time()
                time_diff = current_time - self.last_metrics_update
                
                if time_diff >= 1.0:  # Update every second
                    self.events_per_second = self.events_processed / time_diff
                    self.events_processed = 0
                    self.last_metrics_update = current_time
                
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Error updating metrics: {e}")
                await asyncio.sleep(1.0)
    
    def get_event_history(self, event_types: Optional[List[EventType]] = None,
                         source_engines: Optional[List[str]] = None,
                         limit: int = 100) -> List[EngineEvent]:
        """Get filtered event history"""
        filtered_events = self.event_history
        
        # Filter by event types
        if event_types:
            filtered_events = [e for e in filtered_events if e.event_type in event_types]
        
        # Filter by source engines
        if source_engines:
            filtered_events = [e for e in filtered_events if e.source_engine in source_engines]
        
        # Return most recent events
        return filtered_events[-limit:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get event stream metrics"""
        return {
            "events_per_second": self.events_per_second,
            "total_events_in_history": len(self.event_history),
            "active_subscriptions": len([s for s in self.subscriptions.values() if s.active]),
            "processing_active": self.processing_active,
            "queue_size": self.processing_queue.qsize()
        }
    
    def export_events_json(self, limit: int = 100) -> str:
        """Export recent events as JSON"""
        recent_events = self.event_history[-limit:]
        
        events_data = [
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
            for event in recent_events
        ]
        
        return json.dumps({
            "events": events_data,
            "total_events": len(events_data),
            "metrics": self.get_metrics()
        }, indent=2)

class EngineEventLogger:
    """Event logger for debugging and monitoring"""
    
    def __init__(self, event_stream: EngineEventStream):
        self.event_stream = event_stream
        self.log_file = None
        self.logging_active = False
    
    def start_logging(self, log_file: Optional[str] = None):
        """Start logging events to file"""
        self.log_file = log_file
        self.logging_active = True
        
        # Subscribe to all events
        self.event_stream.subscribe(
            subscriber_id="event_logger",
            event_types=list(EventType),
            callback=self._log_event
        )
        
        logger.info(f"📝 Event logging started{' to ' + log_file if log_file else ''}")
    
    def stop_logging(self):
        """Stop event logging"""
        self.logging_active = False
        self.event_stream.unsubscribe("event_logger")
        logger.info("📝 Event logging stopped")
    
    def _log_event(self, event: EngineEvent):
        """Log event to file or console"""
        if not self.logging_active:
            return
        
        log_entry = {
            "timestamp": event.timestamp.isoformat(),
            "event_type": event.event_type.value,
            "source": event.source_engine,
            "target": event.target_engine,
            "data": event.data
        }
        
        if self.log_file:
            try:
                with open(self.log_file, 'a') as f:
                    f.write(json.dumps(log_entry) + '\n')
            except Exception as e:
                logger.error(f"Error writing to log file: {e}")
        else:
            logger.info(f"🌊 EVENT: {json.dumps(log_entry)}")

# Convenience functions for common event patterns
async def publish_engine_started(event_stream: EngineEventStream, engine_name: str, 
                                config: Dict[str, Any]):
    """Publish engine started event"""
    await event_stream.publish_simple_event(
        event_type=EventType.ENGINE_STARTED,
        source_engine=engine_name,
        data={"config": config, "status": "started"}
    )

async def publish_context_stored(event_stream: EngineEventStream, context_id: str, 
                               context_type: str, session_id: str):
    """Publish context stored event"""
    await event_stream.publish_simple_event(
        event_type=EventType.CONTEXT_STORED,
        source_engine="perfect_recall",
        data={
            "context_id": context_id,
            "context_type": context_type,
            "session_id": session_id
        }
    )

async def publish_task_completed(event_stream: EngineEventStream, task_id: str, 
                                result: Dict[str, Any], execution_time: float):
    """Publish task completed event"""
    await event_stream.publish_simple_event(
        event_type=EventType.TASK_COMPLETED,
        source_engine="parallel_mind",
        data={
            "task_id": task_id,
            "result": result,
            "execution_time_ms": execution_time * 1000
        }
    )

async def publish_solution_generated(event_stream: EngineEventStream, solutions: List[Dict], 
                                   innovation_score: float, generation_time: float):
    """Publish solution generated event"""
    await event_stream.publish_simple_event(
        event_type=EventType.SOLUTION_GENERATED,
        source_engine="creative",
        data={
            "solution_count": len(solutions),
            "innovation_score": innovation_score,
            "generation_time_ms": generation_time * 1000,
            "solutions": solutions
        }
    )