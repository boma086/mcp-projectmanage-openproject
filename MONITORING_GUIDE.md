# Monitoring and Observability Guide

This guide provides comprehensive documentation for monitoring and observability across all MCP OpenProject solutions.

## 📊 Overview

The MCP OpenProject project provides unified monitoring and observability across all four solution types:
- **HTTP Solution** (FastAPI synchronous mode)
- **FastAPI Solution** (FastAPI async mode)
- **FastMCP Solution** (MCP-native implementation)
- **TypeScript Solution** (Node.js/Express implementation)

## 🏗️ Monitoring Architecture

### Components
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **AlertManager**: Alerting and notifications
- **Node Exporter**: System metrics (optional)
- **Structured Logging**: JSON logs with correlation IDs

### Unified Metrics
All solutions expose consistent metrics:
- HTTP request metrics (count, duration, errors)
- MCP operation metrics (count, duration, success/failure)
- OpenProject API metrics
- Health check status
- Solution-specific metrics

## 🚀 Quick Start

### 1. Start Monitoring Stack

```bash
# Navigate to monitoring directory
cd monitoring

# Start Prometheus, Grafana, and AlertManager
docker-compose up -d
```

### 2. Configure Solutions

Each solution exposes metrics on `/metrics` endpoint:

**HTTP Solution** (Port 8010):
```bash
cd solution-http
python -m src.main
```

**FastAPI Solution** (Port 8020):
```bash
cd solution-fastapi
python app/main.py
```

**FastMCP Solution** (Port 8030):
```bash
cd solution-fastmcp
python src/main.py
```

**TypeScript Solution** (Port 8040):
```bash
cd solution-typescript
npm install
npm start
```

### 3. Access Dashboards

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **AlertManager**: http://localhost:9093

## 📈 Available Dashboards

### 1. Unified Overview Dashboard
- **Location**: `monitoring/grafana/dashboards/unified-overview.json`
- **Purpose**: High-level overview of all solutions
- **Key Metrics**:
  - Service health status
  - HTTP request rates
  - Error rates
  - MCP operations
  - OpenProject connections
  - System resources

### 2. HTTP Solution Dashboard
- **Location**: `monitoring/grafana/dashboards/http-solution.json`
- **Purpose**: Detailed metrics for HTTP solution
- **Key Metrics**:
  - HTTP service health
  - Request rates and errors
  - Response time percentiles
  - MCP operations
  - OpenProject API metrics

### 3. FastAPI Solution Dashboard
- **Location**: `monitoring/grafana/dashboards/fastapi-solution.json`
- **Purpose**: Detailed metrics for FastAPI solution
- **Key Metrics**:
  - WebSocket connections
  - Connection pool health
  - Async request performance
  - MCP operations by tool

### 4. FastMCP Solution Dashboard
- **Location**: `monitoring/grafana/dashboards/fastmcp-solution.json`
- **Purpose**: Detailed metrics for FastMCP solution
- **Key Metrics**:
  - MCP protocol operations
  - SSE connections and messages
  - Session management
  - Operation success rates

### 5. TypeScript Solution Dashboard
- **Location**: `monitoring/grafana/dashboards/typescript-solution.json`
- **Purpose**: Detailed metrics for TypeScript solution
- **Key Metrics**:
  - Node.js performance
  - Memory usage and GC
  - Event loop lag
  - Process health

## 🔍 Health Check Endpoints

All solutions provide standardized health check endpoints:

### Liveness Check
```bash
# HTTP Solution
curl http://localhost:8010/health

# FastAPI Solution
curl http://localhost:8020/health

# FastMCP Solution
curl http://localhost:8030/health/live

# TypeScript Solution
curl http://localhost:8040/health/live
```

### Readiness Check
```bash
# HTTP Solution
curl http://localhost:8010/health/ready

# FastAPI Solution
curl http://localhost:8020/health/ready

# FastMCP Solution
curl http://localhost:8030/health/ready

# TypeScript Solution
curl http://localhost:8040/health/ready
```

### Deep Health Check
```bash
# HTTP Solution
curl http://localhost:8010/health/deep

# FastAPI Solution
curl http://localhost:8020/health/deep

# FastMCP Solution
curl http://localhost:8030/health/deep

# TypeScript Solution
curl http://localhost:8040/health?type=deep
```

## 📊 Metrics Reference

### HTTP Metrics
- `http_requests_total`: Total HTTP requests
- `http_request_duration_seconds`: HTTP request duration
- `http_response_size_bytes`: HTTP response size
- `http_errors_total`: HTTP errors

### MCP Metrics
- `mcp_operations_total`: MCP operations
- `mcp_operation_duration_seconds`: MCP operation duration
- `mcp_errors_total`: MCP errors
- `mcp_sessions_total`: Active MCP sessions (FastMCP)

### External Service Metrics
- `openproject_requests_total`: OpenProject API requests
- `openproject_request_duration_seconds`: OpenProject API duration
- `openproject_connection_status`: OpenProject connection status

### Health Metrics
- `health_check_status`: Health check status
- `active_requests`: Active requests
- `websocket_connections_total`: WebSocket connections (FastAPI)
- `sse_connections_total`: SSE connections (FastMCP)

