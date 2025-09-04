# Architecture Overview / 架构概述

This document provides a comprehensive overview of the OpenProject MCP integration architecture.

本文档提供 OpenProject MCP 集成架构的全面概述。

## System Architecture / 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │    │   Claude Code   │    │   Web UI        │
│                 │    │                 │    │                 │
│  • MCP Client   │    │  • Integration  │    │  • Dashboard    │
│  • Web App      │    │  • Tools        │    │  • Reports      │
│  • Mobile App   │    │  • Resources    │    │  • Admin        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Load Balancer  │
                    │                 │
                    │  • SSL Termination│
                    │  • Routing       │
                    │  • Health Checks │
                    └─────────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            │                    │                    │
    ┌───────▼──────┐    ┌───────▼──────┐    ┌───────▼──────┐
    │ HTTP Solution │    │ FastAPI Sol.  │    │TypeScript Sol.│
    │               │    │               │    │               │
    │ • Port 8010   │    │ • Port 8020   │    │ • Port 8040   │
    │ • Sync        │    │ • Async       │    │ • Node.js     │
    │ • Minimal     │    │ • Full-featured│    │ • Type-safe   │
    └───────┬──────┘    └───────┬──────┘    └───────┬──────┘
            │                    │                    │
            └────────────────────┼────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   OpenProject   │
                    │                 │
                    │  • Projects     │
                    │  • Work Packages│
                    │  • Users        │
                    │  • Reports      │
                    └─────────────────┘
```

## Core Components / 核心组件

### 1. MCP Core Library / MCP 核心库

The `mcp-core` library provides shared functionality across all solutions:

`mcp-core` 库为所有解决方案提供共享功能：

```
mcp-core/
├── domain/
│   ├── models/           # Domain models
│   │   ├── Project.py
│   │   ├── WorkPackage.py
│   │   ├── Report.py
│   │   └── User.py
│   └── services/         # Business logic
│       ├── ReportGenerator.py
│       ├── RiskAssessor.py
│       ├── WorkloadAnalyzer.py
│       └── HealthChecker.py
├── application/
│   ├── mcp/
│   │   ├── tools.py      # MCP tools
│   │   └── resources.py  # MCP resources
│   └── templates/        # Report templates
└── infrastructure/       # External integrations
    ├── openproject/
    └── logging/
```

### 2. Solution Implementations / 解决方案实现

Each solution provides a different approach to the same core functionality:

每个解决方案对相同核心功能提供不同的实现方式：

#### HTTP Solution (Port 8010)
- **Architecture**: Synchronous request-response
- **Performance**: Simple, predictable latency
- **Use Case**: Production environments with simple requirements
- **Dependencies**: Minimal (requests, Flask)

#### FastAPI Solution (Port 8020)
- **Architecture**: Asynchronous with WebSocket support
- **Performance**: High concurrency, real-time features
- **Use Case**: Development and feature-rich applications
- **Dependencies**: FastAPI, httpx, WebSocket libraries

#### FastMCP Solution (Port 8030)
- **Architecture**: Protocol-optimized with advanced features
- **Performance**: Enhanced MCP protocol implementation
- **Use Case**: MCP-specific optimizations and extensions
- **Dependencies**: MCP protocol libraries

#### TypeScript Solution (Port 8040)
- **Architecture**: Node.js with TypeScript
- **Performance**: JavaScript ecosystem integration
- **Use Case**: Frontend integration and JavaScript environments
- **Dependencies**: Node.js, TypeScript, Express

### 3. OpenProject Integration / OpenProject 集成

All solutions integrate with OpenProject through a standardized adapter:

所有解决方案都通过标准化适配器与 OpenProject 集成：

```
OpenProject API Integration
├── Authentication / 认证
│   ├── API Key Authentication
│   └── OAuth 2.0 Support
├── Project Management / 项目管理
│   ├── Project CRUD Operations
│   ├── Project Templates
│   └── Project Hierarchies
├── Work Package Management / 工作包管理
│   ├── Work Package CRUD
│   ├── Status Management
│   ├── Assignee Management
│   └── Time Tracking
├── User Management / 用户管理
│   ├── User Information
│   ├── Permissions
│   └── Groups
└── Report Generation / 报告生成
    ├── Weekly Reports
    ├── Monthly Reports
    ├── Progress Reports
    └── Risk Assessments
```

## Data Flow / 数据流

### 1. MCP Protocol Flow / MCP 协议流

```
Client → MCP Server → OpenProject API → Response
   │         │            │              │
   │         │            │              └── Process Response
   │         │            └── Call OpenProject API
   │         └── Parse MCP Request
   └── Send MCP Request
```

### 2. Request Processing / 请求处理

```
1. Request Reception
   ├─ HTTP Server receives request
   ├─ Authentication validation
   └─ Rate limiting check

2. MCP Protocol Handling
   ├─ JSON-RPC parsing
   ├─ Tool/Resource routing
   └─ Parameter validation

3. Business Logic Execution
   ├─ Domain service invocation
   ├─ OpenProject API calls
   └─ Data transformation

4. Response Generation
   ├─ Result formatting
   ├─ Error handling
   └─ Response serialization
```

## Key Design Patterns / 关键设计模式

### 1. Domain-Driven Design (DDD) / 领域驱动设计

- **Domain Models**: Rich domain objects with business logic
- **Repositories**: Data access abstraction
- **Services**: Application services for business operations
- **Value Objects**: Immutable domain concepts

### 2. Repository Pattern / 仓储模式

```python
class ProjectRepository:
    def get_by_id(self, project_id: int) -> Project:
        """Get project by ID from OpenProject"""
        pass
    
    def get_all(self, filters: dict) -> List[Project]:
        """Get all projects with optional filters"""
        pass
    
    def save(self, project: Project) -> Project:
        """Save project to OpenProject"""
        pass
