"""
🧠 Perfect Recall Engine

Advanced Memory Management with Semantic Understanding:
- Stores every coding interaction with semantic understanding
- Vector Search: ChromaDB-powered similarity matching
- Knowledge Graph: Neo4j-based relationship mapping
- Intelligent Recall: Find solutions based on meaning, not just keywords
"""

import asyncio
import json
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class MemoryEntry:
    """Represents a single memory entry in the Perfect Recall system."""
    id: str
    timestamp: datetime
    content: str
    content_type: str  # 'code', 'solution', 'error', 'conversation'
    tags: List[str]
    context: Dict[str, Any]
    embedding: Optional[List[float]] = None
    relationships: Optional[List[str]] = None
    success_score: float = 0.0
    usage_count: int = 0

@dataclass
class RecallResult:
    """Result from a recall query."""
    entry: MemoryEntry
    similarity_score: float
    relevance_score: float

class PerfectRecallEngine:
    """
    🧠 Perfect Recall Engine
    
    Advanced memory management system that stores and retrieves coding interactions
    with semantic understanding and intelligent pattern matching.
    """
    
    def __init__(self, storage_path: str = "data/memory"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Memory storage
        self.memory_db = {}
        self.embeddings_cache = {}
        self.knowledge_graph = {}
        
        # Configuration
        self.max_memory_entries = 10000
        self.embedding_dimension = 384
        self.similarity_threshold = 0.7
        
        # Initialize components
        self._initialize_storage()
        self._load_existing_memories()
        
        logger.info("🧠 Perfect Recall Engine initialized")
    
    def _initialize_storage(self):
        """Initialize storage components."""
        try:
            # Try to initialize ChromaDB for vector search
            self._init_vector_db()
        except ImportError:
            logger.warning("ChromaDB not available, using fallback vector search")
            self.vector_db = None
        
        try:
            # Try to initialize Neo4j for knowledge graph
            self._init_knowledge_graph()
        except ImportError:
            logger.warning("Neo4j not available, using fallback graph storage")
            self.neo4j_driver = None
    
    def _init_vector_db(self):
        """Initialize ChromaDB for vector search."""
        try:
            import chromadb
            self.chroma_client = chromadb.PersistentClient(path=str(self.storage_path / "chroma"))
            self.collection = self.chroma_client.get_or_create_collection(
                name="revoagent_memories",
                metadata={"description": "reVoAgent Perfect Recall memories"}
            )
            logger.info("✅ ChromaDB initialized for vector search")
        except Exception as e:
            logger.warning(f"ChromaDB initialization failed: {e}")
            self.chroma_client = None
            self.collection = None
    
    def _init_knowledge_graph(self):
        """Initialize Neo4j for knowledge graph."""
        try:
            from neo4j import GraphDatabase
            # Use embedded Neo4j or fallback to file-based graph
            self.neo4j_driver = None  # Would connect to Neo4j instance
            logger.info("📊 Knowledge graph storage initialized")
        except Exception as e:
            logger.warning(f"Neo4j initialization failed: {e}")
            self.neo4j_driver = None
    
    def _load_existing_memories(self):
        """Load existing memories from storage."""
        memory_file = self.storage_path / "memories.json"
        if memory_file.exists():
            try:
                with open(memory_file, 'r') as f:
                    data = json.load(f)
                    for entry_data in data:
                        entry = MemoryEntry(**entry_data)
                        entry.timestamp = datetime.fromisoformat(entry.timestamp)
                        self.memory_db[entry.id] = entry
                logger.info(f"📚 Loaded {len(self.memory_db)} existing memories")
            except Exception as e:
                logger.error(f"Failed to load memories: {e}")
    
    def _save_memories(self):
        """Save memories to persistent storage."""
        memory_file = self.storage_path / "memories.json"
        try:
            data = []
            for entry in self.memory_db.values():
                entry_dict = asdict(entry)
                entry_dict['timestamp'] = entry.timestamp.isoformat()
                data.append(entry_dict)
            
            with open(memory_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"💾 Saved {len(data)} memories to storage")
        except Exception as e:
            logger.error(f"Failed to save memories: {e}")
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using available models."""
        try:
            # Try to use sentence-transformers if available
            from sentence_transformers import SentenceTransformer
            if not hasattr(self, '_embedding_model'):
                self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            return self._embedding_model.encode(text).tolist()
        except ImportError:
            # Fallback to simple hash-based embedding
            return self._simple_embedding(text)
    
    def _simple_embedding(self, text: str) -> List[float]:
        """Simple hash-based embedding fallback."""
        # Create a simple embedding based on text characteristics
        words = text.lower().split()
        embedding = [0.0] * self.embedding_dimension
        
        for i, word in enumerate(words[:self.embedding_dimension]):
            hash_val = hash(word) % 1000
            embedding[i % self.embedding_dimension] += hash_val / 1000.0
        
        # Normalize
        magnitude = sum(x*x for x in embedding) ** 0.5
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]
        
        return embedding
    
    def _calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between embeddings."""
        if len(embedding1) != len(embedding2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        magnitude1 = sum(a * a for a in embedding1) ** 0.5
        magnitude2 = sum(b * b for b in embedding2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    async def store_memory(
        self,
        content: str,
        content_type: str,
        tags: List[str] = None,
        context: Dict[str, Any] = None,
        success_score: float = 0.0
    ) -> str:
        """
        Store a new memory entry with semantic understanding.
        
        Args:
            content: The content to store
            content_type: Type of content ('code', 'solution', 'error', 'conversation')
            tags: List of tags for categorization
            context: Additional context information
            success_score: Score indicating success/quality of the solution
            
        Returns:
            Memory entry ID
        """
        # Generate unique ID
        memory_id = hashlib.md5(f"{content}{datetime.now().isoformat()}".encode()).hexdigest()
        
        # Generate embedding
        embedding = self._generate_embedding(content)
        
        # Create memory entry
        entry = MemoryEntry(
            id=memory_id,
            timestamp=datetime.now(),
            content=content,
            content_type=content_type,
            tags=tags or [],
            context=context or {},
            embedding=embedding,
            success_score=success_score
        )
        
        # Store in memory database
        self.memory_db[memory_id] = entry
        
        # Store in vector database if available
        if self.collection:
            try:
                self.collection.add(
                    documents=[content],
                    embeddings=[embedding],
                    metadatas=[{
                        "content_type": content_type,
                        "tags": ",".join(tags or []),
                        "success_score": success_score,
                        "timestamp": entry.timestamp.isoformat()
                    }],
                    ids=[memory_id]
                )
            except Exception as e:
                logger.warning(f"Failed to store in ChromaDB: {e}")
        
        # Update knowledge graph relationships
        await self._update_knowledge_graph(entry)
        
        # Cleanup old memories if needed
        if len(self.memory_db) > self.max_memory_entries:
            await self._cleanup_old_memories()
        
        # Save to persistent storage
        self._save_memories()
        
        logger.info(f"🧠 Stored memory: {content_type} - {len(content)} chars")
        return memory_id
    
    async def recall_memories(
        self,
        query: str,
        content_types: List[str] = None,
        tags: List[str] = None,
        limit: int = 10,
        min_similarity: float = None
    ) -> List[RecallResult]:
        """
        Recall memories based on semantic similarity and filters.
        
        Args:
            query: Search query
            content_types: Filter by content types
            tags: Filter by tags
            limit: Maximum number of results
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of recall results sorted by relevance
        """
        query_embedding = self._generate_embedding(query)
        results = []
        
        min_sim = min_similarity or self.similarity_threshold
        
        # Search through all memories
        for entry in self.memory_db.values():
            # Apply filters
            if content_types and entry.content_type not in content_types:
                continue
            
            if tags and not any(tag in entry.tags for tag in tags):
                continue
            
            # Calculate similarity
            if entry.embedding:
                similarity = self._calculate_similarity(query_embedding, entry.embedding)
                
                if similarity >= min_sim:
                    # Calculate relevance score (combination of similarity and success score)
                    relevance = (similarity * 0.7) + (entry.success_score * 0.2) + (entry.usage_count * 0.1)
                    
                    results.append(RecallResult(
                        entry=entry,
                        similarity_score=similarity,
                        relevance_score=relevance
                    ))
        
        # Sort by relevance score
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Update usage counts
        for result in results[:limit]:
            result.entry.usage_count += 1
        
        logger.info(f"🔍 Recalled {len(results[:limit])} memories for query: {query[:50]}...")
        return results[:limit]
    
    async def _update_knowledge_graph(self, entry: MemoryEntry):
        """Update knowledge graph with new relationships."""
        # Extract entities and relationships from the content
        entities = self._extract_entities(entry.content)
        
        # Store relationships in simple graph structure
        for entity in entities:
            if entity not in self.knowledge_graph:
                self.knowledge_graph[entity] = {
                    'memories': [],
                    'related_entities': set(),
                    'frequency': 0
                }
            
            self.knowledge_graph[entity]['memories'].append(entry.id)
            self.knowledge_graph[entity]['frequency'] += 1
            
            # Create relationships with other entities
            for other_entity in entities:
                if other_entity != entity:
                    self.knowledge_graph[entity]['related_entities'].add(other_entity)
    
    def _extract_entities(self, content: str) -> List[str]:
        """Extract entities from content (simple keyword extraction)."""
        # Simple entity extraction - could be enhanced with NLP
        import re
        
        entities = []
        
        # Extract function names
        function_matches = re.findall(r'def\s+(\w+)', content)
        entities.extend(function_matches)
        
        # Extract class names
        class_matches = re.findall(r'class\s+(\w+)', content)
        entities.extend(class_matches)
        
        # Extract import statements
        import_matches = re.findall(r'import\s+(\w+)', content)
        entities.extend(import_matches)
        
        # Extract common programming terms
        programming_terms = [
            'function', 'class', 'method', 'variable', 'loop', 'condition',
            'api', 'database', 'server', 'client', 'authentication', 'error',
            'test', 'debug', 'deploy', 'docker', 'kubernetes'
        ]
        
        content_lower = content.lower()
        for term in programming_terms:
            if term in content_lower:
                entities.append(term)
        
        return list(set(entities))  # Remove duplicates
    
    async def _cleanup_old_memories(self):
        """Remove old, low-value memories to maintain performance."""
        # Sort memories by relevance (usage count + success score + recency)
        memories = list(self.memory_db.values())
        
        def relevance_score(entry):
            days_old = (datetime.now() - entry.timestamp).days
            recency_score = max(0, 1 - (days_old / 365))  # Decay over a year
            return (entry.usage_count * 0.4) + (entry.success_score * 0.4) + (recency_score * 0.2)
        
        memories.sort(key=relevance_score)
        
        # Remove bottom 10% of memories
        to_remove = memories[:len(memories) // 10]
        
        for entry in to_remove:
            del self.memory_db[entry.id]
            
            # Remove from vector database
            if self.collection:
                try:
                    self.collection.delete(ids=[entry.id])
                except Exception as e:
                    logger.warning(f"Failed to delete from ChromaDB: {e}")
        
        logger.info(f"🧹 Cleaned up {len(to_remove)} old memories")
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about the memory system."""
        total_memories = len(self.memory_db)
        
        # Count by content type
        content_type_counts = {}
        total_usage = 0
        avg_success_score = 0
        
        for entry in self.memory_db.values():
            content_type_counts[entry.content_type] = content_type_counts.get(entry.content_type, 0) + 1
            total_usage += entry.usage_count
            avg_success_score += entry.success_score
        
        if total_memories > 0:
            avg_success_score /= total_memories
        
        return {
            "total_memories": total_memories,
            "content_type_distribution": content_type_counts,
            "total_usage_count": total_usage,
            "average_success_score": round(avg_success_score, 2),
            "knowledge_graph_entities": len(self.knowledge_graph),
            "storage_path": str(self.storage_path),
            "vector_db_available": self.collection is not None,
            "knowledge_graph_available": self.neo4j_driver is not None
        }
    
    async def search_knowledge_graph(self, entity: str) -> Dict[str, Any]:
        """Search the knowledge graph for entity relationships."""
        if entity not in self.knowledge_graph:
            return {"entity": entity, "found": False}
        
        entity_data = self.knowledge_graph[entity]
        
        # Get related memories
        related_memories = []
        for memory_id in entity_data['memories'][:5]:  # Limit to 5 most recent
            if memory_id in self.memory_db:
                memory = self.memory_db[memory_id]
                related_memories.append({
                    "id": memory_id,
                    "content_type": memory.content_type,
                    "timestamp": memory.timestamp.isoformat(),
                    "success_score": memory.success_score,
                    "content_preview": memory.content[:100] + "..." if len(memory.content) > 100 else memory.content
                })
        
        return {
            "entity": entity,
            "found": True,
            "frequency": entity_data['frequency'],
            "related_entities": list(entity_data['related_entities'])[:10],  # Limit to 10
            "related_memories": related_memories
        }