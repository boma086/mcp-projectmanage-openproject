# Unified Deployment Configuration Standard

This document defines the standardized deployment configuration patterns for all MCP OpenProject solutions.

## Environment Variables Standard

### Required Variables (All Solutions)
```bash
# Application Configuration
APP_NAME=<solution-name>-mcp
APP_VERSION=1.0.0
ENVIRONMENT=development|testing|production
DEBUG=false
LOG_LEVEL=INFO|DEBUG|WARNING|ERROR

# Server Configuration
HOST=0.0.0.0
PORT=<solution-specific-port>
WORKERS=<optimized-for-solution>

# OpenProject Configuration
OPENPROJECT_URL=https://your-openproject.com
OPENPROJECT_API_KEY=your-api-key
OPENPROJECT_TIMEOUT=30
OPENPROJECT_MAX_RETRIES=3

# Performance Configuration
REQUEST_TIMEOUT=30
MAX_CONNECTIONS=100
MAX_CONCURRENT_REQUESTS=500
MAX_REQUEST_SIZE=10485760

# Security Configuration
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
CORS_ALLOW_ORIGINS=http://localhost,http://127.0.0.1
TRUSTED_HOSTS=localhost,127.0.0.1

# Monitoring Configuration
ENABLE_METRICS=true
METRICS_ENDPOINT=/metrics
HEALTH_CHECK_INTERVAL=30
DEEP_HEALTH_CHECK_INTERVAL=300
```

### Solution-Specific Variables

#### HTTP Solution (Port 8010)
```bash
# HTTP Solution Specific
WORKERS=2
MAX_CONNECTIONS=100
CACHE_TTL=300
```

#### FastAPI Solution (Port 8020)
```bash
# FastAPI Solution Specific
WORKERS=4
WORKER_CONNECTIONS=1000
ASYNC_POOL_SIZE=20
HTTP_CLIENT_MAX_CONNECTIONS=100
HTTP_CLIENT_MAX_KEEPALIVE=50
WEBSOCKET_MAX_CONNECTIONS=1000
WEBSOCKET_ENABLED=true
REDIS_URL=redis://redis:6379/0
CACHE_ENABLED=true
```

#### FastMCP Solution (Port 8030)
```bash
# FastMCP Solution Specific
SSE_PORT=8031
MAX_SESSIONS=1000
SESSION_TIMEOUT=3600
REDIS_URL=redis://redis:6379/0
```

#### TypeScript Solution (Port 8040)
```bash
# TypeScript Solution Specific
NODE_ENV=production
NODE_OPTIONS=--max-old-space-size=512
UV_THREADPOOL_SIZE=128
REQUEST_TIMEOUT=30000
```

## Resource Limits Standard

### Base Resource Limits (All Solutions)
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### Solution-Specific Resource Limits

#### HTTP Solution
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

#### FastAPI Solution
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

#### FastMCP Solution
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

#### TypeScript Solution
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

## Health Check Standard

### Standard Health Check Endpoints
- `/health` - Basic health check
- `/health/live` - Liveness probe
- `/health/ready` - Readiness probe
- `/health/deep` - Deep health check (includes external dependencies)

### Standard Health Check Configuration
```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: <solution-port>
  initialDelaySeconds: 60
  periodSeconds: 30
  timeoutSeconds: 10
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /health/ready
    port: <solution-port>
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

## Docker Compose Profile Standard

### Standard Profiles
- `development` - Development environment with hot reload
- `testing` - Testing environment with minimal services
- `production` - Production environment with all optimizations
- `monitoring` - Monitoring stack (Prometheus, Grafana)
- `minimal` - Minimal services for local development

### Standard Service Configuration
```yaml
services:
  <solution-name>:
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: <standard-limit>
          cpus: <standard-cpu>
        reservations:
          memory: <standard-request>
          cpus: <standard-cpu>
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:<port>/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
```

## Kubernetes Manifest Standard

### Standard Labels and Annotations
```yaml
metadata:
  labels:
    app: <solution-name>
    version: v1
    component: mcp-server
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "<port>"
    prometheus.io/path: "/metrics"
```

### Standard HPA Configuration
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: <solution-name>-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: <solution-name>
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Monitoring Standard

### Standard Metrics Collection
- HTTP request metrics (count, duration, status codes)
- Resource usage (CPU, memory)
- Business metrics (reports generated, work packages processed)
- Error tracking and alerting

### Standard Alerting Rules
- High error rate (> 10%)
- High latency (> 2s P95)
- High resource usage (> 80% limits)
- Service unavailability

## Security Standard

### Container Security
- Non-root user execution
- Read-only filesystem where possible
- Security context with privilege restrictions
- Network policies for ingress/egress control

### Environment Security
- Secrets management via Kubernetes secrets
- Environment variable validation
- CORS configuration
- Request rate limiting

## Port Allocation Standard

| Solution | HTTP Port | Internal Port | Description |
|----------|-----------|---------------|-------------|
| HTTP Solution | 8010 | 8010 | Synchronous MCP server |
| FastAPI Solution | 8020 | 8020 | Async MCP server with WebSocket support |
| FastMCP Solution | 8030 | 8030 | MCP-native server |
| FastMCP SSE | 8031 | 8031 | Server-Sent Events for FastMCP |
| TypeScript Solution | 8040 | 8040 | Node.js MCP server |

## Network Configuration Standard

### Docker Networks
- `mcp-network` - Internal service communication
- `openproject-network` - OpenProject connectivity
- `monitoring-network` - Monitoring stack communication

### Kubernetes Networks
- Namespace: `mcp-openproject`
- Network policies for service isolation
- Service mesh integration ready

## Volume Mounts Standard

### Standard Volume Mounts
```yaml
volumeMounts:
  - name: logs
    mountPath: /app/logs
  - name: tmp
    mountPath: /app/tmp
  - name: shared-web
    mountPath: /app/shared-web
    readOnly: true
```

### Standard Volumes
```yaml
volumes:
  - name: logs
    emptyDir: {}
  - name: tmp
    emptyDir: {}
  - name: shared-web
    configMap:
      name: shared-web-assets
```

## Deployment Profiles

### Development Profile
- Debug logging enabled
- Hot reload support
- Minimal resource limits
- All services started

### Testing Profile
- Optimized for CI/CD
- Minimal service set
- Automated health checks
- Resource limits for testing

### Production Profile
- Optimized for performance
- Security hardening
- Full monitoring stack
- Resource limits and autoscaling