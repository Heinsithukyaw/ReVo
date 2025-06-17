"""
Memory-enhanced API endpoints for reVoAgent + Cognee integration
Extends existing FastAPI application with memory capabilities
"""

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import asyncio
import json
from datetime import datetime
import uuid
import logging

# Import existing components (adjust imports based on actual structure)
from packages.ai.cognee_model_manager import (
    CogneeModelManager, MemoryEnabledRequest, MemoryEnabledResponse,
    MemoryConfig, MemoryContext, create_memory_enabled_model_manager
)
from packages.agents.memory_enabled_agent import (
    create_memory_enabled_agent, MEMORY_ENABLED_AGENTS
)

logger = logging.getLogger(__name__)

# Create routers
memory_router = APIRouter(prefix="/api/memory", tags=["memory"])
chat_router = APIRouter(prefix="/api/chat", tags=["chat-memory"])
agents_router = APIRouter(prefix="/api/agents", tags=["agents-memory"])
knowledge_router = APIRouter(prefix="/api/knowledge", tags=["knowledge-graph"])

# Pydantic models for API
class MemoryChatRequest(BaseModel):
    content: str
    agents: List[str] = Field(default_factory=list)
    session_id: Optional[str] = None
    include_memory_context: bool = True
    memory_tags: Optional[List[str]] = Field(default_factory=list)
    persist_response: bool = True
    max_tokens: int = 1024
    temperature: float = 0.7

class MemoryChatResponse(BaseModel):
    responses: List[Dict[str, Any]]
    memory_context: Optional[Dict[str, Any]] = None
    session_id: str
    cost_breakdown: Dict[str, float]
    performance_metrics: Dict[str, Any]
    total_processing_time: float

class KnowledgeQueryRequest(BaseModel):
    query: str
    query_type: str = "insights"
    agent_filter: Optional[str] = None
    tags_filter: Optional[List[str]] = Field(default_factory=list)
    limit: int = 10

class KnowledgeQueryResponse(BaseModel):
    results: List[Dict[str, Any]]
    query: str
    total_results: int
    query_time: float
    knowledge_graph_stats: Dict[str, Any]

class BatchProcessRequest(BaseModel):
    requests: List[MemoryChatRequest]
    batch_size: int = 10
    concurrent: bool = True

class MemoryStatsResponse(BaseModel):
    memory_enabled: bool
    cognee_initialized: bool
    statistics: Dict[str, Any]
    configuration: Dict[str, Any]
    performance: Dict[str, Any]

class AgentMemoryRequest(BaseModel):
    query: str
    include_patterns: bool = True
    limit: int = 5

class AgentMemoryResponse(BaseModel):
    agent_id: str
    memory_entries: List[Dict[str, Any]]
    patterns: List[str]
    statistics: Dict[str, Any]

# Global memory manager instance
memory_manager: Optional[CogneeModelManager] = None
agent_instances: Dict[str, Any] = {}

async def get_memory_manager() -> CogneeModelManager:
    """Get the global memory manager instance"""
    global memory_manager
    if memory_manager is None:
        raise HTTPException(
            status_code=503, 
            detail="Memory manager not initialized"
        )
    return memory_manager

async def get_agent_instance(agent_type: str) -> Any:
    """Get or create agent instance"""
    global agent_instances
    
    if agent_type not in agent_instances:
        manager = await get_memory_manager()
        try:
            agent_instances[agent_type] = create_memory_enabled_agent(agent_type, manager)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown agent type: {agent_type}"
            )
    
    return agent_instances[agent_type]

async def initialize_memory_system(config: Dict[str, Any] = None):
    """Initialize the global memory system"""
    global memory_manager
    
    try:
        memory_manager = create_memory_enabled_model_manager(config)
        await memory_manager.initialize()
        logger.info("✅ Memory system initialized successfully")
    except Exception as e:
        logger.error(f"❌ Memory system initialization failed: {e}")
        raise

