# FastMCP 解决方案 🚧 (开发中)

这是一个基于 FastMCP 框架实现的 MCP (Model Context Protocol) 解决方案。

> ⚠️ **开发状态**：此解决方案正在开发中，存在已知问题。建议使用 [HTTP 解决方案](../http-solution/) 进行生产部署。

## ⚠️ 已知问题

FastMCP 目前存在版本兼容性问题：
- [Issue #737](https://github.com/modelcontextprotocol/python-sdk/issues/737) - 初始化竞争条件
- [Issue #423](https://github.com/modelcontextprotocol/python-sdk/issues/423) - SSE 服务器初始化问题

**推荐使用 [HTTP 解决方案](../http-solution/) 以避免这些问题。**

## ✨ 特点

- 🚀 基于 FastMCP 2.10.6 框架
- 📡 支持 HTTP 和 SSE 传输
- 🔧 完整的 MCP 协议支持
- 🔗 与 OpenProject API 集成

## 🚀 快速开始

### 1. 安装依赖

```bash
cd fastmcp-solution
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置环境

```bash
cp .env.example .env
# 编辑 .env 文件，设置你的 OpenProject API 密钥
```

### 3. 启动服务

```bash
python src/main.py
```

服务将在 `http://localhost:8010/mcp/` 启动。

## 🧪 测试服务

### 初始化连接

```bash
curl -X POST http://localhost:8010/mcp/ \
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

**注意**：FastMCP 需要 `Accept: application/json, text/event-stream` 头部。

### 使用 FastMCP 客户端

```python
import asyncio
from fastmcp import Client

async def test_mcp_service():
    async with Client("http://localhost:8010") as client:
        # 列出工具
        tools = await client.list_tools()
        print("Available tools:", [tool.name for tool in tools.tools])
        
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
fastmcp-solution/
├── src/
│   ├── main.py              # 主服务器文件
│   ├── adapters/
│   │   └── openproject.py   # OpenProject API 适配器
│   ├── models/
│   │   └── schemas.py       # 数据模型
│   ├── services/            # 业务逻辑服务
│   └── utils/
│       └── http_client.py   # HTTP 客户端工具
├── requirements.txt         # Python 依赖
├── .env.example            # 环境变量示例
├── Dockerfile              # Docker 配置
└── README.md               # 本文档
```

## 🐛 故障排除

### 常见问题

1. **"Received request before initialization was complete"**
   - 这是 FastMCP 的已知问题
   - 建议使用 HTTP 解决方案

2. **SSE 连接问题**
   - 确保请求头包含 `Accept: application/json, text/event-stream`
   - 使用正确的会话 ID

3. **版本兼容性**
   - 当前使用 FastMCP 2.10.6 + MCP 1.12.1
   - 如遇问题，建议切换到 HTTP 解决方案

## 🔄 迁移到 HTTP 解决方案

如果遇到 FastMCP 相关问题，可以轻松迁移到 HTTP 解决方案：

```bash
cd ../http-solution
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp ../fastmcp-solution/.env .env
python src/main.py
```

HTTP 解决方案提供相同的功能，但更加稳定可靠。
