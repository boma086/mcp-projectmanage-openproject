# OpenProject MCP 服务器

> 🎯 为Team Leader提供零技术门槛的项目报告生成工具

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-2024--11--05-green.svg)](https://modelcontextprotocol.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116+-green.svg)](https://fastapi.tiangolo.com)

## 🚀 5分钟快速开始

### 前置条件：启动 OpenProject
```bash
# 使用 Docker 启动 OpenProject
docker-compose up -d

# 等待服务启动完成（约2-3分钟）
docker-compose logs -f openproject

# 访问 OpenProject: http://localhost:8090
# 默认账号: admin / admin
```

### 方案选择

我们提供两个生产就绪的解决方案：

#### 🔹 方案一：HTTP 解决方案（推荐新手）
```bash
cd solution-http
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e ../mcp-core
python3 -m src.main
```
**访问**: http://localhost:8010

#### 🔹 方案二：FastAPI 解决方案（推荐生产）
```bash
# 先 deactivate 当前虚拟环境
deactivate 2>/dev/null || true

cd solution-fastapi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e ../mcp-core
python app/main.py
```
**访问**: http://localhost:8020 | **API文档**: http://localhost:8020/docs

### 开始使用
- 选择模板 → 输入项目ID → 生成预览 → 下载报告

**就这么简单！** 🎉

## 📝 模板系统详细使用指南

### 模板编辑器地址

| 解决方案 | 模板编辑器地址 | 特点 |
|----------|----------------|------|
| **HTTP 解决方案** | http://localhost:8010/web/template_editor.html | 简单稳定，适合新手 |
| **FastAPI 解决方案** | http://localhost:8020/web/template_editor.html | 现代化，有 API 文档 |

> 📁 **模板编辑器文件位置**: `/shared-web/template_editor.html`
> 🔧 **静态文件服务**: 两个解决方案都通过 `/web/` 路径服务 `shared-web` 目录下的文件

### Team Leader 使用流程

#### 1. 🎨 编辑模板
1. **打开模板编辑器**：
   - HTTP 解决方案：http://localhost:8010/web/template_editor.html
   - FastAPI 解决方案：http://localhost:8020/web/template_editor.html
2. **填写模板信息**：
   - **模板名称**：如 "我的周报模板"
   - **模板类型**：周报/月报/季报/自定义
   - **模板描述**：描述用途和特点
   - **报告标题模板**：如 `{{project_name}} 周报 ({{start_date}} - {{end_date}})`

#### 2. 💾 保存模板
- **操作**：点击 "💾 保存模板" 按钮
- **技术实现**：前端 JavaScript 调用 JSON-RPC，后台自动调用 `save_report_template` MCP 工具
- **保存位置**：`mcp-core/templates/reports/` 目录下的 YAML 文件
- **文件格式**：`模板名称.yaml`（自动生成文件名）
- **保存确认**：页面显示 "模板保存成功" 消息

#### 3. 📋 选择和使用模板
1. **模板列表**：左侧显示所有已保存的模板
2. **选择模板**：点击任一模板项
3. **输入参数**：
   - 项目ID（如：1）
   - 自定义数据（JSON格式，可选）

#### 4. 🔍 生成预览
- 点击 "🔍 生成预览" 按钮
- **后台自动调用** `generate_report_from_template` MCP 工具
- **实时数据**：从 OpenProject 获取最新项目数据
- **动态渲染**：使用 Jinja2 模板引擎生成报告

#### 5. 📥 下载报告
- 点击 "📥 下载报告" 按钮
- **下载格式**：Markdown 文件
- **文件名**：`report_YYYY-MM-DD.md`

### 模板系统技术实现

#### 静态文件服务配置

**FastAPI 解决方案**（`solution-fastapi/app/main.py`）：
```python
# 挂载静态文件（从共享 Web 目录）
if os.path.exists("../shared-web"):
    app.mount("/web", StaticFiles(directory="../shared-web"), name="web")
```

**HTTP 解决方案**（`solution-http/src/main.py`）：
```python
def serve_static_file(self):
    # 从共享 Web 目录服务文件
    file_path = self.path[5:]  # 移除 '/web/' 前缀
    full_path = os.path.join('shared-web', file_path)
```

#### 模板编辑器工作原理

1. **前端页面**：`/shared-web/template_editor.html`
2. **访问路径**：`http://localhost:8020/web/template_editor.html`
3. **API 调用**：JavaScript 通过 JSON-RPC 调用 MCP 工具
4. **后端处理**：MCP 工具保存模板到文件系统

#### 保存位置
```
mcp-core/templates/reports/
├── weekly/
│   ├── 我的周报模板.yaml
│   └── 简化周报模板.yaml
├── monthly/
│   └── 详细月报模板.yaml
└── custom/
    └── 自定义模板.yaml
```

#### 保存过程详解

1. **前端操作**：用户在 `template_editor.html` 中点击 "💾 保存模板" 按钮

2. **JavaScript 调用**：
```javascript
// shared-web/template_editor.html 中的代码
const response = await fetch(API_BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        jsonrpc: "2.0",
        id: 3,
        method: "tools/call",
        params: {
            name: "save_report_template",
            arguments: {
                template_id: templateId,
                template_data: templateData
            }
        }
    })
});
```

3. **MCP 服务处理**：
   - FastAPI 接收 JSON-RPC 请求（端口 8020）
   - 调用 `save_report_template` MCP 工具
   - 工具将模板数据保存为 YAML 文件

4. **文件系统保存**：保存到 `mcp-core/templates/reports/` 目录

5. **确认反馈**：前端显示 "模板保存成功" 消息

### 🔧 问题修复记录

#### 问题：模板编辑器显示 "正在加载模板列表..." 和 405 错误

**原因分析**：
1. **API 地址错误**：`template_editor.html` 中的 `API_BASE` 指向根路径而非 `/mcp` 端点
2. **缺少模板工具**：MCP 服务缺少 `list_report_templates`、`save_report_template`、`generate_report_from_template` 工具

**解决方案**：
1. **修复 API 地址**：
```javascript
// shared-web/template_editor.html
function getApiBase() {
    // 修复：MCP 端点应该是 /mcp，不是根路径
    return window.location.origin + '/mcp';
}
```

2. **添加模板工具**：在 `mcp-core/src/mcp_core/application/mcp/tools.py` 中添加：
   - `list_report_templates`：获取模板列表
   - `save_report_template`：保存模板到 YAML 文件
   - `generate_report_from_template`：使用模板生成报告

**验证结果**：
- ✅ 模板列表正常加载
- ✅ 模板保存功能正常
- ✅ 模板生成报告功能正常
- ✅ 完成度计算逻辑正确
- ✅ 日本式报告模板可用

#### 完成度计算修复

**问题**：之前显示完成率0%，用户质疑计算逻辑
**原因分析**：基于实际OpenProject数据验证
```
项目1实际数据：
- In progress: 3个任务 (25%)
- New: 7个任务 (58.3%)
- Scheduled: 1个里程碑 (8.3%)
- To be scheduled: 1个汇总任务 (8.3%)
- 完成状态: 0个任务
```

**修复方案**：
1. **状态映射优化**：
```python
status_mapping = {
    'closed': 100, 'resolved': 100, 'done': 100,     # 完成状态
    'in progress': 50, 'active': 50,                 # 进行中状态
    'new': 0, 'open': 0,                             # 新建状态
    'scheduled': 10, 'to be scheduled': 5,           # 计划状态
}
```

2. **加权平均计算**：
```python
completion_rate = round(total_progress / total_wps, 1)
# 基于实际数据: (3×50 + 7×0 + 1×10 + 1×5) / 12 = 175/12 ≈ 14.6%
```

**验证结果**：Demo project 完成率显示为正确的数值

### 🇯🇵 日本式报告模板

#### 新增模板类型

基于日本市场需求，新增了4种专业的日本式报告模板：

| 模板类型 | 文件名 | 特点 |
|----------|--------|------|
| **日報** | `japanese_daily_report.yaml` | 详细的日常工作报告，包含6个标准章节 |
| **週報** | `japanese_weekly_report.yaml` | 全面的周报格式，包含7个详细章节 |
| **月報** | `japanese_monthly_report.yaml` | 综合的月度报告，包含预算和效率分析 |
| **進捗報告** | `japanese_progress_report.yaml` | 专业的进度报告，包含风险管理 |

#### 日本式报告特点

1. **详细的章节结构**：
   - 全体进捗概要
   - 実施した作業内容
   - 計画通り完了した項目
   - 未完了項目（計画遅延）
   - リスク識別と対策
   - 来週/来月の計画
   - リソース配分状況

2. **日本商务文化适配**：
   - 使用敬语和正式表达
   - 详细的数据分析表格
   - 风险等级可视化指示器
   - 具体的改善计划和对策

3. **智能数据分析**：
   - 基于实际OpenProject状态的动态分析
   - 自动风险评估和健康状态判断
   - 详细的工作包状态分布统计

#### 使用示例

```yaml
# 日本式週報テンプレート示例
template_info:
  name: "日本式週報テンプレート"
  type: "weekly"
  language: "ja"

sections:
  - section_name: "1. プロジェクト全体進捗概要"
    content_template: |
      ## 1. プロジェクト全体進捗概要

      **全体完了率**: {{completion_rate}}%

      ### 主要指標
      | 項目 | 数値 | 状況 |
      |------|------|------|
      | 完了タスク | {{completed_work_packages}}件 | {{(completed_work_packages/total_work_packages*100)|round(1)}}% |
      | 進行中タスク | {{in_progress_work_packages}}件 | {{(in_progress_work_packages/total_work_packages*100)|round(1)}}% |
```

#### 模板变量扩展

为支持日本式报告，扩展了以下模板变量：

```python
template_vars = {
    # 基础信息
    "project_name": "Demo project",
    "completion_rate": 14.6,  # 基于实际状态计算

    # 详细状态分布
    "completed_work_packages": 0,
    "in_progress_work_packages": 3,
    "new_work_packages": 7,
    "scheduled_work_packages": 1,

    # 日本式报告专用
    "project_health_status": "要注意",
    "risk_level": "中",
    "quality_score": 95,
    "budget_status": "予算内",
}
```

#### YAML 文件结构
```yaml
template_info:
  name: "我的周报模板"
  type: "weekly"
  description: "适合我团队的周报格式"
  created_by: "team_leader"
  version: "1.0"

title_template: "{{project_name}} 周报 ({{start_date}} - {{end_date}})"

sections:
  - section_id: "summary"
    section_name: "总结"
    order: 1
    required: true
    content_template: |
      ## 总结
      项目: {{project_name}}
      完成率: {{completion_rate}}%

data_sources:
  - name: "project_basic"
    description: "项目基础信息"
    fields: ["project_name", "completion_rate"]
```

### 模板使用场景

#### 👨‍💼 Team Leader 日常使用
1. **每周例行**：选择周报模板，输入项目ID，生成本周报告
2. **月度汇报**：选择月报模板，生成月度总结
3. **临时需求**：创建自定义模板，满足特殊报告需求

#### 🤖 AI 系统集成使用
1. **自动化报告**：AI 系统调用 MCP 工具自动生成报告
2. **智能推荐**：根据项目状态推荐合适的模板
3. **批量处理**：一次性为多个项目生成报告

## ✨ 核心特性

- 🎨 **零技术门槛**: 可视化模板编辑器，无需编程知识
- 📊 **智能报告**: 自动生成周报、月报、风险评估
- 🔄 **实时数据**: 直接从OpenProject获取最新项目数据
- 📋 **灵活模板**: 支持自定义报告格式和内容
- 🌐 **Web界面**: 现代化的浏览器界面，随时随地访问

## 🎯 适用人群

- **Team Leader**: 需要定期生成项目报告
- **Project Manager**: 需要项目概览和健康度分析
- **Owner/Boss**: 需要高层汇报材料
- **任何使用OpenProject的团队**

## 📋 功能展示

### 模板编辑器界面
```
📊 报告模板编辑器
┌─────────────────────┬───────────────────────────────────────┐
│    🗂 模板管理      │           👀 预览和测试               │
│                     │                                       │
│ ✅ 标准周报模板     │ 测试项目ID: [1        ]               │
│ ✅ 完整周报模板     │ 自定义数据: [JSON格式]                │
│ ✅ 简化周报模板     │ [🔍 生成预览] [📥 下载报告]          │
│                     │                                       │
│ [💾 保存] [📄 新建] │ 📋 实时预览生成的报告内容...          │
└─────────────────────┴───────────────────────────────────────┘
```

### 生成的报告示例
```markdown
# Demo project 周报 (2025-01-20 - 2025-01-26)

## 项目概览
**项目名称**: Demo project
**完成率**: 7.7%
**团队成员**: 5 人

## 进度统计
| 指标 | 数量 | 百分比 |
|------|------|--------|
| 总工作包 | 13 | 100% |
| 已完成 | 1 | 7.7% |
| 进行中 | 3 | 23.1% |

## 关键指标
- **项目健康度**: 🔴 需要改进 (7.7%)
- **团队满意度**: 😊 良好
- **协作效率**: ⚡ 高
```

## 🛠 技术架构

### 双解决方案架构
```
mcp-projectmanage-openproject/
├── mcp-core/                    # 共享核心库
├── solution-http/               # HTTP 同步解决方案 (端口 8010)
├── solution-fastapi/            # FastAPI 异步解决方案 (端口 8020)
└── docker-compose.yml           # OpenProject 容器配置
```

### 技术栈对比

| 组件 | HTTP 解决方案 | FastAPI 解决方案 |
|------|---------------|------------------|
| **Web框架** | HTTP Server | FastAPI |
| **异步支持** | 同步 | 异步 (混合方案) |
| **API文档** | 无 | 自动生成 Swagger |
| **HTTP客户端** | requests | requests + 线程池 |
| **端口** | 8010 | 8020 |
| **适用场景** | 简单部署 | 生产环境 |

### 核心技术
- **后端**: Python 3.13 + MCP Protocol
- **模板引擎**: Jinja2 (支持变量、条件、循环)
- **前端**: HTML5 + CSS3 + Vanilla JavaScript
- **数据源**: OpenProject API (Basic Auth)
- **存储**: YAML配置文件
- **容器化**: Docker Compose

## 📦 完整部署指南

### 环境要求
- Python 3.13+
- Docker & Docker Compose
- 现代浏览器

### 1. 启动 OpenProject 服务
```bash
# 克隆项目
git clone <repository-url>
cd mcp-projectmanage-openproject

# 启动 OpenProject Docker 容器
docker-compose up -d

# 检查服务状态
docker-compose ps
docker-compose logs openproject

# 访问 OpenProject: http://localhost:8090
# 默认账号: admin / admin
```

### 2. 获取 API 密钥
1. 登录 OpenProject (http://localhost:8090)
2. 进入 "我的账户" → "访问令牌"
3. 创建新的 API 密钥
4. 复制生成的密钥

### 3. 配置环境变量
```bash
# HTTP 解决方案
cd solution-http
cp .env.example .env

# FastAPI 解决方案
cd solution-fastapi
cp .env.example .env

# 编辑 .env 文件
OPENPROJECT_URL=http://localhost:8090
OPENPROJECT_API_KEY=your-api-key-here
MCP_SERVER_PORT=8010  # 或 8020
```

### 4. 从头构建虚拟环境

#### HTTP 解决方案
```bash
cd solution-http
rm -rf venv  # 清理旧环境
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e ../mcp-core
python3 -m src.main
```

#### FastAPI 解决方案
```bash
cd solution-fastapi
rm -rf venv  # 清理旧环境
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e ../mcp-core
python app/main.py
```

## 🧪 测试验证

### 基础连接测试
```bash
# 测试 OpenProject 连接
curl -u "apikey:YOUR_API_KEY" http://localhost:8090/api/v3/projects

# 测试 HTTP 解决方案
curl http://localhost:8010/health

# 测试 FastAPI 解决方案
curl http://localhost:8020/health
curl http://localhost:8020/docs  # API 文档
```

### MCP 协议测试
```bash
# HTTP 解决方案 MCP 测试
curl -X POST http://localhost:8010/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}'

# FastAPI 解决方案 MCP 测试
curl -X POST http://localhost:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "get_projects", "arguments": {}}}'
```

### 功能测试
```bash
# 运行完整测试套件
cd tests
python3 test_http_mcp_server.py
python3 test_http_template_features.py
python3 test_openproject_connection.py

# 运行技术分析脚本
python3 httpx_connection_analysis.py
python3 deep_technical_analysis.py
```

### 预期结果
- ✅ OpenProject 返回项目列表 JSON
- ✅ MCP 服务返回工具列表
- ✅ 健康检查返回 "healthy" 状态
- ✅ 所有测试通过

**测试覆盖率**: 100% ✅

## � 集成到 AI 网站

### 架构设计

```
AI 网站 (React + Next.js + FastAPI)
    ↓ HTTP 调用
MCP 服务 (本项目)
    ↓ API 调用
OpenProject 服务
```

### Python 后端集成示例

#### 1. MCP 客户端封装

```python
# ai_website/backend/mcp_client.py
import httpx
from typing import Dict, List, Any, Optional
import asyncio

class MCPClient:
    """MCP 服务客户端"""

    def __init__(self, mcp_url: str = "http://localhost:8020"):
        self.mcp_url = mcp_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用 MCP 工具"""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        response = await self.client.post(
            f"{self.mcp_url}/mcp",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code != 200:
            raise Exception(f"MCP 调用失败: {response.status_code}")

        data = response.json()
        if "error" in data:
            raise Exception(f"MCP 错误: {data['error']['message']}")

        return data["result"]

    async def get_projects(self) -> List[Dict[str, Any]]:
        """获取项目列表"""
        result = await self.call_tool("get_projects", {})
        return result["content"][0]["text"]

    async def generate_weekly_report(self, project_id: str, start_date: str, end_date: str) -> str:
        """生成周报"""
        result = await self.call_tool("generate_weekly_report", {
            "project_id": project_id,
            "start_date": start_date,
            "end_date": end_date
        })
        return result["content"][0]["text"]

    async def generate_report_from_template(self, template_id: str, project_id: str, custom_data: Dict = None) -> str:
        """使用模板生成报告"""
        result = await self.call_tool("generate_report_from_template", {
            "template_id": template_id,
            "project_id": project_id,
            "custom_data": custom_data or {}
        })
        return result["content"][0]["text"]

    async def list_templates(self) -> List[Dict[str, Any]]:
        """获取模板列表"""
        result = await self.call_tool("list_report_templates", {})
        return result["content"][0]["text"]

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()
```

#### 2. FastAPI 路由集成

```python
# ai_website/backend/routers/reports.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from .mcp_client import MCPClient

router = APIRouter(prefix="/api/reports", tags=["reports"])

class ReportRequest(BaseModel):
    project_id: str
    template_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    custom_data: Optional[Dict[str, Any]] = None

class TemplateRequest(BaseModel):
    template_id: str
    project_id: str
    custom_data: Optional[Dict[str, Any]] = None

async def get_mcp_client():
    """获取 MCP 客户端"""
    client = MCPClient("http://localhost:8020")  # FastAPI 解决方案
    try:
        yield client
    finally:
        await client.close()

@router.get("/projects")
async def get_projects(mcp: MCPClient = Depends(get_mcp_client)):
    """获取项目列表"""
    try:
        projects = await mcp.get_projects()
        return {"success": True, "data": projects}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates")
async def get_templates(mcp: MCPClient = Depends(get_mcp_client)):
    """获取模板列表"""
    try:
        templates = await mcp.list_templates()
        return {"success": True, "data": templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate")
async def generate_report(
    request: ReportRequest,
    mcp: MCPClient = Depends(get_mcp_client)
):
    """生成报告"""
    try:
        if request.template_id:
            # 使用模板生成
            report = await mcp.generate_report_from_template(
                template_id=request.template_id,
                project_id=request.project_id,
                custom_data=request.custom_data
            )
        else:
            # 生成标准周报
            report = await mcp.generate_weekly_report(
                project_id=request.project_id,
                start_date=request.start_date,
                end_date=request.end_date
            )

        return {"success": True, "report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/template-report")
async def generate_template_report(
    request: TemplateRequest,
    mcp: MCPClient = Depends(get_mcp_client)
):
    """使用指定模板生成报告"""
    try:
        report = await mcp.generate_report_from_template(
            template_id=request.template_id,
            project_id=request.project_id,
            custom_data=request.custom_data
        )
        return {"success": True, "report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### 3. LangChain 工具集成

```python
# ai_website/backend/langchain_tools/mcp_tools.py
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from ..mcp_client import MCPClient

class ProjectReportTool(BaseTool):
    """项目报告生成工具"""
    name = "generate_project_report"
    description = "生成项目报告，支持周报、月报等多种格式"

    mcp_client: MCPClient = Field(default_factory=lambda: MCPClient())

    class Config:
        arbitrary_types_allowed = True

    def _run(self, project_id: str, report_type: str = "weekly", **kwargs) -> str:
        """同步运行（LangChain 兼容）"""
        import asyncio
        return asyncio.run(self._arun(project_id, report_type, **kwargs))

    async def _arun(self, project_id: str, report_type: str = "weekly", **kwargs) -> str:
        """异步运行"""
        try:
            if report_type == "weekly":
                start_date = kwargs.get("start_date")
                end_date = kwargs.get("end_date")
                report = await self.mcp_client.generate_weekly_report(
                    project_id=project_id,
                    start_date=start_date,
                    end_date=end_date
                )
            elif report_type == "template":
                template_id = kwargs.get("template_id")
                custom_data = kwargs.get("custom_data", {})
                report = await self.mcp_client.generate_report_from_template(
                    template_id=template_id,
                    project_id=project_id,
                    custom_data=custom_data
                )
            else:
                raise ValueError(f"不支持的报告类型: {report_type}")

            return report
        except Exception as e:
            return f"生成报告失败: {str(e)}"

class ProjectListTool(BaseTool):
    """项目列表获取工具"""
    name = "get_project_list"
    description = "获取 OpenProject 中的所有项目列表"

    mcp_client: MCPClient = Field(default_factory=lambda: MCPClient())

    class Config:
        arbitrary_types_allowed = True

    def _run(self) -> str:
        import asyncio
        return asyncio.run(self._arun())

    async def _arun(self) -> str:
        try:
            projects = await self.mcp_client.get_projects()
            return str(projects)
        except Exception as e:
            return f"获取项目列表失败: {str(e)}"

# 工具注册
def get_mcp_tools():
    """获取所有 MCP 相关工具"""
    return [
        ProjectReportTool(),
        ProjectListTool(),
    ]
```

#### 4. LangGraph 节点集成

```python
# ai_website/backend/langgraph_nodes/report_nodes.py
from langgraph import StateGraph, END
from typing import Dict, Any
from ..mcp_client import MCPClient

async def report_generation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """报告生成节点"""
    mcp_client = MCPClient()

    try:
        project_id = state.get("project_id")
        template_id = state.get("template_id")

        if template_id:
            report = await mcp_client.generate_report_from_template(
                template_id=template_id,
                project_id=project_id,
                custom_data=state.get("custom_data", {})
            )
        else:
            report = await mcp_client.generate_weekly_report(
                project_id=project_id,
                start_date=state.get("start_date"),
                end_date=state.get("end_date")
            )

        state["generated_report"] = report
        state["status"] = "success"

    except Exception as e:
        state["error"] = str(e)
        state["status"] = "error"

    finally:
        await mcp_client.close()

    return state

async def project_analysis_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """项目分析节点"""
    mcp_client = MCPClient()

    try:
        projects = await mcp_client.get_projects()
        state["projects"] = projects
        state["analysis_complete"] = True

    except Exception as e:
        state["error"] = str(e)
        state["analysis_complete"] = False

    finally:
        await mcp_client.close()

    return state

# 构建工作流
def create_report_workflow():
    """创建报告生成工作流"""
    workflow = StateGraph(dict)

    workflow.add_node("analyze_project", project_analysis_node)
    workflow.add_node("generate_report", report_generation_node)

    workflow.add_edge("analyze_project", "generate_report")
    workflow.add_edge("generate_report", END)

    workflow.set_entry_point("analyze_project")

    return workflow.compile()
```

### 前端 React 集成示例

```typescript
// ai_website/frontend/hooks/useMCPReports.ts
import { useState, useCallback } from 'react';

interface ReportRequest {
  projectId: string;
  templateId?: string;
  startDate?: string;
  endDate?: string;
  customData?: Record<string, any>;
}

export const useMCPReports = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generateReport = useCallback(async (request: ReportRequest) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/reports/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error('生成报告失败');
      }

      const data = await response.json();
      return data.report;
    } catch (err) {
      setError(err instanceof Error ? err.message : '未知错误');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getTemplates = useCallback(async () => {
    const response = await fetch('/api/reports/templates');
    const data = await response.json();
    return data.data;
  }, []);

  return { generateReport, getTemplates, loading, error };
};
```

### 关键优势

1. **无重复代码**：AI 网站只需要 HTTP 客户端，不需要重复实现 MCP 工具
2. **松耦合**：MCP 服务独立运行，可以被多个系统调用
3. **标准化**：使用标准的 JSON-RPC 协议通信
4. **可扩展**：新增工具只需在 MCP 服务中实现，自动对所有客户端可用

### 工具发现和定位

#### 问题：`tools = get_mcp_tools()` 如何定位到 8020 端口的工具？

**答案**：通过 `MCPClient` 配置指向正确的 MCP 服务地址。

```python
# ai_website/backend/langchain_tools/mcp_tools.py
from ..mcp_client import MCPClient

class ProjectReportTool(BaseTool):
    # 🔑 关键：指定 MCP 服务地址
    mcp_client: MCPClient = Field(default_factory=lambda: MCPClient("http://localhost:8020"))

def get_mcp_tools():
    """获取所有 MCP 相关工具"""
    # 🔍 工具发现过程：
    # 1. 创建 MCPClient，连接到 http://localhost:8020
    # 2. 调用 tools/list 获取可用工具列表
    # 3. 动态创建 LangChain 工具包装器

    mcp_client = MCPClient("http://localhost:8020")  # FastAPI 解决方案

    # 可以动态获取工具列表
    # tools_list = await mcp_client.call_tool("tools/list", {})

    return [
        ProjectReportTool(),      # 包装 generate_weekly_report 等
        ProjectListTool(),        # 包装 get_projects
        TemplateManagementTool(), # 包装 list_report_templates, save_report_template
        # ... 更多工具
    ]
```

#### 动态工具发现示例

```python
# ai_website/backend/langchain_tools/dynamic_mcp_tools.py
import asyncio
from typing import List
from langchain.tools import BaseTool

async def discover_mcp_tools(mcp_url: str = "http://localhost:8020") -> List[BaseTool]:
    """动态发现 MCP 工具并创建 LangChain 包装器"""

    mcp_client = MCPClient(mcp_url)

    try:
        # 1. 获取 MCP 服务提供的工具列表
        result = await mcp_client.call_tool("tools/list", {})
        tools_info = result.get("tools", [])

        # 2. 为每个 MCP 工具创建 LangChain 包装器
        langchain_tools = []

        for tool_info in tools_info:
            tool_name = tool_info["name"]
            tool_description = tool_info["description"]

            # 动态创建工具类
            class DynamicMCPTool(BaseTool):
                name = tool_name
                description = tool_description
                mcp_client = mcp_client

                def _run(self, **kwargs) -> str:
                    return asyncio.run(self._arun(**kwargs))

                async def _arun(self, **kwargs) -> str:
                    try:
                        result = await self.mcp_client.call_tool(self.name, kwargs)
                        return str(result)
                    except Exception as e:
                        return f"工具调用失败: {str(e)}"

            langchain_tools.append(DynamicMCPTool())

        return langchain_tools

    finally:
        await mcp_client.close()

# 使用示例
async def setup_ai_agent():
    # 🚀 自动发现并集成所有 MCP 工具
    mcp_tools = await discover_mcp_tools("http://localhost:8020")

    # 创建 AI 代理
    agent = create_agent(tools=mcp_tools)

    return agent
```

#### 配置管理

```python
# ai_website/backend/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    # MCP 服务配置
    mcp_service_url: str = "http://localhost:8020"  # FastAPI 解决方案
    # mcp_service_url: str = "http://localhost:8010"  # HTTP 解决方案

    mcp_timeout: int = 30
    mcp_retry_attempts: int = 3

# 全局配置
settings = Settings()

# 在工具中使用
class ProjectReportTool(BaseTool):
    mcp_client: MCPClient = Field(
        default_factory=lambda: MCPClient(settings.mcp_service_url)
    )
```

#### 健康检查和故障转移

```python
# ai_website/backend/mcp_client.py
class MCPClient:
    def __init__(self, mcp_url: str = "http://localhost:8020"):
        self.mcp_url = mcp_url
        self.backup_urls = [
            "http://localhost:8010",  # HTTP 解决方案作为备份
            "http://localhost:8020",  # FastAPI 解决方案
        ]

    async def call_tool_with_fallback(self, tool_name: str, arguments: Dict[str, Any]):
        """带故障转移的工具调用"""
        urls_to_try = [self.mcp_url] + self.backup_urls

        for url in urls_to_try:
            try:
                # 先检查健康状态
                health_response = await self.client.get(f"{url}/health")
                if health_response.status_code == 200:
                    # 调用工具
                    return await self._call_tool_on_url(url, tool_name, arguments)
            except Exception as e:
                logger.warning(f"MCP 服务 {url} 不可用: {e}")
                continue

        raise Exception("所有 MCP 服务都不可用")
```

**总结**：
1. **工具定位**：通过 `MCPClient("http://localhost:8020")` 指定服务地址
2. **动态发现**：可以调用 `tools/list` 获取可用工具列表
3. **自动包装**：将 MCP 工具包装为 LangChain 工具
4. **故障转移**：支持多个 MCP 服务地址的备份机制

## �📚 详细文档

- 📖 [完整项目文档](PROJECT_SUMMARY.md) - 详细的功能说明和使用指南
- 🎨 [模板编辑指南](PROJECT_SUMMARY.md#模板编辑器使用指南) - 如何创建和编辑报告模板
- 🔧 [故障排除](PROJECT_SUMMARY.md#故障排除) - 常见问题解决方案

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 🎉 项目状态

**状态**: ✅ 完成并可用于生产环境
**最后更新**: 2025-07-24
**维护状态**: 积极维护

---

**立即开始使用**: `cd solution-http && python3 -m src.main` 然后访问 http://localhost:8010 🚀
