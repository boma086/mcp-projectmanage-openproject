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
cd fastapi-solution
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，设置你的 OpenProject 配置
```

### 3. 启动服务

```bash
# 使用启动脚本（推荐）
python start.py

# 或直接使用 uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 访问服务

- **API 文档**: http://localhost:8000/docs
- **MCP 端点**: http://localhost:8000/mcp
- **健康检查**: http://localhost:8000/health
- **API v1**: http://localhost:8000/api/v1

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

1. 登录你的 OpenProject 实例
2. 进入 **管理** → **API 和 Webhooks**
3. 创建新的 API 密钥
4. 将 URL 和 API 密钥配置到环境变量中

## 🐳 Docker 部署

### 使用 Docker Compose（推荐）

```bash
# 复制环境变量文件
cp .env.example .env
# 编辑 .env 文件设置你的配置

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 使用 Docker

```bash
# 构建镜像
docker build -t fastapi-mcp .

# 运行容器
docker run -d \
  --name fastapi-mcp \
  -p 8000:8000 \
  -e OPENPROJECT_URL=https://your-openproject.com \
  -e OPENPROJECT_API_KEY=your-api-key \
  fastapi-mcp
```

## 🧪 测试

```bash
# 安装测试依赖
pip install pytest pytest-asyncio httpx

# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_main.py

# 运行测试并显示覆盖率
pytest --cov=app tests/
```

## 📚 API 使用示例

### MCP 协议调用

```bash
# 获取工具列表
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'

# 调用工具
curl -X POST http://localhost:8000/mcp \
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

### REST API 调用

```bash
# 获取项目列表
curl http://localhost:8000/api/v1/projects/

# 生成周报
curl -X POST "http://localhost:8000/api/v1/projects/1/reports/weekly?start_date=2025-01-01&end_date=2025-01-07"

# 检查项目健康度
curl -X POST http://localhost:8000/api/v1/projects/1/health/check
```

## 🔍 监控和维护

### 健康检查

```bash
# 检查服务健康状态
curl http://localhost:8000/health

# 获取系统指标
curl http://localhost:8000/metrics
```

### 缓存管理

```bash
# 清空缓存
curl -X POST http://localhost:8000/cache/clear

# 清理过期缓存
curl -X POST http://localhost:8000/cache/cleanup
```

## 🛠️ 开发指南

### 项目结构

```
fastapi-solution/
├── app/
│   ├── api/v1/          # REST API 路由
│   ├── core/            # 核心模块（配置、MCP处理器等）
│   ├── models/          # 数据模型
│   ├── services/        # 业务逻辑服务
│   └── utils/           # 工具函数
├── tests/               # 测试文件
├── templates/           # 报告模板
├── requirements.txt     # Python 依赖
├── Dockerfile          # Docker 镜像配置
├── docker-compose.yml  # Docker Compose 配置
└── start.py            # 启动脚本
```

### 添加新功能

1. **添加新工具**：在 `app/services/tool_service.py` 中注册新工具
2. **添加新服务**：在 `app/services/` 目录下创建新服务
3. **添加新API**：在 `app/api/v1/` 目录下创建新路由
4. **添加新模板**：在 `templates/` 目录下创建 YAML 模板文件

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](../LICENSE) 文件了解详情。

## 🆘 故障排除

### 常见问题

**Q: 服务启动失败，提示 "MCP handler not initialized"**
A: 检查 OpenProject URL 和 API 密钥是否正确配置，确保网络连接正常。

**Q: API 调用返回 503 错误**
A: 检查服务健康状态 (`/health`)，确认所有依赖服务正常运行。

**Q: 模板渲染失败**
A: 检查模板文件格式是否正确，确保所有必需的变量都已提供。

### 日志查看

```bash
# Docker Compose 环境
docker-compose logs -f fastapi-mcp

# Docker 环境
docker logs -f fastapi-mcp

# 本地开发
# 日志会直接输出到控制台
```

## 📞 支持

如果你遇到问题或有建议，请：

1. 查看 [Issues](../../issues) 页面
2. 创建新的 Issue 描述问题
3. 参考项目文档和示例代码

## 📁 计划的项目结构

```
fastapi-solution/
├── app/
│   ├── main.py              # FastAPI 应用入口
│   ├── api/
│   │   └── v1/              # API 路由
│   ├── core/
│   │   ├── config.py        # 配置管理
│   │   └── security.py      # 安全相关
│   ├── models/
│   │   └── schemas.py       # Pydantic 模型
│   ├── services/
│   │   └── openproject.py   # OpenProject 服务
│   └── utils/
│       └── mcp.py           # MCP 协议工具
├── requirements.txt         # Python 依赖
├── Dockerfile              # Docker 配置
└── README.md               # 本文档
```

## 🔄 迁移建议

在此解决方案完成之前，请使用已测试通过的 HTTP 解决方案：

```bash
cd ../http-solution
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 文件设置 API 密钥
python src/main.py
```

## 📝 开发计划

- [ ] 基础 FastAPI 应用结构
- [ ] MCP 协议实现
- [ ] OpenProject API 集成
- [ ] 自动文档生成
- [ ] 测试套件
- [ ] Docker 支持
- [ ] 监控和日志

## 🤝 贡献

如果你想帮助实现这个解决方案，欢迎提交 PR！
