# OpenProject MCP 服务器启动操作手册

## 🚀 快速开始指南

### 前置条件

1. **Python 3.11+** - 确保系统已安装 Python 3.11 或更高版本
2. **OpenProject 实例** - 可访问的 OpenProject 服务器
3. **API 密钥** - OpenProject 的有效 API 访问令牌

### 环境准备

```bash
# 克隆项目（如果尚未克隆）
git clone <repository-url>
cd mcp-projectmanage-openproject

# 检查 Python 版本
python3 --version  # 应该显示 Python 3.11+
```

## 📋 解决方案选择指南

### 推荐方案对比

| 特性 | HTTP 解决方案 | FastAPI 解决方案 | FastMCP 解决方案 |
|------|---------------|------------------|------------------|
| 稳定性 | ✅ **推荐生产** | ✅ 稳定 | ⚠️ 实验性 |
| 性能 | 中等 | 高 | 高 |
| 功能完整性 | 完整 | 完整 | 部分 |
| 部署复杂度 | 低 | 中等 | 中等 |
| 推荐场景 | 生产环境 | 开发测试 | 实验用途 |

**生产推荐**: HTTP 解决方案  
**开发推荐**: FastAPI 解决方案  
**避免使用**: FastMCP 解决方案（存在已知问题）

## 🔧 HTTP 解决方案启动指南

### 步骤 1: 进入项目目录

```bash
cd solution-http
```

### 步骤 2: 创建虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 步骤 3: 安装依赖

```bash
# 安装解决方案依赖
pip install -r requirements.txt

# 安装核心库（从上级目录）
pip install -e ../mcp-core
```

### 步骤 4: 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，设置你的配置
# 使用文本编辑器编辑 .env 文件
```

**必需的配置项**:
```env
# OpenProject 配置（必需）
OPENPROJECT_URL=https://your-openproject-instance.com
OPENPROJECT_API_KEY=your-api-key-here

# 服务器配置（可选，有默认值）
HOST=0.0.0.0
PORT=8010
LOG_LEVEL=INFO
```

### 步骤 5: 获取 OpenProject API 密钥

1. 登录 OpenProject 管理界面
2. 进入 "我的账户" → "访问令牌"
3. 点击 "生成新的访问令牌"
4. 复制生成的 API 密钥到 `.env` 文件

### 步骤 6: 启动服务器

```bash
# 启动 HTTP MCP 服务器
python3 -m src.main
```

**预期输出**:
```
启动 HTTP MCP 服务器，地址: 0.0.0.0:8010
服务地址:
  - 主页: http://localhost:8010/
  - 健康检查: http://localhost:8010/health
  - MCP 端点: http://localhost:8010/mcp
  - Web 界面: http://localhost:8010/web/template_editor.html
```

### 步骤 7: 验证服务状态

```bash
# 检查健康状态
curl http://localhost:8010/health

# 预期响应:
{
  "status": "healthy",
  "services": {
    "openproject": "connected",
    "mcp_handler": "ready"
  }
}
```

## 🚀 FastAPI 解决方案启动指南

### 步骤 1: 进入项目目录

```bash
cd solution-fastapi
```

### 步骤 2: 创建虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

### 步骤 3: 安装依赖

```bash
# 安装解决方案依赖
pip install -r requirements.txt

# 安装核心库
pip install -e ../mcp-core
```

### 步骤 4: 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件
# 必需的配置项与 HTTP 解决方案相同
```

### 步骤 5: 启动服务器

```bash
# 启动 FastAPI 服务器
python app/main.py
```

**预期输出**:
```
启动 FastAPI MCP 服务器，端口: 8020
服务地址:
  - API 文档: http://localhost:8020/docs
  - 健康检查: http://localhost:8020/health
  - MCP 端点: http://localhost:8020/mcp
  - Web 界面: http://localhost:8020/web/template_editor.html
```

### 步骤 6: 访问 API 文档

在浏览器中打开: `http://localhost:8020/docs`

## 🌐 服务访问端点

### HTTP 解决方案 (端口 8010)

| 端点 | 描述 | 用途 |
|------|------|------|
| `http://localhost:8010/` | 服务信息 | 查看服务器状态 |
| `http://localhost:8010/health` | 健康检查 | 监控服务健康状态 |
| `http://localhost:8010/mcp` | MCP 协议端点 | AI 工具集成 |
| `http://localhost:8010/web/template_editor.html` | Web 模板编辑器 | 可视化模板管理 |

