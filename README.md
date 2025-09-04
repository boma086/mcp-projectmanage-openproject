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

## 🐳 容器化部署

本项目支持完整的容器化部署，包含 Docker 和 Kubernetes 两种部署方式。

### 快速开始 (Docker Compose)

#### 开发环境
```bash
# 启动所有服务 (HTTP + FastAPI + 基础设施)
docker-compose -f docker-compose.dev.yml up -d

# 查看服务状态
docker-compose -f docker-compose.dev.yml ps

# 查看日志
docker-compose -f docker-compose.dev.yml logs -f
```

#### 生产环境
```bash
# 配置生产环境变量
cp .env.production .env
# 编辑 .env 文件，设置实际的生产配置

# 启动生产服务
docker-compose -f docker-compose.prod.yml up -d
```

### 服务访问 (Docker)

| 服务 | 开发环境端口 | 生产环境端口 | 说明 |
|------|-------------|-------------|------|
| HTTP 解决方案 | 8010 | 8010 | 生产推荐方案 |
| FastAPI 解决方案 | 8020 | 8020 | 开发推荐方案 |
| Nginx 负载均衡 | - | 80 | 生产环境入口 |
| PostgreSQL | 5432 | 5432 | 数据库 |
| Redis | 6379 | 6379 | 缓存 |
| Prometheus | - | 9090 | 监控指标 |
| Grafana | - | 3000 | 监控仪表板 |

### Kubernetes 部署

#### 快速部署
```bash
# 部署到 Kubernetes 集群
./deploy/kubernetes.sh

# 或者手动部署
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmaps.yaml
kubectl apply -f k8s/infrastructure.yaml
kubectl apply -f k8s/http-solution.yaml
kubectl apply -f k8s/fastapi-solution.yaml
kubectl apply -f k8s/monitoring.yaml
```

#### 验证部署
```bash
# 检查 Pod 状态
kubectl get pods -n mcp-openproject

# 检查服务状态
kubectl get svc -n mcp-openproject

# 查看部署进度
kubectl rollout status deployment/http-solution -n mcp-openproject
kubectl rollout status deployment/fastapi-solution -n mcp-openproject
```

### 配置管理

#### 环境变量
项目包含多个环境配置文件：

- `.env` - 主配置文件 (包含所有变量和默认值)
- `.env.development` - 开发环境配置
- `.env.production` - 生产环境配置
- `.env.test` - 测试环境配置

#### 关键配置项
```bash
# OpenProject 配置
OPENPROJECT_URL=https://your-openproject.com
OPENPROJECT_API_KEY=your-api-key-here

# 数据库配置
DATABASE_URL=postgresql://mcpuser:mcppass@postgres:5432/mcpdb

# Redis 配置
REDIS_URL=redis://redis:6379

# 安全配置
SECRET_KEY=your-super-secret-key-here
JWT_SECRET_KEY=your-super-secret-jwt-key-here
```

### 监控和日志

#### 健康检查
所有服务都包含健康检查端点：
- HTTP 解决方案: `http://localhost:8010/health`
- FastAPI 解决方案: `http://localhost:8020/health`

#### 监控指标
- Prometheus: `http://localhost:9090` (生产环境)
- Grafana: `http://localhost:3000` (生产环境)

#### 日志查看
```bash
# Docker Compose 日志
docker-compose -f docker-compose.dev.yml logs -f http-solution
docker-compose -f docker-compose.dev.yml logs -f fastapi-solution

# Kubernetes 日志
kubectl logs -f deployment/http-solution -n mcp-openproject
kubectl logs -f deployment/fastapi-solution -n mcp-openproject
```

### 验证和测试

#### 部署验证
```bash
# 运行完整的部署验证
./scripts/validate-deployment.sh validate

# 仅验证 Docker 配置
./scripts/validate-deployment.sh docker

# 仅验证 Docker Compose
./scripts/validate-deployment.sh compose

# 仅验证 Kubernetes
./scripts/validate-deployment.sh k8s
```

#### 功能测试
```bash
# 测试 HTTP 解决方案
curl -f http://localhost:8010/health

# 测试 FastAPI 解决方案
curl -f http://localhost:8020/health

# 测试 MCP 端点
curl -X POST http://localhost:8010/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "generate_report_from_template", "arguments": {"template_id": "japanese_weekly_report", "project_id": "1"}}}'
```

### 生产环境注意事项

1. **安全配置**
   - 替换所有默认密码和密钥
   - 配置 SSL/TLS 证书
   - 启用防火墙和网络策略

2. **资源规划**
   - 根据负载调整 Pod 副本数
   - 配置适当的资源限制和请求
   - 设置自动扩缩容策略

3. **备份和恢复**
   - 定期备份数据库
   - 配置持久化存储
   - 测试恢复流程

4. **监控告警**
   - 配置 Prometheus 告警规则
   - 设置 Grafana 仪表板
   - 配置日志聚合和分析

> 📖 **详细部署文档**: 查看 [VALIDATION_SUMMARY.md](VALIDATION_SUMMARY.md) 获取完整的验证结果和部署指南。

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
