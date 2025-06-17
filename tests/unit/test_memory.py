"""Unit tests for the memory module."""

import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
import pytest

from revoagent.core.memory import MemoryEntry, MemoryManager


class TestMemoryEntry:
    """Test MemoryEntry dataclass."""

    def test_memory_entry_creation(self):
        """Test creating a MemoryEntry."""
        timestamp = datetime.now()
        entry = MemoryEntry(
            id="test-id",
            agent_id="test-agent",
            type="conversation",
            content="Test content",
            metadata={"key": "value"},
            timestamp=timestamp,
            importance=0.8,
            access_count=5,
            last_accessed=timestamp
        )
        
        assert entry.id == "test-id"
        assert entry.agent_id == "test-agent"
        assert entry.type == "conversation"
        assert entry.content == "Test content"
        assert entry.metadata == {"key": "value"}
        assert entry.timestamp == timestamp
        assert entry.importance == 0.8
        assert entry.access_count == 5
        assert entry.last_accessed == timestamp

    def test_memory_entry_defaults(self):
        """Test MemoryEntry with default values."""
        timestamp = datetime.now()
        entry = MemoryEntry(
            id="test-id",
            agent_id="test-agent",
            type="conversation",
            content="Test content",
            metadata={},
            timestamp=timestamp
        )
        
        assert entry.importance == 0.5
        assert entry.access_count == 0
        assert entry.last_accessed is None


