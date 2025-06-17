import asyncio
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)

@dataclass
class MemoryEntry:
    id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any]
    timestamp: datetime
    agent_id: str

class EnhancedMemoryManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cognee_client = None
        self.memory_store = {}  # Fallback in-memory store
        self.initialized = False
        
    async def initialize(self):
        """Initialize memory system with Cognee fallback"""
        try:
            # Try to initialize Cognee
            import cognee
            await cognee.prune.prune_data()
            await cognee.prune.prune_system(metadata=True)
            
            self.cognee_client = cognee
            self.initialized = True
            logger.info("✅ Cognee memory system initialized")
            
        except Exception as e:
            logger.warning(f"⚠️ Cognee initialization failed: {e}")
            logger.info("💡 Using fallback memory system")
            self.initialized = True
    
    async def store_memory(self, agent_id: str, content: str, metadata: Dict[str, Any] = None) -> str:
        """Store a memory entry"""
        if not self.initialized:
            await self.initialize()
        
        memory_id = f"{agent_id}_{datetime.now().timestamp()}"
        
        if self.cognee_client:
            try:
                # Use Cognee for storage
                await self.cognee_client.add(content, metadata=metadata or {})
                logger.info(f"✅ Memory stored via Cognee: {memory_id}")
                return memory_id
            except Exception as e:
                logger.error(f"Cognee storage failed: {e}")
                # Fall through to fallback storage
        
        # Fallback storage
        self.memory_store[memory_id] = {
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Memory stored via fallback: {memory_id}")
        return memory_id
    
    async def retrieve_memory(self, agent_id: str, query: str, limit: int = 5) -> List[MemoryEntry]:
        """Retrieve relevant memories for an agent"""
        if not self.initialized:
            return []
        
        if self.cognee_client:
            try:
                # Use Cognee for retrieval
                results = await self.cognee_client.search(query, limit=limit)
                return self._format_cognee_results(results, agent_id)
            except Exception as e:
                logger.error(f"Cognee retrieval failed: {e}")
                return await self._retrieve_fallback(agent_id, query, limit)
        else:
            return await self._retrieve_fallback(agent_id, query, limit)
    
    async def _retrieve_fallback(self, agent_id: str, query: str, limit: int) -> List[MemoryEntry]:
        """Fallback memory retrieval"""
        results = []
        for memory_id, data in self.memory_store.items():
            if agent_id in memory_id and query.lower() in data["content"].lower():
                results.append(MemoryEntry(
                    id=memory_id,
                    content=data["content"],
                    embedding=[],
                    metadata=data["metadata"],
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    agent_id=agent_id
                ))
        return results[:limit]
    
    def _format_cognee_results(self, results: List, agent_id: str) -> List[MemoryEntry]:
        """Format Cognee results to MemoryEntry objects"""
        formatted = []
        for result in results:
            formatted.append(MemoryEntry(
                id=str(result.get("id", "")),
                content=result.get("content", ""),
                embedding=result.get("embedding", []),
                metadata=result.get("metadata", {}),
                timestamp=datetime.now(),
                agent_id=agent_id
            ))
        return formatted
    
    async def health_check(self) -> Dict[str, Any]:
        """Check memory system health"""
        if not self.initialized:
            return {"status": "not_initialized"}
        
        try:
            if self.cognee_client:
                # Test Cognee connection
                await self.cognee_client.search("test", limit=1)
                return {"status": "healthy", "backend": "cognee"}
            else:
                # Test fallback storage
                test_count = len(self.memory_store)
                return {"status": "healthy", "backend": "fallback", "entries": test_count}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
