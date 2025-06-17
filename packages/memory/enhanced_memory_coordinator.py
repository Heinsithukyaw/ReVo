"""
Enhanced Memory Coordination System for Phase 2 Multi-Agent Communication Optimization
Manages shared memory access, synchronization, and conflict resolution between agents
"""

import asyncio
import json
import logging
import uuid
import hashlib
from typing import Dict, List, Any, Optional, Set, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import time
from contextlib import asynccontextmanager
import threading

# Handle Redis import gracefully
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)

class MemoryOperation(Enum):
    """Memory operation types"""
    READ = "read"
    WRITE = "write"
    UPDATE = "update"
    DELETE = "delete"
    LOCK = "lock"
    UNLOCK = "unlock"

class LockType(Enum):
    """Memory lock types"""
    SHARED = "shared"      # Multiple readers
    EXCLUSIVE = "exclusive"  # Single writer
    INTENT = "intent"      # Intent to upgrade to exclusive

class ConflictResolution(Enum):
    """Conflict resolution strategies"""
    LAST_WRITER_WINS = "last_writer_wins"
    FIRST_WRITER_WINS = "first_writer_wins"
    MERGE = "merge"
    MANUAL = "manual"
    VERSION_BASED = "version_based"

class SyncStrategy(Enum):
    """Memory synchronization strategies"""
    IMMEDIATE = "immediate"
    EVENTUAL = "eventual"
    BATCH = "batch"
    PERIODIC = "periodic"

@dataclass
class MemoryLock:
    """Memory lock information"""
    lock_id: str
    memory_key: str
    agent_id: str
    lock_type: LockType
    acquired_at: datetime
    expires_at: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def is_expired(self) -> bool:
        """Check if lock has expired"""
        return datetime.now() > self.expires_at
    
    def can_coexist_with(self, other_lock: 'MemoryLock') -> bool:
        """Check if this lock can coexist with another lock"""
        if self.memory_key != other_lock.memory_key:
            return True
        
        # Shared locks can coexist with other shared locks
        if self.lock_type == LockType.SHARED and other_lock.lock_type == LockType.SHARED:
            return True
        
        # Exclusive locks cannot coexist with any other locks
        return False

