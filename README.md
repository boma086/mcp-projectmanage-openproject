# MCP OpenProject 集成服务

这个项目提供了多种 MCP（Model Context Protocol）服务实现，用于连接 AI 网站与 OpenProject 项目管理工具，实现项目数据的自动化获取和报告生成。

## 🚀 功能特性

- ✅ 获取 OpenProject 项目列表
- ✅ 获取项目详细信息
- ✅ 获取工作包（Work Packages）数据
- ✅ 生成项目报告
- ✅ 支持多种实现方案
- ✅ 完整的 MCP 协议支持

## 📁 项目结构

```
mcp-projectmanage-openproject/
├── docker-compose.yml          # OpenProject Docker 配置
├── fastmcp-solution/           # FastMCP 实现方案
├── fastapi-solution/           # FastAPI 实现方案
├── http-solution/              # 原生 HTTP 实现方案 (推荐)
├── typescript-solution/        # TypeScript 实现方案
├── tests/                      # 测试文件和示例
└── README.md
```

## 🛠️ 快速开始

### 1. 启动 OpenProject

```bash
docker-compose up -d
```

访问 http://localhost:8090 设置 OpenProject 并获取 API 密钥。

> 💡 **注意**：此 Docker 配置支持 iframe 嵌入，适合集成到 AI 网站中。

### 2. 选择实现方案

#### 🌟 HTTP 解决方案（推荐 - 已测试通过）

最稳定可靠的实现，避免了版本兼容性问题：

```bash
cd http-solution
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置 OPENPROJECT_API_KEY

# 启动服务
python src/main.py
```

#### FastMCP 方案（开发中）

> ⚠️ 存在版本兼容性问题，正在解决中

```bash
cd fastmcp-solution
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置 OPENPROJECT_API_KEY

# 启动服务
python src/main.py
```

#### FastAPI 方案（计划中）

> 📋 尚未实现，欢迎贡献

```bash
cd fastapi-solution
# 待实现
```

#### TypeScript 方案（计划中）

> 📋 尚未实现，欢迎贡献

```bash
cd typescript-solution
# 待实现
```

## 🧪 测试服务

### HTTP 方案测试

```bash
# 初始化连接
curl -X POST http://localhost:8010/ \
  -H "Content-Type: application/json" \
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

# 获取项目列表
curl -X POST http://localhost:8010/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "get_projects",
      "arguments": {}
    }
  }'
```

### FastMCP 方案测试

```bash
# 初始化连接
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

## 🔧 配置说明

每个解决方案都需要配置环境变量：

```env
# OpenProject 配置
OPENPROJECT_URL=http://localhost:8090
OPENPROJECT_API_KEY=your_api_key_here

# 应用配置
PORT=8010
```

## 🐳 Docker 配置说明

本项目的 Docker 配置基于生产环境需求，支持：

- ✅ **iframe 嵌入支持** - 可以嵌入到 AI 网站中
- ✅ **CORS 配置** - 支持跨域请求
- ✅ **API 认证** - 支持查询参数认证
- ✅ **Nginx 代理** - 提供反向代理和负载均衡
- ✅ **数据持久化** - 数据存储在 `./data` 目录

### 端口说明

- **8090**: OpenProject Web 界面（通过 Nginx 代理）
- **内部**: OpenProject 容器内部端口 80

### 数据目录

```
data/
├── pgdata/     # PostgreSQL 数据
└── assets/     # OpenProject 资源文件
```

## 📊 支持的工具

所有实现方案都支持以下 MCP 工具：

- `get_projects` - 获取所有项目列表
- `get_project` - 获取特定项目详情
- `get_work_packages` - 获取工作包列表
- `generate_project_report` - 生成项目报告

## ⚠️ 已知问题

### FastMCP 版本兼容性问题

FastMCP 存在已知的版本兼容性问题：
- [Issue #737](https://github.com/modelcontextprotocol/python-sdk/issues/737)
- [Issue #423](https://github.com/modelcontextprotocol/python-sdk/issues/423)

**解决方案**：推荐使用 HTTP 解决方案，它避免了这些兼容性问题。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License