# VS Code 调试方法

本项目已提供统一的 VS Code 调试配置，所有开发者可直接在 VS Code 中点击“运行和调试”按钮进行断点调试。

调试配置文件：`.vscode/launch.json`

主要内容如下：
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI Debug",
      "type": "python",
      "request": "launch",
      "module": "app.main",
      "cwd": "${workspaceFolder}/solution-fastapi",
      "console": "integratedTerminal"
    }
  ]
}
```

调试前请确保：

1. 已在 `solution-fastapi` 目录下创建并激活虚拟环境：
   ```sh
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. 依赖已安装，且 `mcp_core` 作为本地包被正确识别。
3. 直接点击 VS Code 左侧“运行和调试”即可，无需手动修改代码或配置。

如需自定义调试配置，请参考 `.vscode/launch.json`。
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

### 📋 解决方案选择指南

| 解决方案 | 稳定性 | 推荐场景 | 端口 |
|----------|--------|----------|------|
| **HTTP 方案** | ✅ 生产稳定 | 生产环境部署 | 8010 |
| **FastAPI 方案** | ✅ 功能完整 | 开发测试使用 | 8020 |
| **FastMCP 方案** | ⚠️ 实验性 | 技术评估测试 | 8010 |

**生产环境推荐使用 HTTP 解决方案**

### 1. 启动 OpenProject (可选)
```bash
# 使用 Docker 启动 OpenProject (如果还没有 OpenProject 实例)
docker-compose up -d

# 访问 OpenProject: http://localhost:8090
# 默认账号: admin / admin
```

### 2. 选择并启动解决方案

#### 🎯 方案一：HTTP 解决方案 (推荐生产使用)
```bash
cd solution-http
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e ../mcp-core

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置 OpenProject URL 和 API Key

# 启动服务
python3 -m src.main
```

#### 🚀 方案二：FastAPI 解决方案 (推荐开发使用)
```bash
cd solution-fastapi
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e ../mcp-core

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置 OpenProject URL 和 API Key

# 启动服务
python app/main.py
```

> 💡 **详细启动说明**: 查看 [服务启动操作手册](SERVICE_STARTUP_MANUAL.md)

### 3. 访问服务

#### HTTP 解决方案 (端口 8010)
- 🌐 **Web 界面**: http://localhost:8010/web/template_editor.html
- 🔌 **MCP 端点**: http://localhost:8010/mcp
- ❤️ **健康检查**: http://localhost:8010/health
- 📋 **服务信息**: http://localhost:8010/

#### FastAPI 解决方案 (端口 8020)  
- 🌐 **Web 界面**: http://localhost:8020/web/template_editor.html
- 🔌 **MCP 端点**: http://localhost:8020/mcp
- 📖 **API 文档**: http://localhost:8020/docs
- ❤️ **健康检查**: http://localhost:8020/health
- 📋 **服务信息**: http://localhost:8020/

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

### 生成周报 (使用 HTTP 解决方案)
```bash
curl -X POST http://localhost:8010/mcp \
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
curl -X POST http://localhost:8010/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "assess_project_risks",
      "arguments": {
        "project_id": "1"
      }
    }
  }'
```

> 📖 **更多使用示例**: 查看 [服务启动操作手册](SERVICE_STARTUP_MANUAL.md#mcp-协议使用示例)

## 🔧 配置

### 环境变量
```bash
# OpenProject 配置（必需）
OPENPROJECT_URL=https://your-openproject.com
OPENPROJECT_API_KEY=your-api-key-here

# 服务器配置 (HTTP 解决方案)
HOST=0.0.0.0
PORT=8010
LOG_LEVEL=INFO

# 服务器配置 (FastAPI 解决方案)  
PORT=8020  # 注意端口不同
```

> 🔧 **详细配置说明**: 查看 [服务启动操作手册](SERVICE_STARTUP_MANUAL.md#步骤-4-配置环境变量)

### 获取 API Key
1. 登录 OpenProject
2. 进入 "我的账户" → "访问令牌"
3. 创建新的 API 密钥
4. 复制密钥到 `.env` 文件

## 🆘 故障排除

### 常见问题

**Q: 服务启动失败，提示端口被占用**
```bash
# 查找占用端口的进程并终止
lsof -ti:8010 | xargs kill -9  # HTTP 解决方案端口
lsof -ti:8020 | xargs kill -9  # FastAPI 解决方案端口

# 或者修改配置使用其他端口
# 在 .env 文件中修改 PORT 设置
```

**Q: 无法连接到 OpenProject**
- 检查 OpenProject 是否正在运行
- 验证 API Key 是否正确
- 确认网络连接正常
- 查看服务器日志获取详细错误信息

**Q: 模板预览生成失败**
- 检查项目 ID 是否存在
- 确认有访问该项目的权限
- 查看服务器日志获取详细错误信息

> 🔧 **更多故障排除**: 查看 [服务启动操作手册](SERVICE_STARTUP_MANUAL.md#故障排除)

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📖 扩展文档

查看 [docs/](docs/) 目录获取详细文档：

- [🚀 服务启动操作手册](docs/SERVICE_STARTUP_MANUAL.md) - 详细的安装、配置和使用指南
- [🏗️ 架构优化计划](docs/OPTIMIZATION_PLAN.md) - 项目架构优化和实施路线图
- [📚 文档索引](docs/DOCUMENTATION_INDEX.md) - 所有文档的分类和导航指南
- [🔌 FastAPI 集成示例](docs/FASTAPI_INTEGRATION_SAMPLE.md) - 如何集成到其他应用

**服务链接**: 
- HTTP 解决方案: http://localhost:8010
- FastAPI 解决方案: http://localhost:8020/docs
- Web 模板编辑器: http://localhost:8010/web/template_editor.html
