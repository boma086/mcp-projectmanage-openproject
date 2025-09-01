# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🏗️ Architecture Overview

### Multi-Solution Architecture
This repository contains three distinct solutions for OpenProject MCP integration:

1. **HTTP Solution** (`solution-http/`) - Production-ready synchronous implementation
2. **FastAPI Solution** (`solution-fastapi/`) - Development-focused async implementation with API docs
3. **FastMCP Solution** - Experimental MCP-native implementation

### Core Library (`mcp-core/`)
Shared domain logic and MCP protocol implementation:
- **Domain Models**: Project, WorkPackage, Report, User
- **Services**: ReportGenerator, RiskAssessor, WorkloadAnalyzer, HealthChecker
- **MCP Handler**: Protocol implementation with tools and resources
- **Templates**: Japanese-style report templates (weekly, monthly, progress)

### Key Dependencies
- **MCP Core**: Custom library with domain logic
- **FastAPI/HTTP**: Web framework choices
- **OpenProject**: External API integration via adapters
- **Jinja2**: Template rendering for reports

## 🚀 Development Commands

### Environment Setup
```bash
# For FastAPI solution (recommended for development)
cd solution-fastapi
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e ../mcp-core

# For HTTP solution (production)
cd solution-http
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e ../mcp-core
```

### Service Startup
```bash
# FastAPI solution (port 8020)
cd solution-fastapi && python app/main.py

# HTTP solution (port 8010) 
cd solution-http && python -m src.main
```

### Testing
```bash
# Run core library tests
cd mcp-core && python -m pytest tests/ -v

# Run enhanced report test
python test_enhanced_report.py

# Run specific test file
python -m pytest path/to/test_file.py -v
```

### Code Quality
```bash
# Format code with black
cd mcp-core && python -m black src/

# Type checking with mypy
cd mcp-core && python -m mypy src/

# Lint with ruff
cd mcp-core && python -m ruff check src/
```

## 📁 Key File Locations

### Core Library (`mcp-core/src/mcp_core/`)
- `application/mcp/tools.py` - MCP tool implementations
- `domain/models/` - Data models (Project, WorkPackage, Report)
- `domain/services/` - Business logic services
- `templates/reports/` - Report template definitions

### FastAPI Solution (`solution-fastapi/app/`)
- `main.py` - FastAPI application entry point
- `adapters/async_openproject_adapter.py` - Async OpenProject client
- `services/enhanced_report_generator.py` - Enhanced reporting service
- `core/mcp_handler.py` - MCP protocol adapter

### HTTP Solution (`solution-http/src/`)
- `main.py` - HTTP server entry point
- `adapters/openproject_adapter.py` - Sync OpenProject client

## 🔧 Configuration

### Environment Variables
Required in `.env` file for both solutions:
```bash
OPENPROJECT_URL=https://your-openproject.com
OPENPROJECT_API_KEY=your-api-key-here
PORT=8010  # or 8020 for FastAPI
LOG_LEVEL=INFO
```

### MCP Integration
For Claude Desktop configuration:
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

## 🎯 Common Development Tasks

### Adding New MCP Tools
1. Define tool in `mcp-core/application/mcp/tools.py`
2. Implement service logic in `mcp-core/domain/services/`
3. Add adapter method if needed
4. Update both solution handlers

### Creating Report Templates
1. Add YAML template to `mcp-core/templates/reports/`
2. Implement template rendering in report services
3. Add i18n support in `solution-fastapi/app/i18n/`

### Testing Patterns
- Use `test_enhanced_report.py` as reference for integration tests
- Mock OpenProject client for unit tests
- Follow pytest patterns from mcp-core configuration

## ⚠️ Important Notes

- **Port Conflicts**: HTTP=8010, FastAPI=8020 - check for conflicts
- **Dependency Management**: Always install mcp-core in development mode
- **Async vs Sync**: Choose appropriate solution based on use case
- **Template System**: Supports Japanese-style business reports with i18n
- **Error Handling**: Uses custom MCPError exceptions throughout

## 🔍 Debugging

VS Code launch configuration available in `.vscode/launch.json`:
- FastAPI debugging with breakpoints
- Automatic virtual environment detection
- Integrated terminal support