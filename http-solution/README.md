# HTTP MCP 解决方案 🌟 (推荐 - 已测试通过)

这是一个使用原生 HTTP 服务器实现的 MCP (Model Context Protocol) 解决方案，避免了 FastMCP 的版本兼容性问题。

> ✅ **测试状态**：此解决方案已完全测试通过，可以正常使用。其他解决方案正在开发中。

## ✨ 特点

- ✅ **稳定可靠** - 避免版本兼容性问题
- ✅ **简单实现** - 原生 HTTP 服务器
- ✅ **完整协议** - 完整的 MCP 协议支持
- ✅ **OpenProject 集成** - 与 OpenProject API 无缝集成
- ✅ **易于部署** - 无复杂依赖

## 🚀 快速开始

### 1. 安装依赖

```bash
cd http-solution
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

服务将在 `http://localhost:8010` 启动。

## 🧪 测试服务

### 初始化连接

```bash
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
```

### 获取项目列表

```bash
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

## 🔧 支持的工具

| 工具名称 | 描述 | 参数 |
|---------|------|------|
| `get_projects` | 获取所有项目列表 | 无 |
| `get_project` | 获取特定项目详情 | `project_id` |
| `get_work_packages` | 获取工作包列表 | `project_id` (可选) |
| `generate_project_report` | 生成项目报告 | `project_id` |

## 📁 项目结构

```
http-solution/
├── src/
│   ├── main.py              # 主服务器文件
│   ├── adapters/
│   │   └── openproject.py   # OpenProject API 适配器
│   ├── models/
│   │   └── schemas.py       # 数据模型
│   └── utils/
│       └── http_client.py   # HTTP 客户端工具
├── requirements.txt         # Python 依赖
├── .env.example            # 环境变量示例
└── README.md               # 本文档
```
