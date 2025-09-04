# Installation Guide / 安装指南

This guide provides detailed installation instructions for all OpenProject MCP integration solutions.

本指南提供所有 OpenProject MCP 集成解决方案的详细安装说明。

## System Requirements / 系统要求

### Common Requirements / 通用要求
- **Operating System**: Linux, macOS, or Windows
- **Memory**: Minimum 2GB RAM, 4GB recommended
- **Storage**: Minimum 1GB free space
- **Network**: Internet connection for package downloads

### Python Solutions (HTTP, FastAPI, FastMCP)
- **Python**: 3.8 or higher
- **pip**: Package manager
- **virtualenv**: Recommended for dependency isolation

### TypeScript Solution
- **Node.js**: 16.0 or higher
- **npm**: Package manager

## OpenProject Prerequisites / OpenProject 先决条件

1. **OpenProject Instance**: Version 12.0 or higher
2. **API Access**: Enabled API access in OpenProject
3. **API Key**: Generate API key from user profile
4. **Permissions**: Appropriate project and work package permissions

## Solution Installation / 解决方案安装

### FastAPI Solution (Recommended for Development)

```bash
# Navigate to solution directory
cd solution-fastapi

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install core library in development mode
pip install -e ../mcp-core

# Verify installation
python -c "import mcp_core; print('MCP Core installed successfully')"
```

### HTTP Solution (Production-Ready)

```bash
# Navigate to solution directory
cd solution-http

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install core library
pip install -e ../mcp-core

# Verify installation
python -c "import mcp_core; print('MCP Core installed successfully')"
```

### FastMCP Solution (Experimental)

```bash
# Navigate to solution directory
cd solution-fastmcp

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install core library
pip install -e ../mcp-core

# Verify installation
python -c "import mcp_core; print('MCP Core installed successfully')"
```

### TypeScript Solution (Node.js)

```bash
# Navigate to solution directory
cd solution-typescript

# Install dependencies
npm install

# Verify installation
npm run build

# Test installation
npm test
```

## Configuration / 配置

### Environment Variables / 环境变量

Create a `.env` file in your solution directory:

```bash
# OpenProject Configuration
OPENPROJECT_URL=https://your-openproject.com
OPENPROJECT_API_KEY=your-api-key-here

# Server Configuration
PORT=8020  # HTTP: 8010, FastAPI: 8020, FastMCP: 8030, TypeScript: 8040
HOST=0.0.0.0

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json

# Security Configuration
CORS_ORIGINS=*
API_RATE_LIMIT=100

# Performance Configuration
MAX_CONNECTIONS=100
TIME_SECONDS=30
```

### Configuration File / 配置文件

Some solutions support additional configuration files. Refer to solution-specific documentation for details.

## Verification / 验证

### Health Check / 健康检查

```bash
# Test the health endpoint
curl http://localhost:8020/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-09-04T10:30:00Z",
  "version": "1.0.0"
}
```

### MCP Protocol Test / MCP 协议测试

```bash
# Test MCP protocol endpoint
curl -X POST http://localhost:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": "test-123"
  }'
```

## Development Setup / 开发设置

### IDE Configuration / IDE 配置

#### VS Code
Install the following extensions:
- Python (for Python solutions)
- ESLint and Prettier (for TypeScript solution)
- Docker (if using containerization)

#### PyCharm
- Configure Python interpreter for virtual environment
- Set up run configurations for each solution

### Database Setup / 数据库设置

The solutions use OpenProject's API and don't require separate database setup. Ensure your OpenProject instance is properly configured.

## Troubleshooting / 故障排除

### Common Issues / 常见问题

#### Port Already in Use / 端口已被占用
```bash
# Find process using the port
lsof -i :8020  # Linux/macOS
netstat -ano | findstr :8020  # Windows

# Kill the process or use different port
export PORT=8021
```

#### API Connection Issues / API 连接问题
```bash
# Test OpenProject API connection
curl -H "Authorization: Bearer your-api-key" \
  https://your-openproject.com/api/v3/projects
```

#### Missing Dependencies / 缺少依赖
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Check for conflicts
pip check
```

### Log Files / 日志文件

Check the following locations for log files:
- Console output (default)
- Configured log directory
- Application logs in solution directory

## Production Deployment / 生产部署

For production deployment, refer to the [Deployment Guide](../../deployment/GUIDE.md) for detailed instructions on:
- Containerization with Docker
- Kubernetes deployment
- Cloud platform deployment
- Security configuration

## Next Steps / 下一步

1. **Configuration**: Complete environment setup
2. **Architecture Review**: Understand the system architecture
3. **Testing**: Verify all functionality works
4. **Deployment**: Deploy to your preferred environment

---

**For more information**, see the [Configuration Guide](CONFIGURATION.md).