# Enhanced Chat Endpoints
@chat_router.post("/memory-enabled", response_model=MemoryChatResponse)
async def memory_enabled_chat(
    request: MemoryChatRequest,
    background_tasks: BackgroundTasks,
    manager: CogneeModelManager = Depends(get_memory_manager)
):
    """
    Enhanced chat endpoint with memory capabilities
    Maintains cost optimization while adding persistent memory
    """
    try:
        start_time = datetime.now()
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Process with each requested agent
        responses = []
        total_cost = 0.0
        
        for agent_id in request.agents or ["general"]:
            try:
                # Get agent instance
                if agent_id in MEMORY_ENABLED_AGENTS:
                    agent = await get_agent_instance(agent_id)
                    
                    # Process with memory-enabled agent
                    agent_response = await agent.process_request(
                        request.content,
                        context={"session_id": session_id},
                        session_id=session_id
                    )
                    
                    responses.append({
                        "agent_id": agent_id,
                        "content": agent_response["response"],
                        "provider": "local",
                        "tokens_used": agent_response.get("performance", {}).get("tokens_used", 0),
                        "generation_time": agent_response.get("performance", {}).get("generation_time", 0.0),
                        "cost": agent_response.get("cost", 0.0),
                        "memory_updated": agent_response.get("memory_stats", {}).get("memory_updated", False),
                        "knowledge_entities_created": agent_response.get("memory_stats", {}).get("entities_created", 0),
                        "memory_context_used": agent_response.get("memory_stats", {}).get("context_used", False)
                    })
                    
                else:
                    # Fallback to direct model manager
                    memory_request = MemoryEnabledRequest(
                        prompt=request.content,
                        agent_id=agent_id,
                        memory_tags=request.memory_tags,
                        include_memory_context=request.include_memory_context,
                        persist_response=request.persist_response,
                        session_id=session_id,
                        max_tokens=request.max_tokens,
                        temperature=request.temperature,
                        task_type=agent_id
                    )
                    
                    response = await manager.generate_with_memory(memory_request)
                    
                    responses.append({
                        "agent_id": agent_id,
                        "content": response.content,
                        "provider": response.provider,
                        "tokens_used": response.tokens_used,
                        "generation_time": response.generation_time,
                        "cost": response.cost,
                        "memory_updated": response.memory_updated,
                        "knowledge_entities_created": response.knowledge_entities_created,
                        "reasoning_steps": response.reasoning_steps or []
                    })
                
                # Track cost (should remain $0.00 for local models)
                total_cost += responses[-1]["cost"]
                
            except Exception as e:
                logger.error(f"Agent {agent_id} processing failed: {e}")
                responses.append({
                    "agent_id": agent_id,
                    "content": f"Error processing with agent {agent_id}: {str(e)}",
                    "provider": "error",
                    "cost": 0.0,
                    "error": True
                })
        
        # Aggregate memory context from first successful response
        memory_context = None
        for response in responses:
            if not response.get("error") and "memory_context" in response:
                memory_context = response["memory_context"]
                break
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        # Schedule background memory optimization
        background_tasks.add_task(optimize_memory_performance, session_id)
        
        return MemoryChatResponse(
            responses=responses,
            memory_context=memory_context,
            session_id=session_id,
            cost_breakdown={
                "total_cost": total_cost,
                "local_model_cost": 0.0,  # Always $0.00
                "cloud_fallback_cost": total_cost  # Only if fallback used
            },
            performance_metrics={
                "total_processing_time": total_time,
                "average_response_time": total_time / len(responses) if responses else 0,
                "agents_used": len(responses),
                "memory_enabled": request.include_memory_context,
                "successful_responses": len([r for r in responses if not r.get("error")])
            },
            total_processing_time=total_time
        )
        
    except Exception as e:
        logger.error(f"Memory chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"Memory chat failed: {str(e)}")

@chat_router.post("/multi-agent/memory-enabled", response_model=MemoryChatResponse)
async def memory_enabled_multi_agent_chat(
    request: MemoryChatRequest,
    manager: CogneeModelManager = Depends(get_memory_manager)
):
    """
    Multi-agent collaboration with shared memory context
    """
    try:
        start_time = datetime.now()
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get shared memory context first
        if request.include_memory_context:
            context_request = MemoryEnabledRequest(
                prompt=request.content,
                session_id=session_id,
                memory_tags=request.memory_tags + ["multi_agent_collaboration"],
                include_memory_context=True,
                persist_response=False  # Don't persist the context query
            )
            
            # Get shared context through model manager
            shared_response = await manager.generate_with_memory(context_request)
            shared_context = shared_response.memory_context
        else:
            shared_context = None
        
        # Process with all agents using shared context
        responses = []
        collaboration_prompt = f"""
Multi-Agent Collaboration Request:
{request.content}

Shared Context Available: {bool(shared_context)}
Collaborating Agents: {', '.join(request.agents)}

Please provide your specialized perspective while considering insights from other agents.
"""
        
        for agent_id in request.agents:
            try:
                if agent_id in MEMORY_ENABLED_AGENTS:
                    agent = await get_agent_instance(agent_id)
                    
                    # Add collaboration context
                    collaboration_context = {
                        "session_id": session_id,
                        "collaboration_mode": True,
                        "shared_context": shared_context.__dict__ if shared_context else None,
                        "collaborating_agents": request.agents
                    }
                    
                    agent_response = await agent.process_request(
                        collaboration_prompt,
                        context=collaboration_context,
                        session_id=session_id
                    )
                    
                    responses.append({
                        "agent_id": agent_id,
                        "content": agent_response["response"],
                        "provider": "local",
                        "tokens_used": agent_response.get("performance", {}).get("tokens_used", 0),
                        "generation_time": agent_response.get("performance", {}).get("generation_time", 0.0),
                        "cost": agent_response.get("cost", 0.0),
                        "memory_updated": agent_response.get("memory_stats", {}).get("memory_updated", False),
                        "shared_context_used": shared_context is not None,
                        "collaboration_mode": True
                    })
                    
                else:
                    # Fallback for non-memory agents
                    memory_request = MemoryEnabledRequest(
                        prompt=collaboration_prompt,
                        agent_id=agent_id,
                        memory_tags=request.memory_tags + ["multi_agent", f"collaboration_{session_id}"],
                        include_memory_context=False,  # Use shared context instead
                        persist_response=request.persist_response,
                        session_id=session_id,
                        max_tokens=request.max_tokens,
                        temperature=request.temperature,
                        task_type=f"multi_agent_{agent_id}"
                    )
                    
                    response = await manager.generate_with_memory(memory_request)
                    
                    responses.append({
                        "agent_id": agent_id,
                        "content": response.content,
                        "provider": response.provider,
                        "tokens_used": response.tokens_used,
                        "generation_time": response.generation_time,
                        "cost": response.cost,
                        "memory_updated": response.memory_updated,
                        "shared_context_used": shared_context is not None
                    })
                    
            except Exception as e:
                logger.error(f"Multi-agent collaboration failed for {agent_id}: {e}")
                responses.append({
                    "agent_id": agent_id,
                    "content": f"Collaboration error: {str(e)}",
                    "provider": "error",
                    "cost": 0.0,
                    "error": True
                })
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        return MemoryChatResponse(
            responses=responses,
            memory_context=shared_context.__dict__ if shared_context else None,
            session_id=session_id,
            cost_breakdown={"total_cost": sum(r.get("cost", 0) for r in responses)},
            performance_metrics={
                "collaboration_mode": True,
                "shared_context_used": shared_context is not None,
                "total_processing_time": total_time,
                "agents_collaborated": len(responses)
            },
            total_processing_time=total_time
        )
        
    except Exception as e:
        logger.error(f"Multi-agent memory chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"Multi-agent memory chat failed: {str(e)}")

# Memory Management Endpoints
@memory_router.post("/query", response_model=KnowledgeQueryResponse)
async def query_knowledge_graph(
    request: KnowledgeQueryRequest,
    manager: CogneeModelManager = Depends(get_memory_manager)
):
    """Query the knowledge graph directly"""
    try:
        start_time = datetime.now()
        
        # Prepare filters
        filters = {}
        if request.agent_filter:
            filters["agent_id"] = request.agent_filter
        if request.tags_filter:
            filters["tags"] = request.tags_filter
        
        # Query knowledge graph
        result = await manager.query_knowledge_graph(
            query=request.query,
            query_type=request.query_type,
            filters=filters
        )
        
        query_time = (datetime.now() - start_time).total_seconds()
        
        return KnowledgeQueryResponse(
            results=result["results"][:request.limit],
            query=request.query,
            total_results=len(result["results"]),
            query_time=query_time,
            knowledge_graph_stats={
                "filters_applied": result.get("filters_applied", {}),
                "query_type": request.query_type,
                "total_available": len(result["results"])
            }
        )
        
    except Exception as e:
        logger.error(f"Knowledge query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Knowledge query failed: {str(e)}")

@memory_router.get("/stats", response_model=MemoryStatsResponse)
async def get_memory_statistics(
    manager: CogneeModelManager = Depends(get_memory_manager)
):
    """Get comprehensive memory system statistics"""
    try:
        stats = manager.get_memory_statistics()
        
        return MemoryStatsResponse(
            memory_enabled=stats["memory_enabled"],
            cognee_initialized=stats["cognee_initialized"],
            statistics=stats["statistics"],
            configuration=stats["configuration"],
            performance=stats["performance"]
        )
        
    except Exception as e:
        logger.error(f"Failed to get memory stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get memory stats: {str(e)}")

@memory_router.get("/health")
async def memory_health_check(
    manager: CogneeModelManager = Depends(get_memory_manager)
):
    """Health check for memory system"""
    try:
        stats = manager.get_memory_statistics()
        
        health_status = {
            "status": "healthy" if stats["cognee_initialized"] else "degraded",
            "memory_enabled": stats["memory_enabled"],
            "cognee_initialized": stats["cognee_initialized"],
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }
        
        if not stats["cognee_initialized"]:
            health_status["warnings"] = ["Cognee not initialized - running without memory"]
        
        return health_status
        
    except Exception as e:
        logger.error(f"Memory health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Agent Memory Endpoints
@agents_router.get("/{agent_id}/memory", response_model=AgentMemoryResponse)
async def get_agent_memory(
    agent_id: str,
    request: AgentMemoryRequest,
    manager: CogneeModelManager = Depends(get_memory_manager)
):
    """Get memory entries for a specific agent"""
    try:
        # Query agent-specific memory
        result = await manager.query_knowledge_graph(
            query=f"agent:{agent_id} {request.query}",
            filters={"agent_id": agent_id}
        )
        
        # Get agent instance for statistics
        try:
            agent = await get_agent_instance(agent_id)
            agent_stats = agent.get_agent_stats()
        except:
            agent_stats = {"agent_id": agent_id, "statistics": {}}
        
        # Extract patterns if requested
        patterns = []
        if request.include_patterns:
            for entry in result["results"]:
                if isinstance(entry, dict) and "patterns" in entry:
                    patterns.extend(entry["patterns"])
        
        return AgentMemoryResponse(
            agent_id=agent_id,
            memory_entries=result["results"][:request.limit],
            patterns=list(set(patterns))[:10],  # Unique patterns, max 10
            statistics=agent_stats.get("statistics", {})
        )
        
    except Exception as e:
        logger.error(f"Failed to get agent memory: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent memory: {str(e)}")

@agents_router.delete("/{agent_id}/memory")
async def clear_agent_memory(
    agent_id: str,
    manager: CogneeModelManager = Depends(get_memory_manager)
):
    """Clear memory for a specific agent"""
    try:
        result = await manager.clear_agent_memory(agent_id)
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Failed to clear agent memory: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear agent memory: {str(e)}")

@memory_router.post("/batch-process")
async def batch_process_with_memory(
    request: BatchProcessRequest,
    background_tasks: BackgroundTasks,
    manager: CogneeModelManager = Depends(get_memory_manager)
):
    """Process multiple requests with memory in batches"""
    try:
        # Convert requests to MemoryEnabledRequest objects
        memory_requests = []
        for req in request.requests:
            memory_req = MemoryEnabledRequest(
                prompt=req.content,
                agent_id=req.agents[0] if req.agents else "general",
                memory_tags=req.memory_tags,
                include_memory_context=req.include_memory_context,
                persist_response=req.persist_response,
                session_id=req.session_id or str(uuid.uuid4()),
                max_tokens=req.max_tokens,
                temperature=req.temperature
            )
            memory_requests.append(memory_req)
        
        # Process batch
        responses = await manager.batch_process_with_memory(
            memory_requests, 
            batch_size=request.batch_size
        )
        
        # Format responses
        formatted_responses = []
        for response in responses:
            formatted_responses.append({
                "content": response.content,
                "provider": response.provider,
                "cost": response.cost,
                "memory_updated": response.memory_updated,
                "processing_time": response.total_processing_time
            })
        
        # Schedule background cleanup
        background_tasks.add_task(cleanup_batch_processing, len(formatted_responses))
        
        return {
            "processed_count": len(formatted_responses),
            "total_cost": sum(r["cost"] for r in formatted_responses),
            "batch_size": request.batch_size,
            "responses": formatted_responses,
            "performance": {
                "average_processing_time": sum(r["processing_time"] for r in formatted_responses) / len(formatted_responses),
                "total_memory_updates": sum(1 for r in formatted_responses if r["memory_updated"])
            }
        }
        
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")

# WebSocket handlers for real-time memory interactions
class MemoryWebSocketManager:
    """Manage WebSocket connections for memory-enabled real-time chat"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_contexts: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.session_contexts[session_id] = {
            "connected_at": datetime.now().isoformat(),
            "message_count": 0,
            "agents_used": set()
        }
        logger.info(f"WebSocket connected for session: {session_id}")
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.session_contexts:
            del self.session_contexts[session_id]
        logger.info(f"WebSocket disconnected for session: {session_id}")
    
    async def send_personal_message(self, message: dict, session_id: str):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_json(message)
                
                # Update session context
                if session_id in self.session_contexts:
                    self.session_contexts[session_id]["message_count"] += 1
                    
            except Exception as e:
                logger.error(f"Failed to send WebSocket message: {e}")
                self.disconnect(session_id)
    
    async def broadcast_to_session(self, message: dict, session_id: str):
        await self.send_personal_message(message, session_id)

memory_ws_manager = MemoryWebSocketManager()

@memory_router.websocket("/ws/{session_id}")
async def memory_websocket_endpoint(
    websocket: WebSocket, 
    session_id: str
):
    """WebSocket endpoint for real-time memory-enabled chat"""
    await memory_ws_manager.connect(websocket, session_id)
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            message_type = data.get("type", "chat")
            
            if message_type == "memory_chat":
                await handle_memory_chat_ws(websocket, session_id, data)
            elif message_type == "knowledge_query":
                await handle_knowledge_query_ws(websocket, session_id, data)
            elif message_type == "agent_stats":
                await handle_agent_stats_ws(websocket, session_id, data)
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })
                
    except WebSocketDisconnect:
        memory_ws_manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
        memory_ws_manager.disconnect(session_id)

async def handle_memory_chat_ws(websocket: WebSocket, session_id: str, data: dict):
    """Handle memory-enabled chat via WebSocket"""
    try:
        # Extract message data
        content = data.get("content", "")
        agents = data.get("agents", ["general"])
        include_context = data.get("include_context", True)
        
        # Create chat request
        chat_request = MemoryChatRequest(
            content=content,
            agents=agents,
            session_id=session_id,
            include_memory_context=include_context,
            memory_tags=["websocket", "realtime"],
            persist_response=True
        )
        
        # Process request
        manager = await get_memory_manager()
        
        # Send processing status
        await websocket.send_json({
            "type": "processing",
            "message": "Processing with memory-enabled agents...",
            "agents": agents
        })
        
        # Process each agent
        responses = []
        for agent_id in agents:
            try:
                if agent_id in MEMORY_ENABLED_AGENTS:
                    agent = await get_agent_instance(agent_id)
                    agent_response = await agent.process_request(
                        content,
                        context={"session_id": session_id, "websocket": True},
                        session_id=session_id
                    )
                    
                    response_data = {
                        "agent_id": agent_id,
                        "content": agent_response["response"],
                        "memory_used": agent_response.get("memory_stats", {}).get("context_used", False),
                        "cost": agent_response.get("cost", 0.0)
                    }
                    
                else:
                    # Fallback to model manager
                    memory_request = MemoryEnabledRequest(
                        prompt=content,
                        agent_id=agent_id,
                        session_id=session_id,
                        include_memory_context=include_context
                    )
                    
                    response = await manager.generate_with_memory(memory_request)
                    
                    response_data = {
                        "agent_id": agent_id,
                        "content": response.content,
                        "memory_used": bool(response.memory_context),
                        "cost": response.cost
                    }
                
                responses.append(response_data)
                
                # Send individual agent response
                await websocket.send_json({
                    "type": "agent_response",
                    "agent_id": agent_id,
                    "response": response_data
                })
                
            except Exception as e:
                logger.error(f"WebSocket agent processing failed: {e}")
                await websocket.send_json({
                    "type": "agent_error",
                    "agent_id": agent_id,
                    "error": str(e)
                })
        
        # Send final response
        await websocket.send_json({
            "type": "memory_chat_complete",
            "session_id": session_id,
            "responses": responses,
            "total_cost": sum(r["cost"] for r in responses),
            "memory_enabled": include_context
        })
        
    except Exception as e:
        logger.error(f"WebSocket memory chat failed: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"Memory chat failed: {str(e)}"
        })

async def handle_knowledge_query_ws(websocket: WebSocket, session_id: str, data: dict):
    """Handle knowledge graph queries via WebSocket"""
    try:
        query = data.get("query", "")
        agent_filter = data.get("agent_filter")
        
        manager = await get_memory_manager()
        
        # Query knowledge graph
        result = await manager.query_knowledge_graph(
            query=query,
            filters={"agent_id": agent_filter} if agent_filter else {}
        )
        
        await websocket.send_json({
            "type": "knowledge_query_response",
            "query": query,
            "results": result["results"][:10],  # Limit for WebSocket
            "total_results": len(result["results"])
        })
        
    except Exception as e:
        logger.error(f"WebSocket knowledge query failed: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"Knowledge query failed: {str(e)}"
        })

async def handle_agent_stats_ws(websocket: WebSocket, session_id: str, data: dict):
    """Handle agent statistics requests via WebSocket"""
    try:
        agent_id = data.get("agent_id")
        
        if agent_id and agent_id in MEMORY_ENABLED_AGENTS:
            agent = await get_agent_instance(agent_id)
            stats = agent.get_agent_stats()
        else:
            # Get all agent stats
            stats = {}
            for agent_type in MEMORY_ENABLED_AGENTS.keys():
                try:
                    agent = await get_agent_instance(agent_type)
                    stats[agent_type] = agent.get_agent_stats()
                except:
                    stats[agent_type] = {"error": "Failed to get stats"}
        
        await websocket.send_json({
            "type": "agent_stats_response",
            "agent_id": agent_id,
            "stats": stats
        })
        
    except Exception as e:
        logger.error(f"WebSocket agent stats failed: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"Agent stats failed: {str(e)}"
        })

# Background tasks
async def optimize_memory_performance(session_id: str):
    """Background task to optimize memory performance"""
    try:
        logger.info(f"Optimizing memory performance for session: {session_id}")
        # Placeholder for memory optimization logic
        await asyncio.sleep(1)  # Simulate optimization work
    except Exception as e:
        logger.error(f"Memory optimization failed: {e}")

async def cleanup_batch_processing(batch_count: int):
    """Background task to cleanup after batch processing"""
    try:
        logger.info(f"Cleaning up after batch processing {batch_count} requests")
        # Placeholder for cleanup logic
        await asyncio.sleep(0.5)  # Simulate cleanup work
    except Exception as e:
        logger.error(f"Batch cleanup failed: {e}")

# Include all routers
def get_memory_routers():
    """Get all memory-related routers"""
    return [memory_router, chat_router, agents_router, knowledge_router]