"""
Unified Memory Service for reVoAgent
Provides graceful degradation when advanced memory systems are unavailable
"""

import asyncio
import json
import logging
import time
import sqlite3
import aiosqlite
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from pathlib import Path
import structlog

logger = structlog.get_logger(__name__)

class MemoryType(Enum):
    """Types of memory storage"""
    CONVERSATION = "conversation"
    AGENT_STATE = "agent_state"
    USER_CONTEXT = "user_context"
    TASK_HISTORY = "task_history"
    KNOWLEDGE_BASE = "knowledge_base"
    EMBEDDINGS = "embeddings"

class MemoryProvider(Enum):
    """Available memory providers"""
    COGNEE = "cognee"
    LANCEDB = "lancedb"
    SQLITE = "sqlite"
    IN_MEMORY = "in_memory"
    REDIS = "redis"

@dataclass
class MemoryEntry:
    """Standardized memory entry"""
    id: str
    type: MemoryType
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: float
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "agent_id": self.agent_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        return cls(
            id=data["id"],
            type=MemoryType(data["type"]),
            content=data["content"],
            metadata=data["metadata"],
            timestamp=data["timestamp"],
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            agent_id=data.get("agent_id")
        )

class BaseMemoryProvider:
    """Base class for memory providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_available = False
    
    async def initialize(self) -> bool:
        """Initialize the memory provider"""
        raise NotImplementedError
    
    async def store(self, entry: MemoryEntry) -> bool:
        """Store a memory entry"""
        raise NotImplementedError
    
    async def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry by ID"""
        raise NotImplementedError
    
    async def search(self, query: str, memory_type: MemoryType = None, limit: int = 10) -> List[MemoryEntry]:
        """Search memory entries"""
        raise NotImplementedError
    
    async def list_entries(self, memory_type: MemoryType = None, user_id: str = None, 
                          session_id: str = None, limit: int = 100) -> List[MemoryEntry]:
        """List memory entries with filters"""
        raise NotImplementedError
    
    async def delete(self, entry_id: str) -> bool:
        """Delete a memory entry"""
        raise NotImplementedError
    
    async def cleanup(self, older_than: float = None) -> int:
        """Clean up old entries"""
        raise NotImplementedError

