"""Pydantic schemas for API request/response models."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Authentication schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# Project schemas
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None

class ProjectResponse(ProjectBase):
    id: str
    owner_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Execution schemas
class ExecutionBase(BaseModel):
    agent_type: str
    task_description: str
    parameters: Optional[Dict[str, Any]] = None

class ExecutionCreate(ExecutionBase):
    project_id: Optional[str] = None

class ExecutionUpdate(BaseModel):
    status: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: Optional[int] = None

class ExecutionResponse(ExecutionBase):
    id: str
    user_id: str
    project_id: Optional[str]
    status: str
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    execution_time: Optional[int]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Chat schemas
class ChatSessionBase(BaseModel):
    title: Optional[str] = None

class ChatSessionCreate(ChatSessionBase):
    project_id: Optional[str] = None

class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None
    is_active: Optional[bool] = None

class ChatSessionResponse(ChatSessionBase):
    id: str
    user_id: str
    project_id: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ChatMessageBase(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str
    message_metadata: Optional[Dict[str, Any]] = None

class ChatMessageCreate(ChatMessageBase):
    session_id: str

class ChatMessageResponse(ChatMessageBase):
    id: str
    session_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Agent execution schemas
class AgentExecutionRequest(BaseModel):
    task_description: str
    parameters: Optional[Dict[str, Any]] = None
    project_id: Optional[str] = None

class AgentExecutionResponse(BaseModel):
    execution_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: Optional[int] = None

# Dashboard schemas
class DashboardStats(BaseModel):
    total_executions: int
    successful_executions: int
    failed_executions: int
    total_projects: int
    active_sessions: int

class SystemHealth(BaseModel):
    status: str
    uptime: str
    memory_usage: float
    cpu_usage: float
    active_connections: int

# API Key schemas
class APIKeyCreate(BaseModel):
    name: str
    expires_at: Optional[datetime] = None

class APIKeyResponse(BaseModel):
    id: str
    name: str
    key: str  # Only returned on creation
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class APIKeyList(BaseModel):
    id: str
    name: str
    is_active: bool
    last_used: Optional[datetime]
    created_at: datetime
    expires_at: Optional[datetime]
    
    class Config:
        from_attributes = True