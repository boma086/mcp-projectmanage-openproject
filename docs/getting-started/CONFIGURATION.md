# Configuration Guide / 配置指南

This guide explains how to configure OpenProject MCP integration solutions for different environments and use cases.

本指南说明如何为不同环境和使用场景配置 OpenProject MCP 集成解决方案。

## Environment Variables / 环境变量

### Required Variables / 必需变量

```bash
# OpenProject Configuration
OPENPROJECT_URL=https://your-openproject.com
OPENPROJECT_API_KEY=your-api-key-here

# Server Configuration
PORT=8020
HOST=0.0.0.0
```

### Optional Variables / 可选变量

```bash
# Logging Configuration
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json         # json, text
LOG_FILE=logs/app.log   # Optional log file path

# Security Configuration
CORS_ORIGINS=*          # Comma-separated origins
API_RATE_LIMIT=100      # Requests per minute
AUTH_TIMEOUT=3600       # Authentication timeout in seconds

# Performance Configuration
MAX_CONNECTIONS=100     # Maximum concurrent connections
TIMEOUT_SECONDS=30      # Request timeout
WORKER_PROCESSES=4      # Number of worker processes

# OpenProject API Configuration
API_VERSION=v3          # OpenProject API version
REQUEST_TIMEOUT=30      # API request timeout
RETRY_ATTEMPTS=3        # Number of retry attempts
RETRY_DELAY=1           # Delay between retries in seconds

# MCP Protocol Configuration
MCP_PROTOCOL_VERSION=1.0
ENABLE_WEBSOCKET=true   # Enable WebSocket support
WEBSOCKET_PATH=/ws     # WebSocket endpoint path
```

## Configuration Files / 配置文件

### FastAPI Solution Configuration

The FastAPI solution supports additional configuration through `config.py`:

```python
# config.py
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    # OpenProject Configuration
    openproject_url: str = os.getenv("OPENPROJECT_URL")
    openproject_api_key: str = os.getenv("OPENPROJECT_API_KEY")
    
    # Server Configuration
    port: int = int(os.getenv("PORT", "8020"))
    host: str = os.getenv("HOST", "0.0.0.0")
    
    # Security Configuration
    cors_origins: list = ["*"]
    api_rate_limit: int = 100
    
    # Performance Configuration
    max_connections: int = 100
    timeout_seconds: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### HTTP Solution Configuration

The HTTP solution uses a simpler configuration approach:

```python
# config.py
import os

class Config:
    # OpenProject Configuration
    OPENPROJECT_URL = os.getenv('OPENPROJECT_URL')
    OPENPROJECT_API_KEY = os.getenv('OPENPROJECT_API_KEY')
    
    # Server Configuration
    PORT = int(os.getenv('PORT', '8010'))
    HOST = os.getenv('HOST', '0.0.0.0')
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.getenv('LOG_FORMAT', 'json')
```

## Environment-Specific Configuration / 环境特定配置

### Development Environment / 开发环境

```bash
# .env.development
OPENPROJECT_URL=https://dev-openproject.com
OPENPROJECT_API_KEY=dev-api-key
PORT=8020
LOG_LEVEL=DEBUG
LOG_FORMAT=text
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

### Production Environment / 生产环境

```bash
# .env.production
OPENPROJECT_URL=https://prod-openproject.com
OPENPROJECT_API_KEY=prod-api-key
PORT=8020
LOG_LEVEL=INFO
LOG_FORMAT=json
CORS_ORIGINS=https://your-domain.com
API_RATE_LIMIT=1000
MAX_CONNECTIONS=500
```

### Testing Environment / 测试环境

```bash
# .env.test
OPENPROJECT_URL=https://test-openproject.com
OPENPROJECT_API_KEY=test-api-key
PORT=8020
LOG_LEVEL=WARNING
LOG_FORMAT=json
API_RATE_LIMIT=50
```

## OpenProject Configuration / OpenProject 配置

### API Key Generation / API 密钥生成

1. **Log in to OpenProject** as an administrator
2. **Navigate to** your user profile
3. **Generate API key** in the API section
4. **Copy the key** and save it securely

### Required Permissions / 所需权限

The API key should have permissions for:
- **Project Management**: Read and write access to projects
- **Work Package Management**: Create, read, update, delete work packages
- **User Management**: Read access to user information
- **Report Generation**: Generate and download reports

