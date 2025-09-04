# Quick Start / 快速开始

This guide provides the fastest way to get started with OpenProject MCP integration.

本指南提供开始使用 OpenProject MCP 集成的最快方法。

## Prerequisites / 先决条件

- Python 3.8+ or Node.js 16+
- OpenProject instance with API access
- API key for authentication

## Choose Your Solution / 选择您的解决方案

### Option 1: FastAPI Solution (Recommended)
```bash
cd solution-fastapi
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e ../mcp-core
```

### Option 2: HTTP Solution (Production)
```bash
cd solution-http
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e ../mcp-core
```

### Option 3: TypeScript Solution (Node.js)
```bash
cd solution-typescript
npm install
```

## Configuration / 配置

Create a `.env` file in your solution directory:

```bash
OPENPROJECT_URL=https://your-openproject.com
OPENPROJECT_API_KEY=your-api-key-here
PORT=8020  # 8010 for HTTP, 8030 for FastMCP, 8040 for TypeScript
LOG_LEVEL=INFO
```

## Start the Service / 启动服务

### FastAPI Solution
```bash
cd solution-fastapi
python app/main.py
```

### HTTP Solution
```bash
cd solution-http
python -m src.main
```

### TypeScript Solution
```bash
cd solution-typescript
npm start
```

## Verify Installation / 验证安装

Open your browser or use curl to test the health endpoint:

```bash
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

## Next Steps / 下一步

1. **Review Architecture**: Read the [architecture overview](../../architecture/OVERVIEW.md)
2. **Configure Integration**: Set up OpenProject connection details
3. **Test MCP Tools**: Verify MCP protocol functionality
4. **Deploy to Production**: Follow the [deployment guide](../../deployment/GUIDE.md)

## Troubleshooting / 故障排除

- **Port Conflicts**: Ensure ports 8010-8040 are available
- **API Connection**: Verify OpenProject URL and API key
- **Dependencies**: Check all required packages are installed

---

**For detailed setup instructions**, see the [Installation Guide](INSTALLATION.md).