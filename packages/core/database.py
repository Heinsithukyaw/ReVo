"""
Enhanced database models and configuration for reVoAgent.

Features:
- Async SQLAlchemy with connection pooling
- Performance monitoring and health checks
- Automatic retries and error handling
- Migration support
"""

import os
import asyncio
import time
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass

try:
    from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, JSON, ForeignKey, text
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, relationship, Session
    from sqlalchemy.pool import QueuePool
    from sqlalchemy.dialects.postgresql import UUID
    from sqlalchemy.exc import SQLAlchemyError, DisconnectionError
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

import uuid
from .secret_manager import get_secret, SecretNames
from .logging_config import get_logger

logger = get_logger(__name__)

# Database configuration with connection pooling
@dataclass
class DatabaseConfig:
    """Enhanced database configuration with pooling."""
    url: Optional[str] = None
    secret_name: str = SecretNames.DATABASE_URL
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600  # 1 hour
    pool_pre_ping: bool = True
    echo: bool = False
    connect_timeout: int = 10
    query_timeout: int = 30
    retry_attempts: int = 3

# Enhanced database manager
class DatabaseManager:
    """Enhanced database manager with async support and connection pooling."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.engine = None
        self.async_engine = None
        self.session_factory = None
        self.async_session_factory = None
        self._stats = {
            'total_queries': 0,
            'failed_queries': 0,
            'total_connections': 0,
            'start_time': time.time()
        }
    
    async def initialize(self) -> bool:
        """Initialize both sync and async database engines."""
        try:
            # Get database URL
            db_url = self.config.url or await get_secret(self.config.secret_name) or os.getenv("DATABASE_URL", "sqlite:///./revoagent.db")
            
            # Create sync engine with pooling
            self.engine = create_engine(
                db_url,
                poolclass=QueuePool if "sqlite" not in db_url else None,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                pool_pre_ping=self.config.pool_pre_ping,
                echo=self.config.echo,
                connect_args={"check_same_thread": False} if "sqlite" in db_url else {}
            )
            
            # Create async engine for async operations
            if SQLALCHEMY_AVAILABLE and "sqlite" not in db_url:
                async_url = db_url.replace("postgresql://", "postgresql+asyncpg://").replace("mysql://", "mysql+aiomysql://")
                self.async_engine = create_async_engine(
                    async_url,
                    poolclass=QueuePool,
                    pool_size=self.config.pool_size,
                    max_overflow=self.config.max_overflow,
                    pool_timeout=self.config.pool_timeout,
                    pool_recycle=self.config.pool_recycle,
                    pool_pre_ping=self.config.pool_pre_ping,
                    echo=self.config.echo
                )
                
                self.async_session_factory = async_sessionmaker(
                    self.async_engine,
                    class_=AsyncSession,
                    expire_on_commit=False
                )
            
            # Create session factories
            self.session_factory = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Test connection
            await self._test_connection()
            
            logger.info("Database initialized successfully", extra={
                'database_type': self._get_database_type(db_url),
                'pool_size': self.config.pool_size,
                'async_support': self.async_engine is not None
            })
            
            return True
            
        except Exception as e:
            logger.error("Failed to initialize database", extra={'error': str(e)}, exc_info=True)
            return False
    
    def _get_database_type(self, url: str) -> str:
        """Extract database type from URL."""
        if 'postgresql' in url:
            return 'postgresql'
        elif 'mysql' in url:
            return 'mysql'
        elif 'sqlite' in url:
            return 'sqlite'
        return 'unknown'
    
    async def _test_connection(self):
        """Test database connection."""
        if self.async_engine:
            async with self.async_engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                assert result.scalar() == 1
        else:
            with self.engine.begin() as conn:
                result = conn.execute(text("SELECT 1"))
                assert result.scalar() == 1
        
        self._stats['total_connections'] += 1
    
    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[Any, None]:
        """Get async database session."""
        if not self.async_session_factory:
            raise RuntimeError("Async database not initialized")
        
        session = self.async_session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    def get_session(self) -> Any:
        """Get sync database session."""
        if not self.session_factory:
            raise RuntimeError("Database not initialized")
        return self.session_factory()
    
    async def execute_async_query(self, query: str, params: Optional[Dict] = None):
        """Execute async query with retry logic."""
        for attempt in range(self.config.retry_attempts):
            try:
                async with self.get_async_session() as session:
                    result = await session.execute(text(query), params or {})
                    self._stats['total_queries'] += 1
                    return result.fetchall()
            except (SQLAlchemyError, DisconnectionError) as e:
                self._stats['failed_queries'] += 1
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(0.5 * (2 ** attempt))
                else:
                    logger.error("Query failed after retries", extra={'error': str(e)})
                    raise
    
    async def get_pool_status(self) -> Dict[str, Any]:
        """Get connection pool status."""
        if not self.engine:
            return {'status': 'not_initialized'}
        
        pool = self.engine.pool
        return {
            'size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
            'invalid': pool.invalid(),
            'stats': self._stats
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check."""
        try:
            start_time = time.time()
            if self.async_engine:
                async with self.async_engine.begin() as conn:
                    await conn.execute(text("SELECT 1"))
            else:
                with self.engine.begin() as conn:
                    conn.execute(text("SELECT 1"))
            
            response_time = time.time() - start_time
            
            return {
                'status': 'healthy',
                'response_time': response_time,
                'pool_status': await self.get_pool_status(),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

# Global database manager
_db_manager: Optional[DatabaseManager] = None

def get_database_manager() -> Optional[DatabaseManager]:
    """Get global database manager."""
    return _db_manager

def initialize_database_manager(config: DatabaseConfig) -> DatabaseManager:
    """Initialize global database manager."""
    global _db_manager
    _db_manager = DatabaseManager(config)
    return _db_manager

# Legacy support - keep existing engine and session for backward compatibility
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./revoagent.db")

if SQLALCHEMY_AVAILABLE:
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool if "sqlite" not in DATABASE_URL else None,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=3600,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
    )

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    engine = None
    SessionLocal = None

