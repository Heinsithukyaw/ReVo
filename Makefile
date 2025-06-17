# reVoAgent Development Commands

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
