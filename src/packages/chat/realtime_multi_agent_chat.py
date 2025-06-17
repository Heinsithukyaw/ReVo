#!/usr/bin/env python3
"""
Enhanced Real-time Multi-Agent Chat System
Advanced conversational AI with real-time collaboration and WebSocket support
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, AsyncGenerator, Set
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import websockets
from websockets.server import WebSocketServerProtocol

# Import enhanced components
try:
    from packages.ai.enhanced_model_manager import EnhancedModelManager
    from packages.agents.workflow_intelligence import WorkflowIntelligence
    from packages.agents.code_analysis_agent import EnhancedCodeAnalysisAgent
    from packages.agents.debug_detective_agent import EnhancedDebugDetectiveAgent
except ImportError as e:
    logging.warning(f"Import error: {e}. Using fallback implementations.")
    
    class EnhancedModelManager:
        async def generate_response(self, prompt, **kwargs):
            return {"content": f"Enhanced response for: {prompt[:50]}...", "provider": "local", "cost": 0.001}
    
    class WorkflowIntelligence:
        async def create_workflow(self, name, description):
            return {"workflow_id": f"wf_{uuid.uuid4().hex[:8]}", "status": "created"}
    
    class EnhancedCodeAnalysisAgent:
        async def analyze_code(self, code, context=None):
            return {"analysis": "Code analysis complete", "score": 85, "suggestions": []}
    
    class EnhancedDebugDetectiveAgent:
        async def debug_issue(self, issue_description, context=None):
            return {"root_cause": "Issue identified", "severity": "medium", "fix_suggestions": []}

logger = logging.getLogger(__name__)

class ChatEventType(Enum):
    MESSAGE = "message"
    AGENT_THINKING = "agent_thinking"
    AGENT_RESPONSE = "agent_response"
    COLLABORATION_START = "collaboration_start"
    COLLABORATION_UPDATE = "collaboration_update"
    COLLABORATION_COMPLETE = "collaboration_complete"
    WORKFLOW_CREATED = "workflow_created"
    SESSION_UPDATE = "session_update"
    ERROR = "error"

class AgentStatus(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    RESPONDING = "responding"
    COLLABORATING = "collaborating"
    COMPLETE = "complete"

@dataclass
class ChatEvent:
    """Real-time chat event for WebSocket communication"""
    event_type: ChatEventType
    session_id: str
    data: Dict[str, Any]
    timestamp: datetime = None
    agent_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
    
    def to_json(self) -> str:
        """Convert to JSON for WebSocket transmission"""
        return json.dumps({
            "event_type": self.event_type.value,
            "session_id": self.session_id,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "agent_id": self.agent_id
        })

@dataclass
class AgentState:
    """Track individual agent state in real-time"""
    agent_id: str
    role: str
    status: AgentStatus
    current_task: Optional[str] = None
    progress: float = 0.0
    last_update: datetime = None
    
    def __post_init__(self):
        if self.last_update is None:
            self.last_update = datetime.now(timezone.utc)

class RealTimeMultiAgentChat:
    """Enhanced real-time multi-agent chat system with WebSocket support"""
    
    def __init__(self):
        self.model_manager = EnhancedModelManager()
        self.workflow_intelligence = WorkflowIntelligence()
        self.code_analyst = EnhancedCodeAnalysisAgent()
        self.debug_detective = EnhancedDebugDetectiveAgent()
        
        # Real-time state management
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.connected_clients: Dict[str, WebSocketServerProtocol] = {}
        self.agent_states: Dict[str, AgentState] = {}
        
        # Collaboration patterns
        self.collaboration_patterns = self._initialize_collaboration_patterns()
        
        # Event queue for real-time updates
        self.event_queue: asyncio.Queue = asyncio.Queue()
        
        logger.info("Real-time Multi-Agent Chat System initialized")
    
    def _initialize_collaboration_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize advanced collaboration patterns"""
        return {
            "code_review_swarm": {
                "agents": ["code_analyst", "debug_detective"],
                "pattern": "parallel_analysis",
                "merge_strategy": "consensus_weighted",
                "real_time": True,
                "streaming": True
            },
            "debugging_cascade": {
                "agents": ["debug_detective", "code_analyst", "workflow_manager"],
                "pattern": "sequential_cascade",
                "merge_strategy": "progressive_refinement",
                "real_time": True,
                "streaming": True
            },
            "workflow_orchestration": {
                "agents": ["workflow_manager", "code_analyst"],
                "pattern": "iterative_collaboration",
                "merge_strategy": "integrated_solution",
                "real_time": True,
                "streaming": True
            },
            "comprehensive_swarm": {
                "agents": ["code_analyst", "debug_detective", "workflow_manager", "coordinator"],
                "pattern": "swarm_intelligence",
                "merge_strategy": "holistic_synthesis",
                "real_time": True,
                "streaming": True
            }
        }
    
    async def register_websocket_client(self, websocket: WebSocketServerProtocol, session_id: str):
        """Register a WebSocket client for real-time updates"""
        self.connected_clients[session_id] = websocket
        logger.info(f"WebSocket client registered for session {session_id}")
        
        # Send initial session state
        if session_id in self.active_sessions:
            await self._send_event(ChatEvent(
                event_type=ChatEventType.SESSION_UPDATE,
                session_id=session_id,
                data={"status": "connected", "session_state": self.active_sessions[session_id]}
            ))
    
    async def unregister_websocket_client(self, session_id: str):
        """Unregister a WebSocket client"""
        if session_id in self.connected_clients:
            del self.connected_clients[session_id]
            logger.info(f"WebSocket client unregistered for session {session_id}")
    
    async def _send_event(self, event: ChatEvent):
        """Send event to connected WebSocket clients"""
        if event.session_id in self.connected_clients:
            try:
                websocket = self.connected_clients[event.session_id]
                await websocket.send(event.to_json())
            except Exception as e:
                logger.error(f"Error sending WebSocket event: {e}")
                # Remove disconnected client
                await self.unregister_websocket_client(event.session_id)
    
    async def start_realtime_session(self, user_id: str, initial_message: str, 
                                   collaboration_pattern: str = "comprehensive_swarm") -> str:
        """Start a new real-time multi-agent chat session"""
        session_id = str(uuid.uuid4())
        
        # Initialize session state
        self.active_sessions[session_id] = {
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "active",
            "collaboration_pattern": collaboration_pattern,
            "message_history": [],
            "agent_states": {},
            "shared_context": {},
            "real_time_updates": True
        }
        
        # Send session start event
        await self._send_event(ChatEvent(
            event_type=ChatEventType.SESSION_UPDATE,
            session_id=session_id,
            data={"status": "session_started", "pattern": collaboration_pattern}
        ))
        
        # Process initial message
        await self.process_realtime_message(session_id, initial_message, user_id)
        
        return session_id
    
    async def process_realtime_message(self, session_id: str, message: str, user_id: str):
        """Process a message with real-time multi-agent collaboration"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        pattern = self.collaboration_patterns[session["collaboration_pattern"]]
        
        # Add message to history
        session["message_history"].append({
            "id": str(uuid.uuid4()),
            "type": "user",
            "content": message,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Send message received event
        await self._send_event(ChatEvent(
            event_type=ChatEventType.MESSAGE,
            session_id=session_id,
            data={"message": message, "user_id": user_id}
        ))
        
        # Start collaboration
        await self._start_realtime_collaboration(session_id, message, pattern)
    
    async def _start_realtime_collaboration(self, session_id: str, message: str, pattern: Dict[str, Any]):
        """Start real-time agent collaboration"""
        agents = pattern["agents"]
        collaboration_pattern = pattern["pattern"]
        
        # Send collaboration start event
        await self._send_event(ChatEvent(
            event_type=ChatEventType.COLLABORATION_START,
            session_id=session_id,
            data={
                "agents": agents,
                "pattern": collaboration_pattern,
                "message": message
            }
        ))
        
        # Initialize agent states
        for agent in agents:
            agent_id = f"{agent}_{uuid.uuid4().hex[:8]}"
            self.agent_states[agent_id] = AgentState(
                agent_id=agent_id,
                role=agent,
                status=AgentStatus.THINKING,
                current_task=f"Processing: {message[:50]}..."
            )
        
        # Execute collaboration pattern
        if collaboration_pattern == "parallel_analysis":
            await self._execute_parallel_analysis(session_id, message, agents)
        elif collaboration_pattern == "sequential_cascade":
            await self._execute_sequential_cascade(session_id, message, agents)
        elif collaboration_pattern == "swarm_intelligence":
            await self._execute_swarm_intelligence(session_id, message, agents)
        else:
            await self._execute_default_collaboration(session_id, message, agents)
    
    async def _execute_parallel_analysis(self, session_id: str, message: str, agents: List[str]):
        """Execute parallel analysis collaboration pattern"""
        tasks = []
        
        for agent in agents:
            task = asyncio.create_task(self._agent_process_with_updates(session_id, agent, message))
            tasks.append(task)
        
        # Wait for all agents to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Merge results
        merged_response = await self._merge_agent_responses(session_id, results, "consensus_weighted")
        
        # Send final response
        await self._send_final_response(session_id, merged_response)
    
    async def _execute_sequential_cascade(self, session_id: str, message: str, agents: List[str]):
        """Execute sequential cascade collaboration pattern"""
        context = {"original_message": message}
        
        for i, agent in enumerate(agents):
            # Update agent status
            agent_id = f"{agent}_{uuid.uuid4().hex[:8]}"
            
            # Send agent thinking event
            await self._send_event(ChatEvent(
                event_type=ChatEventType.AGENT_THINKING,
                session_id=session_id,
                agent_id=agent_id,
                data={"agent": agent, "step": i+1, "total_steps": len(agents)}
            ))
            
            # Process with current context
            result = await self._agent_process_with_context(agent, message, context)
            
            # Update context for next agent
            context[f"{agent}_result"] = result
            
            # Send agent response event
            await self._send_event(ChatEvent(
                event_type=ChatEventType.AGENT_RESPONSE,
                session_id=session_id,
                agent_id=agent_id,
                data={"agent": agent, "result": result, "step": i+1}
            ))
        
        # Create final response from cascade
        final_response = await self._create_cascade_response(context)
        await self._send_final_response(session_id, final_response)
    
    async def _execute_swarm_intelligence(self, session_id: str, message: str, agents: List[str]):
        """Execute swarm intelligence collaboration pattern"""
        # Phase 1: Initial parallel processing
        initial_tasks = []
        for agent in agents:
            task = asyncio.create_task(self._agent_process_with_updates(session_id, agent, message))
            initial_tasks.append(task)
        
        initial_results = await asyncio.gather(*initial_tasks, return_exceptions=True)
        
        # Phase 2: Cross-agent collaboration and refinement
        await self._send_event(ChatEvent(
            event_type=ChatEventType.COLLABORATION_UPDATE,
            session_id=session_id,
            data={"phase": "cross_collaboration", "agents": agents}
        ))
        
        # Agents review each other's work
        refined_results = []
        for i, agent in enumerate(agents):
            other_results = [r for j, r in enumerate(initial_results) if j != i and not isinstance(r, Exception)]
            refined_result = await self._agent_refine_with_peer_input(agent, message, initial_results[i], other_results)
            refined_results.append(refined_result)
        
        # Phase 3: Consensus building
        consensus_response = await self._build_consensus_response(session_id, refined_results)
        await self._send_final_response(session_id, consensus_response)
    
    async def _agent_process_with_updates(self, session_id: str, agent: str, message: str):
        """Process message with an agent while sending real-time updates"""
        agent_id = f"{agent}_{uuid.uuid4().hex[:8]}"
        
        try:
            # Send thinking event
            await self._send_event(ChatEvent(
                event_type=ChatEventType.AGENT_THINKING,
                session_id=session_id,
                agent_id=agent_id,
                data={"agent": agent, "status": "analyzing"}
            ))
            
            # Simulate processing time with progress updates
            for progress in [0.2, 0.5, 0.8]:
                await asyncio.sleep(0.5)  # Simulate processing
                await self._send_event(ChatEvent(
                    event_type=ChatEventType.COLLABORATION_UPDATE,
                    session_id=session_id,
                    agent_id=agent_id,
                    data={"agent": agent, "progress": progress, "status": "processing"}
                ))
            
            # Get agent response based on type
            if agent == "code_analyst":
                result = await self.code_analyst.analyze_code(message)
            elif agent == "debug_detective":
                result = await self.debug_detective.debug_issue(message)
            elif agent == "workflow_manager":
                result = await self.workflow_intelligence.create_workflow("Auto-generated", message)
            else:
                result = await self.model_manager.generate_response(f"As a {agent}, analyze: {message}")
            
            # Send response event
            await self._send_event(ChatEvent(
                event_type=ChatEventType.AGENT_RESPONSE,
                session_id=session_id,
                agent_id=agent_id,
                data={"agent": agent, "result": result, "status": "complete"}
            ))
            
            return result
            
        except Exception as e:
            logger.error(f"Error in agent {agent} processing: {e}")
            await self._send_event(ChatEvent(
                event_type=ChatEventType.ERROR,
                session_id=session_id,
                agent_id=agent_id,
                data={"agent": agent, "error": str(e)}
            ))
            return {"error": str(e), "agent": agent}
    
    async def _agent_process_with_context(self, agent: str, message: str, context: Dict[str, Any]):
        """Process message with an agent using provided context"""
        enhanced_prompt = f"Context: {json.dumps(context)}\n\nMessage: {message}"
        
        if agent == "code_analyst":
            return await self.code_analyst.analyze_code(enhanced_prompt, context)
        elif agent == "debug_detective":
            return await self.debug_detective.debug_issue(enhanced_prompt, context)
        elif agent == "workflow_manager":
            return await self.workflow_intelligence.create_workflow("Context-aware", enhanced_prompt)
        else:
            return await self.model_manager.generate_response(enhanced_prompt)
    
    async def _agent_refine_with_peer_input(self, agent: str, original_message: str, 
                                          own_result: Any, peer_results: List[Any]):
        """Refine agent response based on peer input"""
        refinement_prompt = f"""
        Original message: {original_message}
        Your initial response: {json.dumps(own_result)}
        Peer responses: {json.dumps(peer_results)}
        
        Please refine your response considering the peer input.
        """
        
        return await self.model_manager.generate_response(refinement_prompt)
    
    async def _merge_agent_responses(self, session_id: str, results: List[Any], strategy: str):
        """Merge multiple agent responses using specified strategy"""
        valid_results = [r for r in results if not isinstance(r, Exception)]
        
        if strategy == "consensus_weighted":
            # Weight responses by confidence and combine
            merged = {
                "type": "consensus_response",
                "agents_involved": len(valid_results),
                "combined_analysis": valid_results,
                "confidence": sum(r.get("confidence", 0.8) for r in valid_results if isinstance(r, dict)) / len(valid_results),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            # Default merge strategy
            merged = {
                "type": "merged_response",
                "results": valid_results,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        return merged
    
    async def _create_cascade_response(self, context: Dict[str, Any]):
        """Create final response from cascade context"""
        return {
            "type": "cascade_response",
            "final_analysis": "Comprehensive analysis complete",
            "cascade_results": context,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def _build_consensus_response(self, session_id: str, refined_results: List[Any]):
        """Build consensus response from refined agent results"""
        await self._send_event(ChatEvent(
            event_type=ChatEventType.COLLABORATION_UPDATE,
            session_id=session_id,
            data={"phase": "consensus_building", "results_count": len(refined_results)}
        ))
        
        return {
            "type": "consensus_response",
            "consensus_analysis": "Multi-agent consensus achieved",
            "refined_results": refined_results,
            "confidence": 0.95,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def _send_final_response(self, session_id: str, response: Dict[str, Any]):
        """Send final collaboration response"""
        # Add to session history
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["message_history"].append({
                "id": str(uuid.uuid4()),
                "type": "multi_agent_response",
                "content": response,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        # Send collaboration complete event
        await self._send_event(ChatEvent(
            event_type=ChatEventType.COLLABORATION_COMPLETE,
            session_id=session_id,
            data={"response": response, "status": "complete"}
        ))
    
    async def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """Get current session state"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        return self.active_sessions[session_id]
    
    async def end_session(self, session_id: str):
        """End a chat session"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["status"] = "ended"
            self.active_sessions[session_id]["ended_at"] = datetime.now(timezone.utc).isoformat()
            
            # Send session end event
            await self._send_event(ChatEvent(
                event_type=ChatEventType.SESSION_UPDATE,
                session_id=session_id,
                data={"status": "session_ended"}
            ))
            
            # Clean up WebSocket connection
            await self.unregister_websocket_client(session_id)

# WebSocket server for real-time communication
class MultiAgentChatWebSocketServer:
    """WebSocket server for real-time multi-agent chat"""
    
    def __init__(self, chat_system: RealTimeMultiAgentChat):
        self.chat_system = chat_system
        self.server = None
    
    async def handle_websocket(self, websocket: WebSocketServerProtocol, path: str):
        """Handle WebSocket connections"""
        session_id = None
        try:
            # Wait for session registration
            async for message in websocket:
                data = json.loads(message)
                
                if data.get("type") == "register":
                    session_id = data.get("session_id")
                    await self.chat_system.register_websocket_client(websocket, session_id)
                    await websocket.send(json.dumps({"type": "registered", "session_id": session_id}))
                
                elif data.get("type") == "message" and session_id:
                    await self.chat_system.process_realtime_message(
                        session_id, 
                        data.get("content", ""), 
                        data.get("user_id", "anonymous")
                    )
                
                elif data.get("type") == "ping":
                    await websocket.send(json.dumps({"type": "pong"}))
        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"WebSocket connection closed for session {session_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            if session_id:
                await self.chat_system.unregister_websocket_client(session_id)
    
    async def start_server(self, host: str = "localhost", port: int = 8765):
        """Start the WebSocket server"""
        self.server = await websockets.serve(self.handle_websocket, host, port)
        logger.info(f"Multi-Agent Chat WebSocket server started on {host}:{port}")
        return self.server

# Example usage and testing
async def main():
    """Example usage of the real-time multi-agent chat system"""
    chat_system = RealTimeMultiAgentChat()
    
    # Start a session
    session_id = await chat_system.start_realtime_session(
        user_id="test_user",
        initial_message="I need help debugging a performance issue in my Python code",
        collaboration_pattern="debugging_cascade"
    )
    
    print(f"Started session: {session_id}")
    
    # Simulate some processing time
    await asyncio.sleep(5)
    
    # Get session state
    state = await chat_system.get_session_state(session_id)
    print(f"Session state: {json.dumps(state, indent=2)}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())