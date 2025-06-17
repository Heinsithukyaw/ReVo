# reVoAgent - Revolutionary Agentic Coding System Platform
# Multi-stage Docker build for optimized deployment

# Stage 1: Base image with system dependencies
FROM python:3.12-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    build-essential \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Development dependencies
FROM base as development

# Install additional development tools
RUN apt-get update && apt-get install -y \
    vim \
    htop \
    tree \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for web dashboard (optional)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Stage 3: Production image
FROM base as production

# Create non-root user
RUN useradd --create-home --shell /bin/bash revoagent

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install additional ML/AI packages
RUN pip install --no-cache-dir \
    torch --index-url https://download.pytorch.org/whl/cpu \
    transformers \
    sentence-transformers \
    onnxruntime

# Install browser automation dependencies
RUN pip install --no-cache-dir playwright \
    && playwright install chromium \
    && playwright install-deps chromium

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY main.py .
COPY pyproject.toml .

# Create necessary directories
RUN mkdir -p data models temp logs screenshots \
    && chown -R revoagent:revoagent /app

# Switch to non-root user
USER revoagent

# Expose ports
EXPOSE 8000 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Default command
CMD ["python", "main.py"]

# Stage 4: Development image with additional tools
FROM development as dev

# Install development dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    pytest-cov \
    black \
    isort \
    flake8 \
    mypy \
    pre-commit

# Copy everything for development
COPY . /app/
WORKDIR /app

# Install package in development mode
RUN pip install -e .

# Create non-root user for development
RUN useradd --create-home --shell /bin/bash --groups sudo revoagent \
    && echo "revoagent ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER revoagent

CMD ["python", "main.py"]