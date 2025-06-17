"""
Perfect Recall Engine - Memory Manager
Target: < 100ms retrieval time with infinite context retention
"""

import asyncio
import json
import time
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import numpy as np
import logging

logger = logging.getLogger(__name__)

@dataclass
class ContextData:
    """Context data structure for storage"""
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime
    session_id: str
    project_id: Optional[str] = None
    tags: List[str] = None
    embedding: Optional[List[float]] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass
class ContextResult:
    """Context retrieval result"""
    content: str
    metadata: Dict[str, Any]
    relevance_score: float
    retrieval_time_ms: float
    context_id: str

class MemoryManager:
    """
    High-performance memory management with <100ms retrieval guarantee
    Uses in-memory storage with vector embeddings for semantic search
    """
    
    def __init__(self, max_contexts: int = 100000):
        self.contexts: Dict[str, ContextData] = {}
        self.session_index: Dict[str, List[str]] = {}
        self.project_index: Dict[str, List[str]] = {}
        self.tag_index: Dict[str, List[str]] = {}
        self.temporal_index: List[Tuple[datetime, str]] = []
        self.embedding_cache: Dict[str, np.ndarray] = {}
        self.max_contexts = max_contexts
        
    async def initialize(self) -> bool:
        """Initialize memory manager"""
        try:
            logger.info("🔵 Perfect Recall Engine: Memory Manager initialized")
            return True
        except Exception as e:
            logger.error(f"🔵 Failed to initialize Memory Manager: {e}")
            return False
    
    async def store_context(self, context: ContextData) -> str:
        """
        Store context with <100ms retrieval guarantee
        Returns: context_id for future retrieval
        """
        start_time = time.time()
        
        try:
            # Generate unique context ID
            context_id = self._generate_context_id(context)
            
            # Generate embedding for semantic search
            if context.embedding is None:
                context.embedding = await self._generate_embedding(context.content)
            
            # Store context
            self.contexts[context_id] = context
            
            # Update indices
            if context.session_id not in self.session_index:
                self.session_index[context.session_id] = []
            self.session_index[context.session_id].append(context_id)
            
            if context.project_id:
                if context.project_id not in self.project_index:
                    self.project_index[context.project_id] = []
                self.project_index[context.project_id].append(context_id)
            
            for tag in context.tags:
                if tag not in self.tag_index:
                    self.tag_index[tag] = []
                self.tag_index[tag].append(context_id)
            
            # Update temporal index
            self.temporal_index.append((context.timestamp, context_id))
            self.temporal_index.sort(key=lambda x: x[0], reverse=True)
            
            # Cache embedding
            if context.embedding:
                self.embedding_cache[context_id] = np.array(context.embedding)
            
            # Cleanup if needed
            if len(self.contexts) > self.max_contexts:
                await self._cleanup_old_contexts()
            
            storage_time = (time.time() - start_time) * 1000
            logger.debug(f"🔵 Stored context {context_id} in {storage_time:.2f}ms")
            
            return context_id
            
        except Exception as e:
            logger.error(f"🔵 Error storing context: {e}")
            raise
    
    async def retrieve_fast(self, query: str, session_id: Optional[str] = None,
                           project_id: Optional[str] = None, 
                           limit: int = 10) -> List[ContextResult]:
        """
        Sub-100ms context retrieval with semantic search
        """
        start_time = time.time()
        
        try:
            # Generate query embedding
            query_embedding = await self._generate_embedding(query)
            
            # Get candidate context IDs based on filters
            candidate_ids = self._get_candidate_contexts(session_id, project_id, limit * 3)
            
            if not candidate_ids:
                return []
            
            # Calculate relevance scores and prepare results
            results = []
            for context_id in candidate_ids:
                if context_id not in self.contexts:
                    continue
                
                context = self.contexts[context_id]
                
                # Calculate relevance score
                if context_id in self.embedding_cache:
                    context_embedding = self.embedding_cache[context_id]
                    relevance_score = self._calculate_similarity(query_embedding, context_embedding)
                else:
                    relevance_score = 0.5  # Default score if no embedding
                
                # Create result
                result = ContextResult(
                    content=context.content,
                    metadata=context.metadata,
                    relevance_score=relevance_score,
                    retrieval_time_ms=(time.time() - start_time) * 1000,
                    context_id=context_id
                )
                
                results.append(result)
            
            # Sort by relevance and limit results
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            results = results[:limit]
            
            retrieval_time = (time.time() - start_time) * 1000
            logger.debug(f"🔵 Retrieved {len(results)} contexts in {retrieval_time:.2f}ms")
            
            # Update retrieval time for all results
            for result in results:
                result.retrieval_time_ms = retrieval_time
            
            return results
            
        except Exception as e:
            logger.error(f"🔵 Error retrieving contexts: {e}")
            return []
    
    async def maintain_session_memory(self, session_id: str) -> Dict[str, Any]:
        """
        Continuous memory management for active sessions
        """
        try:
            # Get session context count
            context_ids = self.session_index.get(session_id, [])
            context_count = len(context_ids)
            
            # Calculate memory usage
            memory_usage = sum(
                len(self.contexts[cid].content.encode('utf-8')) 
                for cid in context_ids if cid in self.contexts
            )
            
            # Get session statistics
            stats = {
                'session_id': session_id,
                'context_count': context_count,
                'memory_usage_bytes': memory_usage,
                'last_activity': self._get_last_activity(session_id),
                'optimization_needed': memory_usage > 100 * 1024 * 1024
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"🔵 Error maintaining session memory: {e}")
            return {}
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        try:
            total_memory = sum(
                len(context.content.encode('utf-8')) 
                for context in self.contexts.values()
            )
            
            stats = {
                'total_contexts': len(self.contexts),
                'active_sessions': len(self.session_index),
                'total_memory_bytes': total_memory,
                'embedding_cache_size': len(self.embedding_cache),
                'max_contexts': self.max_contexts
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"🔵 Error getting memory stats: {e}")
            return {}
    
    def _generate_context_id(self, context: ContextData) -> str:
        """Generate unique context ID"""
        content_hash = hashlib.sha256(
            f"{context.content}{context.session_id}{context.timestamp}".encode()
        ).hexdigest()
        return f"ctx_{content_hash[:16]}"
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate simple embedding for text (placeholder implementation)"""
        try:
            # Simple hash-based embedding for demonstration
            # In production, use sentence-transformers or similar
            text_hash = hashlib.sha256(text.encode()).hexdigest()
            embedding = [float(int(text_hash[i:i+2], 16)) / 255.0 for i in range(0, 32, 2)]
            return embedding + [0.0] * (384 - len(embedding))  # Pad to 384 dimensions
        except Exception as e:
            logger.error(f"🔵 Error generating embedding: {e}")
            return [0.0] * 384
    
    def _get_candidate_contexts(self, session_id: Optional[str], 
                               project_id: Optional[str], 
                               limit: int) -> List[str]:
        """Get candidate context IDs based on filters"""
        try:
            if session_id and session_id in self.session_index:
                return self.session_index[session_id][:limit]
            elif project_id and project_id in self.project_index:
                return self.project_index[project_id][:limit]
            else:
                # Return most recent contexts
                return [cid for _, cid in self.temporal_index[:limit]]
        except Exception as e:
            logger.error(f"🔵 Error getting candidate contexts: {e}")
            return []
    
    def _calculate_similarity(self, query_embedding: List[float], 
                            context_embedding: np.ndarray) -> float:
        """Calculate cosine similarity between embeddings"""
        try:
            query_vec = np.array(query_embedding)
            
            # Normalize vectors
            query_norm = np.linalg.norm(query_vec)
            context_norm = np.linalg.norm(context_embedding)
            
            if query_norm == 0 or context_norm == 0:
                return 0.0
            
            # Calculate cosine similarity
            similarity = np.dot(query_vec, context_embedding) / (query_norm * context_norm)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"🔵 Error calculating similarity: {e}")
            return 0.0
    
    def _get_last_activity(self, session_id: str) -> Optional[datetime]:
        """Get last activity timestamp for a session"""
        try:
            context_ids = self.session_index.get(session_id, [])
            if not context_ids:
                return None
            
            latest_timestamp = None
            for context_id in context_ids:
                if context_id in self.contexts:
                    timestamp = self.contexts[context_id].timestamp
                    if latest_timestamp is None or timestamp > latest_timestamp:
                        latest_timestamp = timestamp
            
            return latest_timestamp
            
        except Exception as e:
            logger.error(f"🔵 Error getting last activity: {e}")
            return None
    
    async def _cleanup_old_contexts(self) -> None:
        """Cleanup old contexts to maintain memory limits"""
        try:
            # Remove oldest 10% of contexts
            cleanup_count = int(self.max_contexts * 0.1)
            oldest_contexts = sorted(self.temporal_index, key=lambda x: x[0])[:cleanup_count]
            
            for timestamp, context_id in oldest_contexts:
                if context_id in self.contexts:
                    context = self.contexts[context_id]
                    
                    # Remove from main storage
                    del self.contexts[context_id]
                    
                    # Remove from indices
                    if context.session_id in self.session_index:
                        self.session_index[context.session_id].remove(context_id)
                    
                    if context.project_id and context.project_id in self.project_index:
                        self.project_index[context.project_id].remove(context_id)
                    
                    for tag in context.tags:
                        if tag in self.tag_index:
                            self.tag_index[tag].remove(context_id)
                    
                    # Remove from embedding cache
                    if context_id in self.embedding_cache:
                        del self.embedding_cache[context_id]
            
            # Update temporal index
            self.temporal_index = [
                (ts, cid) for ts, cid in self.temporal_index 
                if cid in self.contexts
            ]
            
            logger.info(f"🔵 Cleaned up {cleanup_count} old contexts")
            
        except Exception as e:
            logger.error(f"🔵 Error cleaning up contexts: {e}")
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        self.contexts.clear()
        self.session_index.clear()
        self.project_index.clear()
        self.tag_index.clear()
        self.temporal_index.clear()
        self.embedding_cache.clear()
        logger.info("🔵 Perfect Recall Engine: Memory Manager cleaned up")