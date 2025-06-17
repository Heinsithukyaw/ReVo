"""Memory management for reVoAgent platform."""

import json
import sqlite3
import threading
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path


@dataclass
class MemoryEntry:
    """Individual memory entry."""
    id: str
    agent_id: str
    type: str  # conversation, task, observation, reflection
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime
    importance: float = 0.5  # 0.0 to 1.0
    access_count: int = 0
    last_accessed: Optional[datetime] = None


class MemoryManager:
    """
    Manages agent memory including short-term, long-term, and episodic memory.
    
    Features:
    - Persistent storage using SQLite
    - Memory importance scoring
    - Automatic memory consolidation
    - Context-aware retrieval
    - Memory decay and cleanup
    """
    
    def __init__(self, db_path: str = "data/memory.db", max_memory_size: int = 10000):
        """Initialize memory manager."""
        self.db_path = Path(db_path)
        self.max_memory_size = max_memory_size
        self.lock = threading.RLock()
        
        # In-memory cache for recent memories
        self.memory_cache: Dict[str, List[MemoryEntry]] = {}
        self.cache_size = 100
        
        # Initialize database
        self._initialize_database()
    
    def _initialize_database(self) -> None:
        """Initialize SQLite database for persistent memory storage."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    importance REAL NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_agent_id ON memories(agent_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_type ON memories(type)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance)
            """)
    
    def store_memory(self, memory: MemoryEntry) -> None:
        """Store a memory entry."""
        with self.lock:
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO memories 
                    (id, agent_id, type, content, metadata, timestamp, importance, access_count, last_accessed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    memory.id,
                    memory.agent_id,
                    memory.type,
                    memory.content,
                    json.dumps(memory.metadata),
                    memory.timestamp.isoformat(),
                    memory.importance,
                    memory.access_count,
                    memory.last_accessed.isoformat() if memory.last_accessed else None
                ))
            
            # Update cache
            if memory.agent_id not in self.memory_cache:
                self.memory_cache[memory.agent_id] = []
            
            # Add to cache and maintain size limit
            agent_cache = self.memory_cache[memory.agent_id]
            agent_cache.append(memory)
            
            # Keep only most recent memories in cache
            if len(agent_cache) > self.cache_size:
                agent_cache.sort(key=lambda m: m.timestamp, reverse=True)
                self.memory_cache[memory.agent_id] = agent_cache[:self.cache_size]
    
    def retrieve_memories(
        self,
        agent_id: str,
        memory_type: Optional[str] = None,
        limit: int = 10,
        min_importance: float = 0.0,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> List[MemoryEntry]:
        """Retrieve memories based on criteria."""
        with self.lock:
            query = """
                SELECT id, agent_id, type, content, metadata, timestamp, importance, access_count, last_accessed
                FROM memories 
                WHERE agent_id = ? AND importance >= ?
            """
            params = [agent_id, min_importance]
            
            if memory_type:
                query += " AND type = ?"
                params.append(memory_type)
            
            if time_range:
                query += " AND timestamp BETWEEN ? AND ?"
                params.extend([time_range[0].isoformat(), time_range[1].isoformat()])
            
            query += " ORDER BY importance DESC, timestamp DESC LIMIT ?"
            params.append(limit)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
            
            memories = []
            for row in rows:
                memory = MemoryEntry(
                    id=row[0],
                    agent_id=row[1],
                    type=row[2],
                    content=row[3],
                    metadata=json.loads(row[4]),
                    timestamp=datetime.fromisoformat(row[5]),
                    importance=row[6],
                    access_count=row[7],
                    last_accessed=datetime.fromisoformat(row[8]) if row[8] else None
                )
                memories.append(memory)
                
                # Update access count
                self._update_access_count(memory.id)
            
            return memories
    
    def search_memories(
        self,
        agent_id: str,
        query: str,
        limit: int = 10,
        memory_type: Optional[str] = None
    ) -> List[MemoryEntry]:
        """Search memories by content similarity."""
        # Simple text search for now - could be enhanced with vector similarity
        with self.lock:
            sql_query = """
                SELECT id, agent_id, type, content, metadata, timestamp, importance, access_count, last_accessed
                FROM memories 
                WHERE agent_id = ? AND content LIKE ?
            """
            params = [agent_id, f"%{query}%"]
            
            if memory_type:
                sql_query += " AND type = ?"
                params.append(memory_type)
            
            sql_query += " ORDER BY importance DESC, timestamp DESC LIMIT ?"
            params.append(limit)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(sql_query, params)
                rows = cursor.fetchall()
            
            memories = []
            for row in rows:
                memory = MemoryEntry(
                    id=row[0],
                    agent_id=row[1],
                    type=row[2],
                    content=row[3],
                    metadata=json.loads(row[4]),
                    timestamp=datetime.fromisoformat(row[5]),
                    importance=row[6],
                    access_count=row[7],
                    last_accessed=datetime.fromisoformat(row[8]) if row[8] else None
                )
                memories.append(memory)
                
                # Update access count
                self._update_access_count(memory.id)
            
            return memories
    
    def get_recent_memories(self, agent_id: str, limit: int = 10) -> List[MemoryEntry]:
        """Get most recent memories for an agent."""
        # Check cache first
        if agent_id in self.memory_cache:
            cached_memories = self.memory_cache[agent_id]
            if len(cached_memories) >= limit:
                return sorted(cached_memories, key=lambda m: m.timestamp, reverse=True)[:limit]
        
        # Fallback to database
        return self.retrieve_memories(
            agent_id=agent_id,
            limit=limit
        )
    
    def get_important_memories(self, agent_id: str, limit: int = 10) -> List[MemoryEntry]:
        """Get most important memories for an agent."""
        return self.retrieve_memories(
            agent_id=agent_id,
            limit=limit,
            min_importance=0.7
        )
    
    def update_memory_importance(self, memory_id: str, importance: float) -> bool:
        """Update the importance score of a memory."""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "UPDATE memories SET importance = ? WHERE id = ?",
                    (importance, memory_id)
                )
                return cursor.rowcount > 0
    
    def _update_access_count(self, memory_id: str) -> None:
        """Update access count and last accessed time for a memory."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE memories 
                SET access_count = access_count + 1, last_accessed = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), memory_id))
    
    def consolidate_memories(self, agent_id: str) -> None:
        """Consolidate and clean up old memories."""
        with self.lock:
            # Get memory count for agent
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM memories WHERE agent_id = ?",
                    (agent_id,)
                )
                memory_count = cursor.fetchone()[0]
            
            if memory_count > self.max_memory_size:
                # Remove least important and oldest memories
                memories_to_remove = memory_count - self.max_memory_size
                
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        DELETE FROM memories 
                        WHERE id IN (
                            SELECT id FROM memories 
                            WHERE agent_id = ?
                            ORDER BY importance ASC, timestamp ASC 
                            LIMIT ?
                        )
                    """, (agent_id, memories_to_remove))
    
    def cleanup_old_memories(self, days_old: int = 30) -> int:
        """Clean up memories older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM memories WHERE timestamp < ? AND importance < 0.5",
                    (cutoff_date.isoformat(),)
                )
                return cursor.rowcount
    
    def get_memory_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get memory statistics for an agent."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_memories,
                    AVG(importance) as avg_importance,
                    MAX(timestamp) as latest_memory,
                    MIN(timestamp) as earliest_memory,
                    COUNT(DISTINCT type) as memory_types
                FROM memories 
                WHERE agent_id = ?
            """, (agent_id,))
            
            row = cursor.fetchone()
            
            return {
                "total_memories": row[0],
                "average_importance": row[1] or 0.0,
                "latest_memory": row[2],
                "earliest_memory": row[3],
                "memory_types": row[4]
            }
    
    def clear_agent_memories(self, agent_id: str) -> int:
        """Clear all memories for a specific agent."""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM memories WHERE agent_id = ?",
                    (agent_id,)
                )
                
                # Clear cache
                if agent_id in self.memory_cache:
                    del self.memory_cache[agent_id]
                
                return cursor.rowcount