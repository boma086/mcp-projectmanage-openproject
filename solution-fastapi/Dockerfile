# Multi-stage Docker build for async FastAPI MCP server with performance optimizations
# Stage 1: Build stage for dependencies and compilation
FROM python:3.11-slim as builder

# Set build arguments for optimization
ARG DEBIAN_FRONTEND=noninteractive
ARG BUILD_DEPS="build-essential gcc g++ libc6-dev libffi-dev"

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    ${BUILD_DEPS} \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment for isolated dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime stage for production deployment
FROM python:3.11-slim as runtime

# Set runtime arguments and labels
ARG APP_VERSION=1.0.0
ARG BUILD_DATE
ARG VCS_REF

LABEL maintainer="FastAPI MCP Team" \
      version="${APP_VERSION}" \
      description="High-performance async FastAPI MCP OpenProject server" \
      build-date="${BUILD_DATE}" \
      vcs-ref="${VCS_REF}"

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /tmp/* /var/tmp/*

# Create non-root user for security
RUN groupadd -r fastapi && useradd -r -g fastapi -d /app -s /bin/bash fastapi

# Set up application directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY app/ ./app/
COPY uvicorn.conf.py ./
COPY .env* ./

# Copy and install local MCP core library
COPY ../mcp-core ./mcp-core
RUN pip install --no-cache-dir -e ./mcp-core

# Create necessary directories and set permissions
RUN mkdir -p /app/logs /app/tmp /app/uploads && \
    chown -R fastapi:fastapi /app && \
    chmod 755 /app

# Set environment variables for production optimization
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PYTHONIOENCODING=utf-8 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    ENVIRONMENT=production \
    LOG_LEVEL=INFO \
    WORKERS=4 \
    WORKER_CONNECTIONS=1000 \
    MAX_CONCURRENT_REQUESTS=1000 \
    HOST=0.0.0.0 \
    PORT=8020

# Performance optimizations for async operations
ENV ASYNC_POOL_SIZE=20 \
    HTTP_CLIENT_MAX_CONNECTIONS=100 \
    HTTP_CLIENT_MAX_KEEPALIVE=50 \
    WEBSOCKET_MAX_CONNECTIONS=1000 \
    REQUEST_TIMEOUT=30 \
    CACHE_ENABLED=true \
    ENABLE_METRICS=true

# Switch to non-root user
USER fastapi

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose application port
EXPOSE ${PORT}

# Default command with production-optimized uvicorn configuration
CMD ["python", "-m", "uvicorn", \
     "app.main:app", \
     "--config", "uvicorn.conf.py", \
     "--host", "0.0.0.0", \
     "--port", "8020", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--access-log", \
     "--no-server-header"]

# Alternative development command (override with docker run)
# CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8020", "--reload"]