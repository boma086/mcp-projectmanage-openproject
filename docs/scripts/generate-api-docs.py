#!/usr/bin/env python3
"""
Script to generate API documentation from OpenAPI specifications
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any
import subprocess

def generate_fastapi_docs():
    """Generate FastAPI API documentation"""
    print("Generating FastAPI API documentation...")
    
    # Generate OpenAPI spec
    try:
        result = subprocess.run([
            'curl', '-s', 'http://localhost:8020/openapi.json'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            openapi_spec = json.loads(result.stdout)
            
            # Save to docs directory
            output_path = Path('docs/api/fastapi-openapi.json')
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(openapi_spec, f, indent=2)
            
            print(f"✅ FastAPI OpenAPI spec saved to {output_path}")
        else:
            print(f"⚠️  Could not fetch FastAPI OpenAPI spec: {result.stderr}")
    except Exception as e:
        print(f"⚠️  Error generating FastAPI docs: {e}")

def generate_http_docs():
    """Generate HTTP solution API documentation"""
    print("Generating HTTP solution API documentation...")
    
    # Convert YAML to JSON for HTTP solution
    yaml_path = Path('docs/API_DOCUMENTATION.md')
    
    if yaml_path.exists():
        # Extract OpenAPI spec from documentation
        with open(yaml_path, 'r') as f:
            content = f.read()
        
        # Find YAML block (simplified approach)
        yaml_start = content.find('```yaml')
        yaml_end = content.find('```', yaml_start + 6)
        
        if yaml_start != -1 and yaml_end != -1:
            yaml_content = content[yaml_start + 7:yaml_end]
            
            try:
                openapi_spec = yaml.safe_load(yaml_content)
                
                # Save to docs directory
                output_path = Path('docs/api/http-openapi.json')
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'w') as f:
                    json.dump(openapi_spec, f, indent=2)
                
                print(f"✅ HTTP OpenAPI spec saved to {output_path}")
            except Exception as e:
                print(f"⚠️  Error parsing HTTP OpenAPI spec: {e}")
        else:
            print("⚠️  Could not find OpenAPI spec in HTTP documentation")

def generate_api_reference():
    """Generate API reference documentation"""
    print("Generating API reference documentation...")
    
    api_ref_content = """# API Reference

This section provides comprehensive API reference documentation for all OpenProject MCP integration solutions.

## Authentication

All API endpoints require authentication using Bearer tokens:

```bash
curl -H "Authorization: Bearer your-api-key" http://localhost:8010/api/projects
```

## Base URLs

| Solution | Base URL | Port |
|----------|----------|------|
| HTTP | `http://localhost:8010` | 8010 |
| FastAPI | `http://localhost:8020` | 8020 |
| FastMCP | `http://localhost:8030` | 8030 |
| TypeScript | `http://localhost:8040` | 8040 |

