# OpenProject MCP 服务器优化方案

## 🎯 优化目标

通过系统性的架构重构，解决当前项目中的代码重复、技术债务和架构问题，提升项目的可维护性、可扩展性和稳定性。

## ⚠️ 当前问题分析

### 1. 代码重复问题
- **OpenProject API 集成**：四个解决方案都重复实现了相同的 API 调用逻辑
- **报告生成逻辑**：周报、月报、风险评估等业务逻辑在各方案中重复
- **数据模型定义**：Project、WorkPackage 等模型在各处重复定义
- **模板系统**：Jinja2 模板渲染逻辑重复实现
- **MCP 协议处理**：JSON-RPC 协议解析和工具调用逻辑重复

### 2. 架构设计问题
- **缺乏抽象层**：没有统一的接口定义和抽象基类
- **紧耦合**：业务逻辑与具体实现框架耦合过紧
- **测试重复**：相同的业务逻辑测试在各方案中重复编写
- **维护困难**：修改业务逻辑需要在四个地方同时修改

## 📋 分阶段实施计划

### 阶段1: 核心库抽取 (1-2周)

#### 任务清单
- [ ] 创建 `mcp-core` 包结构
- [ ] 抽取通用数据模型 (Project, WorkPackage, Report)
- [ ] 抽取 OpenProject API 客户端接口和实现
- [ ] 抽取报告生成业务逻辑
- [ ] 抽取模板引擎系统
- [ ] 抽取 MCP 协议处理器
- [ ] 建立统一的配置管理系统
- [ ] 创建共享的异常处理机制

#### 交付物
- 完整的 `mcp-core` Python 包
- 统一的接口定义 (`interfaces/`)
- 共享的业务逻辑 (`services/`)
- 标准化的数据模型 (`models/`)

### 阶段2: 接口标准化 (1-2周)

#### 任务清单
- [ ] 定义统一的接口规范 (抽象基类)
- [ ] 实现接口的适配器模式
- [ ] 标准化错误处理和异常体系
- [ ] 统一配置管理接口
- [ ] 创建依赖注入容器
- [ ] 建立插件系统架构

#### 交付物
- 完整的接口定义文档
- 适配器实现示例
- 统一的错误码规范
- 配置管理最佳实践

### 阶段3: 解决方案重构 (2-3周)

#### 任务清单
- [ ] HTTP Solution 重构 (使用核心库)
- [ ] FastAPI Solution 重构 (使用核心库)
- [ ] FastMCP Solution 问题修复或标记为实验性
- [ ] TypeScript Solution 技术选型和架构设计
- [ ] 统一的构建和部署脚本
- [ ] 跨解决方案的测试套件

#### 交付物
- 重构后的 HTTP 解决方案
- 重构后的 FastAPI 解决方案
- FastMCP 解决方案状态评估报告
- TypeScript 解决方案技术方案

### 阶段4: 测试统一化 (1-2周)

#### 任务清单
- [ ] 核心库单元测试套件
- [ ] 集成测试框架
- [ ] 端到端测试场景
- [ ] 性能测试基准
- [ ] 安全测试方案
- [ ] 兼容性测试矩阵

#### 交付物
- 完整的测试覆盖报告
- 性能基准数据
- 安全审计报告
- 兼容性测试结果

## 🏗️ 技术架构设计

### 共享核心库结构 (`mcp-core/`)

```
mcp-core/
├── domain/                 # 领域层
│   ├── models/            # 数据模型
│   │   ├── project.py     # 项目模型
│   │   ├── work_package.py # 工作包模型
│   │   └── report.py      # 报告模型
│   ├── services/          # 领域服务
│   │   ├── report_generator.py    # 报告生成
│   │   ├── risk_assessor.py       # 风险评估
│   │   └── workload_analyzer.py   # 工作负载分析
│   └── interfaces/        # 接口定义
│       ├── openproject_client.py  # OpenProject 客户端接口
│       └── template_engine.py     # 模板引擎接口
├── infrastructure/        # 基础设施层
│   ├── openproject/       # OpenProject 集成
│   │   ├── client.py      # API 客户端实现
│   │   └── mapper.py      # 数据映射器
│   ├── templates/         # 模板系统
│   │   ├── engine.py      # 模板引擎
│   │   └── repository.py  # 模板仓库
│   └── cache/            # 缓存系统
│       └── memory_cache.py
├── application/          # 应用层
│   ├── mcp/             # MCP 协议处理
│   │   ├── handler.py   # 协议处理器
│   │   ├── tools.py     # 工具定义
│   │   └── resources.py # 资源管理
│   └── use_cases/       # 用例实现
│       ├── generate_report.py
│       └── assess_risks.py
└── shared/              # 共享工具
    ├── exceptions.py    # 异常定义
    ├── logger.py       # 日志工具
    └── config.py       # 配置管理
```

