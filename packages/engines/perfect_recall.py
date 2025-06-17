"""
Three-Engine Architecture for reVoAgent Enterprise
Perfect Recall Engine - Advanced memory and knowledge management
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import json
import hashlib
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class MemoryType(Enum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"

class MemoryPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class MemoryNode:
    id: str
    content: str
    memory_type: MemoryType
    priority: MemoryPriority
    timestamp: datetime
    tags: List[str]
    connections: List[str]  # IDs of related memories
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    decay_rate: float = 0.1
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.last_accessed is None:
            self.last_accessed = self.timestamp

class PerfectRecallEngine:
    """
    Perfect Recall Engine - Manages all memory and knowledge operations
    Features:
    - Hierarchical memory storage (short/long term)
    - Semantic and episodic memory
    - Contextual retrieval
    - Memory consolidation
    - Knowledge graph integration
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.memory_store: Dict[str, MemoryNode] = {}
        self.semantic_index: Dict[str, List[str]] = {}  # keyword -> memory_ids
        self.temporal_index: Dict[str, List[str]] = {}  # date -> memory_ids
        self.connection_graph: Dict[str, set] = {}  # memory_id -> connected_ids
        
        # Configuration
        self.max_short_term_memories = self.config.get('max_short_term', 1000)
        self.max_long_term_memories = self.config.get('max_long_term', 10000)
        self.consolidation_threshold = self.config.get('consolidation_threshold', 3)
        self.decay_interval = self.config.get('decay_interval', 3600)  # seconds
        
        # Statistics
        self.stats = {
            'total_memories': 0,
            'retrievals': 0,
            'consolidations': 0,
            'last_cleanup': datetime.now()
        }
        
        logger.info("🧠 Perfect Recall Engine initialized")
    
    def _generate_memory_id(self, content: str, timestamp: datetime) -> str:
        """Generate unique memory ID"""
        hash_input = f"{content}{timestamp.isoformat()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from content for semantic indexing"""
        # Simple keyword extraction - in production, use NLP libraries
        import re
        words = re.findall(r'\b\w+\b', content.lower())
        # Filter common words and short words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        return list(set(keywords[:10]))  # Limit to 10 keywords
    
    async def store_memory(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.SHORT_TERM,
        priority: MemoryPriority = MemoryPriority.MEDIUM,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Store a new memory"""
        try:
            timestamp = datetime.now()
            memory_id = self._generate_memory_id(content, timestamp)
            
            # Create memory node
            memory = MemoryNode(
                id=memory_id,
                content=content,
                memory_type=memory_type,
                priority=priority,
                timestamp=timestamp,
                tags=tags or [],
                connections=[],
                metadata=metadata or {}
            )
            
            # Store memory
            self.memory_store[memory_id] = memory
            
            # Update indexes
            await self._update_indexes(memory)
            
            # Update statistics
            self.stats['total_memories'] += 1
            
            # Check for consolidation
            if memory_type == MemoryType.SHORT_TERM:
                await self._check_consolidation(memory_id)
            
            logger.debug(f"Stored memory {memory_id}: {content[:50]}...")
            return memory_id
            
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            raise
    
    async def _update_indexes(self, memory: MemoryNode):
        """Update semantic and temporal indexes"""
        # Semantic index
        keywords = self._extract_keywords(memory.content)
        for keyword in keywords:
            if keyword not in self.semantic_index:
                self.semantic_index[keyword] = []
            self.semantic_index[keyword].append(memory.id)
        
        # Temporal index
        date_key = memory.timestamp.strftime('%Y-%m-%d')
        if date_key not in self.temporal_index:
            self.temporal_index[date_key] = []
        self.temporal_index[date_key].append(memory.id)
        
        # Connection graph
        self.connection_graph[memory.id] = set()
    
    async def retrieve_memories(
        self,
        query: str = None,
        memory_type: MemoryType = None,
        tags: List[str] = None,
        limit: int = 10,
        time_range: tuple = None
    ) -> List[MemoryNode]:
        """Retrieve memories based on query and filters"""
        try:
            self.stats['retrievals'] += 1
            candidate_ids = set()
            
            # Query-based retrieval
            if query:
                keywords = self._extract_keywords(query)
                for keyword in keywords:
                    if keyword in self.semantic_index:
                        candidate_ids.update(self.semantic_index[keyword])
            
            # Filter by memory type
            if memory_type:
                type_filtered = [
                    mid for mid in candidate_ids 
                    if self.memory_store.get(mid) and 
                    self.memory_store[mid].memory_type == memory_type
                ]
                candidate_ids = set(type_filtered)
            
            # Filter by tags
            if tags:
                tag_filtered = []
                for mid in candidate_ids:
                    memory = self.memory_store.get(mid)
                    if memory and any(tag in memory.tags for tag in tags):
                        tag_filtered.append(mid)
                candidate_ids = set(tag_filtered)
            
            # Filter by time range
            if time_range:
                start_time, end_time = time_range
                time_filtered = []
                for mid in candidate_ids:
                    memory = self.memory_store.get(mid)
                    if memory and start_time <= memory.timestamp <= end_time:
                        time_filtered.append(mid)
                candidate_ids = set(time_filtered)
            
            # If no query specified, get recent memories
            if not query and not candidate_ids:
                recent_memories = sorted(
                    self.memory_store.keys(),
                    key=lambda mid: self.memory_store[mid].timestamp,
                    reverse=True
                )
                candidate_ids = set(recent_memories[:limit * 2])
            
            # Get memory objects and update access patterns
            memories = []
            for mid in list(candidate_ids)[:limit * 2]:  # Get more than needed for ranking
                if mid in self.memory_store:
                    memory = self.memory_store[mid]
                    memory.access_count += 1
                    memory.last_accessed = datetime.now()
                    memories.append(memory)
            
            # Rank memories by relevance
            ranked_memories = await self._rank_memories(memories, query)
            
            return ranked_memories[:limit]
            
        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")
            return []
    
    async def _rank_memories(self, memories: List[MemoryNode], query: str = None) -> List[MemoryNode]:
        """Rank memories by relevance and importance"""
        def calculate_score(memory: MemoryNode) -> float:
            score = 0.0
            
            # Priority weight
            score += memory.priority.value * 10
            
            # Recency weight (more recent = higher score)
            days_old = (datetime.now() - memory.timestamp).days
            recency_score = max(0, 100 - days_old)
            score += recency_score * 0.1
            
            # Access frequency weight
            score += memory.access_count * 0.5
            
            # Query relevance (if query provided)
            if query:
                query_keywords = set(self._extract_keywords(query))
                content_keywords = set(self._extract_keywords(memory.content))
                overlap = len(query_keywords.intersection(content_keywords))
                if query_keywords:
                    relevance = overlap / len(query_keywords)
                    score += relevance * 50
            
            # Connection strength (memories with more connections are more important)
            score += len(self.connection_graph.get(memory.id, set())) * 2
            
            return score
        
        # Sort by score (descending)
        ranked = sorted(memories, key=calculate_score, reverse=True)
        return ranked
    
    async def connect_memories(self, memory_id1: str, memory_id2: str, connection_type: str = "related"):
        """Create a connection between two memories"""
        if memory_id1 in self.memory_store and memory_id2 in self.memory_store:
            # Update connections in memory nodes
            if memory_id2 not in self.memory_store[memory_id1].connections:
                self.memory_store[memory_id1].connections.append(memory_id2)
            if memory_id1 not in self.memory_store[memory_id2].connections:
                self.memory_store[memory_id2].connections.append(memory_id1)
            
            # Update connection graph
            self.connection_graph[memory_id1].add(memory_id2)
            self.connection_graph[memory_id2].add(memory_id1)
            
            logger.debug(f"Connected memories {memory_id1} <-> {memory_id2}")
    
    async def _check_consolidation(self, memory_id: str):
        """Check if short-term memory should be consolidated to long-term"""
        memory = self.memory_store.get(memory_id)
        if not memory or memory.memory_type != MemoryType.SHORT_TERM:
            return
        
        # Consolidation criteria
        should_consolidate = (
            memory.access_count >= self.consolidation_threshold or
            memory.priority == MemoryPriority.CRITICAL or
            len(memory.connections) >= 3
        )
        
        if should_consolidate:
            await self.consolidate_memory(memory_id)
    
    async def consolidate_memory(self, memory_id: str):
        """Move memory from short-term to long-term storage"""
        memory = self.memory_store.get(memory_id)
        if memory and memory.memory_type == MemoryType.SHORT_TERM:
            memory.memory_type = MemoryType.LONG_TERM
            self.stats['consolidations'] += 1
            logger.debug(f"Consolidated memory {memory_id} to long-term storage")
    
    async def forget_memory(self, memory_id: str):
        """Remove a memory from storage"""
        if memory_id in self.memory_store:
            memory = self.memory_store[memory_id]
            
            # Remove from indexes
            keywords = self._extract_keywords(memory.content)
            for keyword in keywords:
                if keyword in self.semantic_index:
                    self.semantic_index[keyword] = [
                        mid for mid in self.semantic_index[keyword] if mid != memory_id
                    ]
            
            # Remove connections
            for connected_id in memory.connections:
                if connected_id in self.memory_store:
                    self.memory_store[connected_id].connections = [
                        mid for mid in self.memory_store[connected_id].connections if mid != memory_id
                    ]
            
            # Remove from connection graph
            if memory_id in self.connection_graph:
                del self.connection_graph[memory_id]
            
            # Remove memory
            del self.memory_store[memory_id]
            self.stats['total_memories'] -= 1
            
            logger.debug(f"Forgot memory {memory_id}")
    
    async def decay_memories(self):
        """Apply memory decay and cleanup old memories"""
        now = datetime.now()
        to_forget = []
        
        for memory_id, memory in self.memory_store.items():
            # Calculate decay
            if memory.last_accessed:
                days_since_access = (now - memory.last_accessed).days
                decay_factor = memory.decay_rate * days_since_access
                
                # Forget low-priority, old, unaccessed memories
                if (
                    memory.priority == MemoryPriority.LOW and
                    days_since_access > 30 and
                    memory.access_count < 2 and
                    decay_factor > 0.8
                ):
                    to_forget.append(memory_id)
        
        # Remove decayed memories
        for memory_id in to_forget:
            await self.forget_memory(memory_id)
        
        self.stats['last_cleanup'] = now
        logger.info(f"Memory decay: removed {len(to_forget)} memories")
    
    async def get_related_memories(self, memory_id: str, depth: int = 1) -> List[MemoryNode]:
        """Get memories related to a specific memory"""
        if memory_id not in self.memory_store:
            return []
        
        related_ids = set()
        current_level = {memory_id}
        
        for _ in range(depth):
            next_level = set()
            for mid in current_level:
                if mid in self.connection_graph:
                    next_level.update(self.connection_graph[mid])
            related_ids.update(next_level)
            current_level = next_level
        
        # Remove the original memory ID
        related_ids.discard(memory_id)
        
        # Get memory objects
        related_memories = [
            self.memory_store[mid] for mid in related_ids 
            if mid in self.memory_store
        ]
        
        return related_memories
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory engine statistics"""
        stats = self.stats.copy()
        
        # Memory type distribution
        type_counts = {}
        for memory in self.memory_store.values():
            memory_type = memory.memory_type.value
            type_counts[memory_type] = type_counts.get(memory_type, 0) + 1
        
        stats['memory_types'] = type_counts
        stats['total_connections'] = sum(len(connections) for connections in self.connection_graph.values()) // 2
        stats['avg_connections'] = stats['total_connections'] / max(1, len(self.memory_store))
        
        return stats
    
    async def export_memories(self, format: str = "json") -> Union[str, Dict]:
        """Export memories for backup or analysis"""
        if format == "json":
            export_data = {
                'memories': [asdict(memory) for memory in self.memory_store.values()],
                'stats': self.stats,
                'export_timestamp': datetime.now().isoformat()
            }
            return json.dumps(export_data, default=str, indent=2)
        
        return {"error": "Unsupported format"}
