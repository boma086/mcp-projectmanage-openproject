# FastAPI Web 服务集成问答指南

## 🤔 问题一：HTTP 方式和 FastAPI 方式有什么区别？

**Q: HTTP 解决方案是再自建一个服务吗？**

**A:** 是的！HTTP 解决方案是一个独立的服务，你需要：
1. 先启动 OpenProject MCP HTTP 服务（端口 8010）
2. 然后在你的 FastAPI 应用中通过 HTTP 调用它

**Q: FastAPI 解决方案呢？**

**A:** FastAPI 解决方案是作为库直接集成，你不需要启动独立服务，而是：
1. 安装 `mcp-core` 库到你的项目
2. 直接在代码中调用核心功能

## 🎯 方案对比总结

| 问题 | HTTP 解决方案 | FastAPI 解决方案 |
|------|---------------|------------------|
| 需要启动独立服务吗？ | ✅ 需要 | ❌ 不需要 |
| 通信方式？ | HTTP API 调用 | 直接函数调用 |
| 部署复杂度？ | 中等（两个服务） | 简单（一个服务） |
| 推荐场景？ | 生产环境、微服务 | 开发测试、单体应用 |

## 🔧 场景一：已有 FastAPI 服务，集成 HTTP 方式 MCP

### Q: 如何在我的 FastAPI 服务中集成 HTTP 方式的 MCP？

**A:** 你需要创建一个 HTTP 客户端来调用 MCP 服务：

```python
# 1. 安装依赖
# requirements.txt
httpx>=0.25.0
```

```python
# 2. 创建 MCP HTTP 客户端
# services/mcp_http_client.py
import httpx
from typing import Dict, Any

class MCPHttpClient:
    """HTTP 方式 MCP 客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8010"):
        self.base_url = base_url
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
            f"{self.base_url}/mcp",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        
        result = response.json()
        if "error" in result:
            raise Exception(f"MCP Error: {result['error']['message']}")
        
        return result["result"]
    
    async def generate_report(self, project_id: str, template_id: str = "japanese_weekly_report"):
        """生成报告"""
        return await self.call_tool("generate_report_from_template", {
            "template_id": template_id,
            "project_id": project_id
        })
    
    async def assess_risks(self, project_id: str):
        """评估风险"""
        return await self.call_tool("assess_project_risks", {
            "project_id": project_id
        })
    
    async def close(self):
        """关闭连接"""
        await self.client.aclose()
```

```python
# 3. 在 FastAPI 应用中集成
# main.py
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from services.mcp_http_client import MCPHttpClient

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时：初始化 MCP 客户端
    app.state.mcp_client = MCPHttpClient("http://localhost:8010")
    yield
    # 关闭时：清理资源
    await app.state.mcp_client.close()

app = FastAPI(lifespan=lifespan)

@app.get("/projects/{project_id}/report")
async def get_project_report(project_id: str):
    """获取项目报告"""
    try:
        client = app.state.mcp_client
        report = await client.generate_report(project_id)
        return {"success": True, "data": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成报告失败: {e}")

@app.get("/health/mcp")
async def check_mcp_health():
    """检查 MCP 服务健康状态"""
    try:
        # 简单的 ping 测试
        client = app.state.mcp_client
        await client.call_tool("ping", {})
        return {"status": "healthy", "service": "openproject_mcp"}
    except Exception:
        return {"status": "unhealthy", "service": "openproject_mcp"}
```

### 🚀 启动步骤（HTTP 方式）

1. **先启动 MCP HTTP 服务**：
```bash
cd solution-http
python -m src.main  # 启动在端口 8010
```

2. **然后启动你的 FastAPI 服务**：
```bash
python main.py  # 你的应用，比如端口 8000
```

3. **访问你的 API**：
```bash
curl http://localhost:8000/projects/1/report
```

## 🔄 场景二：已有 FastAPI 服务，集成 FastAPI 方式 MCP

### Q: 如何集成 FastAPI 方式的 MCP？

**A:** 你需要将 MCP 核心库作为依赖安装，然后直接调用：

