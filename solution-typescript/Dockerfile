# Multi-stage build for TypeScript Solution
FROM node:18-alpine as builder

# Install build dependencies
RUN apk add --no-cache \
    git \
    python3 \
    make \
    g++ \
    dumb-init

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./
COPY .eslintrc.json ./
COPY .prettierrc ./

# Install dependencies with optimization
RUN npm ci --only=production && \
    npm cache clean --force

# Copy source code
COPY src/ ./src/
COPY tests/ ./tests/

# Build TypeScript with optimization
RUN npm run build && \
    # Remove development dependencies
    npm prune --production

# Production stage
FROM node:18-alpine as production

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# Install runtime dependencies with Node.js optimizations
RUN apk add --no-cache \
    curl \
    dumb-init \
    # Add system dependencies for native modules
    libgcc \
    libstdc++

# Set working directory
WORKDIR /app

# Copy built application from builder
COPY --from=builder --chown=nextjs:nodejs /app/dist ./dist
COPY --from=builder --chown=nextjs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nextjs:nodejs /app/package*.json ./

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/config && \
    chown -R nextjs:nodejs /app

# Copy environment file
COPY .env.example .env.example

# Create startup script with Node.js optimizations
RUN echo '#!/bin/sh' > /app/start.sh && \
    echo 'exec dumb-init node --max-old-space-size=512 --optimize-for-size --max-executable-size=96 --stack-size=8192 dist/index.js' >> /app/start.sh && \
    chmod +x /app/start.sh

# Switch to non-root user
USER nextjs

# Environment variables with Node.js optimizations
ENV NODE_ENV=production
ENV NODE_OPTIONS="--max-old-space-size=512 --optimize-for-size --max-executable-size=96 --stack-size=8192"
ENV UV_THREADPOOL_SIZE=128
ENV HOST=0.0.0.0
ENV PORT=8040

# Health check with better error handling
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:$PORT/health/live || exit 1

# Expose port
EXPOSE $PORT

# Start command with proper signal handling
CMD ["/app/start.sh"]
