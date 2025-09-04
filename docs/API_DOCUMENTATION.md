# API Documentation

This comprehensive API documentation covers all endpoints, authentication methods, request/response formats, and integration examples for the OpenProject MCP integration solutions.

## Table of Contents

- [API Overview](#api-overview)
- [Authentication](#authentication)
- [Base URLs and Endpoints](#base-urls-and-endpoints)
- [HTTP Solution API](#http-solution-api)
- [FastAPI Solution API](#fastapi-solution-api)
- [FastMCP Solution API](#fastmcp-solution-api)
- [TypeScript Solution API](#typescript-solution-api)
- [Common Data Models](#common-data-models)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [WebSockets](#websockets)
- [Integration Examples](#integration-examples)
- [OpenAPI/Swagger Specifications](#openapi-swagger-specifications)

## API Overview

The OpenProject MCP integration provides multiple API solutions with different characteristics:

| Solution | Base URL | Protocol | Features | Best For |
|----------|----------|----------|----------|-----------|
| HTTP | `http://localhost:8010` | HTTP/1.1 | Synchronous, simple | Production deployments |
| FastAPI | `http://localhost:8020` | HTTP/1.1, HTTP/2 | Async, auto-docs | Development, API-first |
| FastMCP | `http://localhost:8030` | HTTP/1.1, SSE | MCP-native, streaming | Real-time updates |
| TypeScript | `http://localhost:8040` | HTTP/1.1, HTTP/2 | TypeScript SDK | Frontend integration |

## Authentication

### API Key Authentication

All solutions support API key authentication via the `Authorization` header:

```bash
curl -X GET "http://localhost:8010/api/projects" \
  -H "Authorization: Bearer your-api-key-here"
```

### OpenProject Authentication

The solutions use OpenProject API keys for backend authentication:

```python
# Environment configuration
OPENPROJECT_URL=https://your-openproject.com
OPENPROJECT_API_KEY=your-openproject-api-key
```

## Base URLs and Endpoints

### Common Endpoints

All solutions provide these common endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/metrics` | Application metrics |
| GET | `/version` | Version information |
| GET | `/config` | Current configuration |

### Solution-Specific Endpoints

| Solution | MCP Endpoint | Admin Endpoint | Reports Endpoint |
|----------|--------------|----------------|------------------|
| HTTP | `/mcp` | `/admin` | `/reports` |
| FastAPI | `/mcp` | `/admin` | `/reports` |
| FastMCP | `/mcp` | `/admin` | `/reports` |
| TypeScript | `/mcp` | `/admin` | `/reports` |

## HTTP Solution API

### OpenAPI 3.0 Specification

```yaml
openapi: 3.0.0
info:
  title: OpenProject MCP HTTP Server
  description: Production-ready HTTP MCP server for OpenProject integration
  version: 1.0.0
  contact:
    name: API Support
    email: support@example.com

servers:
  - url: http://localhost:8010
    description: Development server
  - url: https://api.example.com
    description: Production server

paths:
  /health:
    get:
      summary: Health Check
      description: Returns the health status of the server
      tags:
        - System
      responses:
        '200':
          description: Healthy
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: healthy
                  timestamp:
                    type: string
                    format: date-time
                  version:
                    type: string
                    example: 1.0.0

  /mcp:
    post:
      summary: MCP Request Handler
      description: Processes MCP protocol requests
      tags:
        - MCP
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MCPRequest'
      responses:
        '200':
          description: Successful MCP response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MCPResponse'
        '401':
          $ref: '#/components/responses/UnauthorizedError'
        '400':
          $ref: '#/components/responses/BadRequestError'

  /api/projects:
    get:
      summary: List Projects
      description: Retrieve a list of all projects
      tags:
        - Projects
      security:
        - bearerAuth: []
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: per_page
          in: query
          schema:
            type: integer
            default: 20
            maximum: 100
      responses:
        '200':
          description: List of projects
          content:
            application/json:
              schema:
                type: object
                properties:
                  projects:
                    type: array
                    items:
                      $ref: '#/components/schemas/Project'
                  total:
                    type: integer
                    example: 42
                  page:
                    type: integer
                    example: 1
                  per_page:
                    type: integer
                    example: 20

  /api/projects/{project_id}:
    get:
      summary: Get Project
      description: Retrieve a specific project by ID
      tags:
        - Projects
      security:
        - bearerAuth: []
      parameters:
        - name: project_id
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Project details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Project'
        '404':
          $ref: '#/components/responses/NotFoundError'

  /api/projects/{project_id}/work-packages:
    get:
      summary: List Work Packages
      description: Retrieve work packages for a project
      tags:
        - Work Packages
      security:
        - bearerAuth: []
      parameters:
        - name: project_id
          in: path
          required: true
          schema:
            type: integer
        - name: status
          in: query
          schema:
            type: string
            enum: [open, closed, all]
            default: open
      responses:
        '200':
          description: List of work packages
          content:
            application/json:
              schema:
                type: object
                properties:
                  work_packages:
                    type: array
                    items:
                      $ref: '#/components/schemas/WorkPackage'

  /reports/generate:
    post:
      summary: Generate Report
      description: Generate a project report
      tags:
        - Reports
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - project_id
                - report_type
              properties:
                project_id:
                  type: integer
                  description: Project ID
                report_type:
                  type: string
                  enum: [weekly, monthly, progress, risk]
                  description: Type of report to generate
                format:
                  type: string
                  enum: [json, html, pdf]
                  default: json
                template:
                  type: string
                  description: Custom template name
      responses:
        '200':
          description: Generated report
          content:
            application/json:
              schema:
                type: object
                properties:
                  report_id:
                    type: string
                    format: uuid
                  status:
                    type: string
                    example: completed
                  download_url:
                    type: string
                    format: uri
                  metadata:
                    type: object

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    MCPRequest:
      type: object
      required:
        - jsonrpc
        - method
        - params
        - id
      properties:
        jsonrpc:
          type: string
          example: "2.0"
        method:
          type: string
          example: "tools/call"
        params:
          type: object
          properties:
            name:
              type: string
              example: "get_projects"
            arguments:
              type: object
        id:
          type: string
          format: uuid

    MCPResponse:
      type: object
      properties:
        jsonrpc:
          type: string
          example: "2.0"
        result:
          type: object
        error:
          $ref: '#/components/schemas/MCPError'
        id:
          type: string
          format: uuid

    MCPError:
      type: object
      required:
        - code
        - message
      properties:
        code:
          type: integer
          example: -32601
        message:
          type: string
          example: "Method not found"
        data:
          type: object

    Project:
      type: object
      required:
        - id
        - name
        - identifier
      properties:
        id:
          type: integer
          example: 1
        name:
          type: string
          example: "Website Redesign"
        identifier:
          type: string
          example: "WEBSITE-001"
        description:
          type: string
          example: "Complete website redesign project"
        status:
          type: string
          enum: [on_track, at_risk, off_track]
          example: on_track
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time
        custom_fields:
          type: array
          items:
            $ref: '#/components/schemas/CustomField'

    WorkPackage:
      type: object
      required:
        - id
        - subject
        - type
      properties:
        id:
          type: integer
          example: 101
        subject:
          type: string
          example: "Design homepage layout"
        type:
          type: string
          example: "Task"
        description:
          type: string
          example: "Create responsive homepage design"
        status:
          type: string
          example: "In Progress"
        priority:
          type: string
          example: "High"
        assignee:
          $ref: '#/components/schemas/User'
        due_date:
          type: string
          format: date
        estimated_hours:
          type: number
          example: 8.0
        spent_hours:
          type: number
          example: 4.5

    User:
      type: object
      properties:
        id:
          type: integer
          example: 42
        name:
          type: string
          example: "John Doe"
        email:
          type: string
          format: email
          example: "john@example.com"
        avatar:
          type: string
          format: uri

    CustomField:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string
        value:
          type: string

  responses:
    BadRequestError:
      description: Bad request
      content:
        application/json:
          schema:
            type: object
            properties:
              error:
                type: string
                example: "Invalid request parameters"
              code:
                type: integer
                example: 400

    UnauthorizedError:
      description: Unauthorized
      content:
        application/json:
          schema:
            type: object
            properties:
              error:
                type: string
                example: "Invalid or missing authentication"
              code:
                type: integer
                example: 401

    NotFoundError:
      description: Resource not found
      content:
        application/json:
          schema:
            type: object
            properties:
              error:
                type: string
                example: "Project not found"
              code:
                type: integer
                example: 404
```

### Example Requests

#### Get Projects

```bash
curl -X GET "http://localhost:8010/api/projects?page=1&per_page=10" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json"
```

#### Generate Report

```bash
curl -X POST "http://localhost:8010/reports/generate" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "report_type": "weekly",
    "format": "html"
  }'
```

#### MCP Tool Call

```bash
curl -X POST "http://localhost:8010/mcp" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_projects",
      "arguments": {
        "limit": 10
      }
    },
    "id": "req-123"
  }'
```

## FastAPI Solution API

The FastAPI solution provides automatic OpenAPI documentation at `/docs` and `/redoc` endpoints.

### Interactive API Documentation

- **Swagger UI**: `http://localhost:8020/docs`
- **ReDoc**: `http://localhost:8020/redoc`
- **OpenAPI Schema**: `http://localhost:8020/openapi.json`

### Additional FastAPI Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/docs` | Interactive API documentation (Swagger UI) |
| GET | `/redoc` | Alternative API documentation (ReDoc) |
| GET | `/openapi.json` | OpenAPI specification |
| GET | `/admin/health` | Detailed health information |
| GET | `/admin/metrics` | Performance metrics |
| POST | `/admin/reload` | Reload configuration |

### WebSocket Endpoint

```python
# WebSocket connection for real-time updates
ws://localhost:8020/ws/{client_id}
```

### Example FastAPI Response

```json
{
  "jsonrpc": "2.0",
  "result": {
    "projects": [
      {
        "id": 1,
        "name": "Website Redesign",
        "identifier": "WEBSITE-001",
        "status": "on_track",
        "created_at": "2023-01-15T10:30:00Z",
        "updated_at": "2023-01-20T14:45:00Z",
        "work_packages_count": 15,
        "completed_work_packages": 8
      }
    ],
    "total": 1,
    "page": 1,
    "per_page": 20
  },
  "id": "req-123"
}
```

## FastMCP Solution API

The FastMCP solution implements the native MCP protocol with streaming support.

### MCP Protocol Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/mcp` | Standard MCP requests |
| GET | `/mcp/stream` | Server-Sent Events for streaming |
| GET | `/mcp/sse` | Alternative SSE endpoint |

### Streaming Response Example

```javascript
// Server-Sent Events stream
const eventSource = new EventSource('http://localhost:8030/mcp/stream');

eventSource.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('MCP Event:', data);
};

eventSource.addEventListener('project_update', function(event) {
  const project = JSON.parse(event.data);
  console.log('Project updated:', project.name);
});
```

### FastMCP Tool Schema

```json
{
  "name": "generate_report",
  "description": "Generate a comprehensive project report",
  "inputSchema": {
    "type": "object",
    "properties": {
      "project_id": {
        "type": "integer",
        "description": "Project identifier"
      },
      "report_type": {
        "type": "string",
        "enum": ["weekly", "monthly", "progress", "risk"],
        "description": "Type of report to generate"
      },
      "include_charts": {
        "type": "boolean",
        "default": true,
        "description": "Include charts and graphs"
      }
    },
    "required": ["project_id", "report_type"]
  }
}
```

## TypeScript Solution API

The TypeScript solution provides a type-safe SDK with comprehensive interfaces.

### TypeScript Interfaces

```typescript
// Core types
interface Project {
  id: number;
  name: string;
  identifier: string;
  description?: string;
  status: ProjectStatus;
  createdAt: Date;
  updatedAt: Date;
  workPackages: WorkPackage[];
}

interface WorkPackage {
  id: number;
  subject: string;
  type: WorkPackageType;
  description?: string;
  status: WorkPackageStatus;
  priority: Priority;
  assignee?: User;
  dueDate?: Date;
  estimatedHours?: number;
  spentHours?: number;
}

// API Client
class OpenProjectMCPClient {
  constructor(
    private baseUrl: string,
    private apiKey: string
  ) {}

  async getProjects(params?: GetProjectsParams): Promise<Project[]> {
    const response = await fetch(`${this.baseUrl}/api/projects`, {
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  }

  async generateReport(request: ReportRequest): Promise<ReportResponse> {
    const response = await fetch(`${this.baseUrl}/reports/generate`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(request)
    });
    
    return response.json();
  }
}
```

### Example Usage

```typescript
// Initialize client
const client = new OpenProjectMCPClient(
  'http://localhost:8040',
  'your-api-key'
);

// Get projects
const projects = await client.getProjects({
  page: 1,
  perPage: 10,
  status: 'active'
});

// Generate report
const report = await client.generateReport({
  projectId: 1,
  reportType: 'weekly',
  format: 'html'
});

console.log('Generated report:', report.downloadUrl);
```

## Common Data Models

### Project Status

| Status | Description |
|--------|-------------|
| `on_track` | Project is progressing as planned |
| `at_risk` | Project has some issues but can recover |
| `off_track` | Project is significantly behind |

### Work Package Types

| Type | Description |
|------|-------------|
| `Task` | General task item |
| `Feature` | New feature development |
| `Bug` | Bug fix |
| `Epic` | Large feature group |
| `User Story` | User requirement |

### Priority Levels

| Priority | Description |
|----------|-------------|
| `Low` | Low priority |
| `Normal` | Normal priority |
| `High` | High priority |
| `Urgent` | Urgent priority |

## Error Handling

### Standard Error Response

```json
{
  "error": {
    "code": 400,
    "message": "Invalid request parameters",
    "details": {
      "field": "project_id",
      "issue": "must be a positive integer"
    }
  },
  "timestamp": "2023-01-20T10:30:00Z",
  "request_id": "req-123"
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| -32700 | 400 | Parse error |
| -32600 | 400 | Invalid Request |
| -32601 | 404 | Method not found |
| -32602 | 400 | Invalid params |
| -32603 | 500 | Internal error |
| -32001 | 401 | Unauthorized |
| -32002 | 403 | Forbidden |
| -32003 | 404 | Not found |
| -32004 | 429 | Rate limit exceeded |

## Rate Limiting

### Rate Limit Headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642694400
Retry-After: 60
```

### Rate Limits by Plan

| Plan | Requests/Minute | Burst | Features |
|------|-----------------|-------|----------|
| Free | 60 | 10 | Basic access |
| Pro | 1000 | 100 | All features |
| Enterprise | Unlimited | 1000 | Priority support |

## WebSockets

### Connection Example

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8020/ws/client-123');

ws.onopen = function(event) {
  console.log('WebSocket connected');
  
  // Subscribe to project updates
  ws.send(JSON.stringify({
    type: 'subscribe',
    channel: 'project_updates',
    project_id: 1
  }));
};

ws.onmessage = function(event) {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};

ws.onclose = function(event) {
  console.log('WebSocket disconnected');
};
```

### WebSocket Events

| Event | Description |
|-------|-------------|
| `project_update` | Project information updated |
| `work_package_created` | New work package created |
| `work_package_updated` | Work package modified |
| `report_generated` | Report generation completed |

## Integration Examples

### Python Integration

```python
import requests
import json

class OpenProjectMCPClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def get_projects(self, page=1, per_page=20):
        """Get list of projects"""
        url = f"{self.base_url}/api/projects"
        params = {'page': page, 'per_page': per_page}
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def generate_report(self, project_id, report_type, format='json'):
        """Generate project report"""
        url = f"{self.base_url}/reports/generate"
        data = {
            'project_id': project_id,
            'report_type': report_type,
            'format': format
        }
        
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

# Usage
client = OpenProjectMCPClient('http://localhost:8010', 'your-api-key')
projects = client.get_projects()
report = client.generate_report(1, 'weekly', 'html')
```

### JavaScript Integration

```javascript
class OpenProjectMCPClient {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
        this.headers = {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        };
    }

    async getProjects(params = {}) {
        const url = new URL(`${this.baseUrl}/api/projects`);
        Object.entries(params).forEach(([key, value]) => {
            url.searchParams.append(key, value);
        });

        const response = await fetch(url, {
            headers: this.headers
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return response.json();
    }

    async generateReport(projectId, reportType, format = 'json') {
        const response = await fetch(`${this.baseUrl}/reports/generate`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({
                project_id: projectId,
                report_type: reportType,
                format: format
            })
        });

        return response.json();
    }
}

// Usage
const client = new OpenProjectMCPClient('http://localhost:8010', 'your-api-key');
const projects = await client.getProjects({ page: 1, per_page: 10 });
const report = await client.generateReport(1, 'weekly', 'html');
```

### cURL Examples

```bash
# Health check
curl -X GET "http://localhost:8010/health"

# Get projects with pagination
curl -X GET "http://localhost:8010/api/projects?page=1&per_page=5" \
  -H "Authorization: Bearer your-api-key"

# Generate PDF report
curl -X POST "http://localhost:8010/reports/generate" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "report_type": "monthly",
    "format": "pdf"
  }'

# MCP tool call
curl -X POST "http://localhost:8010/mcp" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_project_work_packages",
      "arguments": {
        "project_id": 1,
        "status": "open"
      }
    },
    "id": "req-456"
  }'
```

## OpenAPI/Swagger Specifications

### Download OpenAPI Specs

| Solution | URL |
|----------|-----|
| HTTP | `http://localhost:8010/openapi.yaml` |
| FastAPI | `http://localhost:8020/openapi.json` |
| FastMCP | `http://localhost:8030/openapi.yaml` |
| TypeScript | `http://localhost:8040/openapi.json` |

### Generate Client SDKs

```bash
# Using OpenAPI Generator
docker run --rm \
  -v "${PWD}:/local" \
  openapitools/openapi-generator-cli generate \
  -i http://localhost:8020/openapi.json \
  -g python \
  -o /local/python-client

# Generate TypeScript client
docker run --rm \
  -v "${PWD}:/local" \
  openapitools/openapi-generator-cli generate \
  -i http://localhost:8020/openapi.json \
  -g typescript-axios \
  -o /local/typescript-client
```

### API Testing with Postman

1. Import OpenAPI specification:
   ```
   File → Import → Link
   Enter: http://localhost:8020/openapi.json
   ```

2. Set up environment variables:
   ```json
   {
     "base_url": "http://localhost:8020",
     "api_key": "your-api-key"
   }
   ```

3. Use pre-request script:
   ```javascript
   pm.request.headers.add({
     key: 'Authorization',
     value: `Bearer ${pm.environment.get('api_key')}`
   });
   ```

### API Documentation Tools

- **Swagger UI**: Interactive API documentation
- **ReDoc**: Clean, responsive documentation
- **Postman**: API testing and collection sharing
- **Insomnia**: Modern API client with GraphQL support
- **Stoplight**: API design and documentation platform

This comprehensive API documentation provides all the information needed to integrate with any of the OpenProject MCP solutions. Each solution maintains compatibility while offering unique features optimized for different use cases.