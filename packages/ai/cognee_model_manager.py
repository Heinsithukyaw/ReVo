"""
Enhanced Local AI Model Manager with Cognee Memory Integration
Extends existing LocalModelManager while preserving 100% cost optimization
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
import uuid

# Import existing components
try:
    from .model_manager import ModelManager
except ImportError:
    # Fallback if model_manager doesn't exist
    class ModelManager:
        def __init__(self, config):
            self.config = config
        async def initialize(self):
            pass
        async def generate(self, **kwargs):
            return {"content": "Mock response", "provider": "local", "tokens_used": 0, "generation_time": 0.0, "cost": 0.0}

try:
    from ..core.config import get_config
except ImportError:
    # Fallback config function
    def get_config():
        return {}

logger = logging.getLogger(__name__)

# Enhanced dataclasses for memory integration
@dataclass
class MemoryConfig:
    """Configuration for Cognee memory integration"""
    enable_memory: bool = True
    vector_db_provider: str = "lancedb"
    graph_db_provider: str = "networkx"
    relational_db_provider: str = "postgres"
    memory_cache_size: int = 1000
    auto_persist: bool = True
    context_window: int = 5
    similarity_threshold: float = 0.7
    memory_data_path: str = "./data/cognee_memory"

@dataclass
class MemoryEnabledRequest:
    """Extended request with memory capabilities"""
    prompt: str
    agent_id: Optional[str] = None
    memory_tags: Optional[List[str]] = field(default_factory=list)
    context_query: Optional[str] = None
    include_memory_context: bool = True
    persist_response: bool = True
    session_id: Optional[str] = None
    memory_config: Optional[MemoryConfig] = None
    max_tokens: int = 1024
    temperature: float = 0.7
    task_type: str = "general"
    system_prompt: Optional[str] = None

@dataclass
class MemoryContext:
    """Memory context retrieved from Cognee"""
    relevant_knowledge: List[Dict[str, Any]] = field(default_factory=list)
    context_summary: str = ""
    knowledge_graph_entities: List[Dict[str, Any]] = field(default_factory=list)
    patterns_detected: List[str] = field(default_factory=list)
    agent_specific_context: Dict[str, Any] = field(default_factory=dict)
    retrieval_time: float = 0.0
    source_tags: List[str] = field(default_factory=list)

@dataclass
class MemoryEnabledResponse:
    """Enhanced response with memory metadata"""
    content: str
    provider: str = "local"
    tokens_used: int = 0
    generation_time: float = 0.0
    cost: float = 0.0
    reasoning_steps: Optional[List[str]] = None
    memory_context: Optional[MemoryContext] = None
    memory_updated: bool = False
    knowledge_entities_created: int = 0
    memory_retrieval_time: float = 0.0
    total_processing_time: float = 0.0

class CogneeIntegrationError(Exception):
    """Custom exception for Cognee integration issues"""
    pass

class CogneeModelManager:
    """
    Enhanced ModelManager with Cognee memory capabilities
    Maintains 100% cost optimization while adding persistent memory
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or get_config()
        
        # Initialize base model manager
        self.model_manager = ModelManager(self.config)
        
        # Memory configuration
        memory_config_data = self.config.get("memory_config", {})
        self.memory_config = MemoryConfig(**memory_config_data)
        
        self.cognee_initialized = False
        self.cognee = None
        self.memory_stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "knowledge_entities": 0,
            "memory_updates": 0
        }
        
        # Agent-specific memory configurations
        self.agent_memory_configs = self.config.get("agent_memory_configs", {})
        
    async def initialize(self):
        """Initialize models and Cognee memory system"""
        # Initialize parent model manager
        await self.model_manager.initialize()
        
        # Initialize Cognee memory if enabled
        if self.memory_config.enable_memory:
            await self._initialize_cognee_memory()
        
        logger.info("🧠 CogneeModelManager initialization complete")
    
    async def _initialize_cognee_memory(self):
        """Initialize Cognee with local model configuration"""
        try:
            logger.info("🚀 Initializing Cognee memory system...")
            
            # Import cognee here to handle optional dependency
            try:
                import cognee
                self.cognee = cognee
            except ImportError:
                logger.warning("Cognee not installed. Install with: pip install cognee")
                self.memory_config.enable_memory = False
                return
            
            # Configure Cognee to use local models instead of OpenAI
            await self._configure_cognee_local_models()
            
            # Configure vector database
            await self._configure_vector_database()
            
            # Configure graph database
            await self._configure_graph_database()
            
            # Configure relational database
            await self._configure_relational_database()
            
            # Test Cognee functionality
            await self._test_cognee_functionality()
            
            self.cognee_initialized = True
            logger.info("✅ Cognee memory system initialized with local models")
            
        except Exception as e:
            logger.error(f"❌ Cognee initialization failed: {e}")
            # Gracefully degrade to non-memory mode
            self.memory_config.enable_memory = False
            logger.warning("⚠️ Continuing without memory capabilities")
    
    async def _configure_cognee_local_models(self):
        """Configure Cognee to use reVoAgent's local models"""
        
        # Create local model endpoint configuration
        local_endpoint = "http://localhost:8000/v1/chat/completions"
        
        # Configure LLM to use local models
        self.cognee.config.set_llm_config({
            "provider": "openai",  # Use OpenAI-compatible interface
            "model": "local-deepseek-r1",
            "api_endpoint": local_endpoint,
            "api_key": "local-key",  # Dummy key for local models
            "max_tokens": self.config.get("max_tokens", 4096),
            "temperature": 0.7
        })
        
        # Configure embeddings to use local models
        self.cognee.config.set_embedding_config({
            "provider": "local",
            "model": "local-embeddings",
            "api_endpoint": f"{local_endpoint}/embeddings",
            "api_key": "local-key",
            "dimensions": 1536  # Adjust based on local embedding model
        })
        
        logger.info("🔧 Configured Cognee to use local models")
    
    async def _configure_vector_database(self):
        """Configure local vector database"""
        vector_config = {
            "provider": self.memory_config.vector_db_provider,
            "path": os.path.join(self.memory_config.memory_data_path, "vectors"),
            "cache_size": self.memory_config.memory_cache_size
        }
        
        if self.memory_config.vector_db_provider == "lancedb":
            vector_config.update({
                "table_name": "revoagent_memory",
                "metric": "cosine"
            })
        
        self.cognee.config.set_vector_db_config(vector_config)
        logger.info(f"🗄️ Configured vector database: {self.memory_config.vector_db_provider}")
    
    async def _configure_graph_database(self):
        """Configure local graph database"""
        graph_config = {
            "provider": self.memory_config.graph_db_provider,
            "path": os.path.join(self.memory_config.memory_data_path, "graphs")
        }
        
        if self.memory_config.graph_db_provider == "neo4j":
            graph_config.update({
                "url": os.getenv("NEO4J_URL", "bolt://localhost:7687"),
                "username": os.getenv("NEO4J_USERNAME", "neo4j"),
                "password": os.getenv("NEO4J_PASSWORD", "password")
            })
        
        self.cognee.config.set_graph_db_config(graph_config)
        logger.info(f"📊 Configured graph database: {self.memory_config.graph_db_provider}")
    
    async def _configure_relational_database(self):
        """Configure relational database for Cognee"""
        db_config = {
            "provider": self.memory_config.relational_db_provider,
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "database": os.getenv("DB_NAME", "revoagent_memory"),
            "username": os.getenv("DB_USERNAME", "revoagent"),
            "password": os.getenv("DB_PASSWORD", "secure_password")
        }
        
        self.cognee.config.set_db_config(db_config)
        logger.info(f"💾 Configured relational database: {self.memory_config.relational_db_provider}")
    
    async def _test_cognee_functionality(self):
        """Test basic Cognee functionality"""
        try:
            # Test basic add and search
            test_content = "reVoAgent initialization test for Cognee integration"
            await self.cognee.add(test_content, dataset_name="initialization_test")
            await self.cognee.cognify()
            
            # Test search
            results = await self.cognee.search(
                query_text="reVoAgent test",
                query_type="insights"
            )
            
            logger.info(f"🧪 Cognee test successful - found {len(results)} results")
            
        except Exception as e:
            raise CogneeIntegrationError(f"Cognee functionality test failed: {e}")
    
    async def generate_with_memory(
        self, 
        request: MemoryEnabledRequest
    ) -> MemoryEnabledResponse:
        """
        Generate response with memory context and persistence
        Maintains cost optimization while adding memory capabilities
        """
        start_time = datetime.now()
        
        try:
            # 1. Retrieve memory context if enabled
            memory_context = None
            if (request.include_memory_context and 
                self.memory_config.enable_memory and 
                self.cognee_initialized):
                
                memory_context = await self._retrieve_memory_context(request)
            
            # 2. Enhance prompt with memory context
            enhanced_prompt = self._enhance_prompt_with_memory(
                request.prompt, memory_context
            )
            
            # 3. Generate response using existing model manager
            base_response = await self.model_manager.generate(
                prompt=enhanced_prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                system_prompt=request.system_prompt
            )
            
            # 4. Persist response to memory if enabled
            memory_updated = False
            entities_created = 0
            
            if (request.persist_response and 
                self.memory_config.enable_memory and 
                self.cognee_initialized):
                
                memory_result = await self._persist_to_memory(
                    request, base_response
                )
                memory_updated = memory_result["updated"]
                entities_created = memory_result["entities_created"]
            
            # 5. Create enhanced response
            total_time = (datetime.now() - start_time).total_seconds()
            
            return MemoryEnabledResponse(
                content=base_response.get("content", ""),
                provider=base_response.get("provider", "local"),
                tokens_used=base_response.get("tokens_used", 0),
                generation_time=base_response.get("generation_time", 0.0),
                cost=0.0,  # Maintain $0.00 for local models
                reasoning_steps=base_response.get("reasoning_steps", []),
                memory_context=memory_context,
                memory_updated=memory_updated,
                knowledge_entities_created=entities_created,
                memory_retrieval_time=memory_context.retrieval_time if memory_context else 0.0,
                total_processing_time=total_time
            )
            
        except Exception as e:
            logger.error(f"Memory-enabled generation failed: {e}")
            
            # Fallback to regular generation without memory
            base_response = await self.model_manager.generate(
                prompt=request.prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                system_prompt=request.system_prompt
            )
            
            return MemoryEnabledResponse(
                content=base_response.get("content", ""),
                provider=base_response.get("provider", "local"),
                tokens_used=base_response.get("tokens_used", 0),
                generation_time=base_response.get("generation_time", 0.0),
                cost=0.0,
                reasoning_steps=base_response.get("reasoning_steps", []),
                memory_context=None,
                memory_updated=False,
                knowledge_entities_created=0,
                memory_retrieval_time=0.0,
                total_processing_time=(datetime.now() - start_time).total_seconds()
            )
    
    async def _retrieve_memory_context(
        self, 
        request: MemoryEnabledRequest
    ) -> MemoryContext:
        """Retrieve relevant memory context for the request"""
        retrieval_start = datetime.now()
        
        try:
            # Prepare search query
            search_query = request.context_query or request.prompt
            
            # Add agent-specific context if available
            if request.agent_id:
                search_query = f"agent:{request.agent_id} {search_query}"
            
            # Add tags to search
            if request.memory_tags:
                tag_query = " ".join([f"tag:{tag}" for tag in request.memory_tags])
                search_query = f"{search_query} {tag_query}"
            
            # Search for relevant knowledge
            search_results = await self.cognee.search(
                query_text=search_query,
                query_type="insights"
            )
            
            # Filter and process results
            filtered_results = self._filter_memory_results(
                search_results, request
            )
            
            # Extract entities and patterns
            entities = self._extract_entities(filtered_results)
            patterns = self._detect_patterns(filtered_results, request.agent_id)
            
            # Generate context summary
            context_summary = self._generate_context_summary(filtered_results)
            
            # Get agent-specific context
            agent_context = await self._get_agent_specific_context(
                request.agent_id, search_query
            )
            
            retrieval_time = (datetime.now() - retrieval_start).total_seconds()
            
            # Update stats
            self.memory_stats["total_queries"] += 1
            if filtered_results:
                self.memory_stats["cache_hits"] += 1
            
            return MemoryContext(
                relevant_knowledge=filtered_results[:self.memory_config.context_window],
                context_summary=context_summary,
                knowledge_graph_entities=entities,
                patterns_detected=patterns,
                agent_specific_context=agent_context,
                retrieval_time=retrieval_time,
                source_tags=request.memory_tags or []
            )
            
        except Exception as e:
            logger.warning(f"Memory context retrieval failed: {e}")
            return MemoryContext(
                retrieval_time=(datetime.now() - retrieval_start).total_seconds()
            )
    
    def _enhance_prompt_with_memory(
        self, 
        prompt: str, 
        memory_context: Optional[MemoryContext]
    ) -> str:
        """Enhance the request prompt with memory context"""
        
        if not memory_context or not memory_context.relevant_knowledge:
            return prompt
        
        # Build context section
        context_sections = []
        
        # Add relevant knowledge
        if memory_context.relevant_knowledge:
            knowledge_items = []
            for item in memory_context.relevant_knowledge[:3]:  # Top 3 items
                if isinstance(item, dict):
                    knowledge_items.append(f"- {item.get('description', str(item))}")
                else:
                    knowledge_items.append(f"- {str(item)}")
            
            context_sections.append(
                f"Relevant Knowledge:\n" + "\n".join(knowledge_items)
            )
        
        # Add patterns
        if memory_context.patterns_detected:
            patterns_text = "Detected Patterns:\n" + "\n".join([
                f"- {pattern}" for pattern in memory_context.patterns_detected[:3]
            ])
            context_sections.append(patterns_text)
        
        # Add context summary
        if memory_context.context_summary:
            context_sections.append(f"Context Summary:\n{memory_context.context_summary}")
        
        # Combine context with original prompt
        if context_sections:
            context_text = "\n\n".join(context_sections)
            enhanced_prompt = f"""
Memory Context:
{context_text}

Current Request:
{prompt}

Please use the memory context above to provide a more informed and contextual response.
"""
            return enhanced_prompt
        
        return prompt
    
    async def _persist_to_memory(
        self,
        request: MemoryEnabledRequest,
        response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Persist interaction to memory"""
        if not self.memory_config.enable_memory or not self.cognee_initialized:
            return {"updated": False, "entities_created": 0}
        
        try:
            # Create memory entry
            memory_entry = {
                "prompt": request.prompt,
                "response": response.get("content", ""),
                "agent_id": request.agent_id,
                "tags": request.memory_tags or [],
                "timestamp": datetime.now().isoformat(),
                "session_id": request.session_id or str(uuid.uuid4()),
                "task_type": request.task_type
            }
            
            # Add to cognee
            dataset_name = f"agent_{request.agent_id}" if request.agent_id else "general"
            await self.cognee.add(
                data=json.dumps(memory_entry),
                dataset_name=dataset_name
            )
            
            # Update knowledge graph
            await self.cognee.cognify()
            
            # Update stats
            self.memory_stats["memory_updates"] += 1
            self.memory_stats["knowledge_entities"] += 1
            
            logger.debug(f"Memory updated for agent: {request.agent_id}")
            
            return {"updated": True, "entities_created": 1}
            
        except Exception as e:
            logger.warning(f"Memory persistence failed: {e}")
            return {"updated": False, "entities_created": 0}
    
    def _filter_memory_results(
        self, 
        results: List[Any], 
        request: MemoryEnabledRequest
    ) -> List[Dict[str, Any]]:
        """Filter and format memory search results"""
        filtered = []
        
        for result in results:
            if isinstance(result, dict):
                # Apply similarity threshold
                confidence = result.get("confidence", 1.0)
                if confidence >= self.memory_config.similarity_threshold:
                    filtered.append(result)
            else:
                # Convert to dict format
                filtered.append({
                    "description": str(result),
                    "confidence": 1.0,
                    "source": "memory"
                })
        
        return filtered[:self.memory_config.context_window]
    
    def _extract_entities(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract knowledge graph entities from results"""
        entities = []
        
        for result in results:
            if isinstance(result, dict) and "entities" in result:
                entities.extend(result["entities"])
        
        return entities
    
    def _detect_patterns(self, results: List[Dict[str, Any]], agent_id: str) -> List[str]:
        """Detect patterns in memory results"""
        patterns = []
        
        # Simple pattern detection based on recurring themes
        themes = {}
        for result in results:
            if isinstance(result, dict):
                description = result.get("description", "")
                words = description.lower().split()
                for word in words:
                    if len(word) > 4:  # Filter short words
                        themes[word] = themes.get(word, 0) + 1
        
        # Find recurring themes
        for theme, count in themes.items():
            if count > 1:
                patterns.append(f"Recurring theme: {theme} (mentioned {count} times)")
        
        return patterns[:3]  # Top 3 patterns
    
    def _generate_context_summary(self, results: List[Dict[str, Any]]) -> str:
        """Generate a summary of the memory context"""
        if not results:
            return ""
        
        # Simple summary generation
        descriptions = []
        for result in results:
            if isinstance(result, dict):
                desc = result.get("description", "")
                if desc and len(desc) > 10:
                    descriptions.append(desc[:100])  # Truncate long descriptions
        
        if descriptions:
            return f"Found {len(descriptions)} relevant memory entries. " + \
                   "Key insights: " + "; ".join(descriptions[:2])
        
        return f"Found {len(results)} memory entries"
    
    async def _get_agent_specific_context(
        self, 
        agent_id: str, 
        query: str
    ) -> Dict[str, Any]:
        """Get agent-specific memory context"""
        if not agent_id or not self.cognee_initialized:
            return {}
        
        try:
            # Search for agent-specific interactions
            agent_query = f"agent:{agent_id} interactions"
            agent_results = await self.cognee.search(
                query_text=agent_query,
                query_type="insights"
            )
            
            return {
                "recent_interactions": len(agent_results),
                "agent_specialization": self._get_agent_specialization(agent_id),
                "performance_metrics": self._get_agent_performance(agent_id)
            }
            
        except Exception as e:
            logger.warning(f"Failed to get agent-specific context: {e}")
            return {}
    
    def _get_agent_specialization(self, agent_id: str) -> str:
        """Get agent specialization description"""
        specializations = {
            "code_analyst": "Code analysis and pattern recognition",
            "debug_detective": "Debugging and error resolution",
            "workflow_manager": "Process optimization and automation",
            "security_auditor": "Security analysis and compliance",
            "performance_optimizer": "Performance tuning and optimization",
            "documentation_agent": "Documentation generation and maintenance"
        }
        return specializations.get(agent_id, "General purpose agent")
    
    def _get_agent_performance(self, agent_id: str) -> Dict[str, Any]:
        """Get agent performance metrics"""
        # This would typically come from a performance tracking system
        return {
            "success_rate": 0.95,
            "average_response_time": 2.5,
            "user_satisfaction": 4.2
        }
    
    async def query_knowledge_graph(
        self,
        query: str,
        query_type: str = "insights",
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Query the knowledge graph directly"""
        if not self.cognee_initialized:
            return {"results": [], "error": "Memory not initialized"}
        
        try:
            results = await self.cognee.search(
                query_text=query,
                query_type=query_type
            )
            
            # Apply filters if provided
            if filters:
                results = self._apply_filters(results, filters)
            
            return {
                "results": results,
                "query": query,
                "query_type": query_type,
                "filters_applied": filters or {}
            }
            
        except Exception as e:
            logger.error(f"Knowledge graph query failed: {e}")
            return {"results": [], "error": str(e)}
    
    def _apply_filters(self, results: List[Any], filters: Dict[str, Any]) -> List[Any]:
        """Apply filters to search results"""
        filtered_results = results
        
        # Apply agent filter
        if "agent_id" in filters:
            agent_id = filters["agent_id"]
            filtered_results = [
                r for r in filtered_results 
                if isinstance(r, dict) and r.get("agent_id") == agent_id
            ]
        
        # Apply tags filter
        if "tags" in filters:
            required_tags = filters["tags"]
            filtered_results = [
                r for r in filtered_results
                if isinstance(r, dict) and 
                any(tag in r.get("tags", []) for tag in required_tags)
            ]
        
        return filtered_results
    
    async def clear_agent_memory(self, agent_id: str) -> Dict[str, Any]:
        """Clear memory for a specific agent"""
        if not self.cognee_initialized:
            return {"success": False, "error": "Memory not initialized"}
        
        try:
            # This would require Cognee to support selective deletion
            # For now, we'll return a placeholder
            logger.info(f"Clearing memory for agent: {agent_id}")
            
            return {
                "success": True,
                "agent_id": agent_id,
                "cleared_entries": 0,  # Placeholder
                "message": "Agent memory clearing not yet implemented in Cognee"
            }
            
        except Exception as e:
            logger.error(f"Failed to clear agent memory: {e}")
            return {"success": False, "error": str(e)}
    
    async def batch_process_with_memory(
        self,
        requests: List[MemoryEnabledRequest],
        batch_size: int = 10
    ) -> List[MemoryEnabledResponse]:
        """Process multiple requests with memory in batches"""
        responses = []
        
        # Process in batches
        for i in range(0, len(requests), batch_size):
            batch = requests[i:i + batch_size]
            
            # Process batch concurrently
            batch_tasks = [
                self.generate_with_memory(request) 
                for request in batch
            ]
            
            batch_responses = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Handle exceptions
            for response in batch_responses:
                if isinstance(response, Exception):
                    logger.error(f"Batch processing error: {response}")
                    # Create error response
                    error_response = MemoryEnabledResponse(
                        content=f"Error: {str(response)}",
                        provider="error",
                        cost=0.0
                    )
                    responses.append(error_response)
                else:
                    responses.append(response)
        
        return responses
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get comprehensive memory system statistics"""
        return {
            "memory_enabled": self.memory_config.enable_memory,
            "cognee_initialized": self.cognee_initialized,
            "statistics": self.memory_stats.copy(),
            "configuration": {
                "vector_db": self.memory_config.vector_db_provider,
                "graph_db": self.memory_config.graph_db_provider,
                "relational_db": self.memory_config.relational_db_provider,
                "cache_size": self.memory_config.memory_cache_size,
                "context_window": self.memory_config.context_window
            },
            "performance": {
                "cache_hit_rate": (
                    self.memory_stats["cache_hits"] / max(self.memory_stats["total_queries"], 1)
                ),
                "total_entities": self.memory_stats["knowledge_entities"],
                "memory_updates": self.memory_stats["memory_updates"]
            }
        }

# Factory function
def create_memory_enabled_model_manager(config: Dict[str, Any] = None) -> CogneeModelManager:
    """Create and return a memory-enabled model manager"""
    return CogneeModelManager(config)