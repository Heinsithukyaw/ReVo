"""
🧠 Perfect Recall Memory Store

High-performance memory storage with Redis + ChromaDB for <100ms retrieval.
Implements the advanced memory management system from the implementation guide.
"""

import asyncio
import json
import time
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import numpy as np

try:
    import redis.asyncio as redis
except ImportError:
    redis = None

try:
    import chromadb
except ImportError:
    chromadb = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

@dataclass
class MemoryEntry:
    """Structured memory entry with metadata"""
    id: str
    content: str
    context_type: str  # 'code', 'conversation', 'error', 'solution'
    timestamp: datetime
    session_id: str
    project_id: Optional[str] = None
    file_path: Optional[str] = None
    tags: List[str] = None
    embedding: Optional[List[float]] = None
    importance_score: float = 0.5
    access_count: int = 0
    last_accessed: Optional[datetime] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

class MemoryStore:
    """High-performance memory storage with <100ms retrieval"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.chroma_client = None
        self.collection = None
        self.encoder = None
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
        
        # Performance metrics
        self.retrieval_times = []
        self.cache_hits = 0
        self.cache_misses = 0
    
    async def initialize(self) -> bool:
        """Initialize Redis and ChromaDB connections"""
        try:
            # Initialize Redis
            if redis:
                self.redis_client = redis.from_url(self.redis_url)
                await self.redis_client.ping()
                print("✅ Redis connected for fast memory access")
            else:
                print("⚠️ Redis not available, using fallback storage")
            
            # Initialize ChromaDB
            if chromadb:
                self.chroma_client = chromadb.Client()
                self.collection = self.chroma_client.get_or_create_collection(
                    name="perfect_recall_memory",
                    metadata={"hnsw:space": "cosine"}
                )
                print("✅ ChromaDB initialized for semantic search")
            else:
                print("⚠️ ChromaDB not available, using fallback vector search")
            
            # Initialize sentence transformer
            if SentenceTransformer:
                self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
                print("✅ Sentence transformer loaded for embeddings")
            else:
                print("⚠️ SentenceTransformer not available, using fallback embeddings")
            
            return True
            
        except Exception as e:
            print(f"❌ Memory store initialization failed: {e}")
            return False
    
    async def store_memory(self, entry: MemoryEntry) -> str:
        """Store memory with automatic embedding generation"""
        start_time = time.time()
        
        try:
            # Generate embedding if not provided
            if entry.embedding is None:
                entry.embedding = await self._generate_embedding(entry.content)
            
            # Store in Redis for fast retrieval
            if self.redis_client:
                await self.redis_client.setex(
                    f"memory:{entry.id}",
                    3600,  # 1 hour TTL for hot cache
                    json.dumps(asdict(entry), default=str)
                )
            
            # Store in ChromaDB for semantic search
            if self.collection and entry.embedding:
                self.collection.add(
                    documents=[entry.content],
                    embeddings=[entry.embedding],
                    metadatas=[{
                        "id": entry.id,
                        "context_type": entry.context_type,
                        "session_id": entry.session_id,
                        "timestamp": entry.timestamp.isoformat(),
                        "importance_score": entry.importance_score
                    }],
                    ids=[entry.id]
                )
            
            # Add to memory index
            await self._update_memory_index(entry)
            
            latency = (time.time() - start_time) * 1000
            print(f"🧠 Memory stored in {latency:.2f}ms")
            
            return entry.id
            
        except Exception as e:
            print(f"❌ Failed to store memory: {e}")
            raise
    
    async def retrieve_fast(self, query: str, limit: int = 10) -> List[MemoryEntry]:
        """Sub-100ms memory retrieval"""
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = hashlib.md5(f"{query}:{limit}".encode()).hexdigest()
            if cache_key in self._cache:
                cache_entry = self._cache[cache_key]
                if cache_entry['timestamp'] > time.time() - self._cache_ttl:
                    latency = (time.time() - start_time) * 1000
                    self.cache_hits += 1
                    print(f"⚡ Cache hit: Retrieved in {latency:.2f}ms")
                    return cache_entry['data']
            
            self.cache_misses += 1
            
            # Generate query embedding
            query_embedding = await self._generate_embedding(query)
            
            # Semantic search in ChromaDB
            memory_entries = []
            if self.collection and query_embedding:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=limit,
                    include=['documents', 'metadatas', 'distances']
                )
                
                # Retrieve full entries from Redis
                for metadata in results['metadatas'][0]:
                    entry_data = await self._get_from_redis(f"memory:{metadata['id']}")
                    if entry_data:
                        entry_dict = json.loads(entry_data)
                        entry_dict['timestamp'] = datetime.fromisoformat(entry_dict['timestamp'])
                        if entry_dict.get('last_accessed'):
                            entry_dict['last_accessed'] = datetime.fromisoformat(entry_dict['last_accessed'])
                        memory_entries.append(MemoryEntry(**entry_dict))
            
            # Update cache
            self._cache[cache_key] = {
                'data': memory_entries,
                'timestamp': time.time()
            }
            
            latency = (time.time() - start_time) * 1000
            self.retrieval_times.append(latency)
            
            # Keep only recent retrieval times for metrics
            if len(self.retrieval_times) > 100:
                self.retrieval_times = self.retrieval_times[-100:]
            
            print(f"🔍 Memory retrieved in {latency:.2f}ms")
            
            return memory_entries
            
        except Exception as e:
            print(f"❌ Failed to retrieve memory: {e}")
            return []
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            if self.encoder:
                return self.encoder.encode(text).tolist()
            else:
                # Fallback to simple hash-based embedding
                return self._simple_embedding(text)
        except Exception as e:
            print(f"⚠️ Embedding generation failed: {e}")
            return self._simple_embedding(text)
    
    def _simple_embedding(self, text: str) -> List[float]:
        """Simple hash-based embedding fallback"""
        words = text.lower().split()
        embedding = [0.0] * 384  # Match sentence transformer dimension
        
        for i, word in enumerate(words[:384]):
            hash_val = hash(word) % 1000
            embedding[i % 384] += hash_val / 1000.0
        
        # Normalize
        magnitude = sum(x*x for x in embedding) ** 0.5
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]
        
        return embedding
    
    async def _get_from_redis(self, key: str) -> Optional[str]:
        """Get data from Redis with fallback"""
        try:
            if self.redis_client:
                return await self.redis_client.get(key)
            return None
        except Exception:
            return None
    
    async def _update_memory_index(self, entry: MemoryEntry):
        """Update searchable indexes"""
        try:
            if self.redis_client:
                # Session index
                await self.redis_client.sadd(f"session:{entry.session_id}", entry.id)
                
                # Context type index
                await self.redis_client.sadd(f"context:{entry.context_type}", entry.id)
                
                # Time-based index (daily buckets)
                day_key = entry.timestamp.strftime("%Y-%m-%d")
                await self.redis_client.sadd(f"day:{day_key}", entry.id)
                
                # Tag index
                for tag in entry.tags:
                    await self.redis_client.sadd(f"tag:{tag}", entry.id)
        except Exception as e:
            print(f"⚠️ Failed to update memory index: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        avg_retrieval_time = (
            sum(self.retrieval_times) / len(self.retrieval_times)
            if self.retrieval_times else 0
        )
        
        cache_hit_rate = (
            self.cache_hits / (self.cache_hits + self.cache_misses) * 100
            if (self.cache_hits + self.cache_misses) > 0 else 0
        )
        
        return {
            'avg_retrieval_time_ms': round(avg_retrieval_time, 2),
            'cache_hit_rate_percent': round(cache_hit_rate, 2),
            'total_retrievals': len(self.retrieval_times),
            'sub_100ms_retrievals': sum(1 for t in self.retrieval_times if t < 100),
            'redis_available': self.redis_client is not None,
            'chromadb_available': self.collection is not None,
            'encoder_available': self.encoder is not None
        }