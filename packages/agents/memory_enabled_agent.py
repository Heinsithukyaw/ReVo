"""
Enhanced Agent Framework with Cognee Memory Integration
Base classes and implementations for memory-enabled agents
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import json
import uuid

from ..ai.cognee_model_manager import (
    CogneeModelManager, MemoryEnabledRequest, MemoryEnabledResponse
)

logger = logging.getLogger(__name__)

class MemoryEnabledAgent(ABC):
    """Base class for all memory-enabled agents"""
    
    def __init__(
        self, 
        agent_id: str, 
        model_manager: CogneeModelManager,
        memory_config: Dict[str, Any] = None
    ):
        self.agent_id = agent_id
        self.model_manager = model_manager
        self.memory_config = memory_config or {}
        self.knowledge_tags = self._get_knowledge_tags()
        self.system_prompt = self._get_system_prompt()
        
        # Agent-specific statistics
        self.stats = {
            "requests_processed": 0,
            "memory_hits": 0,
            "patterns_detected": 0,
            "knowledge_created": 0
        }
        
    async def process_request(
        self, 
        request: str, 
        context: Dict[str, Any] = None,
        session_id: str = None
    ) -> Dict[str, Any]:
        """Process request with memory capabilities"""
        
        start_time = datetime.now()
        
        try:
            # 1. Prepare memory-enabled request
            memory_request = MemoryEnabledRequest(
                prompt=request,
                agent_id=self.agent_id,
                context_query=self._generate_context_query(request, context),
                memory_tags=self.knowledge_tags,
                persist_response=True,
                session_id=session_id or str(uuid.uuid4()),
                system_prompt=self.system_prompt
            )
            
            # 2. Generate response with memory
            response = await self.model_manager.generate_with_memory(memory_request)
            
            # 3. Process agent-specific logic
            processed_response = await self._process_agent_logic(
                request, response, context
            )
            
            # 4. Update agent-specific memory
            await self._update_agent_memory(request, processed_response, context)
            
            # 5. Update statistics
            self.stats["requests_processed"] += 1
            if response.memory_context and response.memory_context.relevant_knowledge:
                self.stats["memory_hits"] += 1
            if response.memory_context and response.memory_context.patterns_detected:
                self.stats["patterns_detected"] += len(response.memory_context.patterns_detected)
            if response.knowledge_entities_created > 0:
                self.stats["knowledge_created"] += response.knowledge_entities_created
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "response": processed_response,
                "memory_context": response.memory_context.__dict__ if response.memory_context else None,
                "agent_id": self.agent_id,
                "cost": response.cost,
                "performance": {
                    "generation_time": response.generation_time,
                    "memory_retrieval_time": response.memory_retrieval_time,
                    "total_processing_time": processing_time,
                    "tokens_used": response.tokens_used
                },
                "memory_stats": {
                    "memory_updated": response.memory_updated,
                    "entities_created": response.knowledge_entities_created,
                    "context_used": bool(response.memory_context)
                }
            }
            
        except Exception as e:
            logger.error(f"Agent {self.agent_id} processing failed: {e}")
            return {
                "response": f"Error processing request: {str(e)}",
                "agent_id": self.agent_id,
                "error": True,
                "cost": 0.0
            }
    
    @abstractmethod
    async def _process_agent_logic(
        self, 
        request: str, 
        response: MemoryEnabledResponse, 
        context: Dict[str, Any]
    ) -> str:
        """Agent-specific processing logic"""
        pass
    
    @abstractmethod
    def _get_knowledge_tags(self) -> List[str]:
        """Get agent-specific knowledge tags"""
        pass
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        """Get agent-specific system prompt"""
        pass
    
    def _generate_context_query(self, request: str, context: Dict[str, Any]) -> str:
        """Generate context query for memory retrieval"""
        base_query = f"{self.agent_id} {request}"
        
        if context:
            # Add relevant context information
            if "file_path" in context:
                base_query += f" file:{context['file_path']}"
            if "repository" in context:
                base_query += f" repo:{context['repository']}"
            if "language" in context:
                base_query += f" lang:{context['language']}"
        
        return base_query
    
    async def _update_agent_memory(
        self,
        request: str,
        response: str,
        context: Dict[str, Any]
    ):
        """Update agent-specific memory with interaction"""
        try:
            # Create agent-specific memory entry
            memory_entry = {
                "agent_id": self.agent_id,
                "request": request,
                "response": response,
                "context": context or {},
                "timestamp": datetime.now().isoformat(),
                "tags": self.knowledge_tags,
                "specialization": self._get_agent_specialization()
            }
            
            # Store in memory (this would be handled by the model manager)
            logger.debug(f"Updated memory for agent {self.agent_id}")
            
        except Exception as e:
            logger.warning(f"Failed to update agent memory: {e}")
    
    def _get_agent_specialization(self) -> str:
        """Get agent specialization description"""
        return f"Specialized agent for {self.agent_id}"
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            "agent_id": self.agent_id,
            "specialization": self._get_agent_specialization(),
            "knowledge_tags": self.knowledge_tags,
            "statistics": self.stats.copy(),
            "memory_config": self.memory_config
        }

class CodeAnalystAgent(MemoryEnabledAgent):
    """Code analysis agent with pattern memory"""
    
    def _get_knowledge_tags(self) -> List[str]:
        return [
            "code_analysis", "code_patterns", "best_practices", 
            "code_quality", "refactoring", "architecture",
            "security", "performance", "maintainability"
        ]
    
    def _get_system_prompt(self) -> str:
        return """You are a specialized Code Analysis Agent with access to extensive code pattern memory.
        
