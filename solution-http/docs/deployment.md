# Deployment Guide - HTTP Solution

This guide covers deploying the HTTP MCP Solution in various environments, from development to production.

## Table of Contents

- [Quick Deployment](#quick-deployment)
- [Environment Configuration](#environment-configuration)
- [Development Deployment](#development-deployment)
- [Production Deployment](#production-deployment)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Reverse Proxy Setup](#reverse-proxy-setup)
- [Monitoring and Logging](#monitoring-and-logging)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)

## Quick Deployment

### Minimal Setup

For a quick test deployment:

```bash
# 1. Clone repository
git clone <repository-url>
cd mcp-projectmanage-openproject/solution-http

# 2. Set environment variables
export OPENPROJECT_URL=http://your-openproject-instance
export OPENPROJECT_API_KEY=your-api-key

# 3. Install and run
pip install -r requirements.txt
python src/main.py
```

Server will be available at `http://localhost:8010`

### Docker Quick Start

```bash
# Using Docker Compose (includes OpenProject)
docker-compose up -d

# Using Docker only
docker run -p 8010:8010 \
  -e OPENPROJECT_URL=http://your-openproject \
  -e OPENPROJECT_API_KEY=your-key \
  mcp-http-server
```

## Environment Configuration

### Required Environment Variables

```bash
# OpenProject Connection (Required)
OPENPROJECT_URL=http://localhost:8090
OPENPROJECT_API_KEY=your_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8010
LOG_LEVEL=INFO

# Security
CORS_ALLOW_ORIGINS=http://localhost,http://127.0.0.1
```

### Complete Environment Configuration

Create a `.env` file or set these environment variables:

```bash
# === OpenProject Configuration ===
OPENPROJECT_URL=http://localhost:8090
OPENPROJECT_API_KEY=your_api_key_here

# === Server Configuration ===
HOST=0.0.0.0
PORT=8010
LOG_LEVEL=INFO
ENVIRONMENT=production

# === CORS Configuration ===
CORS_ALLOW_ORIGINS=http://localhost,http://127.0.0.1,https://yourdomain.com

# === Performance Configuration ===
REQUEST_TIMEOUT=30
MAX_CONNECTIONS=100
CACHE_TTL=300

# === Gunicorn Configuration ===
GUNICORN_WORKERS=4
WORKER_CONNECTIONS=1000
MAX_REQUESTS=1000
MAX_REQUESTS_JITTER=50
WORKER_TIMEOUT=30
GRACEFUL_TIMEOUT=30

# === Security Configuration ===
FORWARDED_ALLOW_IPS=127.0.0.1
PROXY_ALLOW_IPS=127.0.0.1
PROXY_PROTOCOL=false

# === SSL Configuration (Optional) ===
SSL_KEYFILE=/path/to/ssl/key.pem
SSL_CERTFILE=/path/to/ssl/cert.pem
SSL_CA_CERTS=/path/to/ssl/ca-certs.pem

# === Database Configuration (if using external DB) ===
POSTGRES_DB=openproject
POSTGRES_USER=openproject
POSTGRES_PASSWORD=secure_password

# === Logging Configuration ===
ACCESS_LOG_FILE=/app/logs/access.log
ERROR_LOG_FILE=/app/logs/error.log

# === Template Configuration ===
TEMPLATES_DIR=/app/templates
```

### Configuration Validation

Test your configuration:

```bash
# Validate configuration
python -c "from src.config import get_http_config; print(get_http_config())"

# Test OpenProject connection
curl -X GET "${OPENPROJECT_URL}/api/v3/projects" \
  -H "Authorization: Bearer ${OPENPROJECT_API_KEY}"
```

## Development Deployment

### Local Development Setup

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install development dependencies
pip install pytest pytest-asyncio pytest-cov black isort flake8

# 4. Set up pre-commit hooks (optional)
pip install pre-commit
pre-commit install

# 5. Configure for development
export ENVIRONMENT=development
export LOG_LEVEL=DEBUG
export OPENPROJECT_URL=http://localhost:8090
export OPENPROJECT_API_KEY=your_dev_api_key

# 6. Run development server
python src/main.py
```

### Development with Docker

```bash
# Build development image
docker build -t mcp-http-dev .

# Run with development settings
docker run -it --rm \
  -p 8010:8010 \
  -e ENVIRONMENT=development \
  -e LOG_LEVEL=DEBUG \
  -e OPENPROJECT_URL=http://host.docker.internal:8090 \
  -e OPENPROJECT_API_KEY=your_dev_key \
  -v $(pwd)/src:/app/src \
  mcp-http-dev
```

### Hot Reload Setup

For automatic code reloading during development:

```bash
# Install watchdog for file monitoring
pip install watchdog

# Run with auto-reload (built into FastAPI)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8010
```

## Production Deployment

### Production with Gunicorn

```bash
# 1. Install production dependencies
pip install -r requirements.txt gunicorn

# 2. Set production environment
export ENVIRONMENT=production
export LOG_LEVEL=INFO

# 3. Start with Gunicorn
gunicorn --config gunicorn.conf.py src.main:app

# Or with custom settings
gunicorn \
  --bind 0.0.0.0:8010 \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --timeout 30 \
  --keepalive 2 \
  --max-requests 1000 \
  --max-requests-jitter 50 \
  --preload \
  --access-logfile /var/log/mcp-http/access.log \
  --error-logfile /var/log/mcp-http/error.log \
  src.main:app
```

### Systemd Service Setup

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
sudo systemctl status mcp-http
```

### Production Directory Structure

```bash
/opt/mcp-http/
├── venv/                    # Python virtual environment
├── src/                     # Application source code
├── logs/                    # Log files
├── data/                    # Application data
├── templates/               # Custom templates
├── .env                     # Environment configuration
├── requirements.txt         # Python dependencies
├── gunicorn.conf.py        # Gunicorn configuration
└── deploy.sh               # Deployment script
```

## Docker Deployment

### Single Container

```bash
# Build image
docker build -t mcp-http-server .

# Run with environment file
docker run -d \
  --name mcp-http \
  --restart unless-stopped \
  -p 8010:8010 \
  --env-file .env \
  -v mcp-http-logs:/app/logs \
  -v mcp-http-data:/app/data \
  mcp-http-server
```

### Docker Compose - Production

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  mcp-http:
    build:
      context: .
      target: production
    restart: unless-stopped
    ports:
      - "8010:8010"
    environment:
      - ENVIRONMENT=production
      - HOST=0.0.0.0
      - PORT=8010
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    networks:
      - mcp-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8010/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - mcp-http
    networks:
      - mcp-network

networks:
  mcp-network:
    driver: bridge
```

Deploy:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Docker Compose - Full Stack

For a complete deployment including OpenProject:

```bash
# Use the provided docker-compose.yml
docker-compose up -d

# Check all services
docker-compose ps

# View logs
docker-compose logs -f mcp-http
```

## Kubernetes Deployment

### Basic Kubernetes Manifests

Create `k8s/deployment.yaml`:

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
        livenessProbe:
          httpGet:
            path: /health
            port: 8010
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8010
          initialDelaySeconds: 5
          periodSeconds: 5
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
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: mcp-http-config
data:
  openproject-url: "http://openproject-service:8080"
  log-level: "INFO"
  host: "0.0.0.0"
  port: "8010"
---
apiVersion: v1
kind: Secret
metadata:
  name: mcp-http-secrets
type: Opaque
data:
  openproject-api-key: <base64-encoded-api-key>
```

Deploy to Kubernetes:

```bash
# Create namespace
kubectl create namespace mcp

# Apply manifests
kubectl apply -f k8s/ -n mcp

# Check deployment
kubectl get pods -n mcp
kubectl get services -n mcp

# Check logs
kubectl logs -l app=mcp-http -n mcp
```

### Helm Chart

Create a Helm chart for easier management:

```bash
helm create mcp-http-chart

# Edit values.yaml with your configuration
# Deploy with Helm
helm install mcp-http ./mcp-http-chart -n mcp --create-namespace
```

## Reverse Proxy Setup

### Nginx Configuration

Create `/etc/nginx/sites-available/mcp-http`:

```nginx
upstream mcp_http_backend {
    server 127.0.0.1:8010;
    keepalive 32;
}

server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # Proxy settings
    location / {
        proxy_pass http://mcp_http_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;

        # Timeout settings
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;

        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 8k;
        proxy_buffers 8 8k;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://mcp_http_backend/health;
        access_log off;
    }

    # Static files (if any)
    location /static/ {
        alias /opt/mcp-http/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable and test:

```bash
sudo ln -s /etc/nginx/sites-available/mcp-http /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Apache Configuration

Create `/etc/apache2/sites-available/mcp-http.conf`:

```apache
<VirtualHost *:80>
    ServerName your-domain.com
    Redirect permanent / https://your-domain.com/
</VirtualHost>

<VirtualHost *:443>
    ServerName your-domain.com

    # SSL Configuration
    SSLEngine on
    SSLCertificateFile /path/to/ssl/cert.pem
    SSLCertificateKeyFile /path/to/ssl/key.pem

    # Proxy configuration
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8010/
    ProxyPassReverse / http://127.0.0.1:8010/

    # Security headers
    Header always set X-Frame-Options DENY
    Header always set X-Content-Type-Options nosniff
    Header always set X-XSS-Protection "1; mode=block"
    Header always set Strict-Transport-Security "max-age=63072000; includeSubDomains; preload"

    # Logging
    ErrorLog ${APACHE_LOG_DIR}/mcp-http_error.log
    CustomLog ${APACHE_LOG_DIR}/mcp-http_access.log combined
</VirtualHost>
```

Enable and restart:

```bash
sudo a2ensite mcp-http
sudo a2enmod ssl proxy proxy_http headers
sudo systemctl restart apache2
```

## Monitoring and Logging

### Log Configuration

Configure structured logging in production:

```python
# In your .env file
LOG_LEVEL=INFO
ACCESS_LOG_FILE=/var/log/mcp-http/access.log
ERROR_LOG_FILE=/var/log/mcp-http/error.log
```

### Log Rotation

Create `/etc/logrotate.d/mcp-http`:

```
/var/log/mcp-http/*.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    create 644 mcpuser mcpuser
    postrotate
        systemctl reload mcp-http
    endscript
}
```

### Health Monitoring

Set up health check monitoring:

```bash
#!/bin/bash
# health-check.sh
HEALTH_URL="http://localhost:8010/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL")

if [ "$RESPONSE" -eq 200 ]; then
    echo "MCP HTTP Server is healthy"
    exit 0
else
    echo "MCP HTTP Server is unhealthy (HTTP $RESPONSE)"
    exit 1
fi
```

### Prometheus Metrics

Add metrics endpoint for Prometheus monitoring:

```python
# Add to main.py
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## Security Considerations

### Production Security Checklist

- [ ] Use HTTPS with valid SSL certificates
- [ ] Configure firewall to allow only necessary ports
- [ ] Set up proper CORS origins
- [ ] Use strong API keys
- [ ] Enable rate limiting
- [ ] Configure security headers
- [ ] Run with non-root user
- [ ] Keep dependencies updated
- [ ] Monitor for security vulnerabilities
- [ ] Set up log monitoring
- [ ] Configure backup procedures

### Environment Security

```bash
# Set secure file permissions
chmod 600 .env
chown mcpuser:mcpuser .env

# Restrict log file access
chmod 640 /var/log/mcp-http/*.log
chown mcpuser:adm /var/log/mcp-http/*.log
```

### Rate Limiting

Add rate limiting with nginx:

```nginx
# In nginx.conf
http {
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    server {
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            # ... rest of configuration
        }
    }
}
```

## Troubleshooting

### Common Deployment Issues

1. **Port Already in Use**
   ```bash
   # Find process using port
   lsof -i :8010
   # Kill process or change port
   export PORT=8011
   ```

2. **Permission Denied**
   ```bash
   # Fix file permissions
   chmod +x deploy.sh
   chown -R mcpuser:mcpuser /opt/mcp-http
   ```

3. **OpenProject Connection Failed**
   ```bash
   # Test connectivity
   curl -v "${OPENPROJECT_URL}/api/v3/projects" \
     -H "Authorization: Bearer ${OPENPROJECT_API_KEY}"
   ```

4. **Memory Issues**
   ```bash
   # Check memory usage
   docker stats mcp-http
   # Adjust resource limits
   docker update --memory=512m mcp-http
   ```

### Debugging Steps

1. **Check application logs:**
   ```bash
   tail -f /var/log/mcp-http/error.log
   ```

2. **Test health endpoint:**
   ```bash
   curl -v http://localhost:8010/health
   ```

3. **Verify configuration:**
   ```bash
   python -c "from src.config import get_http_config; print(get_http_config())"
   ```

4. **Check service status:**
   ```bash
   systemctl status mcp-http
   ```

### Performance Tuning

1. **Adjust worker count:**
   ```bash
   # In gunicorn.conf.py
   workers = multiprocessing.cpu_count() * 2 + 1
   ```

2. **Optimize memory usage:**
   ```bash
   # Add to environment
   export MAX_CONNECTIONS=50
   export WORKER_CONNECTIONS=500
   ```

3. **Enable caching:**
   ```bash
   export CACHE_TTL=600  # 10 minutes
   ```

### Recovery Procedures

1. **Graceful restart:**
   ```bash
   systemctl reload mcp-http
   ```

2. **Hard restart:**
   ```bash
   systemctl restart mcp-http
   ```

3. **Rollback deployment:**
   ```bash
   # With Docker
   docker-compose down
   docker-compose up -d --force-recreate
   
   # With systemd
   git checkout previous-version
   systemctl restart mcp-http
   ```

This completes the deployment guide for the HTTP MCP Solution. For additional support, refer to the main README.md and API documentation.