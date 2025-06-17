# 🛠️ reVoAgent Development Guide

## Development Environment Setup

### Prerequisites

- Python 3.9+
- Node.js 18+
- Docker & Docker Compose
- Git

### Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend && npm install

# Setup configuration
cp config/base.yaml config/local.yaml
```

### Running Tests

```bash
# Run transformation tests
python test_transformation.py

# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/
```

### Development Server

```bash
# Start backend
python main.py

# Start frontend (in another terminal)
cd frontend && npm run dev
```

## Project Structure

```
reVoAgent/
├── src/                    # Source code
│   ├── backend/           # Backend services
│   ├── packages/          # Shared packages
│   └── shared/            # Shared utilities
├── frontend/              # React frontend
├── config/                # Configuration files
├── tests/                 # Test suites
├── docs/                  # Documentation
├── scripts/               # Utility scripts
└── archive/               # Archived files
```

## Development Workflow

1. Create feature branch
2. Implement changes
3. Run tests
4. Update documentation
5. Submit pull request

## Code Standards

- Python: Black formatting, type hints required
- TypeScript: ESLint, Prettier formatting
- Documentation: Comprehensive docstrings
- Testing: 90%+ coverage target
