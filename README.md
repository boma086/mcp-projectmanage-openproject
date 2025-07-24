# OpenProject MCP 服务器

> 🎯 为Team Leader提供零技术门槛的项目报告生成工具

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-2024--11--05-green.svg)](https://modelcontextprotocol.io)

## 🚀 5分钟快速开始

### 1. 启动服务器
```bash
cd http-solution
source venv/bin/activate
python3 -m src.main
```

### 2. 打开模板编辑器
在浏览器中访问：**http://localhost:8010**

### 3. 开始使用
- 选择模板 → 输入项目ID → 生成预览 → 下载报告

**就这么简单！** 🎉

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

- **后端**: Python 3.13 + HTTP Server + MCP Protocol
- **模板引擎**: Jinja2 (支持变量、条件、循环)
- **前端**: HTML5 + CSS3 + Vanilla JavaScript
- **数据源**: OpenProject API
- **存储**: YAML配置文件

## 📦 安装和配置

### 环境要求
- Python 3.13+
- OpenProject实例
- 现代浏览器

### 配置步骤
```bash
# 1. 克隆项目
git clone <repository-url>
cd mcp-projectmanage-openproject

# 2. 配置环境
cd http-solution
cp .env.example .env
# 编辑 .env 文件，填入OpenProject配置

# 3. 安装依赖
source venv/bin/activate
pip install -r requirements.txt

# 4. 启动服务
python3 -m src.main
```

## 🧪 测试验证

```bash
# 测试基础功能
python3 ../tests/test_http_mcp_server.py

# 测试模板功能
python3 ../tests/test_http_template_features.py
```

**测试覆盖率**: 100% ✅

## 📚 详细文档

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

**立即开始使用**: `cd http-solution && python3 -m src.main` 然后访问 http://localhost:8010 🚀
