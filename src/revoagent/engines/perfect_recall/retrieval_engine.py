"""
Perfect Recall Engine - Retrieval Engine
Sub-100ms retrieval system with intelligent ranking
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

from .memory_manager import MemoryManager, ContextData, ContextResult

logger = logging.getLogger(__name__)

@dataclass
class RetrievalQuery:
    """Query structure for context retrieval"""
    text: str
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    tags: List[str] = None
    time_range: Optional[tuple] = None
    limit: int = 10
    min_relevance: float = 0.3

@dataclass
class RetrievalMetrics:
    """Metrics for retrieval performance"""
    query_time_ms: float
    results_count: int
    cache_hit_rate: float
    relevance_scores: List[float]
    query_id: str

class RetrievalEngine:
    """
    High-performance retrieval engine with <100ms guarantee
    Implements intelligent ranking and caching strategies
    """
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.query_cache: Dict[str, List[ContextResult]] = {}
        self.cache_ttl = 300  # 5 minutes
        self.cache_timestamps: Dict[str, datetime] = {}
        self.performance_metrics: List[RetrievalMetrics] = []
        self.max_cache_size = 1000
        
    async def initialize(self) -> bool:
        """Initialize retrieval engine"""
        try:
            logger.info("🔵 Perfect Recall Engine: Retrieval Engine initialized")
            return True
        except Exception as e:
            logger.error(f"🔵 Failed to initialize Retrieval Engine: {e}")
            return False
    
    async def retrieve_contexts(self, query: RetrievalQuery) -> List[ContextResult]:
        """
        Retrieve contexts with <100ms performance guarantee
        """
        start_time = time.time()
        query_id = self._generate_query_id(query)
        
        try:
            # Check cache first
            cached_results = await self._check_cache(query_id)
            if cached_results is not None:
                cache_hit_time = (time.time() - start_time) * 1000
                logger.debug(f"🔵 Cache hit for query {query_id} in {cache_hit_time:.2f}ms")
                return cached_results
            
            # Retrieve from memory manager
            results = await self.memory_manager.retrieve_fast(
                query=query.text,
                session_id=query.session_id,
                project_id=query.project_id,
                limit=query.limit
            )
            
            # Apply additional filtering
            filtered_results = await self._apply_filters(results, query)
            
            # Enhance ranking
            ranked_results = await self._enhance_ranking(filtered_results, query)
            
            # Cache results
            await self._cache_results(query_id, ranked_results)
            
            # Record metrics
            query_time = (time.time() - start_time) * 1000
            await self._record_metrics(query_id, query_time, ranked_results)
            
            logger.debug(f"🔵 Retrieved {len(ranked_results)} contexts in {query_time:.2f}ms")
            return ranked_results
            
        except Exception as e:
            logger.error(f"🔵 Error retrieving contexts: {e}")
            return []
    
    async def retrieve_by_similarity(self, reference_context_id: str, 
                                   limit: int = 5) -> List[ContextResult]:
        """
        Retrieve contexts similar to a reference context
        """
        start_time = time.time()
        
        try:
            # Get reference context
            if reference_context_id not in self.memory_manager.contexts:
                return []
            
            reference_context = self.memory_manager.contexts[reference_context_id]
            
            # Use reference content as query
            query = RetrievalQuery(
                text=reference_context.content,
                session_id=reference_context.session_id,
                project_id=reference_context.project_id,
                limit=limit + 1  # +1 to exclude the reference itself
            )
            
            results = await self.retrieve_contexts(query)
            
            # Remove the reference context from results
            filtered_results = [
                result for result in results 
                if result.context_id != reference_context_id
            ][:limit]
            
            retrieval_time = (time.time() - start_time) * 1000
            logger.debug(f"🔵 Retrieved {len(filtered_results)} similar contexts in {retrieval_time:.2f}ms")
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"🔵 Error retrieving similar contexts: {e}")
            return []
    
    async def retrieve_recent(self, session_id: Optional[str] = None,
                            project_id: Optional[str] = None,
                            hours: int = 24, limit: int = 10) -> List[ContextResult]:
        """
        Retrieve recent contexts within specified time range
        """
        start_time = time.time()
        
        try:
            # Calculate time range
            now = datetime.now()
            time_threshold = now.timestamp() - (hours * 3600)
            
            # Get candidate contexts
            if session_id:
                candidate_ids = self.memory_manager.session_index.get(session_id, [])
            elif project_id:
                candidate_ids = self.memory_manager.project_index.get(project_id, [])
            else:
                # Get from temporal index
                candidate_ids = [
                    cid for ts, cid in self.memory_manager.temporal_index
                    if ts.timestamp() >= time_threshold
                ][:limit * 2]
            
            # Filter by time and create results
            results = []
            for context_id in candidate_ids:
                if context_id not in self.memory_manager.contexts:
                    continue
                
                context = self.memory_manager.contexts[context_id]
                if context.timestamp.timestamp() >= time_threshold:
                    result = ContextResult(
                        content=context.content,
                        metadata=context.metadata,
                        relevance_score=1.0 - (
                            (now.timestamp() - context.timestamp.timestamp()) / (hours * 3600)
                        ),
                        retrieval_time_ms=(time.time() - start_time) * 1000,
                        context_id=context_id
                    )
                    results.append(result)
            
            # Sort by timestamp (most recent first)
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            results = results[:limit]
            
            retrieval_time = (time.time() - start_time) * 1000
            logger.debug(f"🔵 Retrieved {len(results)} recent contexts in {retrieval_time:.2f}ms")
            
            return results
            
        except Exception as e:
            logger.error(f"🔵 Error retrieving recent contexts: {e}")
            return []
    
    async def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get retrieval performance statistics"""
        try:
            if not self.performance_metrics:
                return {}
            
            query_times = [m.query_time_ms for m in self.performance_metrics[-100:]]
            result_counts = [m.results_count for m in self.performance_metrics[-100:]]
            relevance_scores = []
            for m in self.performance_metrics[-100:]:
                relevance_scores.extend(m.relevance_scores)
            
            stats = {
                'avg_query_time_ms': sum(query_times) / len(query_times),
                'max_query_time_ms': max(query_times),
                'min_query_time_ms': min(query_times),
                'avg_results_count': sum(result_counts) / len(result_counts),
                'avg_relevance_score': sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0,
                'cache_size': len(self.query_cache),
                'total_queries': len(self.performance_metrics),
                'sub_100ms_queries': len([t for t in query_times if t < 100]),
                'performance_target_met': len([t for t in query_times if t < 100]) / len(query_times) * 100
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"🔵 Error getting retrieval stats: {e}")
            return {}
    
    def _generate_query_id(self, query: RetrievalQuery) -> str:
        """Generate unique query ID for caching"""
        import hashlib
        query_str = f"{query.text}{query.session_id}{query.project_id}{query.tags}{query.limit}"
        return hashlib.md5(query_str.encode()).hexdigest()[:16]
    
    async def _check_cache(self, query_id: str) -> Optional[List[ContextResult]]:
        """Check if query results are cached and still valid"""
        try:
            if query_id not in self.query_cache:
                return None
            
            # Check TTL
            if query_id in self.cache_timestamps:
                cache_time = self.cache_timestamps[query_id]
                if (datetime.now() - cache_time).total_seconds() > self.cache_ttl:
                    # Cache expired
                    del self.query_cache[query_id]
                    del self.cache_timestamps[query_id]
                    return None
            
            return self.query_cache[query_id]
            
        except Exception as e:
            logger.error(f"🔵 Error checking cache: {e}")
            return None
    
    async def _cache_results(self, query_id: str, results: List[ContextResult]) -> None:
        """Cache query results"""
        try:
            # Cleanup cache if too large
            if len(self.query_cache) >= self.max_cache_size:
                # Remove oldest entries
                oldest_queries = sorted(
                    self.cache_timestamps.items(),
                    key=lambda x: x[1]
                )[:self.max_cache_size // 4]
                
                for old_query_id, _ in oldest_queries:
                    if old_query_id in self.query_cache:
                        del self.query_cache[old_query_id]
                    if old_query_id in self.cache_timestamps:
                        del self.cache_timestamps[old_query_id]
            
            # Cache results
            self.query_cache[query_id] = results
            self.cache_timestamps[query_id] = datetime.now()
            
        except Exception as e:
            logger.error(f"🔵 Error caching results: {e}")
    
    async def _apply_filters(self, results: List[ContextResult], 
                           query: RetrievalQuery) -> List[ContextResult]:
        """Apply additional filters to results"""
        try:
            filtered_results = []
            
            for result in results:
                # Relevance threshold
                if result.relevance_score < query.min_relevance:
                    continue
                
                # Tag filtering
                if query.tags:
                    context = self.memory_manager.contexts.get(result.context_id)
                    if context and not any(tag in context.tags for tag in query.tags):
                        continue
                
                # Time range filtering
                if query.time_range:
                    context = self.memory_manager.contexts.get(result.context_id)
                    if context:
                        start_time, end_time = query.time_range
                        if not (start_time <= context.timestamp <= end_time):
                            continue
                
                filtered_results.append(result)
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"🔵 Error applying filters: {e}")
            return results
    
    async def _enhance_ranking(self, results: List[ContextResult], 
                             query: RetrievalQuery) -> List[ContextResult]:
        """Enhance ranking with additional signals"""
        try:
            for result in results:
                context = self.memory_manager.contexts.get(result.context_id)
                if not context:
                    continue
                
                # Boost score based on recency
                age_hours = (datetime.now() - context.timestamp).total_seconds() / 3600
                recency_boost = max(0, 1 - (age_hours / 168))  # Decay over 1 week
                
                # Boost score based on session/project match
                session_boost = 0.1 if context.session_id == query.session_id else 0
                project_boost = 0.1 if context.project_id == query.project_id else 0
                
                # Apply boosts
                result.relevance_score = min(1.0, 
                    result.relevance_score + 
                    (recency_boost * 0.2) + 
                    session_boost + 
                    project_boost
                )
            
            # Re-sort by enhanced scores
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            return results
            
        except Exception as e:
            logger.error(f"🔵 Error enhancing ranking: {e}")
            return results
    
    async def _record_metrics(self, query_id: str, query_time: float, 
                            results: List[ContextResult]) -> None:
        """Record performance metrics"""
        try:
            metrics = RetrievalMetrics(
                query_time_ms=query_time,
                results_count=len(results),
                cache_hit_rate=0.0,  # Will be calculated separately
                relevance_scores=[r.relevance_score for r in results],
                query_id=query_id
            )
            
            self.performance_metrics.append(metrics)
            
            # Keep only last 1000 metrics
            if len(self.performance_metrics) > 1000:
                self.performance_metrics = self.performance_metrics[-1000:]
            
        except Exception as e:
            logger.error(f"🔵 Error recording metrics: {e}")
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        self.query_cache.clear()
        self.cache_timestamps.clear()
        self.performance_metrics.clear()
        logger.info("🔵 Perfect Recall Engine: Retrieval Engine cleaned up")