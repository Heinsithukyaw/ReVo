# 🐳 reVoAgent Enterprise Platform - Multi-stage Production Build
FROM node:18-alpine AS frontend-builder

# Set working directory for frontend
WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./
RUN npm ci --only=production

# Copy frontend source
COPY frontend/ ./

# Build frontend for production
RUN npm run build

# Python backend stage
FROM python:3.12-slim AS backend-base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM backend-base AS production

# Create non-root user for security
RUN groupadd -r revoagent && useradd -r -g revoagent revoagent

# Copy application code
COPY . .

# Copy built frontend from frontend-builder stage
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create necessary directories and set permissions
RUN mkdir -p /app/data /app/logs && \
    chown -R revoagent:revoagent /app

# Switch to non-root user
USER revoagent

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/system/health || exit 1

# Default command
CMD ["python", "apps/backend/main_with_auth.py"]

# Development stage
FROM backend-base AS development

# Install development dependencies
RUN pip install --no-cache-dir pytest pytest-asyncio pytest-cov black flake8 mypy

# Copy application code
COPY . .

# Expose ports for development (backend + frontend dev server)
EXPOSE 8000 3000

# Development command
CMD ["python", "apps/backend/main_with_auth.py"]