### Rate Limiting / 速率限制

OpenProject API has rate limits. Configure accordingly:

```bash
# Conservative settings for limited API access
REQUEST_TIMEOUT=60
RETRY_ATTEMPTS=5
RETRY_DELAY=2
API_RATE_LIMIT=50
```

## Security Configuration / 安全配置

### Authentication / 认证

```bash
# Enable API key authentication
AUTH_TYPE=api_key

# Set token expiration
AUTH_TIMEOUT=7200  # 2 hours

# Enable token refresh
ENABLE_TOKEN_REFRESH=true
```

### CORS Configuration / CORS 配置

```bash
# Restrict to specific origins
CORS_ORIGINS=https://your-domain.com,https://app.your-domain.com

# Enable credentials
CORS_ALLOW_CREDENTIALS=true

# Set allowed headers
CORS_ALLOW_HEADERS=Content-Type,Authorization
```

### SSL/TLS Configuration / SSL/TLS 配置

```bash
# Enable HTTPS
ENABLE_HTTPS=true
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem

# Force HTTPS redirect
FORCE_HTTPS_REDIRECT=true
```

## Performance Configuration / 性能配置

### Connection Pooling / 连接池

```bash
# HTTP connection pool size
HTTP_POOL_SIZE=100

# Connection timeout
HTTP_POOL_TIMEOUT=30

# Maximum retries
HTTP_MAX_RETRIES=3
```

### Caching Configuration / 缓存配置

```bash
# Enable response caching
ENABLE_CACHE=true

# Cache timeout in seconds
CACHE_TIMEOUT=300

# Cache size limit
CACHE_MAX_SIZE=1000
```

### Worker Configuration / 工作进程配置

```bash
# Number of worker processes
WORKER_PROCESSES=4

# Worker type (sync, async)
WORKER_TYPE=async

# Worker timeout
WORKER_TIMEOUT=30
```

## Monitoring Configuration / 监控配置

### Metrics Configuration / 指标配置

```bash
# Enable metrics collection
ENABLE_METRICS=true

# Metrics port
METRICS_PORT=9090

# Metrics path
METRICS_PATH=/metrics
```

### Health Check Configuration / 健康检查配置

```bash
# Health check endpoint
HEALTH_CHECK_PATH=/health

# Health check interval
HEALTH_CHECK_INTERVAL=30

# Enable detailed health check
DETAILED_HEALTH_CHECK=true
```

## Configuration Validation / 配置验证

### Validate Configuration / 验证配置

```bash
# Check environment variables
python -c "import os; print('OPENPROJECT_URL:', os.getenv('OPENPROJECT_URL'))"

# Test configuration loading
python -c "from config import settings; print('Settings loaded:', settings.openproject_url)"
```

### Configuration Testing / 配置测试

```bash
# Test OpenProject connection
curl -H "Authorization: Bearer your-api-key" \
  https://your-openproject.com/api/v3/projects

# Test server startup
python app/main.py &
sleep 5
curl http://localhost:8020/health
```

## Troubleshooting / 故障排除

### Common Configuration Issues / 常见配置问题

#### Missing Environment Variables / 缺少环境变量
```bash
# Check if variables are set
echo $OPENPROJECT_URL

# Load environment file
source .env
```

#### Invalid API Key / 无效的 API 密钥
```bash
# Test API key
curl -H "Authorization: Bearer your-api-key" \
  https://your-openproject.com/api/v3/projects
```

#### Port Already in Use / 端口已被占用
```bash
# Find process using port
lsof -i :8020

# Use different port
export PORT=8021
```

## Best Practices / 最佳实践

### Security Best Practices / 安全最佳实践
- Use environment variables for sensitive data
- Rotate API keys regularly
- Restrict CORS origins to specific domains
- Enable HTTPS in production
- Monitor API usage and rate limits

### Performance Best Practices / 性能最佳实践
- Use connection pooling for HTTP requests
- Enable caching for frequently accessed data
- Monitor memory usage and connection counts
- Configure appropriate timeout values
- Use async processing for I/O operations

### Configuration Management Best Practices / 配置管理最佳实践
- Use separate configuration files for different environments
- Version control configuration templates
- Document all configuration options
- Validate configuration before deployment
- Use configuration management tools for large deployments

---

**For more information**, see the [Architecture Overview](../../architecture/OVERVIEW.md).