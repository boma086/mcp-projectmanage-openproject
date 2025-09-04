# FastMCP 解决方案 🚀 (包含完整监控)

这是一个基于 FastMCP 框架实现的 MCP (Model Context Protocol) 解决方案，具有完整的监控和可观测性功能。

## ✨ 特点

- 🚀 基于 FastMCP 2.10.6 框架
- 📊 **Prometheus 指标收集** - 完整的应用程序监控
- 📝 **结构化日志** - 带有相关性 ID 的 JSON 日志
- ❤️ **健康检查** - 存活、就绪和深度健康检查
- 🔧 完整的 MCP 协议支持
- 📡 支持 HTTP 和 SSE 传输
- 🔗 与 OpenProject API 集成
- 📈 **实时监控** - 内置监控端点
- 🎯 **性能优化** - 异步处理和连接池

## 🏗️ 监控架构

### 指标收集 (Prometheus)
- **HTTP 请求指标**: `http_requests_total`, `http_request_duration_seconds`
- **MCP 操作指标**: `mcp_operations_total`, `mcp_operation_duration_seconds`
- **MCP 协议指标**: `mcp_protocol_operations_total`, `mcp_sessions_total`
- **错误指标**: `http_errors_total`, `mcp_errors_total`
- **外部服务指标**: `openproject_requests_total`
- **健康指标**: `health_check_status`, `openproject_connection_status`

### 结构化日志
```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "level": "INFO",
  "correlation_id": "corr_abc123def456",
  "service": "fastmcp-solution",
  "method": "POST",
  "path": "/mcp",
  "duration_ms": 45.2,
  "status_code": 200,
  "message": "Request processed successfully"
}
```

### 健康检查
- `/health/live` - 基本存活检查
- `/health/ready` - 就绪检查
- `/health/deep` - 深度健康检查（依赖项、资源）
- `/metrics` - Prometheus 指标端点
- `/info` - 服务信息端点

## 🚀 快速开始

### 1. 安装依赖

```bash
cd solution-fastmcp
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置环境

```bash
cp .env.example .env
# 编辑 .env 文件，设置你的 OpenProject API 密钥
```

**必需的环境变量:**
```bash
OPENPROJECT_URL=https://your-openproject.com
OPENPROJECT_API_KEY=your-api-key-here
PORT=8030
```

### 3. 启动服务

```bash
python src/main.py
```

服务将在 `http://localhost:8030` 启动。

## 📊 监控端点

### 健康检查
```bash
# 存活检查
curl http://localhost:8030/health/live

# 就绪检查
curl http://localhost:8030/health/ready

# 深度健康检查
curl http://localhost:8030/health/deep
```

### 指标收集
```bash
# Prometheus 指标
curl http://localhost:8030/metrics

# 服务信息
curl http://localhost:8030/info
```

### 示例健康检查响应
```json
{
  "status": "healthy",
  "timestamp": 1640995200.0,
  "service": "fastmcp-solution",
  "total_checks": 6,
  "healthy_checks": 6,
  "degraded_checks": 0,
  "unhealthy_checks": 0,
  "checks": [
    {
      "name": "service_health",
      "status": "healthy",
      "duration_ms": 2.5,
      "message": "Service monitoring is active"
    },
    {
      "name": "openproject_connection",
      "status": "healthy",
      "duration_ms": 150.2,
      "message": "OpenProject API connection successful",
      "details": {
        "response_time_ms": 150.2,
        "status_code": 200,
        "projects_count": 25
      }
    }
  ]
}
```

## 🧪 测试服务

### 初始化连接
```bash
curl -X POST http://localhost:8030/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {"tools": {}},
      "clientInfo": {"name": "test-client", "version": "1.0.0"}
    }
  }'
```

### 使用 FastMCP 客户端
```python
import asyncio
from fastmcp import Client

async def test_mcp_service():
    async with Client("http://localhost:8030") as client:
        # 列出工具
        tools = await client.list_tools()
        print("Available tools:", [tool.name for tool in tools])
        
        # 调用工具
        result = await client.call_tool("get_projects", {})
        print("Projects:", result)

if __name__ == "__main__":
    asyncio.run(test_mcp_service())
```

## 🔧 支持的工具