```python
# 1. 安装核心库
# requirements.txt
# 添加这一行（假设 mcp-core 在上级目录）
-e ../mcp-core
```

```python
# 2. 直接集成核心功能
# services/mcp_direct_client.py
from mcp_core.infrastructure.openproject.client import OpenProjectClient
from mcp_core.domain.services.report_generator import ReportGeneratorService
from typing import Dict, Any

class MCPDirectClient:
    """直接集成方式的 MCP 客户端"""
    
    def __init__(self):
        self.openproject_client = OpenProjectClient()
        self.report_service = ReportGeneratorService(self.openproject_client)
    
    async def generate_weekly_report(self, project_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """直接生成周报"""
        report = await self.report_service.generate_weekly_report(project_id, start_date, end_date)
        return report.to_dict()  # 假设有 to_dict 方法
    
    async def assess_risks(self, project_id: str) -> Dict[str, Any]:
        """直接评估风险"""
        from mcp_core.domain.services.risk_assessor import RiskAssessorService
        risk_service = RiskAssessorService(self.openproject_client)
        return await risk_service.assess_project_risks(project_id)
```

```python
# 3. 在 FastAPI 应用中集成
# main.py
from fastapi import FastAPI, HTTPException
from services.mcp_direct_client import MCPDirectClient

app = FastAPI()

# 初始化客户端（不需要 lifespan，因为不需要清理网络连接）
mcp_client = MCPDirectClient()

@app.get("/projects/{project_id}/report")
async def get_project_report(project_id: str):
    """获取项目报告"""
    try:
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        report = await mcp_client.generate_weekly_report(project_id, start_date, end_date)
        return {"success": True, "data": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成报告失败: {e}")
```

### 🚀 启动步骤（FastAPI 方式）

1. **只需要启动你的 FastAPI 服务**：
```bash
python main.py  # 端口 8000
```

2. **不需要启动独立的 MCP 服务**！

3. **访问你的 API**：
```bash
curl http://localhost:8000/projects/1/report
```

## ❓ 常见问题解答

### Q: 我应该选择哪种方式？

**A:** 
- **选 HTTP 方式**如果：你要生产部署、需要服务隔离、已经熟悉微服务架构
- **选 FastAPI 方式**如果：你在开发测试、想要最简单集成、不介意耦合

### Q: 两种方式可以同时使用吗？

**A:** 技术上可以，但不推荐。选择一种方式并保持一致。

### Q: 性能差异大吗？

**A:** HTTP 方式有网络开销（约 10-50ms），FastAPI 方式几乎没有开销。但对于报告生成这种操作，网络开销通常可以忽略。

### Q: 如何切换方式？

**A:** 很简单！只需要：
1. 修改 `requirements.txt` 中的依赖
2. 替换客户端实现
3. 调整启动流程

## 🎯 推荐方案

**对于生产环境，推荐 HTTP 方式**，因为：
- ✅ 服务隔离，一个服务挂了不影响另一个
- ✅ 独立扩展，可以根据负载单独扩容
- ✅ 技术栈解耦，可以用不同语言开发
- ✅ 故障排查更容易

**对于开发环境，可以选择 FastAPI 方式**，因为：
- ✅ 启动简单，只需要一个命令
- ✅ 调试方便，没有网络环节
- ✅ 依赖更少，不需要管理多个服务

## 🔧 实战示例：从 HTTP 切换到 FastAPI 方式

如果你一开始用了 HTTP 方式，后来想切换到 FastAPI 方式：

```python
# 之前（HTTP 方式）
# from services.mcp_http_client import MCPHttpClient
# client = MCPHttpClient("http://localhost:8010")

# 之后（FastAPI 方式）
from services.mcp_direct_client import MCPDirectClient
client = MCPDirectClient()

# 接口保持不变！
report = await client.generate_report(project_id)
```

接口设计保持一致，切换成本很低！

---

**总结**: 
- HTTP 方式 = 独立服务 + HTTP 调用 = 推荐生产使用  
- FastAPI 方式 = 直接库调用 = 推荐开发使用
- 选择取决于你的架构偏好和部署需求