Your expertise includes:
- Code quality assessment and improvement suggestions
- Security vulnerability detection
- Performance optimization recommendations
- Architecture pattern recognition
- Best practices enforcement
- Refactoring strategies

Use your memory of similar code patterns to provide contextual and informed analysis.
Always consider maintainability, scalability, and security in your recommendations."""
    
    async def _process_agent_logic(
        self, 
        request: str, 
        response: MemoryEnabledResponse, 
        context: Dict[str, Any]
    ) -> str:
        """Enhanced code analysis with pattern recognition"""
        
        # Extract code from request if present
        code = self._extract_code(request)
        
        if code:
            # Analyze patterns against memory
            patterns = await self._analyze_code_patterns(code, response.memory_context)
            
            # Enhance response with pattern insights
            enhanced_response = self._enhance_with_patterns(
                response.content, patterns, response.memory_context
            )
            
            return enhanced_response
        
        return response.content
    
    def _extract_code(self, request: str) -> Optional[str]:
        """Extract code snippets from request"""
        # Simple code extraction - look for code blocks
        if "```" in request:
            parts = request.split("```")
            if len(parts) >= 3:
                return parts[1]
        
        # Look for common code indicators
        code_indicators = ["def ", "class ", "function ", "import ", "from "]
        for indicator in code_indicators:
            if indicator in request:
                return request  # Treat entire request as code
        
        return None
    
    async def _analyze_code_patterns(
        self, 
        code: str, 
        memory_context: Optional[Any]
    ) -> List[Dict[str, Any]]:
        """Analyze code patterns using memory"""
        patterns = []
        
        # Basic pattern detection
        if "class " in code:
            patterns.append({
                "type": "class_definition",
                "description": "Class-based architecture pattern detected"
            })
        
        if "def " in code:
            patterns.append({
                "type": "function_definition", 
                "description": "Function-based pattern detected"
            })
        
        if "async def" in code:
            patterns.append({
                "type": "async_pattern",
                "description": "Asynchronous programming pattern detected"
            })
        
        # Add memory-based patterns if available
        if memory_context and memory_context.patterns_detected:
            for pattern in memory_context.patterns_detected:
                patterns.append({
                    "type": "memory_pattern",
                    "description": pattern
                })
        
        return patterns
    
    def _enhance_with_patterns(
        self, 
        response: str, 
        patterns: List[Dict[str, Any]], 
        memory_context: Optional[Any]
    ) -> str:
        """Enhance response with pattern insights"""
        
        if not patterns:
            return response
        
        pattern_section = "\n\n**Code Patterns Detected:**\n"
        for pattern in patterns[:3]:  # Top 3 patterns
            pattern_section += f"- {pattern['description']}\n"
        
        # Add memory insights if available
        if memory_context and memory_context.relevant_knowledge:
            pattern_section += "\n**Similar Code Patterns from Memory:**\n"
            for knowledge in memory_context.relevant_knowledge[:2]:
                if isinstance(knowledge, dict):
                    desc = knowledge.get("description", str(knowledge))
                    pattern_section += f"- {desc[:100]}...\n"
        
        return response + pattern_section

class DebugDetectiveAgent(MemoryEnabledAgent):
    """Debug analysis agent with solution memory"""
    
    def _get_knowledge_tags(self) -> List[str]:
        return [
            "debugging", "error_patterns", "solutions", "fixes", 
            "troubleshooting", "error_analysis", "stack_traces",
            "performance_issues", "memory_leaks", "concurrency"
        ]
    
    def _get_system_prompt(self) -> str:
        return """You are a specialized Debug Detective Agent with access to extensive error pattern memory.