## Common Endpoints

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2023-01-20T10:30:00Z",
  "version": "1.0.0"
}
```

### Version

```http
GET /version
```

**Response:**
```json
{
  "version": "1.0.0",
  "build": "abc123",
  "timestamp": "2023-01-20T10:30:00Z"
}
```

## MCP Protocol

### Tool Call

```http
POST /mcp
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "get_projects",
    "arguments": {
      "limit": 10
    }
  },
  "id": "req-123"
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "projects": [
      {
        "id": 1,
        "name": "Example Project",
        "identifier": "EX-001"
      }
    ]
  },
  "id": "req-123"
}
```

## Project Management

### Get Projects

```http
GET /api/projects
```

**Parameters:**
- `page` (integer): Page number (default: 1)
- `per_page` (integer): Items per page (default: 20)
- `status` (string): Filter by status

**Response:**
```json
{
  "projects": [
    {
      "id": 1,
      "name": "Website Redesign",
      "identifier": "WEB-001",
      "status": "on_track",
      "created_at": "2023-01-15T10:30:00Z",
      "updated_at": "2023-01-20T14:45:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20
}
```

### Get Project

```http
GET /api/projects/{project_id}
```

**Response:**
```json
{
  "id": 1,
  "name": "Website Redesign",
  "identifier": "WEB-001",
  "description": "Complete website redesign project",
  "status": "on_track",
  "created_at": "2023-01-15T10:30:00Z",
  "updated_at": "2023-01-20T14:45:00Z",
  "custom_fields": []
}
```

## Work Package Management

### Get Work Packages

```http
GET /api/projects/{project_id}/work-packages
```

**Parameters:**
- `status` (string): Filter by status (open, closed, all)
- `type` (string): Filter by type
- `assignee` (integer): Filter by assignee ID

**Response:**
```json
{
  "work_packages": [
    {
      "id": 101,
      "subject": "Design homepage layout",
      "type": "Task",
      "description": "Create responsive homepage design",
      "status": "In Progress",
      "priority": "High",
      "assignee": {
        "id": 42,
        "name": "John Doe",
        "email": "john@example.com"
      },
      "due_date": "2023-02-01",
      "estimated_hours": 8.0,
      "spent_hours": 4.5
    }
  ]
}
```

## Report Generation

### Generate Report

```http
POST /reports/generate
Content-Type: application/json

{
  "project_id": 1,
  "report_type": "weekly",
  "format": "html"
}
```

**Parameters:**
- `project_id` (integer, required): Project ID
- `report_type` (string, required): weekly, monthly, progress, risk
- `format` (string, optional): json, html, pdf (default: json)
- `template` (string, optional): Custom template name

**Response:**
```json
{
  "report_id": "report-123",
  "status": "completed",
  "download_url": "/reports/download/report-123",
  "metadata": {
    "project_id": 1,
    "report_type": "weekly",
    "format": "html",
    "generated_at": "2023-01-20T10:30:00Z"
  }
}
```

## Error Handling

All endpoints return appropriate HTTP status codes and error messages:

### Error Response Format

```json
{
  "error": {
    "code": 404,
    "message": "Project not found",
    "details": {
      "project_id": 999
    }
  },
  "timestamp": "2023-01-20T10:30:00Z",
  "request_id": "req-456"
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 429 | Rate Limited |
| 500 | Internal Server Error |

## Rate Limiting

API endpoints are rate limited to prevent abuse:

- **Free tier**: 60 requests per minute
- **Pro tier**: 1000 requests per minute
- **Enterprise**: Unlimited

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642694400
```

## WebSockets

Real-time updates are available via WebSocket connections:

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8020/ws/client-123');
```

### Events

- `project_update`: Project information updated
- `work_package_created`: New work package created
- `work_package_updated`: Work package modified
- `report_generated`: Report generation completed

## SDK Examples

### Python

```python
import requests

class OpenProjectMCPClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def get_projects(self):
        response = requests.get(
            f'{self.base_url}/api/projects',
            headers=self.headers
        )
        return response.json()
```

### JavaScript

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
    
    async getProjects() {
        const response = await fetch(
            `${this.baseUrl}/api/projects`,
            { headers: this.headers }
        );
        return response.json();
    }
}
```

### TypeScript

```typescript
interface Project {
    id: number;
    name: string;
    identifier: string;
    status: string;
}

class OpenProjectMCPClient {
    constructor(
        private baseUrl: string,
        private apiKey: string
    ) {}
    
    async getProjects(): Promise<Project[]> {
        const response = await fetch(
            `${this.baseUrl}/api/projects`,
            {
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`,
                    'Content-Type': 'application/json'
                }
            }
        );
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return response.json();
    }
}
```

## OpenAPI Specifications

Complete OpenAPI specifications are available:

- [HTTP Solution](api/http-openapi.json)
- [FastAPI Solution](api/fastapi-openapi.json)

These can be used with API documentation tools like:
- Swagger UI
- Postman
- Insomnia
- OpenAPI Generator
"""
    
    output_path = Path('docs/reference/api-reference.md')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(api_ref_content)
    
    print(f"✅ API reference documentation saved to {output_path}")

def main():
    """Main function to generate all API documentation"""
    print("🚀 Starting API documentation generation...")
    
    # Create necessary directories
    Path('docs/api').mkdir(parents=True, exist_ok=True)
    Path('docs/reference').mkdir(parents=True, exist_ok=True)
    
    # Generate documentation
    generate_fastapi_docs()
    generate_http_docs()
    generate_api_reference()
    
    print("✅ API documentation generation completed!")

if __name__ == '__main__':
    main()