```

### 3. Strategy Pattern / 策略模式

Different solutions implement the same interface with different strategies:

不同解决方案使用不同策略实现相同接口：

```python
class OpenProjectAdapter(ABC):
    @abstractmethod
    def get_projects(self) -> List[Project]:
        pass
    
    @abstractmethod
    def create_work_package(self, work_package: WorkPackage) -> WorkPackage:
        pass

class HttpOpenProjectAdapter(OpenProjectAdapter):
    def get_projects(self) -> List[Project]:
        # HTTP implementation
        pass

class AsyncOpenProjectAdapter(OpenProjectAdapter):
    def get_projects(self) -> List[Project]:
        # Async implementation
        pass
```

### 4. Template Method Pattern / 模板方法模式

Report generation follows a consistent template:

报告生成遵循一致的模板：

```python
class ReportGenerator:
    def generate_report(self, report_type: str, data: dict) -> str:
        template = self.load_template(report_type)
        rendered = self.render_template(template, data)
        return self.format_output(rendered)
```

## Security Architecture / 安全架构

### 1. Authentication / 认证

- **API Key Authentication**: Primary authentication method
- **OAuth 2.0**: Alternative authentication method
- **Token Management**: Secure token storage and refresh
- **Session Management**: Session timeout and cleanup

### 2. Authorization / 授权

- **Role-Based Access Control**: User role-based permissions
- **Resource-Level Security**: Project and work package access control
- **API Rate Limiting**: Prevent abuse and ensure fair usage
- **IP Whitelisting**: Restrict access to trusted IP addresses

### 3. Data Protection / 数据保护

- **Encryption in Transit**: HTTPS/TLS for all communications
- **Input Validation**: Sanitize all user inputs
- **Output Encoding**: Prevent XSS and injection attacks
- **Audit Logging**: Track all API interactions

## Performance Architecture / 性能架构

### 1. Scalability / 可扩展性

- **Horizontal Scaling**: Load balancer with multiple instances
- **Vertical Scaling**: Resource allocation based on demand
- **Connection Pooling**: Efficient database and API connections
- **Caching Strategy**: Multi-level caching for frequently accessed data

### 2. Reliability / 可靠性

- **High Availability**: Redundant instances and failover
- **Circuit Breaker**: Prevent cascading failures
- **Retry Logic**: Exponential backoff for failed requests
- **Health Checks**: Continuous monitoring and self-healing

### 3. Monitoring / 监控

- **Metrics Collection**: Performance and business metrics
- **Distributed Tracing**: Request lifecycle tracking
- **Error Tracking**: Comprehensive error logging and alerting
- **Performance Profiling**: Response time and resource usage analysis

## Integration Points / 集成点

### 1. External Integrations / 外部集成

- **OpenProject API**: Primary integration point
- **MCP Protocol**: Model Context Protocol support
- **WebHooks**: Real-time event notifications
- **File Storage**: Document and attachment management

### 2. Internal Integrations / 内部集成

- **Authentication Services**: Centralized authentication
- **Logging Services**: Structured logging and aggregation
- **Monitoring Services**: Metrics and alerting
- **Configuration Services**: Centralized configuration management

## Deployment Architecture / 部署架构

### 1. Container Architecture / 容器架构

```yaml
# docker-compose.yml
version: '3.8'
services:
  http-solution:
    build: ./solution-http
    ports:
      - "8010:8010"
    environment:
      - OPENPROJECT_URL=${OPENPROJECT_URL}
      - OPENPROJECT_API_KEY=${OPENPROJECT_API_KEY}
  
  fastapi-solution:
    build: ./solution-fastapi
    ports:
      - "8020:8020"
    environment:
      - OPENPROJECT_URL=${OPENPROJECT_URL}
      - OPENPROJECT_API_KEY=${OPENPROJECT_API_KEY}
```

### 2. Kubernetes Architecture / Kubernetes 架构

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: openproject-mcp-fastapi
spec:
  replicas: 3
  selector:
    matchLabels:
      app: openproject-mcp-fastapi
  template:
    metadata:
      labels:
        app: openproject-mcp-fastapi
    spec:
      containers:
      - name: fastapi
        image: openproject-mcp-fastapi:latest
        ports:
        - containerPort: 8020
        env:
        - name: OPENPROJECT_URL
          valueFrom:
            secretKeyRef:
              name: openproject-secrets
              key: url
```

## Future Considerations / 未来考虑

### 1. Scalability Enhancements / 可扩展性增强

- **Microservices Architecture**: Split into smaller, focused services
- **Event-Driven Architecture**: Asynchronous processing with events
- **CQRS**: Command Query Responsibility Segregation
- **Event Sourcing**: Track all state changes as events

### 2. Technology Evolution / 技术演进

- **Serverless Deployment**: AWS Lambda, Azure Functions
- **Edge Computing**: Deploy closer to users
- **AI/ML Integration**: Intelligent recommendations and automation
- **Advanced Analytics**: Business intelligence and reporting

### 3. Protocol Enhancements / 协议增强

- **MCP Protocol Extensions**: Custom tools and resources
- **Real-time Collaboration**: WebSocket-based collaboration
- **Advanced Security**: Zero-trust security model
- **Performance Optimization**: Protocol-level optimizations

---

**For more information**, see the [Solution Types Comparison](SOLUTION_TYPES.md) and [Protocol Implementation](PROTOCOL.md).