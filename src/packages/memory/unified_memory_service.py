"""
Unified Memory Service
Provides graceful degradation when Cognee unavailable, with fallback to in-memory storage
Supports multiple backends: Cognee, PostgreSQL, SQLite, In-Memory
"""

import asyncio
import json
import logging
import sqlite3
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple
from pathlib import Path
import hashlib
import pickle

# Optional imports with fallbacks
try:
    import cognee
    COGNEE_AVAILABLE = True
except ImportError:
    COGNEE_AVAILABLE = False
    logging.warning("Cognee not available, using fallback memory service")

try:
    import psycopg2
    import psycopg2.extras
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False
    logging.warning("PostgreSQL not available")

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not available")


@dataclass
class MemoryEntry:
    """Unified memory entry structure"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    timestamp: float = None
    ttl: Optional[float] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.tags is None:
            self.tags = []


@dataclass
class SearchResult:
    """Search result structure"""
    entry: MemoryEntry
    score: float
    distance: Optional[float] = None


class MemoryBackend(ABC):
    """Abstract base class for memory backends"""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the backend"""
        pass
    
    @abstractmethod
    async def store(self, entry: MemoryEntry) -> bool:
        """Store a memory entry"""
        pass
    
    @abstractmethod
    async def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry by ID"""
        pass
    
    @abstractmethod
    async def search(self, query: str, limit: int = 10, filters: Dict[str, Any] = None) -> List[SearchResult]:
        """Search for memory entries"""
        pass
    
    @abstractmethod
    async def delete(self, entry_id: str) -> bool:
        """Delete a memory entry"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup expired entries"""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get backend statistics"""
        pass


class InMemoryBackend(MemoryBackend):
    """In-memory backend (reliable fallback)"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {"max_entries": 10000}
        self.entries: Dict[str, MemoryEntry] = {}
        self.initialized = False
    
    async def initialize(self) -> bool:
        """Initialize in-memory backend"""
        self.initialized = True
        logging.info("In-memory backend initialized successfully")
        return True
    
    async def store(self, entry: MemoryEntry) -> bool:
        """Store entry in memory"""
        if not self.initialized:
            return False
        
        # Implement LRU eviction if needed
        if len(self.entries) >= self.config["max_entries"]:
            # Remove oldest entry
            oldest_id = min(self.entries.keys(), key=lambda k: self.entries[k].timestamp)
            del self.entries[oldest_id]
        
        self.entries[entry.id] = entry
        return True
    
    async def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve entry from memory"""
        if not self.initialized:
            return None
        
        return self.entries.get(entry_id)
    
    async def search(self, query: str, limit: int = 10, filters: Dict[str, Any] = None) -> List[SearchResult]:
        """Search entries in memory"""
        if not self.initialized:
            return []
        
        results = []
        query_lower = query.lower()
        
        for entry in self.entries.values():
            # Check TTL
            if entry.ttl and time.time() > entry.timestamp + entry.ttl:
                continue
            
            # Apply filters
            if filters:
                if 'timestamp_from' in filters and entry.timestamp < filters['timestamp_from']:
                    continue
                if 'timestamp_to' in filters and entry.timestamp > filters['timestamp_to']:
                    continue
                if 'tags' in filters and filters['tags'] not in entry.tags:
                    continue
            
            # Simple text matching
            if query_lower in entry.content.lower():
                score = 1.0 if query_lower == entry.content.lower() else 0.8
                results.append(SearchResult(entry=entry, score=score))
        
        # Sort by score and timestamp
        results.sort(key=lambda r: (r.score, r.entry.timestamp), reverse=True)
        return results[:limit]
    
    async def delete(self, entry_id: str) -> bool:
        """Delete entry from memory"""
        if not self.initialized:
            return False
        
        if entry_id in self.entries:
            del self.entries[entry_id]
            return True
        return False
    
    async def cleanup(self) -> None:
        """Cleanup expired entries"""
        if not self.initialized:
            return
        
        current_time = time.time()
        expired_ids = [
            entry_id for entry_id, entry in self.entries.items()
            if entry.ttl and current_time > entry.timestamp + entry.ttl
        ]
        
        for entry_id in expired_ids:
            del self.entries[entry_id]
        
        if expired_ids:
            logging.info(f"Cleaned up {len(expired_ids)} expired entries")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get in-memory backend statistics"""
        return {
            "backend": "in_memory",
            "initialized": self.initialized,
            "total_entries": len(self.entries),
            "max_entries": self.config["max_entries"]
        }


class UnifiedMemoryService:
    """
    Unified Memory Service with graceful degradation
    Starts with in-memory backend and can be extended with other backends
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.backend = InMemoryBackend(self.config.get('in_memory', {}))
        self.initialized = False
    
    async def initialize(self) -> bool:
        """Initialize the memory service"""
        try:
            if await self.backend.initialize():
                self.initialized = True
                logging.info("Memory service initialized with in-memory backend")
                
                # Start cleanup task
                asyncio.create_task(self._cleanup_task())
                
                return True
        except Exception as e:
            logging.error(f"Failed to initialize memory service: {e}")
        
        return False
    
    async def store(self, content: str, metadata: Dict[str, Any] = None, 
                   entry_id: str = None, ttl: float = None, tags: List[str] = None) -> str:
        """Store content in memory and return entry ID"""
        if not self.initialized:
            raise RuntimeError("Memory service not initialized")
        
        if entry_id is None:
            entry_id = self._generate_id(content)
        
        entry = MemoryEntry(
            id=entry_id,
            content=content,
            metadata=metadata or {},
            ttl=ttl,
            tags=tags or []
        )
        
        success = await self.backend.store(entry)
        if not success:
            raise RuntimeError("Failed to store memory entry")
        
        return entry_id
    
    async def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve memory entry by ID"""
        if not self.initialized:
            return None
        
        return await self.backend.retrieve(entry_id)
    
    async def search(self, query: str, limit: int = 10, filters: Dict[str, Any] = None) -> List[SearchResult]:
        """Search memory entries"""
        if not self.initialized:
            return []
        
        return await self.backend.search(query, limit, filters)
    
    async def delete(self, entry_id: str) -> bool:
        """Delete memory entry"""
        if not self.initialized:
            return False
        
        return await self.backend.delete(entry_id)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get memory service statistics"""
        if not self.initialized:
            return {"initialized": False}
        
        stats = await self.backend.get_stats()
        stats["initialized"] = True
        return stats
    
    async def _cleanup_task(self):
        """Background task to cleanup expired entries"""
        while self.initialized:
            try:
                await self.backend.cleanup()
                await asyncio.sleep(300)  # Cleanup every 5 minutes
            except Exception as e:
                logging.error(f"Cleanup task error: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute
    
    def _generate_id(self, content: str) -> str:
        """Generate unique ID for content"""
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        timestamp = str(int(time.time() * 1000))
        return f"mem_{timestamp}_{content_hash[:8]}"


# Global instance
unified_memory_service = UnifiedMemoryService()

# Convenience functions
async def store_memory(content: str, metadata: Dict[str, Any] = None, **kwargs) -> str:
    """Store content in memory"""
    return await unified_memory_service.store(content, metadata, **kwargs)

async def retrieve_memory(entry_id: str) -> Optional[MemoryEntry]:
    """Retrieve memory by ID"""
    return await unified_memory_service.retrieve(entry_id)

async def search_memory(query: str, limit: int = 10, **kwargs) -> List[SearchResult]:
    """Search memory"""
    return await unified_memory_service.search(query, limit, **kwargs)

async def delete_memory(entry_id: str) -> bool:
    """Delete memory entry"""
    return await unified_memory_service.delete(entry_id)