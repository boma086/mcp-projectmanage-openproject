# MCP Core Library

**共享核心库：MCP (Model Context Protocol) 项目管理系统**

这是一个共享的核心库，为多种 MCP 实现方案提供统一的业务逻辑、数据模型和基础设施组件。

## 🎯 设计目标

- **消除重复代码**：将通用业务逻辑抽取到共享库中
- **标准化接口**：定义统一的接口规范和数据模型
- **提高可维护性**：修改业务逻辑只需在一处修改
- **简化测试**：共享测试逻辑，减少测试重复
- **提升开发效率**：新增功能只需实现一次

## 🏗️ 架构设计

### 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                    应用层 (Application)                     │
│  • MCP Protocol Handler  • Use Cases                       │
│  • Tool Manager         • Command Handlers                 │
├─────────────────────────────────────────────────────────────┤
│                    领域层 (Domain)                          │
│  • Business Logic       • Domain Models                    │
│  • Domain Services      • Validation Rules                 │
├─────────────────────────────────────────────────────────────┤
│                   基础设施层 (Infrastructure)                │
│  • OpenProject Client   • Template Engine                  │
│  • Cache System         • Monitoring                       │
└─────────────────────────────────────────────────────────────┘
```

## 📦 包结构

```
src/mcp_core/
├── domain/                 # 领域层
│   ├── models/            # 领域模型
│   ├── services/          # 领域服务
│   └── interfaces/        # 接口定义
├── application/           # 应用层
│   ├── mcp/              # MCP 协议处理
│   └── use_cases/        # 用例实现
├── infrastructure/       # 基础设施层
│   ├── openproject/      # OpenProject 集成
│   ├── templates/        # 模板系统
│   └── cache/           # 缓存系统
└── shared/              # 共享工具
    ├── exceptions.py    # 异常定义
    ├── logger.py       # 日志工具
    └── config.py       # 配置管理
```

## 🚀 快速开始

### 安装

```bash
# 开发安装
pip install -e .

# 包含异步支持
pip install -e ".[async]"

# 开发依赖
pip install -e ".[dev]"
```

### 基本使用

```python
from mcp_core.domain.models import Project, WorkPackage
from mcp_core.infrastructure.openproject import OpenProjectClient
from mcp_core.application.use_cases import GenerateReportUseCase

# 创建客户端
client = OpenProjectClient(
    url="https://your-openproject.com",
    api_key="your-api-key"
)

# 使用用例
use_case = GenerateReportUseCase(client)
report = await use_case.execute(project_id="1", report_type="weekly")
```

## 🔧 支持的解决方案

这个核心库被以下解决方案使用：

- **HTTP Solution** (Python + HTTP Server)
- **FastAPI Solution** (Python + FastAPI)
- **TypeScript Solution** (Node.js + TypeScript)
- **FastMCP Solution** (Python + FastMCP)

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 生成覆盖率报告
pytest --cov=src/mcp_core --cov-report=html
```

## 📚 文档

- [API 文档](docs/api.md)
- [架构设计](docs/architecture.md)
- [开发指南](docs/development.md)
- [贡献指南](CONTRIBUTING.md)

## 🤝 贡献

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。