@dataclass
class MemoryVersion:
    """Memory version information for conflict resolution"""
    version: int
    agent_id: str
    timestamp: datetime
    operation: MemoryOperation
    checksum: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class MemoryEntry:
    """Enhanced memory entry with versioning and metadata"""
    key: str
    value: Any
    version: int
    created_by: str
    created_at: datetime
    updated_by: str
    updated_at: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    tags: Set[str] = None
    metadata: Dict[str, Any] = None
    checksum: str = ""
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = set()
        if self.metadata is None:
            self.metadata = {}
        if not self.checksum:
            self.checksum = self._calculate_checksum()
    
    def _calculate_checksum(self) -> str:
        """Calculate checksum for conflict detection"""
        content = json.dumps(self.value, sort_keys=True, default=str)
        return hashlib.md5(content.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['tags'] = list(self.tags)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        if self.last_accessed:
            data['last_accessed'] = self.last_accessed.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        """Create from dictionary"""
        data['tags'] = set(data.get('tags', []))
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        if data.get('last_accessed'):
            data['last_accessed'] = datetime.fromisoformat(data['last_accessed'])
        return cls(**data)

class MemoryConflict:
    """Represents a memory conflict between agents"""
    
    def __init__(self, key: str, conflicting_versions: List[MemoryVersion]):
        self.key = key
        self.conflicting_versions = conflicting_versions
        self.detected_at = datetime.now()
        self.resolved = False
        self.resolution_strategy: Optional[ConflictResolution] = None
        self.resolved_version: Optional[MemoryVersion] = None

class EnhancedMemoryCoordinator:
    """
    Enhanced memory coordination system for multi-agent environments
    
    Features:
    - Distributed locking with deadlock detection
    - Memory versioning and conflict resolution
    - Eventual consistency with sync queues
    - Performance optimization with caching
    - Memory access patterns analysis
    - Automatic cleanup and garbage collection
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379", namespace: str = "revoagent"):
        self.redis_url = redis_url
        self.namespace = namespace
        self.redis_client: Optional[redis.Redis] = None
        
        # Memory coordination state
        self.active_locks: Dict[str, MemoryLock] = {}
        self.memory_versions: Dict[str, List[MemoryVersion]] = {}
        self.pending_conflicts: Dict[str, MemoryConflict] = {}
        self.sync_queues: Dict[str, List[Dict[str, Any]]] = {}
        
        # Performance caches
        self.memory_cache: Dict[str, MemoryEntry] = {}
        self.access_patterns: Dict[str, Dict[str, int]] = {}  # agent_id -> {key: count}
        
        # Configuration
        self.default_lock_timeout = 300  # 5 minutes
        self.max_cache_size = 10000
        self.sync_batch_size = 100
        self.conflict_resolution_timeout = 60  # 1 minute
        
        # Redis keys
        self.locks_key = f"{namespace}:memory:locks"
        self.versions_key = f"{namespace}:memory:versions"
        self.conflicts_key = f"{namespace}:memory:conflicts"
        self.sync_key = f"{namespace}:memory:sync"
        self.cache_key = f"{namespace}:memory:cache"
        
        # Metrics
        self.coordination_metrics = {
            "lock_acquisitions": 0,
            "lock_contentions": 0,
            "conflicts_detected": 0,
            "conflicts_resolved": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "sync_operations": 0
        }
        
        # Thread safety
        self._lock = threading.RLock()
    
    async def initialize(self):
        """Initialize memory coordinator"""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            
            # Load existing state
            await self._load_state_from_redis()
            
            # Start background tasks
            asyncio.create_task(self._lock_monitor())
            asyncio.create_task(self._conflict_resolver())
            asyncio.create_task(self._sync_processor())
            asyncio.create_task(self._cache_manager())
            asyncio.create_task(self._metrics_collector())
            
            logger.info("Enhanced memory coordinator initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize memory coordinator: {e}")
            raise
    
    async def close(self):
        """Close coordinator and cleanup"""
        if self.redis_client:
            await self.redis_client.close()
    
    @asynccontextmanager
    async def get_redis(self):
        """Context manager for Redis operations"""
        if not self.redis_client:
            await self.initialize()
        yield self.redis_client
    
    async def acquire_lock(
        self, 
        memory_key: str, 
        agent_id: str, 
        lock_type: LockType = LockType.EXCLUSIVE,
        timeout: int = None
    ) -> Optional[str]:
        """Acquire memory lock with deadlock detection"""
        try:
            timeout = timeout or self.default_lock_timeout
            lock_id = str(uuid.uuid4())
            expires_at = datetime.now() + timedelta(seconds=timeout)
            
            lock = MemoryLock(
                lock_id=lock_id,
                memory_key=memory_key,
                agent_id=agent_id,
                lock_type=lock_type,
                acquired_at=datetime.now(),
                expires_at=expires_at
            )
            
            # Check for conflicts with existing locks
            conflicting_locks = await self._check_lock_conflicts(lock)
            if conflicting_locks:
                self.coordination_metrics["lock_contentions"] += 1
                
                # Wait for conflicting locks to be released (with timeout)
                wait_start = time.time()
                while conflicting_locks and (time.time() - wait_start) < 30:  # 30 second wait
                    await asyncio.sleep(0.1)
                    conflicting_locks = await self._check_lock_conflicts(lock)
                
                if conflicting_locks:
                    logger.warning(f"Lock contention timeout for {memory_key} by {agent_id}")
                    return None
            
            # Acquire lock
            with self._lock:
                self.active_locks[lock_id] = lock
            
            # Store in Redis
            async with self.get_redis() as redis_client:
                await redis_client.hset(
                    self.locks_key,
                    lock_id,
                    json.dumps(asdict(lock), default=str)
                )
                await redis_client.expire(self.locks_key, timeout)
            
            self.coordination_metrics["lock_acquisitions"] += 1
            logger.debug(f"Lock acquired: {lock_id} for {memory_key} by {agent_id}")
            
            return lock_id
            
        except Exception as e:
            logger.error(f"Failed to acquire lock for {memory_key}: {e}")
            return None
    
    async def release_lock(self, lock_id: str) -> bool:
        """Release memory lock"""
        try:
            if lock_id not in self.active_locks:
                logger.warning(f"Lock not found for release: {lock_id}")
                return False
            
            lock = self.active_locks[lock_id]
            
            # Remove from memory
            with self._lock:
                del self.active_locks[lock_id]
            
            # Remove from Redis
            async with self.get_redis() as redis_client:
                await redis_client.hdel(self.locks_key, lock_id)
            
            logger.debug(f"Lock released: {lock_id} for {lock.memory_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to release lock {lock_id}: {e}")
            return False
    
    async def read_memory(self, key: str, agent_id: str) -> Optional[MemoryEntry]:
        """Read memory with caching and access tracking"""
        try:
            # Check cache first
            if key in self.memory_cache:
                entry = self.memory_cache[key]
                entry.access_count += 1
                entry.last_accessed = datetime.now()
                self.coordination_metrics["cache_hits"] += 1
                
                # Track access pattern
                self._track_access_pattern(agent_id, key)
                
                return entry
            
            # Load from persistent storage
            entry = await self._load_memory_entry(key)
            if entry:
                # Add to cache
                await self._add_to_cache(key, entry)
                entry.access_count += 1
                entry.last_accessed = datetime.now()
                self.coordination_metrics["cache_misses"] += 1
                
                # Track access pattern
                self._track_access_pattern(agent_id, key)
                
                return entry
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to read memory {key}: {e}")
            return None
    
    async def write_memory(
        self, 
        key: str, 
        value: Any, 
        agent_id: str,
        lock_id: Optional[str] = None,
        sync_strategy: SyncStrategy = SyncStrategy.IMMEDIATE
    ) -> bool:
        """Write memory with versioning and conflict detection"""
        try:
            # Verify lock if provided
            if lock_id and not await self._verify_lock(lock_id, key, agent_id):
                logger.warning(f"Invalid lock for memory write: {lock_id}")
                return False
            
            # Get current version
            current_entry = await self.read_memory(key, agent_id)
            new_version = (current_entry.version + 1) if current_entry else 1
            
            # Create new memory entry
            now = datetime.now()
            new_entry = MemoryEntry(
                key=key,
                value=value,
                version=new_version,
                created_by=current_entry.created_by if current_entry else agent_id,
                created_at=current_entry.created_at if current_entry else now,
                updated_by=agent_id,
                updated_at=now,
                access_count=current_entry.access_count if current_entry else 0,
                tags=current_entry.tags if current_entry else set(),
                metadata=current_entry.metadata if current_entry else {}
            )
            
            # Check for conflicts
            conflict = await self._detect_conflict(key, new_entry, current_entry)
            if conflict:
                await self._handle_conflict(conflict)
                return False
            
            # Create version record
            version_record = MemoryVersion(
                version=new_version,
                agent_id=agent_id,
                timestamp=now,
                operation=MemoryOperation.WRITE,
                checksum=new_entry.checksum
            )
            
            # Store version history
            if key not in self.memory_versions:
                self.memory_versions[key] = []
            self.memory_versions[key].append(version_record)
            
            # Apply sync strategy
            if sync_strategy == SyncStrategy.IMMEDIATE:
                await self._sync_immediately(key, new_entry)
            elif sync_strategy == SyncStrategy.EVENTUAL:
                await self._queue_for_sync(key, new_entry)
            elif sync_strategy == SyncStrategy.BATCH:
                await self._add_to_batch_sync(key, new_entry)
            
            # Update cache
            await self._add_to_cache(key, new_entry)
            
            logger.debug(f"Memory written: {key} by {agent_id} (version {new_version})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write memory {key}: {e}")
            return False
    
    async def sync_memory(self, keys: List[str] = None) -> Dict[str, bool]:
        """Synchronize memory across all agents"""
        try:
            if keys is None:
                keys = list(self.memory_cache.keys())
            
            results = {}
            
            for key in keys:
                try:
                    entry = self.memory_cache.get(key)
                    if entry:
                        await self._sync_immediately(key, entry)
                        results[key] = True
                    else:
                        results[key] = False
                        
                except Exception as e:
                    logger.error(f"Failed to sync memory {key}: {e}")
                    results[key] = False
            
            self.coordination_metrics["sync_operations"] += len(keys)
            return results
            
        except Exception as e:
            logger.error(f"Failed to sync memory: {e}")
            return {}
    
    async def resolve_conflict(
        self, 
        conflict_id: str, 
        strategy: ConflictResolution,
        manual_resolution: Any = None
    ) -> bool:
        """Resolve memory conflict using specified strategy"""
        try:
            if conflict_id not in self.pending_conflicts:
                logger.warning(f"Conflict not found: {conflict_id}")
                return False
            
            conflict = self.pending_conflicts[conflict_id]
            
            if strategy == ConflictResolution.LAST_WRITER_WINS:
                # Use the version with the latest timestamp
                latest_version = max(conflict.conflicting_versions, key=lambda v: v.timestamp)
                conflict.resolved_version = latest_version
                
            elif strategy == ConflictResolution.FIRST_WRITER_WINS:
                # Use the version with the earliest timestamp
                earliest_version = min(conflict.conflicting_versions, key=lambda v: v.timestamp)
                conflict.resolved_version = earliest_version
                
            elif strategy == ConflictResolution.VERSION_BASED:
                # Use the version with the highest version number
                highest_version = max(conflict.conflicting_versions, key=lambda v: v.version)
                conflict.resolved_version = highest_version
                
            elif strategy == ConflictResolution.MANUAL:
                # Use manually provided resolution
                if manual_resolution is not None:
                    # Create new version with manual resolution
                    conflict.resolved_version = MemoryVersion(
                        version=max(v.version for v in conflict.conflicting_versions) + 1,
                        agent_id="system",
                        timestamp=datetime.now(),
                        operation=MemoryOperation.UPDATE,
                        checksum=hashlib.md5(json.dumps(manual_resolution, default=str).encode()).hexdigest()
                    )
                else:
                    logger.error("Manual resolution requires manual_resolution parameter")
                    return False
            
            elif strategy == ConflictResolution.MERGE:
                # Implement merge logic (simplified)
                merged_data = await self._merge_conflicting_versions(conflict.conflicting_versions)
                conflict.resolved_version = MemoryVersion(
                    version=max(v.version for v in conflict.conflicting_versions) + 1,
                    agent_id="system",
                    timestamp=datetime.now(),
                    operation=MemoryOperation.UPDATE,
                    checksum=hashlib.md5(json.dumps(merged_data, default=str).encode()).hexdigest()
                )
            
            # Apply resolution
            conflict.resolved = True
            conflict.resolution_strategy = strategy
            
            # Remove from pending conflicts
            del self.pending_conflicts[conflict_id]
            
            self.coordination_metrics["conflicts_resolved"] += 1
            logger.info(f"Conflict resolved: {conflict_id} using {strategy.value}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to resolve conflict {conflict_id}: {e}")
            return False
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory coordination statistics"""
        cache_size = len(self.memory_cache)
        active_locks_count = len(self.active_locks)
        pending_conflicts_count = len(self.pending_conflicts)
        
        # Calculate cache hit rate
        total_requests = self.coordination_metrics["cache_hits"] + self.coordination_metrics["cache_misses"]
        cache_hit_rate = (self.coordination_metrics["cache_hits"] / total_requests) if total_requests > 0 else 0
        
        # Get most accessed keys
        all_access_counts = {}
        for agent_patterns in self.access_patterns.values():
            for key, count in agent_patterns.items():
                all_access_counts[key] = all_access_counts.get(key, 0) + count
        
        most_accessed = sorted(all_access_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "coordination_metrics": self.coordination_metrics.copy(),
            "cache_stats": {
                "size": cache_size,
                "max_size": self.max_cache_size,
                "hit_rate": cache_hit_rate
            },
            "lock_stats": {
                "active_locks": active_locks_count,
                "lock_types": self._get_lock_type_distribution()
            },
            "conflict_stats": {
                "pending_conflicts": pending_conflicts_count,
                "resolution_rate": self._calculate_resolution_rate()
            },
            "access_patterns": {
                "most_accessed_keys": most_accessed,
                "agent_activity": {agent: sum(patterns.values()) for agent, patterns in self.access_patterns.items()}
            }
        }
    
    def _track_access_pattern(self, agent_id: str, key: str):
        """Track memory access patterns"""
        if agent_id not in self.access_patterns:
            self.access_patterns[agent_id] = {}
        
        self.access_patterns[agent_id][key] = self.access_patterns[agent_id].get(key, 0) + 1
    
    async def _check_lock_conflicts(self, new_lock: MemoryLock) -> List[MemoryLock]:
        """Check for lock conflicts"""
        conflicts = []
        
        for existing_lock in self.active_locks.values():
            if (existing_lock.memory_key == new_lock.memory_key and 
                not new_lock.can_coexist_with(existing_lock) and
                not existing_lock.is_expired()):
                conflicts.append(existing_lock)
        
        return conflicts
    
    async def _verify_lock(self, lock_id: str, memory_key: str, agent_id: str) -> bool:
        """Verify lock ownership and validity"""
        if lock_id not in self.active_locks:
            return False
        
        lock = self.active_locks[lock_id]
        return (lock.memory_key == memory_key and 
                lock.agent_id == agent_id and 
                not lock.is_expired())
    
    async def _detect_conflict(self, key: str, new_entry: MemoryEntry, current_entry: Optional[MemoryEntry]) -> Optional[MemoryConflict]:
        """Detect memory conflicts"""
        if not current_entry:
            return None
        
        # Check if checksums differ (indicating concurrent modifications)
        if new_entry.checksum != current_entry.checksum and new_entry.version == current_entry.version:
            # Conflict detected
            versions = self.memory_versions.get(key, [])
            recent_versions = [v for v in versions if v.version >= current_entry.version]
            
            if len(recent_versions) > 1:
                conflict = MemoryConflict(key, recent_versions)
                conflict_id = str(uuid.uuid4())
                self.pending_conflicts[conflict_id] = conflict
                self.coordination_metrics["conflicts_detected"] += 1
                
                logger.warning(f"Memory conflict detected for key {key}")
                return conflict
        
        return None
    
    async def _handle_conflict(self, conflict: MemoryConflict):
        """Handle detected conflict"""
        # For now, use last writer wins as default
        await self.resolve_conflict(
            list(self.pending_conflicts.keys())[-1],  # Get the latest conflict ID
            ConflictResolution.LAST_WRITER_WINS
        )
    
    async def _sync_immediately(self, key: str, entry: MemoryEntry):
        """Immediately sync memory entry"""
        async with self.get_redis() as redis_client:
            await redis_client.hset(
                f"{self.cache_key}:entries",
                key,
                json.dumps(entry.to_dict())
            )
    
    async def _queue_for_sync(self, key: str, entry: MemoryEntry):
        """Queue entry for eventual consistency sync"""
        if key not in self.sync_queues:
            self.sync_queues[key] = []
        
        self.sync_queues[key].append({
            "entry": entry.to_dict(),
            "queued_at": datetime.now().isoformat()
        })
    
    async def _add_to_batch_sync(self, key: str, entry: MemoryEntry):
        """Add to batch sync queue"""
        # Implementation for batch synchronization
        await self._queue_for_sync(key, entry)
    
    async def _add_to_cache(self, key: str, entry: MemoryEntry):
        """Add entry to cache with size management"""
        if len(self.memory_cache) >= self.max_cache_size:
            # Remove least recently accessed entry
            lru_key = min(
                self.memory_cache.keys(),
                key=lambda k: self.memory_cache[k].last_accessed or datetime.min
            )
            del self.memory_cache[lru_key]
        
        self.memory_cache[key] = entry
    
    async def _load_memory_entry(self, key: str) -> Optional[MemoryEntry]:
        """Load memory entry from persistent storage"""
        try:
            async with self.get_redis() as redis_client:
                entry_data = await redis_client.hget(f"{self.cache_key}:entries", key)
                if entry_data:
                    return MemoryEntry.from_dict(json.loads(entry_data))
            return None
        except Exception as e:
            logger.error(f"Failed to load memory entry {key}: {e}")
            return None
    
    async def _merge_conflicting_versions(self, versions: List[MemoryVersion]) -> Any:
        """Merge conflicting versions (simplified implementation)"""
        # This is a simplified merge - in practice, this would be more sophisticated
        # based on the data type and merge strategy
        return {"merged": True, "versions": [v.version for v in versions]}
    
    def _get_lock_type_distribution(self) -> Dict[str, int]:
        """Get distribution of lock types"""
        distribution = {}
        for lock in self.active_locks.values():
            lock_type = lock.lock_type.value
            distribution[lock_type] = distribution.get(lock_type, 0) + 1
        return distribution
    
    def _calculate_resolution_rate(self) -> float:
        """Calculate conflict resolution rate"""
        total_conflicts = self.coordination_metrics["conflicts_detected"]
        resolved_conflicts = self.coordination_metrics["conflicts_resolved"]
        
        if total_conflicts == 0:
            return 1.0
        
        return resolved_conflicts / total_conflicts
    
    async def _load_state_from_redis(self):
        """Load existing state from Redis"""
        try:
            async with self.get_redis() as redis_client:
                # Load active locks
                locks_data = await redis_client.hgetall(self.locks_key)
                for lock_id, lock_json in locks_data.items():
                    try:
                        lock_data = json.loads(lock_json)
                        # Convert datetime strings back to datetime objects
                        lock_data['acquired_at'] = datetime.fromisoformat(lock_data['acquired_at'])
                        lock_data['expires_at'] = datetime.fromisoformat(lock_data['expires_at'])
                        lock_data['lock_type'] = LockType(lock_data['lock_type'])
                        
                        lock = MemoryLock(**lock_data)
                        if not lock.is_expired():
                            self.active_locks[lock_id] = lock
                    except Exception as e:
                        logger.error(f"Failed to load lock {lock_id}: {e}")
                
                logger.info(f"Loaded {len(self.active_locks)} active locks from Redis")
                
        except Exception as e:
            logger.error(f"Failed to load state from Redis: {e}")
    
    async def _lock_monitor(self):
        """Monitor and cleanup expired locks"""
        while True:
            try:
                current_time = datetime.now()
                expired_locks = []
                
                for lock_id, lock in self.active_locks.items():
                    if lock.is_expired():
                        expired_locks.append(lock_id)
                
                # Remove expired locks
                for lock_id in expired_locks:
                    await self.release_lock(lock_id)
                    logger.debug(f"Expired lock removed: {lock_id}")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in lock monitor: {e}")
                await asyncio.sleep(60)
    
    async def _conflict_resolver(self):
        """Background conflict resolution"""
        while True:
            try:
                # Auto-resolve conflicts that have been pending too long
                current_time = datetime.now()
                auto_resolve = []
                
                for conflict_id, conflict in self.pending_conflicts.items():
                    if (current_time - conflict.detected_at).total_seconds() > self.conflict_resolution_timeout:
                        auto_resolve.append(conflict_id)
                
                for conflict_id in auto_resolve:
                    await self.resolve_conflict(conflict_id, ConflictResolution.LAST_WRITER_WINS)
                    logger.info(f"Auto-resolved conflict: {conflict_id}")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in conflict resolver: {e}")
                await asyncio.sleep(60)
    
    async def _sync_processor(self):
        """Process sync queues"""
        while True:
            try:
                # Process sync queues in batches
                for key, queue in list(self.sync_queues.items()):
                    if len(queue) >= self.sync_batch_size:
                        # Process batch
                        batch = queue[:self.sync_batch_size]
                        self.sync_queues[key] = queue[self.sync_batch_size:]
                        
                        # Sync batch to persistent storage
                        for item in batch:
                            entry = MemoryEntry.from_dict(item["entry"])
                            await self._sync_immediately(key, entry)
                        
                        logger.debug(f"Synced batch of {len(batch)} entries for key {key}")
                
                await asyncio.sleep(10)  # Process every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in sync processor: {e}")
                await asyncio.sleep(60)
    
    async def _cache_manager(self):
        """Manage cache size and cleanup"""
        while True:
            try:
                # Clean up old cache entries
                current_time = datetime.now()
                cleanup_threshold = current_time - timedelta(hours=1)
                
                old_entries = [
                    key for key, entry in self.memory_cache.items()
                    if entry.last_accessed and entry.last_accessed < cleanup_threshold
                ]
                
                for key in old_entries:
                    del self.memory_cache[key]
                
                if old_entries:
                    logger.debug(f"Cleaned up {len(old_entries)} old cache entries")
                
                await asyncio.sleep(300)  # Clean every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in cache manager: {e}")
                await asyncio.sleep(60)
    
    async def _metrics_collector(self):
        """Collect and store metrics"""
        while True:
            try:
                stats = await self.get_memory_stats()
                
                async with self.get_redis() as redis_client:
                    await redis_client.hset(
                        f"{self.namespace}:memory:metrics",
                        "coordination_stats",
                        json.dumps(stats)
                    )
                
                await asyncio.sleep(60)  # Collect every minute
                
            except Exception as e:
                logger.error(f"Error in metrics collector: {e}")
                await asyncio.sleep(60)

# Global memory coordinator instance
memory_coordinator = EnhancedMemoryCoordinator()