| 工具名称 | 描述 | 参数 |
|---------|------|------|
| `get_projects` | 获取所有项目列表 | 无 |
| `get_project` | 获取特定项目详情 | `project_id` |
| `get_work_packages` | 获取工作包列表 | `project_id` (可选) |
| `create_work_package` | 创建新工作包 | `project_id`, `subject`, `description`, `work_package_type` |
| `update_work_package` | 更新工作包 | `work_package_id`, `subject`, `description`, `status` |
| `generate_project_report` | 生成项目报告 | `project_id` |

## 📁 项目结构

```
solution-fastmcp/
├── src/
│   ├── main.py                  # 主服务器文件
│   ├── monitoring/              # 监控包
│   │   ├── __init__.py
│   │   ├── metrics.py          # Prometheus 指标
│   │   ├── health.py           # 健康检查
│   │   └── endpoints.py        # 监控端点
│   ├── adapters/
│   │   └── openproject_adapter.py  # OpenProject API 适配器
│   ├── config.py               # 配置管理
│   └── utils/                  # 工具函数
├── requirements.txt             # Python 依赖
├── .env.example                # 环境变量示例
├── Dockerfile                  # Docker 配置
├── test_monitoring.py          # 监控测试
└── README.md                   # 本文档
```

## 🔧 配置选项

### 监控配置
```bash
# 启用/禁用监控
ENABLE_METRICS=true
STRUCTURED_LOGGING=true
CORRELATION_IDS=true

# 健康检查配置
HEALTH_CHECK_ENABLED=true
HEALTH_CHECK_INTERVAL=30
HEALTH_CHECK_TIMEOUT=10

# 日志配置
LOG_LEVEL=INFO
```

### 性能配置
```bash
# 服务器配置
MAX_CONCURRENT_REQUESTS=100
REQUEST_TIMEOUT=30

# MCP 配置
MCP_SESSION_TIMEOUT=300
MCP_PROTOCOL_VERSION=2024-11-05

# SSE 配置
SSE_ENABLED=true
SSE_PORT=8031
```

## 🐳 Docker 部署

```bash
# 构建镜像
docker build -t fastmcp-solution .

# 运行容器
docker run -p 8030:8030 \
  -e OPENPROJECT_URL=https://your-openproject.com \
  -e OPENPROJECT_API_KEY=your-api-key \
  fastmcp-solution
```

## 📈 Prometheus 配置

在 `prometheus.yml` 中添加以下配置：

```yaml
scrape_configs:
  - job_name: 'fastmcp-solution'
    static_configs:
      - targets: ['localhost:8030']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

## 🎨 Grafana 仪表板

使用以下指标创建仪表板：

- **HTTP 请求率**: `rate(http_requests_total[5m])`
- **请求延迟**: `histogram_quantile(0.95, http_request_duration_seconds_bucket)`
- **错误率**: `rate(http_errors_total[5m])`
- **MCP 操作延迟**: `histogram_quantile(0.95, mcp_operation_duration_seconds_bucket)`
- **OpenProject 连接状态**: `openproject_connection_status`

## 🧪 运行测试

```bash
# 运行监控测试
python test_monitoring.py

# 运行 pytest
pytest test_monitoring.py -v
```

## 🐛 故障排除

### 常见问题

1. **"Connection refused"**
   - 检查服务是否正在运行
   - 验证端口配置 (默认: 8030)

2. **OpenProject API 认证失败**
   - 验证 API 密钥是否正确
   - 检查 OpenProject URL 是否正确

3. **健康检查失败**
   - 检查 OpenProject 连接
   - 验证环境变量配置
   - 查看日志文件获取详细信息

4. **指标收集失败**
   - 验证 `ENABLE_METRICS=true`
   - 检查 Prometheus 客户端库是否正确安装

### 日志查看
```bash
# 查看应用日志
tail -f logs/app.log

# 使用 journalctl (systemd)
journalctl -u fastmcp-solution -f
```

## 🔒 安全考虑

- **API 密钥安全**: 使用环境变量存储敏感信息
- **监控端点**: 在生产环境中考虑添加认证
- **日志安全**: 确保日志不包含敏感信息
- **网络安全**: 使用防火墙规则限制访问

## 🔄 迁移指南

### 从 HTTP 解决方案迁移
1. 复制 `.env` 配置文件
2. 更新端口从 8010 到 8030
3. 使用 FastMCP 客户端库替代直接 HTTP 调用
4. 更新监控端点路径

## 📝 许可证

本项目采用 MIT 许可证。详见 [LICENSE](../LICENSE) 文件。