# Base class for all models
Base = declarative_base() if SQLALCHEMY_AVAILABLE else None

# Enhanced models with monitoring and performance tracking
if SQLALCHEMY_AVAILABLE and Base:
    class RequestLog(Base):
        """Enhanced request logging for monitoring and analytics."""
        __tablename__ = 'request_logs'
        
        id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
        request_id = Column(String, unique=True, nullable=False)
        user_id = Column(String, nullable=True)
        ip_address = Column(String(45), nullable=True)
        endpoint = Column(String(255), nullable=False)
        method = Column(String(10), nullable=False)
        status_code = Column(Integer, nullable=False)
        response_time = Column(Integer, nullable=False)  # milliseconds
        request_size = Column(Integer, nullable=True)  # bytes
        response_size = Column(Integer, nullable=True)  # bytes
        user_agent = Column(String(500), nullable=True)
        rate_limited = Column(Boolean, default=False)
        created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class ModelUsage(Base):
    """Track AI model usage and performance."""
    __tablename__ = 'model_usage'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    model_id = Column(String(255), nullable=False)
    request_id = Column(String(255), nullable=False)
    user_id = Column(String, nullable=True)
    prompt_tokens = Column(Integer, nullable=False)
    completion_tokens = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=False)
    response_time = Column(Integer, nullable=False)  # milliseconds
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    model_version = Column(String(100), nullable=True)
    temperature = Column(String(10), nullable=True)  # Store as string for flexibility
    max_tokens = Column(Integer, nullable=True)
    cost_estimate = Column(String(20), nullable=True)  # Store as string to avoid decimal issues
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class RateLimitLog(Base):
    """Log rate limiting events for monitoring."""
    __tablename__ = 'rate_limit_logs'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    identifier = Column(String(255), nullable=False)
    identifier_type = Column(String(50), nullable=False)  # ip, user_id, api_key
    rule_name = Column(String(255), nullable=False)
    blocked = Column(Boolean, nullable=False)
    current_usage = Column(Integer, nullable=False)
    limit_value = Column(Integer, nullable=False)
    window_seconds = Column(Integer, nullable=False)
    retry_after = Column(Integer, nullable=True)
    endpoint = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class SystemMetrics(Base):
    """Store system performance metrics."""
    __tablename__ = 'system_metrics'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    metric_type = Column(String(100), nullable=False)  # cpu, memory, gpu, disk
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(String(50), nullable=False)  # Store as string for flexibility
    unit = Column(String(20), nullable=True)  # %, GB, MB/s, etc.
    hostname = Column(String(255), nullable=True)
    service_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    executions = relationship("Execution", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")

class Project(Base):
    """Project model for organizing user work."""
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    settings = Column(JSON, default=dict)  # Project-specific settings
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    owner = relationship("User", back_populates="projects")
    executions = relationship("Execution", back_populates="project", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="project", cascade="all, delete-orphan")

class Execution(Base):
    """Execution model for tracking agent task executions."""
    __tablename__ = "executions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True)
    agent_type = Column(String, nullable=False)  # code-generator, debug-agent, etc.
    task_description = Column(Text, nullable=False)
    parameters = Column(JSON, default=dict)
    status = Column(String, default="pending")  # pending, running, completed, failed
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    execution_time = Column(Integer, nullable=True)  # in milliseconds
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="executions")
    project = relationship("Project", back_populates="executions")

class ChatSession(Base):
    """Chat session model for storing conversation history."""
    __tablename__ = "chat_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True)
    title = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    project = relationship("Project", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    """Chat message model for storing individual messages."""
    __tablename__ = "chat_messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    message_metadata = Column(JSON, default=dict)  # Additional message metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")

class APIKey(Base):
    """API key model for external integrations."""
    __tablename__ = "api_keys"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    key_hash = Column(String, nullable=False)  # Hashed API key
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User")

# Database utility functions
def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """Drop all database tables."""
    Base.metadata.drop_all(bind=engine)

def init_database():
    """Initialize database with tables."""
    create_tables()
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_database()