Your expertise includes:
- Error pattern recognition and analysis
- Root cause identification
- Solution recommendation based on similar issues
- Performance debugging
- Memory leak detection
- Concurrency issue analysis

Use your memory of similar debugging cases to provide targeted solutions.
Always provide step-by-step debugging approaches and preventive measures."""
    
    async def _process_agent_logic(
        self, 
        request: str, 
        response: MemoryEnabledResponse, 
        context: Dict[str, Any]
    ) -> str:
        """Enhanced debugging with solution memory"""
        
        # Extract error information
        error_info = self._extract_error_info(request)
        
        if error_info:
            # Get similar solutions from memory
            similar_solutions = await self._get_similar_solutions(
                error_info, response.memory_context
            )
            
            # Generate enhanced debugging response
            enhanced_response = self._enhance_with_solutions(
                response.content, error_info, similar_solutions
            )
            
            return enhanced_response
        
        return response.content
    
    def _extract_error_info(self, request: str) -> Dict[str, Any]:
        """Extract error information from request"""
        error_info = {
            "error_type": None,
            "error_message": None,
            "stack_trace": None,
            "context": None
        }
        
        # Look for common error patterns
        error_keywords = ["error", "exception", "traceback", "failed", "bug"]
        
        for keyword in error_keywords:
            if keyword.lower() in request.lower():
                error_info["error_type"] = keyword
                break
        
        # Extract error messages (simple pattern matching)
        lines = request.split('\n')
        for line in lines:
            if any(word in line.lower() for word in ["error:", "exception:", "traceback"]):
                error_info["error_message"] = line.strip()
                break
        
        # Look for stack traces
        if "Traceback" in request or "at " in request:
            error_info["stack_trace"] = request
        
        return error_info
    
    async def _get_similar_solutions(
        self, 
        error_info: Dict[str, Any], 
        memory_context: Optional[Any]
    ) -> List[Dict[str, Any]]:
        """Get similar solutions from memory"""
        solutions = []
        
        if memory_context and memory_context.relevant_knowledge:
            for knowledge in memory_context.relevant_knowledge:
                if isinstance(knowledge, dict):
                    # Look for solution-related content
                    desc = knowledge.get("description", "")
                    if any(word in desc.lower() for word in ["solution", "fix", "resolve"]):
                        solutions.append({
                            "solution": desc,
                            "confidence": knowledge.get("confidence", 0.5)
                        })
        
        return solutions
    
    def _enhance_with_solutions(
        self, 
        response: str, 
        error_info: Dict[str, Any], 
        similar_solutions: List[Dict[str, Any]]
    ) -> str:
        """Enhance response with solution insights"""
        
        enhanced = response
        
        if error_info.get("error_type"):
            enhanced += f"\n\n**Error Analysis:**\n"
            enhanced += f"- Error Type: {error_info['error_type']}\n"
            
            if error_info.get("error_message"):
                enhanced += f"- Error Message: {error_info['error_message']}\n"
        
        if similar_solutions:
            enhanced += "\n**Similar Solutions from Memory:**\n"
            for solution in similar_solutions[:3]:
                enhanced += f"- {solution['solution'][:150]}...\n"
        
        return enhanced

class WorkflowManagerAgent(MemoryEnabledAgent):
    """Workflow management agent with process memory"""
    
    def _get_knowledge_tags(self) -> List[str]:
        return [
            "workflows", "processes", "automation", "templates",
            "best_practices", "optimization", "ci_cd", "deployment",
            "project_management", "task_orchestration"
        ]
    
    def _get_system_prompt(self) -> str:
        return """You are a specialized Workflow Manager Agent with access to extensive process memory.

