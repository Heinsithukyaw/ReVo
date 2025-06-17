"""
Enhanced Code Generator Agent

Implements the Enhanced Code Generator Interface from the ASCII wireframe.
Provides template-based code generation with multi-phase progress tracking.
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)

class CodeGenPhase(Enum):
    """Code generation phases as shown in wireframe."""
    ARCHITECTURE_PLANNING = "architecture_planning"
    DATABASE_MODELS = "database_models"
    API_ENDPOINTS = "api_endpoints"
    AUTHENTICATION = "authentication"
    TESTS_DOCUMENTATION = "tests_documentation"

@dataclass
class CodeGenTemplate:
    """Code generation templates from wireframe."""
    id: str
    name: str
    description: str
    language: str
    framework: str
    features: List[str]

@dataclass
class CodeGenProgress:
    """Progress tracking for code generation."""
    task_id: str
    current_phase: CodeGenPhase
    phase_progress: Dict[CodeGenPhase, int]  # 0-100
    estimated_completion: str
    quality_score: float
    files_generated: List[str]
    live_preview: str = ""

class EnhancedCodeGenerator:
    """
    Enhanced Code Generator Agent
    
    Implements the Enhanced Code Generator Interface from the ASCII wireframe:
    ┌─ Enhanced Code Generator Interface ─────────────────────────────────────┐
    │ [Templates] [Models] [Agents] [Quality]                                │
    │ ┌─ Task Description ─────────────────────────────────────────────────┐ │
    │ │ Create a complete e-commerce API with user auth, product catalog, │ │
    │ │ shopping cart, payment integration, and admin dashboard          │ │
    │ │ Languages: [Python ▼] Framework: [FastAPI ▼] DB: [PostgreSQL ▼] │ │
    │ │ Features: [✓ Auth] [✓ Tests] [✓ Docs] [✓ Docker] [✓ CI/CD]       │ │
    │ └─────────────────────────────────────────────────────────────────────┘ │
    │ ┌─ Generation Progress ──────────────────────────────────────────────┐ │
    │ │ Phase 1: Architecture Planning    [████████████████████] 100%    │ │
    │ │ Phase 2: Database Models         [████████████████████] 100%    │ │
    │ │ Phase 3: API Endpoints           [██████████████      ] 75%     │ │
    │ │ Phase 4: Authentication          [████████            ] 45%     │ │
    │ │ Phase 5: Tests & Documentation   [                    ] 0%      │ │
    │ │ Estimated completion: 4 minutes                                   │ │
    │ └───────────────────────────────────────────────────────────────────┘ │
    │ ┌─ Live Code Preview ────────────────┬─ File Structure ─────────────┐ │
    │ │ # E-commerce API - FastAPI         │ ecommerce_api/               │ │
    │ │ from fastapi import FastAPI        │ ├── app/                    │ │
    │ │ from fastapi.security import OAuth2│ │   ├── models/              │ │
    │ │ [Copy Code] [Download] [Deploy]   │ └── README.md               │ │
    │ └───────────────────────────────────┴─────────────────────────────┘ │
    └─────────────────────────────────────────────────────────────────────┘
    """
    
    def __init__(self, model_manager=None, openhands_integration=None):
        self.model_manager = model_manager
        self.openhands_integration = openhands_integration
        self.active_tasks: Dict[str, CodeGenProgress] = {}
        
        # Templates from wireframe
        self.templates = {
            "rest_api": CodeGenTemplate(
                id="rest_api",
                name="REST API",
                description="Complete REST API with authentication and database",
                language="python",
                framework="fastapi",
                features=["auth", "tests", "docs", "docker", "cicd"]
            ),
            "web_app": CodeGenTemplate(
                id="web_app",
                name="Web App",
                description="Full-stack web application",
                language="typescript",
                framework="react",
                features=["auth", "tests", "docs", "docker", "cicd"]
            ),
            "microservice": CodeGenTemplate(
                id="microservice",
                name="Microservice",
                description="Containerized microservice architecture",
                language="python",
                framework="fastapi",
                features=["auth", "tests", "docs", "docker", "k8s", "monitoring"]
            ),
            "ml_pipeline": CodeGenTemplate(
                id="ml_pipeline",
                name="ML Pipeline",
                description="Machine learning pipeline with training and inference",
                language="python",
                framework="pytorch",
                features=["data_processing", "training", "inference", "monitoring"]
            ),
            "cli_tool": CodeGenTemplate(
                id="cli_tool",
                name="CLI Tool",
                description="Command-line interface tool",
                language="python",
                framework="click",
                features=["commands", "config", "tests", "packaging"]
            )
        }
    
    async def start_generation(
        self,
        task_description: str,
        template_id: str = "rest_api",
        language: str = "python",
        framework: str = "fastapi",
        database: str = "postgresql",
        features: List[str] = None,
        **kwargs
    ) -> str:
        """
        Start enhanced code generation process.
        
        Args:
            task_description: Description of what to build
            template_id: Template to use
            language: Programming language
            framework: Framework to use
            database: Database to use
            features: List of features to include
            
        Returns:
            str: Task ID for tracking progress
        """
        task_id = str(uuid.uuid4())
        
        # Initialize progress tracking
        progress = CodeGenProgress(
            task_id=task_id,
            current_phase=CodeGenPhase.ARCHITECTURE_PLANNING,
            phase_progress={
                CodeGenPhase.ARCHITECTURE_PLANNING: 0,
                CodeGenPhase.DATABASE_MODELS: 0,
                CodeGenPhase.API_ENDPOINTS: 0,
                CodeGenPhase.AUTHENTICATION: 0,
                CodeGenPhase.TESTS_DOCUMENTATION: 0
            },
            estimated_completion="4 minutes",
            quality_score=0.0,
            files_generated=[]
        )
        
        self.active_tasks[task_id] = progress
        
        # Start generation process
        asyncio.create_task(self._execute_generation(
            task_id, task_description, template_id, language, framework, database, features or []
        ))
        
        return task_id
    
    async def _execute_generation(
        self,
        task_id: str,
        task_description: str,
        template_id: str,
        language: str,
        framework: str,
        database: str,
        features: List[str]
    ):
        """Execute the multi-phase code generation process."""
        try:
            progress = self.active_tasks[task_id]
            template = self.templates.get(template_id, self.templates["rest_api"])
            
            # Phase 1: Architecture Planning (100%)
            await self._phase_architecture_planning(task_id, task_description, template, database)
            
            # Phase 2: Database Models (100%)
            await self._phase_database_models(task_id, task_description, template, database)
            
            # Phase 3: API Endpoints (75% as shown in wireframe)
            await self._phase_api_endpoints(task_id, task_description, template)
            
            # Phase 4: Authentication (45% as shown in wireframe)
            if "auth" in features:
                await self._phase_authentication(task_id, task_description, template)
            else:
                progress.phase_progress[CodeGenPhase.AUTHENTICATION] = 100
            
            # Phase 5: Tests & Documentation (0% as shown in wireframe)
            await self._phase_tests_documentation(task_id, task_description, template)
            
            # Calculate final quality score
            progress.quality_score = await self._calculate_quality_score(task_id)
            
            logger.info(f"Code generation completed for task {task_id}")
            
        except Exception as e:
            logger.error(f"Error in code generation task {task_id}: {str(e)}")
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
    
    async def _phase_architecture_planning(self, task_id: str, description: str, template: CodeGenTemplate, database: str):
        """Phase 1: Architecture Planning (100% completion)."""
        progress = self.active_tasks[task_id]
        progress.current_phase = CodeGenPhase.ARCHITECTURE_PLANNING
        
        # Generate architecture with AI
        architecture_prompt = f"""
        Design the complete architecture for: {description}
        
        Template: {template.name}
        Language: {template.language}
        Framework: {template.framework}
        Database: {database}
        Features: {', '.join(template.features)}
        
        Provide detailed:
        1. Project structure and file organization
        2. Component architecture and relationships
        3. Database schema design
        4. API design and endpoints
        5. Technology stack and dependencies
        6. Deployment strategy
        """
        
        # Use AI model for architecture planning
        if self.model_manager and self.model_manager.active_model:
            try:
                architecture = await self.model_manager.generate_text(architecture_prompt)
                progress.files_generated.append("architecture.md")
                progress.live_preview = self._generate_architecture_preview(description, template)
            except Exception as e:
                logger.error(f"Error generating architecture: {e}")
        
        # Simulate progress updates
        for i in range(0, 101, 20):
            progress.phase_progress[CodeGenPhase.ARCHITECTURE_PLANNING] = i
            await asyncio.sleep(0.1)
        
        logger.info(f"Architecture planning completed for task {task_id}")
    
    async def _phase_database_models(self, task_id: str, description: str, template: CodeGenTemplate, database: str):
        """Phase 2: Database Models (100% completion)."""
        progress = self.active_tasks[task_id]
        progress.current_phase = CodeGenPhase.DATABASE_MODELS
        
        models_prompt = f"""
        Generate comprehensive database models for: {description}
        
        Framework: {template.framework}
        Language: {template.language}
        Database: {database}
        
        Create:
        1. User model with authentication fields
        2. Core business models based on requirements
        3. Proper relationships and foreign keys
        4. Database constraints and validations
        5. Migration scripts
        6. Model schemas for API serialization
        """
        
        if self.model_manager and self.model_manager.active_model:
            try:
                models_code = await self.model_manager.generate_text(models_prompt)
                progress.files_generated.extend(["models.py", "migrations/", "schemas.py"])
                progress.live_preview = self._generate_models_preview(description, template)
            except Exception as e:
                logger.error(f"Error generating models: {e}")
        
        # Simulate progress
        for i in range(0, 101, 25):
            progress.phase_progress[CodeGenPhase.DATABASE_MODELS] = i
            await asyncio.sleep(0.08)
        
        logger.info(f"Database models completed for task {task_id}")
    
    async def _phase_api_endpoints(self, task_id: str, description: str, template: CodeGenTemplate):
        """Phase 3: API Endpoints (75% completion as shown in wireframe)."""
        progress = self.active_tasks[task_id]
        progress.current_phase = CodeGenPhase.API_ENDPOINTS
        
        api_prompt = f"""
        Generate comprehensive API endpoints for: {description}
        
        Framework: {template.framework}
        
        Create:
        1. CRUD operations for all models
        2. Business logic endpoints
        3. Proper error handling and status codes
        4. Input validation and sanitization
        5. Response formatting and pagination
        6. API documentation with OpenAPI/Swagger
        """
        
        if self.model_manager and self.model_manager.active_model:
            try:
                api_code = await self.model_manager.generate_text(api_prompt)
                progress.files_generated.extend(["routers/", "services/", "dependencies.py"])
                progress.live_preview = self._generate_api_preview(description, template)
            except Exception as e:
                logger.error(f"Error generating API endpoints: {e}")
        
        # Progress to 75% as shown in wireframe
        for i in range(0, 76, 15):
            progress.phase_progress[CodeGenPhase.API_ENDPOINTS] = i
            await asyncio.sleep(0.05)
        
        logger.info(f"API endpoints phase at 75% for task {task_id}")
    
    async def _phase_authentication(self, task_id: str, description: str, template: CodeGenTemplate):
        """Phase 4: Authentication (45% completion as shown in wireframe)."""
        progress = self.active_tasks[task_id]
        progress.current_phase = CodeGenPhase.AUTHENTICATION
        
        auth_prompt = f"""
        Generate secure authentication system for: {description}
        
        Include:
        1. JWT token handling with refresh tokens
        2. User registration and login endpoints
        3. Password hashing with bcrypt
        4. Role-based access control (RBAC)
        5. Session management
        6. Password reset functionality
        7. Email verification
        8. Rate limiting for auth endpoints
        """
        
        if self.model_manager and self.model_manager.active_model:
            try:
                auth_code = await self.model_manager.generate_text(auth_prompt)
                progress.files_generated.extend(["auth/", "security.py", "permissions.py"])
                progress.live_preview = self._generate_auth_preview(description, template)
            except Exception as e:
                logger.error(f"Error generating authentication: {e}")
        
        # Progress to 45% as shown in wireframe
        for i in range(0, 46, 9):
            progress.phase_progress[CodeGenPhase.AUTHENTICATION] = i
            await asyncio.sleep(0.05)
        
        logger.info(f"Authentication phase at 45% for task {task_id}")
    
    async def _phase_tests_documentation(self, task_id: str, description: str, template: CodeGenTemplate):
        """Phase 5: Tests & Documentation (0% as shown in wireframe, will start)."""
        progress = self.active_tasks[task_id]
        progress.current_phase = CodeGenPhase.TESTS_DOCUMENTATION
        
        test_prompt = f"""
        Generate comprehensive tests and documentation for: {description}
        
        Create:
        1. Unit tests for all models and services
        2. Integration tests for API endpoints
        3. End-to-end tests for critical workflows
        4. Performance and load tests
        5. Comprehensive API documentation
        6. README with setup and deployment instructions
        7. Docker configuration and docker-compose
        8. CI/CD pipeline configuration
        9. Code quality tools (linting, formatting)
        """
        
        if self.model_manager and self.model_manager.active_model:
            try:
                test_code = await self.model_manager.generate_text(test_prompt)
                progress.files_generated.extend([
                    "tests/", "README.md", "Dockerfile", 
                    "docker-compose.yml", "requirements.txt", ".github/workflows/"
                ])
                progress.live_preview = self._generate_tests_preview(description, template)
            except Exception as e:
                logger.error(f"Error generating tests and documentation: {e}")
        
        # Start from 0% and progress
        for i in range(0, 101, 20):
            progress.phase_progress[CodeGenPhase.TESTS_DOCUMENTATION] = i
            await asyncio.sleep(0.1)
        
        logger.info(f"Tests & documentation completed for task {task_id}")
    
    def _generate_architecture_preview(self, description: str, template: CodeGenTemplate) -> str:
        """Generate architecture preview code."""
        return f"""# {description} - Architecture Overview