class InMemoryProvider(BaseMemoryProvider):
    """In-memory storage provider (fallback)"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.storage: Dict[str, MemoryEntry] = {}
        self.max_entries = config.get("max_entries", 10000)
    
    async def initialize(self) -> bool:
        """Initialize in-memory storage"""
        self.is_available = True
        logger.info("In-memory storage initialized")
        return True
    
    async def store(self, entry: MemoryEntry) -> bool:
        """Store entry in memory"""
        try:
            # Cleanup if we're at capacity
            if len(self.storage) >= self.max_entries:
                await self._cleanup_oldest()
            
            self.storage[entry.id] = entry
            return True
        except Exception as e:
            logger.error(f"Error storing entry in memory: {e}")
            return False
    
    async def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve entry from memory"""
        return self.storage.get(entry_id)
    
    async def search(self, query: str, memory_type: MemoryType = None, limit: int = 10) -> List[MemoryEntry]:
        """Simple text search in memory"""
        results = []
        query_lower = query.lower()
        
        for entry in self.storage.values():
            if memory_type and entry.type != memory_type:
                continue
            
            # Simple text search in content
            content_str = json.dumps(entry.content).lower()
            if query_lower in content_str:
                results.append(entry)
                if len(results) >= limit:
                    break
        
        # Sort by timestamp (newest first)
        results.sort(key=lambda x: x.timestamp, reverse=True)
        return results[:limit]
    
    async def list_entries(self, memory_type: MemoryType = None, user_id: str = None, 
                          session_id: str = None, limit: int = 100) -> List[MemoryEntry]:
        """List entries with filters"""
        results = []
        
        for entry in self.storage.values():
            if memory_type and entry.type != memory_type:
                continue
            if user_id and entry.user_id != user_id:
                continue
            if session_id and entry.session_id != session_id:
                continue
            
            results.append(entry)
            if len(results) >= limit:
                break
        
        # Sort by timestamp (newest first)
        results.sort(key=lambda x: x.timestamp, reverse=True)
        return results[:limit]
    
    async def delete(self, entry_id: str) -> bool:
        """Delete entry from memory"""
        if entry_id in self.storage:
            del self.storage[entry_id]
            return True
        return False
    
    async def cleanup(self, older_than: float = None) -> int:
        """Clean up old entries"""
        if older_than is None:
            older_than = time.time() - (7 * 24 * 60 * 60)  # 7 days
        
        to_delete = []
        for entry_id, entry in self.storage.items():
            if entry.timestamp < older_than:
                to_delete.append(entry_id)
        
        for entry_id in to_delete:
            del self.storage[entry_id]
        
        return len(to_delete)
    
    async def _cleanup_oldest(self):
        """Remove oldest entries to make space"""
        if not self.storage:
            return
        
        # Remove 10% of oldest entries
        entries_to_remove = max(1, len(self.storage) // 10)
        sorted_entries = sorted(self.storage.items(), key=lambda x: x[1].timestamp)
        
        for i in range(entries_to_remove):
            entry_id = sorted_entries[i][0]
            del self.storage[entry_id]

class SQLiteProvider(BaseMemoryProvider):
    """SQLite storage provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.db_path = config.get("db_path", "data/memory.db")
        self.db = None
    
    async def initialize(self) -> bool:
        """Initialize SQLite database"""
        try:
            # Create directory if it doesn't exist
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            self.db = await aiosqlite.connect(self.db_path)
            
            # Create table
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS memory_entries (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    user_id TEXT,
                    session_id TEXT,
                    agent_id TEXT
                )
            """)
            
            # Create indexes
            await self.db.execute("CREATE INDEX IF NOT EXISTS idx_type ON memory_entries(type)")
            await self.db.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON memory_entries(user_id)")
            await self.db.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON memory_entries(session_id)")
            await self.db.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON memory_entries(timestamp)")
            
            await self.db.commit()
            self.is_available = True
            logger.info(f"SQLite storage initialized: {self.db_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing SQLite storage: {e}")
            return False
    
    async def store(self, entry: MemoryEntry) -> bool:
        """Store entry in SQLite"""
        try:
            await self.db.execute("""
                INSERT OR REPLACE INTO memory_entries 
                (id, type, content, metadata, timestamp, user_id, session_id, agent_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.id,
                entry.type.value,
                json.dumps(entry.content),
                json.dumps(entry.metadata),
                entry.timestamp,
                entry.user_id,
                entry.session_id,
                entry.agent_id
            ))
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error storing entry in SQLite: {e}")
            return False
    
    async def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve entry from SQLite"""
        try:
            cursor = await self.db.execute(
                "SELECT * FROM memory_entries WHERE id = ?", (entry_id,)
            )
            row = await cursor.fetchone()
            
            if row:
                return MemoryEntry(
                    id=row[0],
                    type=MemoryType(row[1]),
                    content=json.loads(row[2]),
                    metadata=json.loads(row[3]),
                    timestamp=row[4],
                    user_id=row[5],
                    session_id=row[6],
                    agent_id=row[7]
                )
            return None
        except Exception as e:
            logger.error(f"Error retrieving entry from SQLite: {e}")
            return None
    
    async def search(self, query: str, memory_type: MemoryType = None, limit: int = 10) -> List[MemoryEntry]:
        """Search entries in SQLite"""
        try:
            sql = "SELECT * FROM memory_entries WHERE content LIKE ?"
            params = [f"%{query}%"]
            
            if memory_type:
                sql += " AND type = ?"
                params.append(memory_type.value)
            
            sql += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor = await self.db.execute(sql, params)
            rows = await cursor.fetchall()
            
            results = []
            for row in rows:
                results.append(MemoryEntry(
                    id=row[0],
                    type=MemoryType(row[1]),
                    content=json.loads(row[2]),
                    metadata=json.loads(row[3]),
                    timestamp=row[4],
                    user_id=row[5],
                    session_id=row[6],
                    agent_id=row[7]
                ))
            
            return results
        except Exception as e:
            logger.error(f"Error searching entries in SQLite: {e}")
            return []
    
    async def list_entries(self, memory_type: MemoryType = None, user_id: str = None, 
                          session_id: str = None, limit: int = 100) -> List[MemoryEntry]:
        """List entries with filters"""
        try:
            sql = "SELECT * FROM memory_entries WHERE 1=1"
            params = []
            
            if memory_type:
                sql += " AND type = ?"
                params.append(memory_type.value)
            
            if user_id:
                sql += " AND user_id = ?"
                params.append(user_id)
            
            if session_id:
                sql += " AND session_id = ?"
                params.append(session_id)
            
            sql += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor = await self.db.execute(sql, params)
            rows = await cursor.fetchall()
            
            results = []
            for row in rows:
                results.append(MemoryEntry(
                    id=row[0],
                    type=MemoryType(row[1]),
                    content=json.loads(row[2]),
                    metadata=json.loads(row[3]),
                    timestamp=row[4],
                    user_id=row[5],
                    session_id=row[6],
                    agent_id=row[7]
                ))
            
            return results
        except Exception as e:
            logger.error(f"Error listing entries from SQLite: {e}")
            return []
    
    async def delete(self, entry_id: str) -> bool:
        """Delete entry from SQLite"""
        try:
            await self.db.execute("DELETE FROM memory_entries WHERE id = ?", (entry_id,))
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting entry from SQLite: {e}")
            return False
    
    async def cleanup(self, older_than: float = None) -> int:
        """Clean up old entries"""
        try:
            if older_than is None:
                older_than = time.time() - (7 * 24 * 60 * 60)  # 7 days
            
            cursor = await self.db.execute(
                "DELETE FROM memory_entries WHERE timestamp < ?", (older_than,)
            )
            await self.db.commit()
            return cursor.rowcount
        except Exception as e:
            logger.error(f"Error cleaning up SQLite entries: {e}")
            return 0

class CogneeProvider(BaseMemoryProvider):
    """Cognee memory provider (when available)"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.cognee = None
    
    async def initialize(self) -> bool:
        """Initialize Cognee"""
        try:
            import cognee
            self.cognee = cognee
            
            # Initialize cognee with config
            await self.cognee.config.set_config(self.config.get("cognee_config", {}))
            self.is_available = True
            logger.info("Cognee memory provider initialized")
            return True
        except ImportError:
            logger.warning("Cognee not available - install with: pip install cognee")
            return False
        except Exception as e:
            logger.error(f"Error initializing Cognee: {e}")
            return False
    
    async def store(self, entry: MemoryEntry) -> bool:
        """Store entry using Cognee"""
        try:
            # Convert to Cognee format and store
            await self.cognee.add(entry.content, metadata=entry.metadata)
            return True
        except Exception as e:
            logger.error(f"Error storing entry in Cognee: {e}")
            return False
    
    async def search(self, query: str, memory_type: MemoryType = None, limit: int = 10) -> List[MemoryEntry]:
        """Search using Cognee"""
        try:
            results = await self.cognee.search(query, limit=limit)
            # Convert Cognee results to MemoryEntry format
            entries = []
            for result in results:
                entry = MemoryEntry(
                    id=str(uuid.uuid4()),
                    type=memory_type or MemoryType.KNOWLEDGE_BASE,
                    content=result,
                    metadata={},
                    timestamp=time.time()
                )
                entries.append(entry)
            return entries
        except Exception as e:
            logger.error(f"Error searching in Cognee: {e}")
            return []
    
    # Implement other methods as needed...

class UnifiedMemoryService:
    """
    Unified memory service with graceful degradation
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.providers: Dict[MemoryProvider, BaseMemoryProvider] = {}
        self.primary_provider: Optional[BaseMemoryProvider] = None
        self.fallback_provider: Optional[BaseMemoryProvider] = None
        self.stats = {
            "entries_stored": 0,
            "entries_retrieved": 0,
            "searches_performed": 0,
            "errors_encountered": 0
        }
    
    async def initialize(self):
        """Initialize memory service with fallback providers"""
        logger.info("Initializing unified memory service...")
        
        # Try to initialize providers in order of preference
        provider_configs = [
            (MemoryProvider.COGNEE, CogneeProvider),
            (MemoryProvider.SQLITE, SQLiteProvider),
            (MemoryProvider.IN_MEMORY, InMemoryProvider)
        ]
        
        for provider_type, provider_class in provider_configs:
            try:
                provider_config = self.config.get(provider_type.value, {})
                provider = provider_class(provider_config)
                
                if await provider.initialize():
                    self.providers[provider_type] = provider
                    
                    if self.primary_provider is None:
                        self.primary_provider = provider
                        logger.info(f"Primary memory provider: {provider_type.value}")
                    elif self.fallback_provider is None:
                        self.fallback_provider = provider
                        logger.info(f"Fallback memory provider: {provider_type.value}")
                
            except Exception as e:
                logger.error(f"Failed to initialize {provider_type.value}: {e}")
        
        if self.primary_provider is None:
            raise RuntimeError("No memory providers could be initialized")
        
        logger.info("Memory service initialized successfully")
    
    async def store(self, memory_type: MemoryType, content: Dict[str, Any], 
                   metadata: Dict[str, Any] = None, user_id: str = None, 
                   session_id: str = None, agent_id: str = None) -> str:
        """Store a memory entry"""
        entry_id = str(uuid.uuid4())
        entry = MemoryEntry(
            id=entry_id,
            type=memory_type,
            content=content,
            metadata=metadata or {},
            timestamp=time.time(),
            user_id=user_id,
            session_id=session_id,
            agent_id=agent_id
        )
        
        # Try primary provider first
        if await self._store_with_provider(self.primary_provider, entry):
            self.stats["entries_stored"] += 1
            return entry_id
        
        # Fallback to secondary provider
        if self.fallback_provider and await self._store_with_provider(self.fallback_provider, entry):
            self.stats["entries_stored"] += 1
            logger.warning("Used fallback provider for storage")
            return entry_id
        
        self.stats["errors_encountered"] += 1
        raise RuntimeError("Failed to store memory entry")
    
    async def _store_with_provider(self, provider: BaseMemoryProvider, entry: MemoryEntry) -> bool:
        """Store entry with a specific provider"""
        try:
            return await provider.store(entry)
        except Exception as e:
            logger.error(f"Error storing with provider: {e}")
            return False
    
    async def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry"""
        # Try primary provider first
        entry = await self._retrieve_with_provider(self.primary_provider, entry_id)
        if entry:
            self.stats["entries_retrieved"] += 1
            return entry
        
        # Try fallback provider
        if self.fallback_provider:
            entry = await self._retrieve_with_provider(self.fallback_provider, entry_id)
            if entry:
                self.stats["entries_retrieved"] += 1
                logger.warning("Used fallback provider for retrieval")
                return entry
        
        return None
    
    async def _retrieve_with_provider(self, provider: BaseMemoryProvider, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve entry with a specific provider"""
        try:
            return await provider.retrieve(entry_id)
        except Exception as e:
            logger.error(f"Error retrieving with provider: {e}")
            return None
    
    async def search(self, query: str, memory_type: MemoryType = None, limit: int = 10) -> List[MemoryEntry]:
        """Search memory entries"""
        self.stats["searches_performed"] += 1
        
        # Try primary provider first
        results = await self._search_with_provider(self.primary_provider, query, memory_type, limit)
        if results:
            return results
        
        # Try fallback provider
        if self.fallback_provider:
            results = await self._search_with_provider(self.fallback_provider, query, memory_type, limit)
            if results:
                logger.warning("Used fallback provider for search")
                return results
        
        return []
    
    async def _search_with_provider(self, provider: BaseMemoryProvider, query: str, 
                                   memory_type: MemoryType = None, limit: int = 10) -> List[MemoryEntry]:
        """Search with a specific provider"""
        try:
            return await provider.search(query, memory_type, limit)
        except Exception as e:
            logger.error(f"Error searching with provider: {e}")
            return []
    
    async def list_entries(self, memory_type: MemoryType = None, user_id: str = None, 
                          session_id: str = None, limit: int = 100) -> List[MemoryEntry]:
        """List memory entries with filters"""
        # Try primary provider first
        results = await self._list_with_provider(self.primary_provider, memory_type, user_id, session_id, limit)
        if results:
            return results
        
        # Try fallback provider
        if self.fallback_provider:
            results = await self._list_with_provider(self.fallback_provider, memory_type, user_id, session_id, limit)
            if results:
                logger.warning("Used fallback provider for listing")
                return results
        
        return []
    
    async def _list_with_provider(self, provider: BaseMemoryProvider, memory_type: MemoryType = None, 
                                 user_id: str = None, session_id: str = None, limit: int = 100) -> List[MemoryEntry]:
        """List entries with a specific provider"""
        try:
            return await provider.list_entries(memory_type, user_id, session_id, limit)
        except Exception as e:
            logger.error(f"Error listing with provider: {e}")
            return []
    
    async def delete(self, entry_id: str) -> bool:
        """Delete a memory entry"""
        success = False
        
        # Try to delete from all providers
        for provider in self.providers.values():
            try:
                if await provider.delete(entry_id):
                    success = True
            except Exception as e:
                logger.error(f"Error deleting from provider: {e}")
        
        return success
    
    async def cleanup(self, older_than: float = None) -> int:
        """Clean up old entries from all providers"""
        total_cleaned = 0
        
        for provider in self.providers.values():
            try:
                cleaned = await provider.cleanup(older_than)
                total_cleaned += cleaned
            except Exception as e:
                logger.error(f"Error cleaning up provider: {e}")
        
        return total_cleaned
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            **self.stats,
            "primary_provider": type(self.primary_provider).__name__ if self.primary_provider else None,
            "fallback_provider": type(self.fallback_provider).__name__ if self.fallback_provider else None,
            "providers_available": len(self.providers)
        }

# Global memory service instance
memory_service = UnifiedMemoryService()

# Convenience functions for external use
async def initialize_memory_service(config: Dict[str, Any] = None):
    """Initialize the memory service"""
    global memory_service
    memory_service = UnifiedMemoryService(config)
    await memory_service.initialize()

async def store_memory(memory_type: MemoryType, content: Dict[str, Any], 
                      metadata: Dict[str, Any] = None, user_id: str = None, 
                      session_id: str = None, agent_id: str = None) -> str:
    """Store a memory entry"""
    return await memory_service.store(memory_type, content, metadata, user_id, session_id, agent_id)

async def retrieve_memory(entry_id: str) -> Optional[MemoryEntry]:
    """Retrieve a memory entry"""
    return await memory_service.retrieve(entry_id)

async def search_memory(query: str, memory_type: MemoryType = None, limit: int = 10) -> List[MemoryEntry]:
    """Search memory entries"""
    return await memory_service.search(query, memory_type, limit)

async def list_memory(memory_type: MemoryType = None, user_id: str = None, 
                     session_id: str = None, limit: int = 100) -> List[MemoryEntry]:
    """List memory entries"""
    return await memory_service.list_entries(memory_type, user_id, session_id, limit)