Your expertise includes:
- Workflow design and optimization
- Process automation strategies
- CI/CD pipeline configuration
- Project management best practices
- Task orchestration and scheduling
- Performance optimization

Use your memory of successful workflows to recommend proven patterns and approaches.
Always consider scalability, maintainability, and team collaboration in your recommendations."""
    
    async def _process_agent_logic(
        self, 
        request: str, 
        response: MemoryEnabledResponse, 
        context: Dict[str, Any]
    ) -> str:
        """Enhanced workflow management with process memory"""
        
        # Analyze workflow requirements
        workflow_type = self._identify_workflow_type(request)
        
        # Get similar workflow templates from memory
        similar_workflows = await self._get_similar_workflows(
            workflow_type, response.memory_context
        )
        
        # Enhance response with workflow insights
        enhanced_response = self._enhance_with_workflows(
            response.content, workflow_type, similar_workflows
        )
        
        return enhanced_response
    
    def _identify_workflow_type(self, request: str) -> str:
        """Identify the type of workflow being requested"""
        workflow_types = {
            "ci_cd": ["ci", "cd", "pipeline", "build", "deploy"],
            "testing": ["test", "testing", "qa", "quality"],
            "deployment": ["deploy", "deployment", "release"],
            "development": ["dev", "development", "coding"],
            "monitoring": ["monitor", "monitoring", "alerts"]
        }
        
        request_lower = request.lower()
        
        for workflow_type, keywords in workflow_types.items():
            if any(keyword in request_lower for keyword in keywords):
                return workflow_type
        
        return "general"
    
    async def _get_similar_workflows(
        self, 
        workflow_type: str, 
        memory_context: Optional[Any]
    ) -> List[Dict[str, Any]]:
        """Get similar workflow templates from memory"""
        workflows = []
        
        if memory_context and memory_context.relevant_knowledge:
            for knowledge in memory_context.relevant_knowledge:
                if isinstance(knowledge, dict):
                    desc = knowledge.get("description", "")
                    if workflow_type in desc.lower() or "workflow" in desc.lower():
                        workflows.append({
                            "template": desc,
                            "type": workflow_type,
                            "confidence": knowledge.get("confidence", 0.5)
                        })
        
        return workflows
    
    def _enhance_with_workflows(
        self, 
        response: str, 
        workflow_type: str, 
        similar_workflows: List[Dict[str, Any]]
    ) -> str:
        """Enhance response with workflow insights"""
        
        enhanced = response
        
        enhanced += f"\n\n**Workflow Analysis:**\n"
        enhanced += f"- Workflow Type: {workflow_type}\n"
        
        if similar_workflows:
            enhanced += "\n**Similar Workflow Templates from Memory:**\n"
            for workflow in similar_workflows[:2]:
                enhanced += f"- {workflow['template'][:100]}...\n"
        
        return enhanced

class KnowledgeCoordinatorAgent(MemoryEnabledAgent):
    """Special agent for coordinating knowledge across other agents"""
    
    def _get_knowledge_tags(self) -> List[str]:
        return [
            "knowledge_coordination", "cross_agent_learning", "insights",
            "patterns", "collaboration", "knowledge_sharing", "synthesis"
        ]
    
    def _get_system_prompt(self) -> str:
        return """You are the Knowledge Coordinator Agent responsible for synthesizing insights across all agents.

Your responsibilities include:
- Coordinating knowledge sharing between agents
- Identifying cross-domain patterns and insights
- Synthesizing information from multiple agent specializations
- Facilitating collaborative problem-solving
- Maintaining knowledge consistency and quality

