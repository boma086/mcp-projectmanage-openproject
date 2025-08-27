# FastAPI MCP 解决方案 ✅ (已实现)

这是一个基于 FastAPI 框架实现的 MCP (Model Context Protocol) 解决方案，提供高性能的异步项目管理服务。

> ✅ **开发状态**：此解决方案已完成核心功能实现，包含完整的 MCP 协议支持和 OpenProject 集成。

## ✨ 主要特性

- 🚀 **高性能异步实现**：基于 FastAPI 的现代异步 Python 框架
- 📚 **自动 API 文档**：完整的 OpenAPI/Swagger 文档自动生成
- 🔧 **完整 MCP 协议**：支持工具调用、资源管理、提示生成
- 🔗 **OpenProject 集成**：与 OpenProject API 的完整集成
- 📊 **Team Leader 功能**：报告生成、风险评估、工作负载分析
- 🎨 **模板系统**：灵活的报告模板管理和渲染
- 🛡️ **错误处理**：完善的异常处理和错误响应
- 📈 **健康监控**：内置健康检查和状态监控

## 🚀 快速开始

### 1. 环境准备

```bash
cd solution-fastapi
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
#pip install -e ../mcp-core
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，设置你的 OpenProject 配置
```

### 3. 启动服务

```bash
直接使用 uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 访问服务

- **API 文档**: http://localhost:8000/docs
- **MCP 端点**: http://localhost:8000/mcp
- **健康检查**: http://localhost:8000/health
- **API**: http://localhost:8000/openapi.json

## 🔧 配置说明

### 环境变量

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `OPENPROJECT_URL` | ✅ | - | OpenProject 实例 URL |
| `OPENPROJECT_API_KEY` | ✅ | - | OpenProject API 密钥 |
| `HOST` | ❌ | 0.0.0.0 | 服务器监听地址 |
| `PORT` | ❌ | 8000 | 服务器端口 |
| `DEBUG` | ❌ | false | 调试模式 |
| `LOG_LEVEL` | ❌ | INFO | 日志级别 |
| `CACHE_TTL` | ❌ | 300 | 缓存过期时间（秒） |

### OpenProject 配置
docker compose部署

### MCP 协议调用

```bash
# 调用工具
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "generate_weekly_report",
      "arguments": {
        "project_id": "2",
        "start_date": "2025-08-18",
        "end_date": "2025-08-24"
      }
    }
  }'
```

### REST API 调用

```bash
# 获取项目列表
curl http://localhost:8000/api/v1/projects/

# 生成周报
curl -X POST "http://localhost:8000/api/v1/projects/1/reports/weekly?start_date=2025-01-01&end_date=2025-01-07"

# 检查项目健康度
curl -X POST http://localhost:8000/api/v1/projects/1/health/check
```

