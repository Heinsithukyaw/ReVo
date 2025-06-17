# Migration Guide: Strategic Refactoring

## Overview
This guide helps developers migrate from the old structure to the new enterprise-ready architecture.

## Import Changes

### Old Imports
```python
from src.revoagent.core import Config
from src.revoagent.engines import ReasoningEngine
from src.revoagent.agents import CodeGenerationAgent
```

### New Imports
```python
from packages.core.config import config
from packages.engines import ReasoningEngine
from packages.agents import CodeGenerationAgent
```

## Configuration Changes

### Old Configuration
Multiple config files scattered throughout the project.

### New Configuration
Centralized configuration system:
```python
from packages.core.config import config

# Load all configuration
app_config = config.load_all_config()

# Load specific configuration
env_config = config.load_environment_config()
agents_config = config.load_agents_config()
```

## Development Workflow

### Starting Development
```bash
# Backend
make dev

# Frontend
make dev-frontend

# CLI
python apps/cli/main.py --help
```

### Testing
```bash
# All tests
make test

# Specific test types
make test-unit
make test-integration
```

### Deployment
```bash
# Development environment
make deploy-dev

# Production environment
make deploy-prod
```

## File Organization

### Apps
- Place application entry points in `apps/`
- Each app should be self-contained
- Use packages for shared functionality

### Packages
- Core functionality goes in `packages/`
- Each package should be independently testable
- Follow single responsibility principle

### Configuration
- Environment configs in `config/environments/`
- Component configs in respective `config/` subdirectories
- Use YAML for human-readable configuration

## Best Practices

1. **Import Management**: Always use the new package structure
2. **Configuration**: Use centralized config system
3. **Testing**: Write tests in appropriate `tests/` subdirectories
4. **Documentation**: Update docs when adding features
5. **Security**: Follow security guidelines in centralized config
