# API Reference - HTTP Solution

Complete API documentation for the HTTP MCP Solution, including all endpoints, request/response formats, and usage examples.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Base URLs and Endpoints](#base-urls-and-endpoints)
- [Common Response Formats](#common-response-formats)
- [Error Handling](#error-handling)
- [Core Endpoints](#core-endpoints)
- [Project Management API](#project-management-api)
- [Work Package Management API](#work-package-management-api)
- [User Management API](#user-management-api)
- [MCP Protocol API](#mcp-protocol-api)
- [Health and Monitoring](#health-and-monitoring)
- [Rate Limiting](#rate-limiting)
- [Examples](#examples)

## Overview

The HTTP Solution provides a RESTful API interface to OpenProject functionality through synchronous HTTP endpoints. All endpoints return JSON responses and support standard HTTP methods.

### API Characteristics

- **Protocol**: HTTP/1.1 and HTTP/2
- **Format**: JSON request/response
- **Authentication**: OpenProject API key (configured server-side)
- **Encoding**: UTF-8
- **CORS**: Configurable origins
- **Rate Limiting**: Configurable per endpoint

### Base URL

```
http://localhost:8010  # Development
https://your-domain.com  # Production
```

## Authentication

The HTTP Solution handles OpenProject authentication server-side using API keys. Client applications do not need to provide authentication headers for the MCP endpoints.

### Server Configuration

Authentication is configured via environment variables:

```bash
OPENPROJECT_URL=http://your-openproject-instance
OPENPROJECT_API_KEY=your_api_key_here
```

### API Key Validation

The server validates the OpenProject connection on startup and provides connection status via health endpoints.

## Base URLs and Endpoints

### Endpoint Categories

| Category | Base Path | Description |
|----------|-----------|-------------|
| Core | `/` | Service information and health |
| Projects | `/api/projects` | Project management operations |
| Work Packages | `/api/work-packages` | Work package CRUD operations |
| Users | `/api/users` | User information and management |
| MCP Protocol | `/mcp` | JSON-RPC MCP protocol endpoint |
| Documentation | `/docs`, `/redoc` | Interactive API documentation |

## Common Response Formats

### Success Response

```json
{
  "data": { /* response data */ },
  "status": "success",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Response

```json
{
  "error": {
    "code": 400,
    "message": "Validation error",
    "data": {
      "field": "project_id",
      "issue": "required field missing"
    }
  },
  "status": "error",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Pagination Response

```json
{
  "data": [ /* array of items */ ],
  "total": 150,
  "offset": 0,
  "limit": 50,
  "has_more": true
}
```

## Error Handling

### HTTP Status Codes

| Code | Description | Usage |
|------|-------------|-------|
| 200 | OK | Successful request |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | OpenProject authentication failed |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation errors |
| 500 | Internal Server Error | Server-side error |
| 502 | Bad Gateway | OpenProject connection error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Error Response Format

```json
{
  "error": {
    "code": -32603,
    "message": "Internal error",
    "data": "Detailed error information"
  }
}
```

## Core Endpoints

### Get Service Information

Get basic service information and available endpoints.

**Endpoint:** `GET /`

**Response:**

```json
{
  "name": "MCP OpenProject Server",
  "version": "1.0.0",
  "framework": "FastAPI (Synchronous Mode)",
  "solution": "HTTP",
  "status": "running",
  "endpoints": {
    "mcp": "/mcp",
    "health": "/health",
    "docs": "/docs",
    "redoc": "/redoc",
    "openapi": "/openapi.json",
    "projects": "/api/projects",
    "work_packages": "/api/work-packages",
    "users": "/api/users"
  },
  "features": [
    "Synchronous request-response pattern",
    "Simple REST API endpoints",
    "Minimal dependencies",
    "WSGI server deployment ready"
  ]
}
```

### Health Check

Check service health and component status.

**Endpoint:** `GET /health`

**Response:**

```json
{
  "status": "healthy",
  "services": {
    "mcp_handler": "ready",
    "openproject": "connected"
  },
  "config": {
    "openproject_url": "http://localhost:8090",
    "port": 8010,
    "log_level": "INFO"
  }
}
```

**Status Values:**
- `healthy`: All services operational
- `degraded`: Some services have issues
- `unhealthy`: Critical services down

## Project Management API

### List Projects

Retrieve all projects with pagination support.

**Endpoint:** `GET /api/projects`

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `offset` | integer | 0 | Number of projects to skip |
| `limit` | integer | 100 | Maximum projects to return (1-1000) |

**Example Request:**

```bash
curl -X GET "http://localhost:8010/api/projects?offset=0&limit=10" \
  -H "Accept: application/json"
```

**Response:**

```json
{
  "projects": [
    {
      "id": "1",
      "name": "Sample Project",
      "identifier": "sample-project",
      "description": "A sample project for demonstration",
      "status": "active",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1
}
```

### Get Project by ID

Retrieve specific project details.

**Endpoint:** `GET /api/projects/{project_id}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | string | The ID of the project |

**Example Request:**

```bash
curl -X GET "http://localhost:8010/api/projects/1" \
  -H "Accept: application/json"
```

**Response:**

```json
{
  "id": "1",
  "name": "Sample Project",
  "identifier": "sample-project",
  "description": "A sample project for demonstration",
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Generate Weekly Report

Generate a weekly report for a specific project.

**Endpoint:** `POST /api/projects/{project_id}/reports/weekly`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | string | The ID of the project |

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `start_date` | string | Start date (YYYY-MM-DD format) |
| `end_date` | string | End date (YYYY-MM-DD format) |

**Example Request:**

```bash
curl -X POST "http://localhost:8010/api/projects/1/reports/weekly?start_date=2024-01-01&end_date=2024-01-07" \
  -H "Accept: application/json"
```

**Response:**

```json
{
  "id": "report_12345",
  "title": "Weekly Report: Sample Project (2024-01-01 to 2024-01-07)",
  "content": "# Weekly Report\n\n## Summary\n...",
  "generated_at": "2024-01-15T10:30:00Z",
  "project_id": "1",
  "report_type": "weekly"
}
```

### Generate Monthly Report

Generate a monthly report for a specific project.

**Endpoint:** `POST /api/projects/{project_id}/reports/monthly`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | string | The ID of the project |

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `year` | integer | Year for the report |
| `month` | integer | Month for the report (1-12) |

**Example Request:**

```bash
curl -X POST "http://localhost:8010/api/projects/1/reports/monthly?year=2024&month=1" \
  -H "Accept: application/json"
```

**Response:**

```json
{
  "id": "report_12346",
  "title": "Monthly Report: Sample Project (January 2024)",
  "content": "# Monthly Report\n\n## Overview\n...",
  "generated_at": "2024-01-15T10:30:00Z",
  "project_id": "1",
  "report_type": "monthly"
}
```

### Generate Risk Assessment

Generate a risk assessment report for a specific project.

**Endpoint:** `POST /api/projects/{project_id}/reports/risk-assessment`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | string | The ID of the project |

**Example Request:**

```bash
curl -X POST "http://localhost:8010/api/projects/1/reports/risk-assessment" \
  -H "Accept: application/json"
```

**Response:**

```json
{
  "id": "report_12347",
  "title": "Risk Assessment: Sample Project",
  "content": "# Risk Assessment\n\n## Identified Risks\n...",
  "generated_at": "2024-01-15T10:30:00Z",
  "project_id": "1",
  "report_type": "risk_assessment"
}
```

## Work Package Management API

### List Work Packages

Retrieve work packages with optional project filtering.

**Endpoint:** `GET /api/work-packages`

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project_id` | string | null | Filter by project ID |
| `offset` | integer | 0 | Number of items to skip |
| `limit` | integer | 100 | Maximum items to return |
| `status` | string | null | Filter by status |
| `type` | string | null | Filter by type |
| `assigned_to` | string | null | Filter by assignee ID |

**Example Request:**

```bash
curl -X GET "http://localhost:8010/api/work-packages?project_id=1&limit=10" \
  -H "Accept: application/json"
```

**Response:**

```json
{
  "work_packages": [
    {
      "id": "101",
      "subject": "Sample Task",
      "description": "This is a sample task",
      "type": "Task",
      "status": "In Progress",
      "priority": "Normal",
      "project_id": "1",
      "assigned_to": "user_1",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-15T10:30:00Z",
      "due_date": "2024-01-20T00:00:00Z",
      "estimated_hours": 8.0,
      "spent_hours": 4.0
    }
  ],
  "total": 1
}
```

### Get Work Package by ID

Retrieve specific work package details.

**Endpoint:** `GET /api/work-packages/{work_package_id}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `work_package_id` | string | The ID of the work package |

**Example Request:**

```bash
curl -X GET "http://localhost:8010/api/work-packages/101" \
  -H "Accept: application/json"
```

**Response:**

```json
{
  "id": "101",
  "subject": "Sample Task",
  "description": "This is a sample task",
  "type": "Task",
  "status": "In Progress",
  "priority": "Normal",
  "project_id": "1",
  "assigned_to": "user_1",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "due_date": "2024-01-20T00:00:00Z",
  "estimated_hours": 8.0,
  "spent_hours": 4.0
}
```

### Create Work Package

Create a new work package.

**Endpoint:** `POST /api/work-packages`

**Request Body:**

```json
{
  "subject": "New Task",
  "description": "Description of the new task",
  "type": "Task",
  "project_id": "1",
  "assigned_to": "user_1",
  "priority": "High",
  "due_date": "2024-02-01T00:00:00Z",
  "estimated_hours": 16.0
}
```

**Example Request:**

```bash
curl -X POST "http://localhost:8010/api/work-packages" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "New Task",
    "description": "Description of the new task",
    "type": "Task",
    "project_id": "1"
  }'
```

**Response:**

```json
{
  "id": "102",
  "subject": "New Task",
  "description": "Description of the new task",
  "type": "Task",
  "status": "New",
  "priority": "Normal",
  "project_id": "1",
  "assigned_to": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "due_date": null,
  "estimated_hours": null,
  "spent_hours": 0.0
}
```

### Update Work Package

Update an existing work package.

**Endpoint:** `PUT /api/work-packages/{work_package_id}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `work_package_id` | string | The ID of the work package |

**Request Body:**

```json
{
  "subject": "Updated Task Title",
  "description": "Updated description",
  "status": "Closed",
  "assigned_to": "user_2",
  "spent_hours": 8.0
}
```

**Example Request:**

```bash
curl -X PUT "http://localhost:8010/api/work-packages/102" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Updated Task Title",
    "status": "Closed"
  }'
```

**Response:**

```json
{
  "id": "102",
  "subject": "Updated Task Title",
  "description": "Description of the new task",
  "type": "Task",
  "status": "Closed",
  "priority": "Normal",
  "project_id": "1",
  "assigned_to": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:31:00Z",
  "due_date": null,
  "estimated_hours": null,
  "spent_hours": 0.0
}
```

## User Management API

### List Users

Retrieve all users in the OpenProject instance.

**Endpoint:** `GET /api/users`

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `offset` | integer | 0 | Number of users to skip |
| `limit` | integer | 100 | Maximum users to return |
| `status` | string | null | Filter by status (active, locked, etc.) |

**Example Request:**

```bash
curl -X GET "http://localhost:8010/api/users?limit=10" \
  -H "Accept: application/json"
```

**Response:**

```json
{
  "users": [
    {
      "id": "1",
      "name": "John Doe",
      "email": "john.doe@example.com",
      "login": "john.doe",
      "first_name": "John",
      "last_name": "Doe",
      "status": "active",
      "admin": false,
      "avatar_url": "https://example.com/avatar.jpg",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1
}
```

### Get User by ID

Retrieve specific user details.

**Endpoint:** `GET /api/users/{user_id}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | string | The ID of the user |

**Example Request:**

```bash
curl -X GET "http://localhost:8010/api/users/1" \
  -H "Accept: application/json"
```

**Response:**

```json
{
  "id": "1",
  "name": "John Doe",
  "email": "john.doe@example.com",
  "login": "john.doe",
  "first_name": "John",
  "last_name": "Doe",
  "status": "active",
  "admin": false,
  "avatar_url": "https://example.com/avatar.jpg",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

## MCP Protocol API

### MCP JSON-RPC Endpoint

The main MCP protocol endpoint supporting JSON-RPC 2.0 format.

**Endpoint:** `POST /mcp`

**Content-Type:** `application/json`

### MCP Tool Calls

#### Get Projects Tool

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "get_projects",
    "arguments": {}
  }
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Found 1 project(s):\n\n1. Sample Project (ID: 1)\n   Status: active\n   Description: A sample project for demonstration"
      }
    ]
  }
}
```

#### Get Work Packages Tool

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "get_work_packages",
    "arguments": {
      "project_id": "1"
    }
  }
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Found 1 work package(s) in project 1:\n\n1. Sample Task (ID: 101)\n   Type: Task\n   Status: In Progress\n   Assigned to: user_1"
      }
    ]
  }
}
```

#### Generate Report Tool

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "generate_weekly_report",
    "arguments": {
      "project_id": "1",
      "start_date": "2024-01-01",
      "end_date": "2024-01-07"
    }
  }
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "# Weekly Report: Sample Project\n\n## Period: 2024-01-01 to 2024-01-07\n\n### Summary\n- Total work packages: 5\n- Completed: 2\n- In progress: 3\n\n### Details\n..."
      }
    ]
  }
}
```

### MCP Resource Access

#### List Resources

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "resources/list",
  "params": {}
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "resources": [
      {
        "uri": "openproject://projects",
        "name": "OpenProject Projects",
        "description": "List of all OpenProject projects",
        "mimeType": "application/json"
      },
      {
        "uri": "openproject://work-packages",
        "name": "OpenProject Work Packages",
        "description": "List of all work packages",
        "mimeType": "application/json"
      }
    ]
  }
}
```

#### Read Resource

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "resources/read",
  "params": {
    "uri": "openproject://projects"
  }
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "result": {
    "contents": [
      {
        "uri": "openproject://projects",
        "mimeType": "application/json",
        "text": "{\"projects\": [{\"id\": \"1\", \"name\": \"Sample Project\", ...}]}"
      }
    ]
  }
}
```

## Health and Monitoring

### Service Health Checks

#### Main Health Check

**Endpoint:** `GET /health`

**Response:**

```json
{
  "status": "healthy",
  "services": {
    "mcp_handler": "ready",
    "openproject": "connected"
  },
  "config": {
    "openproject_url": "http://localhost:8090",
    "port": 8010,
    "log_level": "INFO"
  }
}
```

#### Component Health Checks

**Projects Service:**

```bash
GET /api/projects/health
```

**Work Packages Service:**

```bash
GET /api/work-packages/health
```

**Users Service:**

```bash
GET /api/users/health
```

**Response Format:**

```json
{
  "status": "healthy",
  "service": "projects",
  "project_count": 5,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Rate Limiting

### Default Limits

| Endpoint Category | Requests per Minute | Burst Limit |
|-------------------|---------------------|-------------|
| Health checks | 300 | 20 |
| MCP protocol | 60 | 10 |
| API endpoints | 100 | 15 |
| Report generation | 10 | 3 |

### Rate Limit Headers

Rate limit information is included in response headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248600
```

### Rate Limit Exceeded Response

```json
{
  "error": {
    "code": 429,
    "message": "Rate limit exceeded",
    "data": {
      "limit": 100,
      "reset_time": "2024-01-15T10:31:00Z"
    }
  }
}
```

## Examples

### Complete Workflow Example

This example demonstrates a complete workflow: listing projects, creating a work package, and generating a report.

#### 1. List Projects

```bash
curl -X GET "http://localhost:8010/api/projects" \
  -H "Accept: application/json"
```

#### 2. Create Work Package

```bash
curl -X POST "http://localhost:8010/api/work-packages" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "API Integration Task",
    "description": "Implement new API endpoints",
    "type": "Task",
    "project_id": "1",
    "priority": "High",
    "estimated_hours": 16
  }'
```

#### 3. Generate Weekly Report

```bash
curl -X POST "http://localhost:8010/api/projects/1/reports/weekly?start_date=2024-01-08&end_date=2024-01-14" \
  -H "Accept: application/json"
```

### MCP Client Integration Example

```python
import requests
import json

class MCPClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
    
    def call_tool(self, tool_name, arguments):
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        response = self.session.post(
            f"{self.base_url}/mcp",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        return response.json()
    
    def get_projects(self):
        return self.call_tool("get_projects", {})
    
    def generate_report(self, project_id, start_date, end_date):
        return self.call_tool("generate_weekly_report", {
            "project_id": project_id,
            "start_date": start_date,
            "end_date": end_date
        })

# Usage
client = MCPClient("http://localhost:8010")
projects = client.get_projects()
print(json.dumps(projects, indent=2))
```

### Error Handling Example

```python
import requests

def safe_api_call(url, method="GET", **kwargs):
    try:
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("Authentication failed - check API key")
        elif e.response.status_code == 404:
            print("Resource not found")
        elif e.response.status_code == 503:
            print("Service unavailable - check OpenProject connection")
        else:
            print(f"HTTP error: {e.response.status_code}")
        return None
    except requests.exceptions.ConnectionError:
        print("Connection error - check server status")
        return None
    except requests.exceptions.Timeout:
        print("Request timeout")
        return None

# Usage
result = safe_api_call("http://localhost:8010/api/projects")
if result:
    print("Projects:", result)
```

## Interactive Documentation

The HTTP Solution provides interactive API documentation through Swagger UI and ReDoc:

- **Swagger UI**: `http://localhost:8010/docs`
- **ReDoc**: `http://localhost:8010/redoc`
- **OpenAPI Schema**: `http://localhost:8010/openapi.json`

These interfaces allow you to:
- Browse all available endpoints
- View request/response schemas
- Test API calls directly from the browser
- Download OpenAPI specifications

For additional examples and advanced usage patterns, refer to the test files in the repository and the main README.md.