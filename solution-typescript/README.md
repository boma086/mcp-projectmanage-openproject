# TypeScript Solution - OpenProject MCP Server

A comprehensive TypeScript/Node.js implementation of the OpenProject MCP (Model Context Protocol) server with enterprise-grade monitoring and observability features.

## 🎯 Features

- **✅ Complete Implementation**: Fully functional MCP server with TypeScript
- **📊 Comprehensive Monitoring**: Prometheus metrics collection and visualization
- **🔍 Health Checks**: Liveness, readiness, and deep health checks
- **📝 Structured Logging**: JSON-formatted logs with correlation IDs
- **🔒 Security**: CORS, helmet, rate limiting, and input validation
- **🚀 Performance**: Connection pooling, caching, and optimized API calls
- **🧪 Testing**: Jest test suite with coverage reporting
- **🐳 Docker**: Multi-stage Docker build for production deployment
- **📈 Observability**: Unified monitoring architecture across all solutions

## 🏗️ Architecture

### Core Components

- **Express.js Server**: Fast HTTP server with middleware
- **MCP Protocol**: Full Model Context Protocol implementation
- **OpenProject Adapter**: Type-safe API client with monitoring
- **Monitoring System**: Prometheus metrics and health checks
- **Structured Logging**: Winston-based logging with correlation IDs

### Monitoring Features

- **Prometheus Metrics**: HTTP requests, MCP operations, OpenProject API calls
- **Health Checks**: Service health, OpenProject connectivity, resource usage
- **Node.js Metrics**: Memory usage, CPU usage, event loop metrics
- **Structured Logging**: JSON logs with request tracing
- **Correlation IDs**: Request tracking across the system

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- npm or yarn
- OpenProject instance with API access

### Installation

```bash
cd solution-typescript
npm install
cp .env.example .env
```

### Configuration

Edit `.env` file with your OpenProject configuration:

```bash
OPENPROJECT_URL=https://your-openproject.com
OPENPROJECT_API_KEY=your-api-key-here
PORT=8040
ENABLE_METRICS=true
LOG_LEVEL=info
```

### Development

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run tests
npm test

# Run tests with coverage
npm run test:coverage
```

### Docker Deployment

```bash
# Build Docker image
docker build -t openproject-mcp-typescript .

# Run container
docker run -p 8040:8040 \
  -e OPENPROJECT_URL=https://your-openproject.com \
  -e OPENPROJECT_API_KEY=your-api-key \
  openproject-mcp-typescript
```

## 📊 Monitoring

### Metrics Endpoint

Access Prometheus metrics at:
```
GET /metrics
```

### Health Checks

- **Liveness**: `GET /health/live`
- **Readiness**: `GET /health/ready`
- **Deep Health**: `GET /health?type=deep`

### Server Information

```
GET /info
```

### Node.js Metrics

```
GET /nodejs-metrics
```

## 🔧 API Usage

### MCP Endpoint

Send MCP requests to:
```
POST /mcp
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "list_projects",
  "params": {}
}
```

### Available Methods

- `list_projects` - List all projects
- `get_project` - Get project by ID
- `list_work_packages` - List work packages with filters
- `get_work_package` - Get work package by ID
- `create_work_package` - Create new work package
- `update_work_package` - Update existing work package
- `search_work_packages` - Search work packages
- `get_server_info` - Get server information

## 📁 Project Structure

```
solution-typescript/
├── src/
│   ├── adapters/              # External service adapters
│   │   └── openproject.ts     # OpenProject API adapter
│   ├── config/                # Configuration management
│   │   └── index.ts           # Main configuration
│   ├── monitoring/            # Monitoring and observability
│   │   ├── endpoints.ts       # Monitoring endpoints
│   │   ├── health.ts          # Health checks
│   │   ├── metrics.ts         # Prometheus metrics
│   │   └── middleware.ts      # Monitoring middleware
│   ├── services/              # Business logic services
│   │   └── mcp.ts             # MCP service implementation
│   ├── types/                 # TypeScript type definitions
│   │   └── index.ts           # Core types
│   ├── utils/                 # Utility functions
│   │   ├── correlation.ts     # Correlation ID management
│   │   └── logger.ts          # Structured logging
│   └── index.ts               # Main application entry
├── tests/                     # Test files
├── package.json               # Dependencies and scripts
├── tsconfig.json             # TypeScript configuration
├── jest.config.json          # Jest configuration
├── .eslintrc.json            # ESLint configuration
├── .prettierrc               # Prettier configuration
├── Dockerfile                # Docker configuration
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## 🔒 Security Features

- **Input Validation**: Express-validator for request validation
- **Rate Limiting**: Configurable request rate limits
- **CORS**: Configurable Cross-Origin Resource Sharing
- **Helmet**: Security headers for Express.js
- **Environment Variables**: Secure configuration management
- **Non-root User**: Docker runs as non-root user

## 📈 Performance Features

- **Connection Pooling**: Efficient OpenProject API connections
- **Caching**: Health check result caching
- **Compression**: Response compression for better performance
- **Metrics Collection**: Real-time performance monitoring
- **Correlation IDs**: Request tracing and debugging

## 🧪 Testing

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run linting
npm run lint

# Run type checking
npm run type-check

# Format code
npm run format
```

## 🔄 Integration with Monitoring Stack

This solution integrates seamlessly with the unified monitoring architecture:

### Prometheus Configuration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'typescript-mcp'
    static_configs:
      - targets: ['localhost:8040']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Grafana Dashboard

The solution exposes metrics that can be visualized in Grafana dashboards:

- HTTP request metrics
- MCP operation metrics
- OpenProject API metrics
- Node.js performance metrics
- Health check status

### Alerting

Configure alerts for:

- High error rates (> 5%)
- Slow response times (> 2s)
- Service unavailability
- OpenProject connection issues
- Resource exhaustion

## 🛠️ Development

### Adding New MCP Methods

1. Add method to `src/services/mcp.ts`
2. Add appropriate monitoring decorators
3. Update type definitions in `src/types/index.ts`
4. Add tests in `tests/mcp.test.ts`

### Adding New Metrics

1. Update `src/monitoring/metrics.ts`
2. Add metric collection in relevant services
3. Update monitoring documentation

### Adding New Health Checks

1. Update `src/monitoring/health.ts`
2. Add check to appropriate health check method
3. Update monitoring endpoints if needed

## 📋 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENPROJECT_URL` | OpenProject instance URL | Required |
| `OPENPROJECT_API_KEY` | OpenProject API key | Required |
| `PORT` | Server port | 8040 |
| `HOST` | Server host | 0.0.0.0 |
| `NODE_ENV` | Environment | development |
| `ENABLE_METRICS` | Enable metrics collection | true |
| `METRICS_PATH` | Metrics endpoint path | /metrics |
| `LOG_LEVEL` | Logging level | info |
| `STRUCTURED_LOGGING` | Enable structured logging | true |
| `CORRELATION_IDS` | Enable correlation IDs | true |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🔗 Related Solutions

- [HTTP Solution](../solution-http/) - Python/Flask implementation
- [FastAPI Solution](../solution-fastapi/) - Python/FastAPI implementation
- [FastMCP Solution](../solution-fastmcp/) - Python/FastMCP implementation

## 📞 Support

For issues and questions:
- Create an issue in the repository
- Check the monitoring documentation
- Review the unified monitoring architecture guide
