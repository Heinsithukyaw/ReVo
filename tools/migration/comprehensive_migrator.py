"""Comprehensive Structure Migrator"""
import shutil
import os
from pathlib import Path

def migrate_structure():
    """Perform comprehensive structure migration"""
    print("🔄 Running comprehensive structure migration...")
    
    project_root = Path.cwd()
    
    # Create new directory structure
    new_structure = {
        "apps": ["backend", "frontend", "cli"],
        "packages": ["core", "engines", "agents", "ai", "integrations", "tools"],
        "config": ["environments", "agents", "engines", "ai", "integrations"],
        "deployment": ["scripts", "docker", "k8s"],
        "tests": ["unit", "integration", "e2e"],
        "docs": ["api", "guides", "architecture"]
    }
    
    for main_dir, subdirs in new_structure.items():
        main_path = project_root / main_dir
        main_path.mkdir(exist_ok=True)
        
        for subdir in subdirs:
            sub_path = main_path / subdir
            sub_path.mkdir(exist_ok=True)
            
            # Create __init__.py for Python packages
            if main_dir == "packages":
                init_file = sub_path / "__init__.py"
                init_file.write_text(f'"""Package: {subdir}"""\n')
            
        print(f"   ✅ Created {main_dir}/ structure")
    
    # Create root-level organizational files
    root_files = {
        "Makefile": create_makefile_content(),
        "ARCHITECTURE.md": create_architecture_content(),
        ".gitignore": create_gitignore_content()
    }
    
    for filename, content in root_files.items():
        file_path = project_root / filename
        if not file_path.exists():  # Don't overwrite existing files
            file_path.write_text(content)
            print(f"   ✅ Created {filename}")
    
    print("✅ Comprehensive structure migration completed")
    return True

def create_makefile_content():
    return """# reVoAgent Development Commands

.PHONY: dev test deploy clean install

# Development
dev:
	python apps/backend/main.py

dev-frontend:
	cd apps/frontend && npm run dev

# Testing
test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

# Deployment
deploy-dev:
	python deployment/scripts/deploy.py --env development

deploy-prod:
	python deployment/scripts/deploy.py --env production

# Maintenance
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

install:
	pip install -e .

# Documentation
docs:
	mkdocs serve

docs-build:
	mkdocs build
"""

def create_architecture_content():
    return """# reVoAgent Architecture

## Overview
reVoAgent is a multi-engine AI platform with enterprise-grade architecture.

## Structure

### Apps Layer (`apps/`)
- `backend/` - FastAPI backend application
- `frontend/` - React TypeScript frontend
- `cli/` - Command-line interface

### Packages Layer (`packages/`)
- `core/` - Core platform functionality
- `engines/` - AI processing engines
- `agents/` - Specialized AI agents
- `ai/` - AI model integrations
- `integrations/` - External service integrations
- `tools/` - Utility tools and helpers

### Configuration (`config/`)
- `environments/` - Environment-specific configs
- `agents/` - Agent configurations
- `engines/` - Engine configurations
- `ai/` - AI model configurations
- `integrations/` - Integration configurations

### Deployment (`deployment/`)
- `scripts/` - Deployment automation
- `docker/` - Docker configurations
- `k8s/` - Kubernetes manifests

### Testing (`tests/`)
- `unit/` - Unit tests
- `integration/` - Integration tests
- `e2e/` - End-to-end tests

## Design Principles
1. **Separation of Concerns** - Clear boundaries between layers
2. **Modularity** - Independent, reusable packages
3. **Scalability** - Enterprise-ready architecture
4. **Maintainability** - Clean, organized codebase
"""

def create_gitignore_content():
    return """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Environment variables
.env
.env.local
.env.production

# Node.js (for frontend)
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Build outputs
dist/
build/

# AI Models (large files)
*.bin
*.safetensors
models/

# Temporary files
tmp/
temp/
"""

if __name__ == "__main__":
    migrate_structure()