### FastAPI 解决方案 (端口 8020)

| 端点 | 描述 | 用途 |
|------|------|------|
| `http://localhost:8020/docs` | API 文档 | 接口文档和测试 |
| `http://localhost:8020/health` | 健康检查 | 监控服务健康状态 |
| `http://localhost:8020/mcp` | MCP 协议端点 | AI 工具集成 |
| `http://localhost:8020/web/template_editor.html` | Web 模板编辑器 | 可视化模板管理 |
| `http://localhost:8020/projects` | 项目列表 API | 获取所有项目 |
| `http://localhost:8020/projects/{id}` | 项目详情 API | 获取特定项目 |

## 🎯 MCP 协议使用示例

### 初始化连接

```bash
curl -X POST http://localhost:8010/mcp \
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

### 生成周报

```bash
curl -X POST http://localhost:8010/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
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
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "assess_project_risks",
      "arguments": {
        "project_id": "1"
      }
    }
  }'
```

## 🎨 Web 模板编辑器使用

### 访问编辑器

在浏览器中打开: `http://localhost:8010/web/template_editor.html`

### 功能说明

1. **模板选择** - 左侧选择预设模板
2. **模板编辑** - 修改模板名称、描述、标题格式
3. **预览测试** - 输入项目ID，生成预览
4. **报告下载** - 下载生成的 Markdown 报告
5. **模板保存** - 保存自定义模板

### 自定义数据示例

```json
{
  "team_morale": "良好",
  "collaboration_efficiency": "高",
  "support_needed": "需要更多测试资源",
  "target_completion_rate": 85,
  "planned_new_work_packages": 3
}
```

## 🔧 故障排除

### 常见问题及解决方案

#### 问题 1: 端口被占用
```bash
# 查找占用端口的进程
lsof -ti:8010 | xargs kill -9

# 或者使用其他端口
# 修改 .env 文件中的 PORT 设置
PORT=8011
```

#### 问题 2: 无法连接到 OpenProject
- 检查 OpenProject URL 是否正确
- 验证 API 密钥是否有效
- 确认网络连接正常
- 查看服务器日志获取详细错误信息

#### 问题 3: 模板预览生成失败
- 检查项目 ID 是否存在
- 确认有访问该项目的权限
- 查看服务器日志获取详细错误信息

#### 问题 4: 依赖安装失败
```bash
# 更新 pip
pip install --upgrade pip

# 清除缓存重试
pip cache purge
pip install -r requirements.txt
```

### 日志查看

服务器运行时会在终端显示详细日志，包含：
- 请求处理信息
- 错误和异常详情
- OpenProject API 调用状态

### 调试模式

```bash
# 启用调试模式（输出更详细日志）
export LOG_LEVEL=DEBUG
python3 -m src.main
```

## 📊 服务监控

### 健康检查端点

```bash
# 检查服务健康状态
curl http://localhost:8010/health

# 预期响应:
{
  "status": "healthy",
  "services": {
    "openproject": "connected",
    "mcp_handler": "ready"
  },
  "timestamp": "2025-01-24T20:00:00Z"
}
```

### 性能监控指标

- **启动时间**: < 1秒
- **API响应时间**: 0.02-3.57秒
- **内存占用**: < 50MB
- **并发支持**: 多请求同时处理

## 🐳 Docker 部署（可选）

### 使用 Docker Compose

```bash
# 启动 OpenProject（如果需要）
docker-compose up -d

# 访问 OpenProject: http://localhost:8090
# 默认账号: admin / admin
```

## 🔒 安全建议

1. **API 密钥保护** - 不要将 API 密钥提交到版本控制
2. **网络隔离** - 在生产环境中使用内网访问 OpenProject
3. **访问控制** - 限制服务器的访问权限
4. **日志监控** - 定期检查服务器日志
5. **更新维护** - 定期更新依赖包

## 📞 支持资源

- **项目文档**: 查看项目根目录的 README.md
- **问题报告**: 创建 GitHub Issue
- **社区支持**: 项目讨论区
- **紧急支持**: 查看服务器日志和健康检查端点

---

**最后更新**: 2025-01-24  
**版本**: v1.0.0  
**状态**: ✅ 生产就绪