### Solution-Specific Metrics
- `connection_pool_*`: Connection pool metrics (FastAPI)
- `nodejs_*`: Node.js metrics (TypeScript)
- `mcp_protocol_*`: MCP protocol metrics (FastMCP)

## 🚨 Alerting Rules

### Critical Alerts
- **Service Down**: MCP service unhealthy
- **OpenProject Connection Lost**: API connection lost
- **Service Unreachable**: Service not responding
- **High Disk Usage**: Disk space critical

### Warning Alerts
- **High HTTP Error Rate**: Error rate > 5%
- **High HTTP Response Time**: P95 > 2s
- **High MCP Error Rate**: Error rate > 10%
- **High Memory Usage**: Memory > 85%
- **High CPU Usage**: CPU > 80%

### Solution-Specific Alerts
- **High WebSocket Connections**: > 100 connections (FastAPI)
- **High SSE Connections**: > 50 connections (FastMCP)
- **High Event Loop Lag**: > 500ms (TypeScript)
- **High Heap Memory**: > 90% (TypeScript)

## 🔧 Configuration

### Environment Variables
```bash
# Prometheus configuration
PROMETHEUS_RETENTION_DAYS=15
PROMETHEUS_SCRAPE_INTERVAL=15s

# Grafana configuration
GRAFANA_ADMIN_PASSWORD=admin
GRAFANA_SECRET_KEY=your-secret-key

# AlertManager configuration
ALERTMANAGER_SMTP_HOST=smtp.gmail.com
ALERTMANAGER_SMTP_PORT=587
ALERTMANAGER_SMTP_USER=your-email@gmail.com
ALERTMANAGER_SMTP_PASSWORD=your-password
```

### Custom Metrics
To add custom metrics to any solution:

1. **HTTP/FastAPI Solutions**:
```python
from prometheus_client import Counter, Histogram

# Create custom metric
custom_counter = Counter('custom_operations_total', 'Custom operations', ['type'])

# Record metric
custom_counter.labels(type='custom').inc()
```

2. **TypeScript Solution**:
```typescript
import { Counter, Histogram } from 'prom-client';

// Create custom metric
const customCounter = new Counter({
  name: 'custom_operations_total',
  help: 'Custom operations',
  labelNames: ['type']
});

// Record metric
customCounter.inc({ type: 'custom' });
```

## 📝 Logging

### Structured Logging
All solutions use structured JSON logging with correlation IDs:

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "info",
  "message": "Request completed",
  "request_id": "req_123456",
  "correlation_id": "corr_abcdef",
  "method": "GET",
  "path": "/health",
  "duration_ms": 15.2,
  "status_code": 200
}
```

### Log Levels
- **error**: Critical errors
- **warn**: Warning conditions
- **info**: Informational messages
- **debug**: Debug information

### Log Aggregation
For production, consider:
- **ELK Stack**: Elasticsearch, Logstash, Kibana
- **Loki**: Grafana Loki for log aggregation
- **Cloud Logging**: AWS CloudWatch, Google Cloud Logging

## 🐳 Docker Deployment

### Monitoring Stack
```yaml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml

  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "9093:9093"
    volumes:
      - ./alerting/alert_rules.yml:/etc/alertmanager/alert_rules.yml

volumes:
  prometheus_data:
```

### Solution Deployment
Each solution includes Docker configuration with health checks:

```yaml
# HTTP Solution
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8010/health"]
  interval: 30s
  timeout: 10s
  retries: 3

# FastAPI Solution
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8020/health"]
  interval: 30s
  timeout: 10s
  retries: 3

# FastMCP Solution
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8030/health/live"]
  interval: 30s
  timeout: 10s
  retries: 3

# TypeScript Solution
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8040/health/live"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## 🔍 Troubleshooting

### Common Issues

1. **Metrics Not Showing**:
   - Check if `/metrics` endpoint is accessible
   - Verify Prometheus configuration
   - Check firewall rules

2. **High Memory Usage**:
   - Monitor heap usage (TypeScript)
   - Check for memory leaks
   - Adjust garbage collection settings

3. **Slow Response Times**:
   - Check database queries
   - Monitor external API calls
   - Review connection pool settings

4. **WebSocket/SSE Issues**:
   - Check connection limits
   - Monitor message rates
   - Review client connection handling

### Performance Tuning

1. **Prometheus**:
   - Adjust retention period
   - Optimize scrape intervals
   - Configure recording rules

2. **Grafana**:
   - Optimize dashboard queries
   - Use template variables
   - Configure caching

3. **Solutions**:
   - Adjust connection pool sizes
   - Optimize cache settings
   - Tune async operations

## 📚 Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [AlertManager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [Node Exporter Documentation](https://github.com/prometheus/node_exporter)

## 🔄 Updates and Maintenance

### Regular Tasks
- Review and update alert thresholds
- Monitor disk usage for Prometheus
- Update Grafana dashboards
- Review log retention policies

### Best Practices
- Use labels effectively
- Keep dashboards simple
- Test alert rules regularly
- Document custom metrics

---

This monitoring setup provides comprehensive observability across all MCP OpenProject solutions, enabling effective monitoring, alerting, and troubleshooting in production environments.