class TestMemoryManager:
    """Test MemoryManager class."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_memory.db"
        self.memory_manager = MemoryManager(str(self.db_path), max_memory_size=100)

    def teardown_method(self):
        """Clean up test environment."""
        if self.db_path.exists():
            self.db_path.unlink()

    def test_initialization(self):
        """Test MemoryManager initialization."""
        assert self.memory_manager.db_path == self.db_path
        assert self.memory_manager.max_memory_size == 100
        assert self.memory_manager.cache_size == 100
        assert self.db_path.exists()

    def test_database_schema(self):
        """Test that database schema is created correctly."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='memories'
            """)
            assert cursor.fetchone() is not None
            
            # Check indexes
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND tbl_name='memories'
            """)
            indexes = [row[0] for row in cursor.fetchall()]
            assert "idx_agent_id" in indexes
            assert "idx_type" in indexes
            assert "idx_timestamp" in indexes
            assert "idx_importance" in indexes

    def test_store_memory(self):
        """Test storing a memory entry."""
        timestamp = datetime.now()
        memory = MemoryEntry(
            id="test-memory-1",
            agent_id="agent-1",
            type="conversation",
            content="Test conversation",
            metadata={"session": "test"},
            timestamp=timestamp,
            importance=0.7
        )
        
        self.memory_manager.store_memory(memory)
        
        # Verify memory was stored in database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM memories WHERE id = ?",
                ("test-memory-1",)
            )
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == "test-memory-1"  # id
            assert row[1] == "agent-1"  # agent_id
            assert row[2] == "conversation"  # type
            assert row[3] == "Test conversation"  # content

    def test_store_memory_updates_cache(self):
        """Test that storing memory updates the cache."""
        timestamp = datetime.now()
        memory = MemoryEntry(
            id="test-memory-1",
            agent_id="agent-1",
            type="conversation",
            content="Test conversation",
            metadata={},
            timestamp=timestamp
        )
        
        self.memory_manager.store_memory(memory)
        
        # Check cache was updated
        assert "agent-1" in self.memory_manager.memory_cache
        assert len(self.memory_manager.memory_cache["agent-1"]) == 1
        assert self.memory_manager.memory_cache["agent-1"][0].id == "test-memory-1"

    def test_retrieve_memories_basic(self):
        """Test basic memory retrieval."""
        timestamp = datetime.now()
        memory1 = MemoryEntry(
            id="memory-1",
            agent_id="agent-1",
            type="conversation",
            content="First memory",
            metadata={},
            timestamp=timestamp,
            importance=0.8
        )
        memory2 = MemoryEntry(
            id="memory-2",
            agent_id="agent-1",
            type="task",
            content="Second memory",
            metadata={},
            timestamp=timestamp + timedelta(minutes=1),
            importance=0.6
        )
        
        self.memory_manager.store_memory(memory1)
        self.memory_manager.store_memory(memory2)
        
        memories = self.memory_manager.retrieve_memories("agent-1")
        
        assert len(memories) == 2
        # Should be ordered by importance DESC, then timestamp DESC
        assert memories[0].id == "memory-1"  # Higher importance
        assert memories[1].id == "memory-2"

    def test_retrieve_memories_with_type_filter(self):
        """Test memory retrieval with type filter."""
        timestamp = datetime.now()
        memory1 = MemoryEntry(
            id="memory-1",
            agent_id="agent-1",
            type="conversation",
            content="Conversation memory",
            metadata={},
            timestamp=timestamp,
            importance=0.8
        )
        memory2 = MemoryEntry(
            id="memory-2",
            agent_id="agent-1",
            type="task",
            content="Task memory",
            metadata={},
            timestamp=timestamp,
            importance=0.6
        )
        
        self.memory_manager.store_memory(memory1)
        self.memory_manager.store_memory(memory2)
        
        memories = self.memory_manager.retrieve_memories(
            "agent-1", 
            memory_type="conversation"
        )
        
        assert len(memories) == 1
        assert memories[0].id == "memory-1"
        assert memories[0].type == "conversation"

    def test_retrieve_memories_with_importance_filter(self):
        """Test memory retrieval with importance filter."""
        timestamp = datetime.now()
        memory1 = MemoryEntry(
            id="memory-1",
            agent_id="agent-1",
            type="conversation",
            content="Important memory",
            metadata={},
            timestamp=timestamp,
            importance=0.8
        )
        memory2 = MemoryEntry(
            id="memory-2",
            agent_id="agent-1",
            type="conversation",
            content="Less important memory",
            metadata={},
            timestamp=timestamp,
            importance=0.3
        )
        
        self.memory_manager.store_memory(memory1)
        self.memory_manager.store_memory(memory2)
        
        memories = self.memory_manager.retrieve_memories(
            "agent-1",
            min_importance=0.5
        )
        
        assert len(memories) == 1
        assert memories[0].id == "memory-1"

    def test_retrieve_memories_with_time_range(self):
        """Test memory retrieval with time range filter."""
        base_time = datetime.now()
        memory1 = MemoryEntry(
            id="memory-1",
            agent_id="agent-1",
            type="conversation",
            content="Old memory",
            metadata={},
            timestamp=base_time - timedelta(hours=2),
            importance=0.8
        )
        memory2 = MemoryEntry(
            id="memory-2",
            agent_id="agent-1",
            type="conversation",
            content="Recent memory",
            metadata={},
            timestamp=base_time,
            importance=0.6
        )
        
        self.memory_manager.store_memory(memory1)
        self.memory_manager.store_memory(memory2)
        
        # Retrieve memories from last hour
        time_range = (base_time - timedelta(hours=1), base_time + timedelta(hours=1))
        memories = self.memory_manager.retrieve_memories(
            "agent-1",
            time_range=time_range
        )
        
        assert len(memories) == 1
        assert memories[0].id == "memory-2"

    def test_search_memories(self):
        """Test memory search functionality."""
        timestamp = datetime.now()
        memory1 = MemoryEntry(
            id="memory-1",
            agent_id="agent-1",
            type="conversation",
            content="Python programming discussion",
            metadata={},
            timestamp=timestamp,
            importance=0.8
        )
        memory2 = MemoryEntry(
            id="memory-2",
            agent_id="agent-1",
            type="conversation",
            content="JavaScript development tips",
            metadata={},
            timestamp=timestamp,
            importance=0.6
        )
        
        self.memory_manager.store_memory(memory1)
        self.memory_manager.store_memory(memory2)
        
        # Search for Python-related memories
        memories = self.memory_manager.search_memories("agent-1", "Python")
        
        assert len(memories) == 1
        assert memories[0].id == "memory-1"
        assert "Python" in memories[0].content

    def test_get_recent_memories_from_cache(self):
        """Test getting recent memories from cache."""
        timestamp = datetime.now()
        memory = MemoryEntry(
            id="memory-1",
            agent_id="agent-1",
            type="conversation",
            content="Recent memory",
            metadata={},
            timestamp=timestamp,
            importance=0.8
        )
        
        self.memory_manager.store_memory(memory)
        
        # Should get from cache
        memories = self.memory_manager.get_recent_memories("agent-1", limit=5)
        
        assert len(memories) == 1
        assert memories[0].id == "memory-1"

    def test_get_important_memories(self):
        """Test getting important memories."""
        timestamp = datetime.now()
        memory1 = MemoryEntry(
            id="memory-1",
            agent_id="agent-1",
            type="conversation",
            content="Very important memory",
            metadata={},
            timestamp=timestamp,
            importance=0.9
        )
        memory2 = MemoryEntry(
            id="memory-2",
            agent_id="agent-1",
            type="conversation",
            content="Less important memory",
            metadata={},
            timestamp=timestamp,
            importance=0.5
        )
        
        self.memory_manager.store_memory(memory1)
        self.memory_manager.store_memory(memory2)
        
        memories = self.memory_manager.get_important_memories("agent-1")
        
        assert len(memories) == 1
        assert memories[0].id == "memory-1"
        assert memories[0].importance >= 0.7

    def test_update_memory_importance(self):
        """Test updating memory importance."""
        timestamp = datetime.now()
        memory = MemoryEntry(
            id="memory-1",
            agent_id="agent-1",
            type="conversation",
            content="Test memory",
            metadata={},
            timestamp=timestamp,
            importance=0.5
        )
        
        self.memory_manager.store_memory(memory)
        
        # Update importance
        result = self.memory_manager.update_memory_importance("memory-1", 0.9)
        assert result is True
        
        # Verify update
        memories = self.memory_manager.retrieve_memories("agent-1")
        assert memories[0].importance == 0.9

    def test_update_memory_importance_nonexistent(self):
        """Test updating importance of non-existent memory."""
        result = self.memory_manager.update_memory_importance("nonexistent", 0.9)
        assert result is False

    def test_consolidate_memories(self):
        """Test memory consolidation."""
        # Create a memory manager with small max size
        small_manager = MemoryManager(str(self.db_path), max_memory_size=2)
        
        timestamp = datetime.now()
        
        # Add 3 memories (exceeds max size of 2)
        memories = [
            MemoryEntry(
                id=f"memory-{i}",
                agent_id="agent-1",
                type="conversation",
                content=f"Memory {i}",
                metadata={},
                timestamp=timestamp + timedelta(minutes=i),
                importance=0.3 + (i * 0.1)  # Increasing importance
            )
            for i in range(3)
        ]
        
        for memory in memories:
            small_manager.store_memory(memory)
        
        # Consolidate memories
        small_manager.consolidate_memories("agent-1")
        
        # Should have only 2 memories left (most important ones)
        remaining_memories = small_manager.retrieve_memories("agent-1", limit=10)
        assert len(remaining_memories) == 2
        
        # Should keep the most important ones
        remaining_ids = [m.id for m in remaining_memories]
        assert "memory-2" in remaining_ids  # Highest importance
        assert "memory-1" in remaining_ids  # Second highest

    def test_cleanup_old_memories(self):
        """Test cleaning up old memories."""
        old_time = datetime.now() - timedelta(days=35)
        recent_time = datetime.now() - timedelta(days=5)
        
        old_memory = MemoryEntry(
            id="old-memory",
            agent_id="agent-1",
            type="conversation",
            content="Old memory",
            metadata={},
            timestamp=old_time,
            importance=0.3  # Low importance
        )
        
        recent_memory = MemoryEntry(
            id="recent-memory",
            agent_id="agent-1",
            type="conversation",
            content="Recent memory",
            metadata={},
            timestamp=recent_time,
            importance=0.3
        )
        
        important_old_memory = MemoryEntry(
            id="important-old-memory",
            agent_id="agent-1",
            type="conversation",
            content="Important old memory",
            metadata={},
            timestamp=old_time,
            importance=0.8  # High importance
        )
        
        self.memory_manager.store_memory(old_memory)
        self.memory_manager.store_memory(recent_memory)
        self.memory_manager.store_memory(important_old_memory)
        
        # Clean up memories older than 30 days
        deleted_count = self.memory_manager.cleanup_old_memories(days_old=30)
        
        # Should delete only the old, low-importance memory
        assert deleted_count == 1
        
        remaining_memories = self.memory_manager.retrieve_memories("agent-1", limit=10)
        remaining_ids = [m.id for m in remaining_memories]
        
        assert "old-memory" not in remaining_ids
        assert "recent-memory" in remaining_ids
        assert "important-old-memory" in remaining_ids  # Kept due to high importance

    def test_get_memory_stats(self):
        """Test getting memory statistics."""
        timestamp = datetime.now()
        memories = [
            MemoryEntry(
                id=f"memory-{i}",
                agent_id="agent-1",
                type="conversation" if i % 2 == 0 else "task",
                content=f"Memory {i}",
                metadata={},
                timestamp=timestamp + timedelta(minutes=i),
                importance=0.5 + (i * 0.1)
            )
            for i in range(3)
        ]
        
        for memory in memories:
            self.memory_manager.store_memory(memory)
        
        stats = self.memory_manager.get_memory_stats("agent-1")
        
        assert stats["total_memories"] == 3
        assert stats["average_importance"] == pytest.approx(0.6, rel=1e-2)
        assert stats["memory_types"] == 2  # conversation and task
        assert stats["latest_memory"] is not None
        assert stats["earliest_memory"] is not None

    def test_clear_agent_memories(self):
        """Test clearing all memories for an agent."""
        timestamp = datetime.now()
        memory1 = MemoryEntry(
            id="memory-1",
            agent_id="agent-1",
            type="conversation",
            content="Agent 1 memory",
            metadata={},
            timestamp=timestamp,
            importance=0.8
        )
        memory2 = MemoryEntry(
            id="memory-2",
            agent_id="agent-2",
            type="conversation",
            content="Agent 2 memory",
            metadata={},
            timestamp=timestamp,
            importance=0.8
        )
        
        self.memory_manager.store_memory(memory1)
        self.memory_manager.store_memory(memory2)
        
        # Clear agent-1 memories
        deleted_count = self.memory_manager.clear_agent_memories("agent-1")
        assert deleted_count == 1
        
        # Verify agent-1 memories are gone
        agent1_memories = self.memory_manager.retrieve_memories("agent-1")
        assert len(agent1_memories) == 0
        
        # Verify agent-2 memories remain
        agent2_memories = self.memory_manager.retrieve_memories("agent-2")
        assert len(agent2_memories) == 1
        
        # Verify cache was cleared
        assert "agent-1" not in self.memory_manager.memory_cache

    def test_access_count_update(self):
        """Test that access count is updated when retrieving memories."""
        timestamp = datetime.now()
        memory = MemoryEntry(
            id="memory-1",
            agent_id="agent-1",
            type="conversation",
            content="Test memory",
            metadata={},
            timestamp=timestamp,
            importance=0.8,
            access_count=0
        )
        
        self.memory_manager.store_memory(memory)
        
        # Retrieve memory multiple times
        self.memory_manager.retrieve_memories("agent-1")
        self.memory_manager.retrieve_memories("agent-1")
        
        # Check access count was updated
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT access_count FROM memories WHERE id = ?",
                ("memory-1",)
            )
            access_count = cursor.fetchone()[0]
            assert access_count == 2

    def test_cache_size_limit(self):
        """Test that cache respects size limit."""
        # Create manager with small cache size
        small_cache_manager = MemoryManager(str(self.db_path), max_memory_size=1000)
        small_cache_manager.cache_size = 2
        
        timestamp = datetime.now()
        
        # Add 3 memories (exceeds cache size of 2)
        for i in range(3):
            memory = MemoryEntry(
                id=f"memory-{i}",
                agent_id="agent-1",
                type="conversation",
                content=f"Memory {i}",
                metadata={},
                timestamp=timestamp + timedelta(minutes=i),
                importance=0.5
            )
            small_cache_manager.store_memory(memory)
        
        # Cache should only contain 2 most recent memories
        cache = small_cache_manager.memory_cache["agent-1"]
        assert len(cache) == 2
        
        # Should contain the most recent memories
        cached_ids = [m.id for m in cache]
        assert "memory-2" in cached_ids
        assert "memory-1" in cached_ids
        assert "memory-0" not in cached_ids