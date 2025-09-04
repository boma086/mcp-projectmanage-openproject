# Comprehensive Deployment Guide

This guide provides detailed deployment instructions for all four solution types in the OpenProject MCP integration project, covering local development, containerized, cloud, and production deployments.

## 📋 Table of Contents

1. [Deployment Overview](#deployment-overview)
2. [Solution-Specific Deployment](#solution-specific-deployment)
3. [Local Development Deployment](#local-development-deployment)
4. [Containerized Deployment](#containerized-deployment)
5. [Cloud Deployment](#cloud-deployment)
6. [Production Deployment](#production-deployment)
7. [High Availability Deployment](#high-availability-deployment)
8. [Monitoring and Observability](#monitoring-and-observability)
9. [Security and Compliance](#security-and-compliance)
10. [Backup and Recovery](#backup-and-recovery)
11. [Troubleshooting](#troubleshooting)

## 🚀 Deployment Overview

### Deployment Matrix

| Solution | Local Dev | Docker | Kubernetes | Cloud | Production Ready |
|----------|-----------|--------|------------|-------|------------------|
| **HTTP Solution** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **FastAPI Solution** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **FastMCP Solution** | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| **TypeScript Solution** | ✅ | ✅ | ✅ | ✅ | ✅ |

### Deployment Requirements

#### Minimum Requirements
- **CPU**: 2 cores
- **Memory**: 4GB RAM
- **Storage**: 20GB disk
- **Network**: 1Gbps
- **OS**: Linux (Ubuntu 20.04+), macOS, Windows

#### Recommended Requirements
- **CPU**: 4+ cores
- **Memory**: 8GB+ RAM
- **Storage**: 50GB+ SSD
- **Network**: 1Gbps+
- **OS**: Ubuntu 22.04 LTS

### Environment Variables

All solutions require these core environment variables:

```bash
# OpenProject Configuration
OPENPROJECT_URL=http://localhost:8090
OPENPROJECT_API_KEY=your-api-key-here

# Server Configuration
HOST=0.0.0.0
LOG_LEVEL=INFO

# Security
CORS_ALLOW_ORIGINS=http://localhost,http://127.0.0.1
```

## 🌐 HTTP Solution Deployment

### Quick Start

```bash
# Navigate to HTTP solution
cd solution-http

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start development server
python src/main.py
```

### Production Deployment

#### Method 1: Gunicorn

```bash
# Install production dependencies
pip install -r requirements.txt gunicorn

# Set production environment
export ENVIRONMENT=production
export LOG_LEVEL=INFO

# Start with Gunicorn
gunicorn --config gunicorn.conf.py src.main:app
```

#### Method 2: Systemd Service

Create `/etc/systemd/system/mcp-http.service`:

```ini
[Unit]
Description=MCP HTTP Server
After=network.target

[Service]
Type=exec
User=mcpuser
Group=mcpuser
WorkingDirectory=/opt/mcp-http
Environment=PATH=/opt/mcp-http/venv/bin
EnvironmentFile=/opt/mcp-http/.env
ExecStart=/opt/mcp-http/venv/bin/gunicorn --config gunicorn.conf.py src.main:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable mcp-http
sudo systemctl start mcp-http
```

### Docker Deployment

```bash
# Build image
docker build -t mcp-http-server .

# Run container
docker run -d \
  --name mcp-http \
  --restart unless-stopped \
  -p 8010:8010 \
  -e OPENPROJECT_URL=http://your-openproject \
  -e OPENPROJECT_API_KEY=your-key \
  mcp-http-server
```

### Docker Compose Deployment

```yaml
# docker-compose.yml
version: '3.8'

services:
  mcp-http:
    build: ./solution-http
    restart: unless-stopped
    ports:
      - "8010:8010"
    environment:
      - OPENPROJECT_URL=http://openproject:8080
      - OPENPROJECT_API_KEY=demo-api-key
    depends_on:
      - openproject
    networks:
      - mcp-network

  openproject:
    image: openproject/community:latest
    ports:
      - "8090:8080"
    environment:
      - OPENPROJECT_SECRET_KEY_BASE=secret
    volumes:
      - openproject_data:/var/lib/openproject
    networks:
      - mcp-network

networks:
  mcp-network:
    driver: bridge

volumes:
  openproject_data:
```

Deploy:

```bash
docker-compose up -d
```

### Kubernetes Deployment

Create `k8s/http-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-http-server
  labels:
    app: mcp-http
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-http
  template:
    metadata:
      labels:
        app: mcp-http
    spec:
      containers:
      - name: mcp-http
        image: mcp-http-server:latest
        ports:
        - containerPort: 8010
        env:
        - name: OPENPROJECT_URL
          valueFrom:
            configMapKeyRef:
              name: mcp-http-config
              key: openproject-url
        - name: OPENPROJECT_API_KEY
          valueFrom:
            secretKeyRef:
              name: mcp-http-secrets
              key: openproject-api-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-http-service
spec:
  selector:
    app: mcp-http
  ports:
  - protocol: TCP
    port: 8010
    targetPort: 8010
  type: LoadBalancer
```

Deploy to Kubernetes:

```bash
kubectl apply -f k8s/http-deployment.yaml
```

## 🚀 FastAPI Solution Deployment

### Quick Start

```bash
# Navigate to FastAPI solution
cd solution-fastapi

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Deployment

#### Method 1: Uvicorn with Multiple Workers

```bash
# Install production dependencies
pip install -r requirements.txt

# Start with multiple workers
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8020 \
  --workers 4 \
  --log-level info \
  --access-log \
  --proxy-headers
```

#### Method 2: Gunicorn with Uvicorn Workers

```bash
# Start with Gunicorn
gunicorn app.main:app \
  --bind 0.0.0.0:8020 \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --timeout 30 \
  --keep-alive 2 \
  --max-requests 1000 \
  --max-requests-jitter 50
```

### Docker Deployment

```dockerfile
# solution-fastapi/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8020

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8020/health || exit 1

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8020"]
```

Build and run:

```bash
# Build image
docker build -t fastapi-mcp-server .

# Run container
docker run -d \
  --name fastapi-mcp \
  --restart unless-stopped \
  -p 8020:8020 \
  -e OPENPROJECT_URL=http://your-openproject \
  -e OPENPROJECT_API_KEY=your-key \
  fastapi-mcp-server
```

### Docker Compose with Monitoring

```yaml
# solution-fastapi/docker-compose.yml
version: '3.8'

services:
  fastapi-mcp:
    build: .
    restart: unless-stopped
    ports:
      - "8020:8020"
    environment:
      - OPENPROJECT_URL=http://openproject:8080
      - OPENPROJECT_API_KEY=demo-api-key
      - REDIS_URL=redis://redis:6379
    depends_on:
      - openproject
      - redis
    networks:
      - mcp-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8020/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - mcp-network
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    networks:
      - mcp-network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - mcp-network
    restart: unless-stopped

  openproject:
    image: openproject/community:latest
    ports:
      - "8090:8080"
    environment:
      - OPENPROJECT_SECRET_KEY_BASE=secret
    volumes:
      - openproject_data:/var/lib/openproject
    networks:
      - mcp-network

networks:
  mcp-network:
    driver: bridge

volumes:
  grafana_data:
  openproject_data:
```

### Kubernetes Deployment with Auto-scaling

```yaml
# k8s/fastapi-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-mcp-server
  labels:
    app: fastapi-mcp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastapi-mcp
  template:
    metadata:
      labels:
        app: fastapi-mcp
    spec:
      containers:
      - name: fastapi-mcp
        image: fastapi-mcp-server:latest
        ports:
        - containerPort: 8020
        env:
        - name: OPENPROJECT_URL
          valueFrom:
            configMapKeyRef:
              name: fastapi-mcp-config
              key: openproject-url
        - name: OPENPROJECT_API_KEY
          valueFrom:
            secretKeyRef:
              name: fastapi-mcp-secrets
              key: openproject-api-key
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8020
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8020
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: fastapi-mcp-service
spec:
  selector:
    app: fastapi-mcp
  ports:
  - protocol: TCP
    port: 8020
    targetPort: 8020
  type: LoadBalancer
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fastapi-mcp-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fastapi-mcp-server
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## ⚡ FastMCP Solution Deployment

### Quick Start

```bash
# Navigate to FastMCP solution
cd solution-fastmcp

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start server
python main.py
```

### Production Deployment

#### Method 1: Direct Execution

```bash
# Install dependencies
pip install -r requirements.txt

# Set production environment
export ENVIRONMENT=production
export LOG_LEVEL=INFO

# Start server
python main.py
```

#### Method 2: Process Manager (PM2)

```bash
# Install PM2
npm install -g pm2

# Start with PM2
pm2 start main.py --name "fastmcp-server" \
  --interpreter python3 \
  --env production \
  --log-date-format "YYYY-MM-DD HH:mm:ss Z"

# Save PM2 configuration
pm2 save
pm2 startup
```

### Docker Deployment

```dockerfile
# solution-fastmcp/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8010

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8010/health')" || exit 1

# Start the application
CMD ["python", "main.py"]
```

### Docker Compose Deployment

```yaml
# solution-fastmcp/docker-compose.yml
version: '3.8'

services:
  fastmcp:
    build: .
    restart: unless-stopped
    ports:
      - "8010:8010"
    environment:
      - OPENPROJECT_URL=http://openproject:8080
      - OPENPROJECT_API_KEY=demo-api-key
    depends_on:
      - openproject
    networks:
      - mcp-network

  openproject:
    image: openproject/community:latest
    ports:
      - "8090:8080"
    environment:
      - OPENPROJECT_SECRET_KEY_BASE=secret
    volumes:
      - openproject_data:/var/lib/openproject
    networks:
      - mcp-network

networks:
  mcp-network:
    driver: bridge

volumes:
  openproject_data:
```

## 🟨 TypeScript Solution Deployment

### Quick Start

```bash
# Navigate to TypeScript solution
cd solution-typescript

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Build and start
npm run build
npm start
```

### Production Deployment

#### Method 1: Node.js Production

```bash
# Install dependencies
npm install --production

# Build application
npm run build

# Start with PM2
pm2 start dist/index.js --name "typescript-mcp" \
  --env production \
  --log-date-format "YYYY-MM-DD HH:mm:ss Z"

# Save PM2 configuration
pm2 save
pm2 startup
```

#### Method 2: Systemd Service

Create `/etc/systemd/system/mcp-typescript.service`:

```ini
[Unit]
Description=MCP TypeScript Server
After=network.target

[Service]
Type=exec
User=nodeuser
Group=nodeuser
WorkingDirectory=/opt/mcp-typescript
Environment=PATH=/opt/mcp-typescript/node_modules/.bin
EnvironmentFile=/opt/mcp-typescript/.env
ExecStart=/usr/bin/node dist/index.js
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable mcp-typescript
sudo systemctl start mcp-typescript
```

### Docker Deployment

```dockerfile
# solution-typescript/Dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Build application
RUN npm run build

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nodeuser -u 1001

# Switch to non-root user
USER nodeuser

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

# Start the application
CMD ["npm", "start"]
```

### Docker Compose Deployment

```yaml
# solution-typescript/docker-compose.yml
version: '3.8'

services:
  typescript-mcp:
    build: .
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - OPENPROJECT_URL=http://openproject:8080
      - OPENPROJECT_API_KEY=demo-api-key
    depends_on:
      - openproject
    networks:
      - mcp-network

  openproject:
    image: openproject/community:latest
    ports:
      - "8090:8080"
    environment:
      - OPENPROJECT_SECRET_KEY_BASE=secret
    volumes:
      - openproject_data:/var/lib/openproject
    networks:
      - mcp-network

networks:
  mcp-network:
    driver: bridge

volumes:
  openproject_data:
```

## ☁️ Cloud Deployment

### AWS Deployment

#### AWS ECS (Elastic Container Service)

```json
// task-definition.json
{
  "family": "mcp-fastapi",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::123456789012:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "fastapi-mcp",
      "image": "your-account.dkr.ecr.us-east-1.amazonaws.com/fastapi-mcp:latest",
      "portMappings": [
        {
          "containerPort": 8020,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "OPENPROJECT_URL",
          "value": "https://your-openproject.com"
        },
        {
          "name": "OPENPROJECT_API_KEY",
          "value": "your-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/fastapi-mcp",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": [
          "CMD-SHELL",
          "curl -f http://localhost:8020/health || exit 1"
        ],
        "interval": 30,
        "timeout": 10,
        "retries": 3
      }
    }
  ]
}
```

Deploy to ECS:

```bash
# Create task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create service
aws ecs create-service \
  --cluster your-cluster \
  --service-name fastapi-mcp \
  --task-definition mcp-fastapi:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}"
```

#### AWS EKS (Elastic Kubernetes Service)

```yaml
# eks-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-mcp
  namespace: mcp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastapi-mcp
  template:
    metadata:
      labels:
        app: fastapi-mcp
    spec:
      containers:
      - name: fastapi-mcp
        image: your-account.dkr.ecr.us-east-1.amazonaws.com/fastapi-mcp:latest
        ports:
        - containerPort: 8020
        env:
        - name: OPENPROJECT_URL
          valueFrom:
            configMapKeyRef:
              name: mcp-config
              key: openproject-url
        - name: OPENPROJECT_API_KEY
          valueFrom:
            secretKeyRef:
              name: mcp-secrets
              key: openproject-api-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: fastapi-mcp-service
  namespace: mcp
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: nlb
spec:
  selector:
    app: fastapi-mcp
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8020
  type: LoadBalancer
```

### Google Cloud Deployment

#### Google Cloud Run

```yaml
# cloud-run.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: fastapi-mcp
  namespace: default
spec:
  template:
    spec:
      containers:
      - image: gcr.io/your-project/fastapi-mcp:latest
        env:
        - name: OPENPROJECT_URL
          value: "https://your-openproject.com"
        - name: OPENPROJECT_API_KEY
          valueFrom:
            secretKeyRef:
              name: openproject-api-key
              key: latest
        resources:
          limits:
            cpu: "1000m"
            memory: "512Mi"
        ports:
        - containerPort: 8020
```

Deploy to Cloud Run:

```bash
# Deploy service
gcloud run services replace cloud-run.yaml

# Set IAM permissions
gcloud run services add-iam-policy-binding fastapi-mcp \
  --member="allUsers" \
  --role="roles/run.invoker"
```

### Azure Deployment

#### Azure Container Instances

```bash
# Create container group
az container create \
  --resource-group your-resource-group \
  --name fastapi-mcp \
  --image your-registry.azurecr.io/fastapi-mcp:latest \
  --dns-name-label fastapi-mcp-unique \
  --ports 8020 \
  --environment-variables \
    'OPENPROJECT_URL'='https://your-openproject.com' \
    'OPENPROJECT_API_KEY'='your-api-key' \
  --cpu 1 \
  --memory 1.5 \
  --restart-policy Always
```

## 🏗️ High Availability Deployment

### Load Balancer Setup

#### Nginx Load Balancer

```nginx
# nginx.conf
upstream mcp_http_backend {
    server 10.0.1.10:8010;
    server 10.0.1.11:8010;
    server 10.0.1.12:8010;
    keepalive 32;
}

upstream fastapi_backend {
    server 10.0.1.20:8020;
    server 10.0.1.21:8020;
    server 10.0.1.22:8020;
    keepalive 32;
}

server {
    listen 80;
    server_name mcp.yourdomain.com;

    # HTTP Solution
    location /http/ {
        proxy_pass http://mcp_http_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # FastAPI Solution
    location /fastapi/ {
        proxy_pass http://fastapi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health checks
    location /health {
        proxy_pass http://mcp_http_backend/health;
        access_log off;
    }
}
```

### Database High Availability

#### PostgreSQL Replication

```yaml
# docker-compose.ha.yml
version: '3.8'

services:
  postgres-primary:
    image: postgres:15
    environment:
      POSTGRES_DB: openproject
      POSTGRES_USER: openproject
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_primary_data:/var/lib/postgresql/data
    networks:
      - mcp-network

  postgres-replica:
    image: postgres:15
    environment:
      POSTGRES_DB: openproject
      POSTGRES_USER: openproject
      POSTGRES_PASSWORD: secure_password
      POSTGRES_PRIMARY_HOST: postgres-primary
      POSTGRES_PRIMARY_PORT: 5432
    depends_on:
      - postgres-primary
    volumes:
      - postgres_replica_data:/var/lib/postgresql/data
    networks:
      - mcp-network

  redis-primary:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_primary_data:/data
    networks:
      - mcp-network

  redis-replica:
    image: redis:7-alpine
    command: redis-server --appendonly yes --slaveof redis-primary 6379
    depends_on:
      - redis-primary
    volumes:
      - redis_replica_data:/data
    networks:
      - mcp-network

networks:
  mcp-network:
    driver: bridge

volumes:
  postgres_primary_data:
  postgres_replica_data:
  redis_primary_data:
  redis_replica_data:
```

### Multi-Region Deployment

```yaml
# k8s-multi-region.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mcp-config
  namespace: mcp
data:
  openproject-url: "https://openproject.global.yourdomain.com"
  log-level: "INFO"
---
apiVersion: v1
kind: Secret
metadata:
  name: mcp-secrets
  namespace: mcp
type: Opaque
data:
  openproject-api-key: <base64-encoded-api-key>
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-mcp-us-east
  namespace: mcp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastapi-mcp
      region: us-east
  template:
    metadata:
      labels:
        app: fastapi-mcp
        region: us-east
    spec:
      containers:
      - name: fastapi-mcp
        image: your-registry/fastapi-mcp:latest
        ports:
        - containerPort: 8020
        env:
        - name: OPENPROJECT_URL
          valueFrom:
            configMapKeyRef:
              name: mcp-config
              key: openproject-url
        - name: OPENPROJECT_API_KEY
          valueFrom:
            secretKeyRef:
              name: mcp-secrets
              key: openproject-api-key
        - name: REGION
          value: "us-east"
---
apiVersion: v1
kind: Service
metadata:
  name: fastapi-mcp-service-us-east
  namespace: mcp
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: nlb
spec:
  selector:
    app: fastapi-mcp
    region: us-east
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8020
  type: LoadBalancer
```

## 📊 Monitoring and Observability

### Prometheus Monitoring

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'mcp-http'
    static_configs:
      - targets: ['mcp-http:8010']
    metrics_path: '/metrics'
    scrape_interval: 15s

  - job_name: 'fastapi-mcp'
    static_configs:
      - targets: ['fastapi-mcp:8020']
    metrics_path: '/metrics'
    scrape_interval: 15s

  - job_name: 'typescript-mcp'
    static_configs:
      - targets: ['typescript-mcp:3000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "id": null,
    "title": "MCP Server Metrics",
    "tags": ["mcp"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "HTTP Requests Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "id": 2,
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, http_request_duration_seconds_bucket)",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "id": 3,
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m]) * 100",
            "legendFormat": "Error Rate %"
          }
        ]
      }
    ]
  }
}
```

### Logging with ELK Stack

```yaml
# docker-compose.logging.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.8.0
    volumes:
      - ./logstash/config:/usr/share/logstash/config
      - ./logstash/pipeline:/usr/share/logstash/pipeline
    ports:
      - "5044:5044"
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.8.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch

  filebeat:
    image: docker.elastic.co/beats/filebeat:8.8.0
    volumes:
      - ./filebeat.yml:/usr/share/filebeat/filebeat.yml
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    depends_on:
      - elasticsearch
      - kibana

networks:
  default:
    name: elk-network

volumes:
  elasticsearch_data:
```

## 🔒 Security and Compliance

### SSL/TLS Configuration

```nginx
# nginx-ssl.conf
server {
    listen 80;
    server_name mcp.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name mcp.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/mcp.yourdomain.com.crt;
    ssl_certificate_key /etc/ssl/private/mcp.yourdomain.com.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=mcp_api:10m rate=10r/s;
    limit_req zone=mcp_api burst=20 nodelay;

    location / {
        proxy_pass http://mcp_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Network Security

```yaml
# docker-compose.security.yml
version: '3.8'

services:
  mcp-http:
    build: ./solution-http
    restart: unless-stopped
    networks:
      - mcp-network
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
      - /var/tmp
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETGID
      - SETUID
      - NET_BIND_SERVICE

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    networks:
      - mcp-network
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
      - /var/tmp
      - /var/cache/nginx
      - /var/run/nginx.pid
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETGID
      - SETUID
      - NET_BIND_SERVICE

networks:
  mcp-network:
    driver: bridge
    internal: true
```

## 💾 Backup and Recovery

### Database Backup Strategy

```bash
#!/bin/bash
# backup.sh
set -euo pipefail

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
OPENPROJECT_DB="openproject"
REDIS_DB="0"

# Create backup directory
mkdir -p "$BACKUP_DIR/$DATE"

# Backup PostgreSQL
docker exec postgres pg_dump -U openproject "$OPENPROJECT_DB" > "$BACKUP_DIR/$DATE/openproject.sql"

# Backup Redis
docker exec redis redis-cli --rdb "$BACKUP_DIR/$DATE/redis_dump.rdb"

# Backup application data
docker cp mcp-http:/app/data "$BACKUP_DIR/$DATE/app_data"

# Compress backup
tar -czf "$BACKUP_DIR/$DATE.tar.gz" -C "$BACKUP_DIR" "$DATE"

# Remove temporary directory
rm -rf "$BACKUP_DIR/$DATE"

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/$DATE.tar.gz"
```

### Disaster Recovery Plan

```bash
#!/bin/bash
# disaster-recovery.sh
set -euo pipefail

BACKUP_FILE="$1"
RESTORE_DIR="/restore"

if [[ -z "$BACKUP_FILE" ]]; then
    echo "Usage: $0 <backup-file>"
    exit 1
fi

# Extract backup
mkdir -p "$RESTORE_DIR"
tar -xzf "$BACKUP_FILE" -C "$RESTORE_DIR"

# Stop services
docker-compose down

# Restore PostgreSQL
docker exec -i postgres psql -U openproject openproject < "$RESTORE_DIR"/openproject.sql

# Restore Redis
docker cp "$RESTORE_DIR"/redis_dump.rdb redis:/data/dump.rdb
docker exec redis redis-cli BGSAVE

# Restore application data
docker cp "$RESTORE_DIR"/app_data mcp-http:/app/

# Start services
docker-compose up -d

echo "Recovery completed from: $BACKUP_FILE"
```

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. Port Conflicts

```bash
# Check port usage
lsof -i :8010
lsof -i :8020
lsof -i :3000

# Kill processes using ports
kill -9 $(lsof -ti:8010)
```

#### 2. OpenProject Connection Issues

```bash
# Test OpenProject connectivity
curl -v "${OPENPROJECT_URL}/api/v3/projects" \
  -H "Authorization: Bearer ${OPENPROJECT_API_KEY}"

# Check OpenProject logs
docker logs openproject
```

#### 3. Memory Issues

```bash
# Check memory usage
docker stats
free -h

# Increase memory limits
docker update --memory=1g --memory-swap=2g mcp-http
```

#### 4. SSL Certificate Issues

```bash
# Test SSL configuration
openssl s_client -connect mcp.yourdomain.com:443

# Check certificate expiration
openssl x509 -in /etc/ssl/certs/mcp.yourdomain.com.crt -noout -dates
```

### Performance Tuning

#### HTTP Solution Performance

```bash
# Optimize Gunicorn workers
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
```

#### FastAPI Solution Performance

```bash
# Optimize Uvicorn workers
workers = 4
worker_class = 'uvicorn.workers.UvicornWorker'
limit_concurrency = 1000
timeout_keep_alive = 30
```

### Health Check Scripts

```bash
#!/bin/bash
# health-check.sh
HEALTH_URL="http://localhost:8010/health"
TIMEOUT=10

if curl -f -s --max-time "$TIMEOUT" "$HEALTH_URL" > /dev/null; then
    echo "✅ MCP HTTP Server is healthy"
    exit 0
else
    echo "❌ MCP HTTP Server is unhealthy"
    exit 1
fi
```

This comprehensive deployment guide covers all deployment scenarios for the four solution types. Each deployment method includes detailed instructions, configuration examples, and troubleshooting guidance.

## 📚 Additional Resources

- [Architecture Guide](docs/ARCHITECTURE_GUIDE.md)
- [Implementation Examples](docs/IMPLEMENTATION_EXAMPLES.md)
- [API Documentation](docs/API_DOCUMENTATION.md)
- [Security Guide](docs/SECURITY.md)
- [Monitoring Guide](docs/MONITORING.md)