### 适配器模式实现

每个解决方案只需实现特定的适配器：

```python
# 示例：FastAPI 适配器
from mcp_core.application.mcp.handler import MCPHandler
from mcp_core.infrastructure.openproject.client import OpenProjectClient

class FastAPIMCPAdapter:
    def __init__(self):
        self.client = OpenProjectClient()
        self.handler = MCPHandler(self.client)

    async def handle_request(self, request):
        return await self.handler.process(request)
```

## 🔧 关键技术问题解决方案

### httpx 异步连接兼容性问题

**问题**: `httpx.RemoteProtocolError: Server disconnected without sending a response.`

**解决方案**: 混合架构（requests + 线程池）
```python
async def _make_request(self, endpoint: str) -> Dict[str, Any]:
    def sync_request():
        session = requests.Session()
        session.auth = ('apikey', self.api_key)
        return session.get(url, timeout=30).json()

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, sync_request)
```

**技术要点**:
- ✅ 保持异步接口，使用同步实现
- ✅ 通过线程池实现真正并发
- ✅ 绕过 httpx 与 OpenProject 的兼容性问题
- ✅ 性能更优（0.076s vs 0.645s）

### OpenProject API 认证

**正确方式**: Basic Auth
```python
auth = ('apikey', 'your-api-key')  # ✅ 正确
```

**错误方式**: Bearer Token
```python
headers = {'Authorization': f'Bearer {key}'}  # ❌ 错误
```

## 🧪 测试策略

### 测试分层
```
tests/
├── unit/                  # 单元测试 (mcp-core)
│   ├── domain/
│   ├── infrastructure/
│   └── application/
├── integration/           # 集成测试 (跨层测试)
│   ├── openproject_integration/
│   └── template_integration/
├── e2e/                  # 端到端测试
│   ├── http_solution/
│   ├── fastapi_solution/
│   ├── typescript_solution/
│   └── fastmcp_solution/
└── performance/          # 性能测试
    └── load_tests/
```

## 📊 预期成果

### 量化指标
- **代码重复率降低**: 80% → <10%
- **维护成本降低**: 修改一处，处处生效
- **测试覆盖率提升**: 达到 90%+
- **构建时间减少**: 统一的构建流程
- **部署复杂度降低**: 标准化的部署方案

### 质量指标
- ✅ 架构清晰，职责分离
- ✅ 接口标准化，易于扩展
- ✅ 错误处理统一，易于调试
- ✅ 配置管理集中，易于维护
- ✅ 测试覆盖完整，质量可靠

## 🚀 实施优先级

1. **高优先级**: 核心库抽取 + HTTP 解决方案重构
2. **中优先级**: FastAPI 解决方案重构 + 测试套件
3. **低优先级**: FastMCP 问题修复 + TypeScript 方案

## 📅 时间安排

| 阶段 | 时间 | 状态 |
|------|------|------|
| 阶段1: 核心库抽取 | 第1-2周 | 🟡 进行中 |
| 阶段2: 接口标准化 | 第3-4周 | ⚪ 待开始 |
| 阶段3: 解决方案重构 | 第5-7周 | ⚪ 待开始 |
| 阶段4: 测试统一化 | 第8-9周 | ⚪ 待开始 |

## 🤝 团队协作

### 角色分工
- **架构师**: 技术方案设计和评审
- **后端开发**: 核心库实现和重构
- **前端开发**: Web 界面优化
- **测试工程师**: 测试套件建设和执行
- **DevOps**: 构建部署流水线

### 代码规范
- 遵循 PEP 8 Python 代码规范
- 使用 Black 进行代码格式化
- 使用 MyPy 进行类型检查
- 使用 Ruff 进行代码质量检查

## 🔄 持续集成

### GitHub Actions 工作流
```yaml
name: CI Pipeline
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12, 3.13]
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: pip install -e .[dev]
    - name: Run tests
      run: pytest -v --cov=src/mcp_core --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## 📈 成功标准

- [ ] 核心库抽取完成，代码重复率 <10%
- [ ] HTTP 和 FastAPI 解决方案重构完成
- [ ] 测试覆盖率 >90%
- [ ] 构建部署流水线自动化
- [ ] 性能指标达到预期
- [ ] 文档完整且最新

---

**最后更新**: 2025-01-24  
**负责人**: 架构团队  
**状态**: 🟡 进行中