# Multi-stage build for HTTP MCP Solution
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files
COPY requirements.txt .
COPY ../mcp-core/pyproject.toml ../mcp-core/

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Create non-root user for security
RUN groupadd -r mcpuser && useradd -r -g mcpuser mcpuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy application code
COPY src/ ./src/
COPY requirements.txt .
COPY gunicorn.conf.py .

# Copy shared web assets if they exist
COPY ../shared-web/ ./shared-web/ 2>/dev/null || true

# Copy mcp-core package
COPY ../mcp-core/ ./mcp-core/

# Install mcp-core in editable mode
RUN pip install -e ./mcp-core/

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/templates

# Set proper ownership
RUN chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8010

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Expose port
EXPOSE $PORT

# Start command using Gunicorn for production WSGI deployment
CMD ["gunicorn", "--config", "gunicorn.conf.py", "src.main:app"]