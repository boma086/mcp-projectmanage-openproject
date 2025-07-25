# OpenProject MCP 服务器

> 🎯 为团队领导者提供智能化的项目报告生成工具

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-2024--11--05-green.svg)](https://modelcontextprotocol.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116+-green.svg)](https://fastapi.tiangolo.com)

## ✨ 核心功能

- 📊 **智能报告生成** - 自动生成周报、月报、进度报告
- 🎯 **风险评估** - 实时项目风险识别和评估  
- 👥 **工作负载分析** - 团队成员工作量分析和优化建议
- 🎨 **模板系统** - 支持自定义报告模板，包含专业的日本式商务报告
- 🔌 **MCP 协议** - 标准协议，易于集成到 Claude Desktop、Cursor 等 AI 工具

## 🚀 快速开始

### 1. 启动 OpenProject
```bash
# 使用 Docker 启动 OpenProject
docker-compose up -d

# 访问 OpenProject: http://localhost:8090
# 默认账号: admin / admin
```

### 2. 选择解决方案

#### 方案一：FastAPI（推荐）
```bash
cd solution-fastapi
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e ../mcp-core

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置你的 OpenProject API Key

# 启动服务
python app/main.py
```

#### 方案二：HTTP（简单）
```bash
cd solution-http
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e ../mcp-core
python3 -m src.main
```

### 3. 访问服务

| 服务 | FastAPI 方案 | HTTP 方案 |
|------|-------------|-----------|
| **Web 界面** | http://localhost:8020/web/template_editor.html | http://localhost:8010 |
| **API 文档** | http://localhost:8020/docs | - |
| **MCP 端点** | http://localhost:8020/mcp | http://localhost:8010/mcp |

## 🎨 模板系统

支持多种专业报告模板：

- **日本式週報** - 符合日本商务文化的详细周报
- **日本式月報** - 综合的月度总结报告
- **日本式進捗報告** - 专业的进度状况报告
- **自定义模板** - 通过 Web 界面创建和编辑

## 🔧 集成到 AI 工具

### Claude Desktop
```json
{
  "mcpServers": {
    "openproject": {
      "command": "curl",
      "args": ["-X", "POST", "http://localhost:8020/mcp"]
    }
  }
}
```

### Cursor
在 Cursor 中添加 MCP 服务器配置，指向 `http://localhost:8020/mcp`

## 📚 使用示例

### 生成周报
```bash
curl -X POST http://localhost:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "generate_report_from_template",
      "arguments": {
        "template_id": "japanese_weekly_report",
        "project_id": "1"
      }
    }
  }'
```

### 评估项目风险
```bash
curl -X POST http://localhost:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "assess_project_risks",
      "arguments": {
        "project_id": "1"
      }
    }
  }'
```

## 🔧 配置

### 环境变量
```bash
# OpenProject 配置（必需）
OPENPROJECT_URL=https://your-openproject.com
OPENPROJECT_API_KEY=your-api-key-here

# 服务器配置
HOST=0.0.0.0
PORT=8020

# 日志配置
LOG_LEVEL=INFO
```

### 获取 API Key
1. 登录 OpenProject
2. 进入 "我的账户" → "访问令牌"
3. 创建新的 API 密钥
4. 复制密钥到 `.env` 文件

## 🆘 故障排除

### 常见问题

**Q: 服务启动失败，提示端口被占用**
```bash
# 查找占用端口的进程
lsof -ti:8020 | xargs kill -9
# 重新启动服务
```

**Q: 无法连接到 OpenProject**
- 检查 OpenProject 是否正在运行
- 验证 API Key 是否正确
- 确认网络连接正常

**Q: 模板预览生成失败**
- 检查项目 ID 是否存在
- 确认有访问该项目的权限
- 查看服务器日志获取详细错误信息

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**快速链接**: [API 文档](http://localhost:8020/docs) | [Web 界面](http://localhost:8020/web/template_editor.html) | [项目详情](PROJECT_SUMMARY.md)