Use your access to all agent memories to provide comprehensive, multi-perspective solutions."""
    
    async def _process_agent_logic(
        self, 
        request: str, 
        response: MemoryEnabledResponse, 
        context: Dict[str, Any]
    ) -> str:
        """Coordinate knowledge across agents"""
        
        # Identify relevant agents for the request
        relevant_agents = self._identify_relevant_agents(request)
        
        # Synthesize cross-agent insights
        cross_insights = await self._synthesize_cross_agent_insights(
            request, response.memory_context, relevant_agents
        )
        
        # Enhance response with coordinated knowledge
        enhanced_response = self._enhance_with_coordination(
            response.content, cross_insights, relevant_agents
        )
        
        return enhanced_response
    
    def _identify_relevant_agents(self, request: str) -> List[str]:
        """Identify which agents are relevant for the request"""
        agent_keywords = {
            "code_analyst": ["code", "analysis", "quality", "refactor"],
            "debug_detective": ["debug", "error", "bug", "fix"],
            "workflow_manager": ["workflow", "process", "automation"],
            "security_auditor": ["security", "vulnerability", "audit"],
            "performance_optimizer": ["performance", "optimization", "speed"]
        }
        
        relevant = []
        request_lower = request.lower()
        
        for agent, keywords in agent_keywords.items():
            if any(keyword in request_lower for keyword in keywords):
                relevant.append(agent)
        
        return relevant or ["general"]
    
    async def _synthesize_cross_agent_insights(
        self, 
        request: str, 
        memory_context: Optional[Any], 
        relevant_agents: List[str]
    ) -> Dict[str, Any]:
        """Synthesize insights from multiple agent perspectives"""
        
        insights = {
            "cross_patterns": [],
            "collaborative_solutions": [],
            "agent_perspectives": {}
        }
        
        if memory_context and memory_context.relevant_knowledge:
            for knowledge in memory_context.relevant_knowledge:
                if isinstance(knowledge, dict):
                    agent_id = knowledge.get("agent_id", "unknown")
                    if agent_id in relevant_agents:
                        if agent_id not in insights["agent_perspectives"]:
                            insights["agent_perspectives"][agent_id] = []
                        insights["agent_perspectives"][agent_id].append(
                            knowledge.get("description", "")
                        )
        
        return insights
    
    def _enhance_with_coordination(
        self, 
        response: str, 
        cross_insights: Dict[str, Any], 
        relevant_agents: List[str]
    ) -> str:
        """Enhance response with coordinated knowledge"""
        
        enhanced = response
        
        enhanced += f"\n\n**Knowledge Coordination:**\n"
        enhanced += f"- Relevant Agents: {', '.join(relevant_agents)}\n"
        
        if cross_insights["agent_perspectives"]:
            enhanced += "\n**Multi-Agent Perspectives:**\n"
            for agent, perspectives in cross_insights["agent_perspectives"].items():
                enhanced += f"- {agent}: {perspectives[0][:80]}...\n"
        
        return enhanced

# Factory functions for creating memory-enabled agents
def create_code_analyst_agent(model_manager: CogneeModelManager) -> CodeAnalystAgent:
    """Create a memory-enabled code analyst agent"""
    return CodeAnalystAgent("code_analyst", model_manager)

def create_debug_detective_agent(model_manager: CogneeModelManager) -> DebugDetectiveAgent:
    """Create a memory-enabled debug detective agent"""
    return DebugDetectiveAgent("debug_detective", model_manager)

def create_workflow_manager_agent(model_manager: CogneeModelManager) -> WorkflowManagerAgent:
    """Create a memory-enabled workflow manager agent"""
    return WorkflowManagerAgent("workflow_manager", model_manager)

def create_knowledge_coordinator_agent(model_manager: CogneeModelManager) -> KnowledgeCoordinatorAgent:
    """Create a knowledge coordinator agent"""
    return KnowledgeCoordinatorAgent("knowledge_coordinator", model_manager)

# Agent registry for easy access
MEMORY_ENABLED_AGENTS = {
    "code_analyst": create_code_analyst_agent,
    "debug_detective": create_debug_detective_agent,
    "workflow_manager": create_workflow_manager_agent,
    "knowledge_coordinator": create_knowledge_coordinator_agent
}

def create_memory_enabled_agent(
    agent_type: str, 
    model_manager: CogneeModelManager
) -> MemoryEnabledAgent:
    """Factory function to create any memory-enabled agent"""
    if agent_type not in MEMORY_ENABLED_AGENTS:
        raise ValueError(f"Unknown agent type: {agent_type}")
    
    return MEMORY_ENABLED_AGENTS[agent_type](model_manager)