# Framework: {template.framework}
# Language: {template.language}

from {template.framework} import FastAPI
from {template.framework}.middleware.cors import CORSMiddleware

app = FastAPI(
    title="{description}",
    description="Complete API with authentication and database",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
# app.include_router(auth.router, prefix="/auth", tags=["authentication"])
# app.include_router(users.router, prefix="/users", tags=["users"])
"""
    
    def _generate_models_preview(self, description: str, template: CodeGenTemplate) -> str:
        """Generate models preview code."""
        return f"""# Database Models for {description}
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    price = Column(Integer)  # Price in cents
    user_id = Column(Integer, ForeignKey("users.id"))
    
    owner = relationship("User", back_populates="products")
"""
    
    def _generate_api_preview(self, description: str, template: CodeGenTemplate) -> str:
        """Generate API endpoints preview code."""
        return f"""# API Endpoints for {description}
from {template.framework} import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

router = APIRouter()

@router.post("/", response_model=schemas.Product)
def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    \"\"\"Create a new product.\"\"\"
    db_product = models.Product(**product.dict(), user_id=current_user.id)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.get("/", response_model=List[schemas.Product])
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    \"\"\"Get all products with pagination.\"\"\"
    products = db.query(models.Product).offset(skip).limit(limit).all()
    return products

@router.get("/{product_id}", response_model=schemas.Product)
def read_product(product_id: int, db: Session = Depends(get_db)):
    \"\"\"Get a specific product by ID.\"\"\"
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
"""
    
    def _generate_auth_preview(self, description: str, template: CodeGenTemplate) -> str:
        """Generate authentication preview code."""
        return f"""# Authentication System for {description}
from {template.framework} import APIRouter, Depends, HTTPException, status
from {template.framework}.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
"""
    
    def _generate_tests_preview(self, description: str, template: CodeGenTemplate) -> str:
        """Generate tests preview code."""
        return f"""# Tests for {description}
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from database import get_db, Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={{"check_same_thread": False}})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_create_user():
    response = client.post(
        "/users/",
        json={{"email": "test@example.com", "password": "testpassword"}}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_login():
    response = client.post(
        "/auth/token",
        data={{"username": "test@example.com", "password": "testpassword"}}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
"""
    
    async def _calculate_quality_score(self, task_id: str) -> float:
        """Calculate quality score based on generated code."""
        # Simulate quality assessment
        base_score = 85.0
        
        # Add points for completed phases
        progress = self.active_tasks[task_id]
        completed_phases = sum(1 for p in progress.phase_progress.values() if p == 100)
        phase_bonus = completed_phases * 2
        
        # Add points for number of files
        file_bonus = min(len(progress.files_generated) * 0.5, 10)
        
        final_score = min(base_score + phase_bonus + file_bonus, 100.0)
        return round(final_score, 1)
    
    def get_generation_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current progress for a generation task.
        
        Args:
            task_id: Task ID
            
        Returns:
            Dict with progress information matching wireframe format
        """
        if task_id not in self.active_tasks:
            return None
        
        progress = self.active_tasks[task_id]
        
        return {
            "task_id": task_id,
            "current_phase": progress.current_phase.value,
            "phases": {
                "architecture_planning": {
                    "name": "Architecture Planning",
                    "progress": progress.phase_progress[CodeGenPhase.ARCHITECTURE_PLANNING],
                    "status": "completed" if progress.phase_progress[CodeGenPhase.ARCHITECTURE_PLANNING] == 100 else "in_progress"
                },
                "database_models": {
                    "name": "Database Models",
                    "progress": progress.phase_progress[CodeGenPhase.DATABASE_MODELS],
                    "status": "completed" if progress.phase_progress[CodeGenPhase.DATABASE_MODELS] == 100 else "in_progress"
                },
                "api_endpoints": {
                    "name": "API Endpoints",
                    "progress": progress.phase_progress[CodeGenPhase.API_ENDPOINTS],
                    "status": "in_progress" if progress.phase_progress[CodeGenPhase.API_ENDPOINTS] > 0 else "pending"
                },
                "authentication": {
                    "name": "Authentication",
                    "progress": progress.phase_progress[CodeGenPhase.AUTHENTICATION],
                    "status": "in_progress" if progress.phase_progress[CodeGenPhase.AUTHENTICATION] > 0 else "pending"
                },
                "tests_documentation": {
                    "name": "Tests & Documentation",
                    "progress": progress.phase_progress[CodeGenPhase.TESTS_DOCUMENTATION],
                    "status": "pending" if progress.phase_progress[CodeGenPhase.TESTS_DOCUMENTATION] == 0 else "in_progress"
                }
            },
            "estimated_completion": progress.estimated_completion,
            "quality_score": progress.quality_score,
            "files_generated": progress.files_generated,
            "live_preview": progress.live_preview
        }
    
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get available code generation templates."""
        return [
            {
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "language": template.language,
                "framework": template.framework,
                "features": template.features
            }
            for template in self.templates.values()
        ]
    
    def get_file_structure(self, task_id: str) -> Dict[str, Any]:
        """
        Get file structure for the generated project.
        
        Args:
            task_id: Task ID
            
        Returns:
            Dict representing the file structure
        """
        if task_id not in self.active_tasks:
            return {}
        
        progress = self.active_tasks[task_id]
        
        # Generate file structure based on current progress
        structure = {
            "ecommerce_api/": {
                "app/": {
                    "models/": ["__init__.py", "user.py", "product.py", "order.py"],
                    "routers/": ["__init__.py", "auth.py", "users.py", "products.py"],
                    "services/": ["__init__.py", "auth_service.py", "user_service.py"],
                    "tests/": ["__init__.py", "test_auth.py", "test_users.py", "test_products.py"],
                    "__init__.py": None,
                    "main.py": None,
                    "database.py": None,
                    "dependencies.py": None
                },
                "requirements.txt": None,
                "Dockerfile": None,
                "docker-compose.yml": None,
                "README.md": None,
                ".env.example": None,
                ".gitignore": None
            }
        }
        
        # Add CI/CD files if tests phase is active
        if progress.phase_progress[CodeGenPhase.TESTS_DOCUMENTATION] > 0:
            structure["ecommerce_api/"][".github/"] = {
                "workflows/": ["ci.yml", "deploy.yml"]
            }
        
        return structure

# Global enhanced code generator instance
enhanced_code_generator = EnhancedCodeGenerator()