# Troubleshooting Guide and FAQ

This comprehensive troubleshooting guide covers common issues, their solutions, and frequently asked questions for all OpenProject MCP integration solutions.

## Table of Contents

- [Quick Start Troubleshooting](#quick-start-troubleshooting)
- [Installation and Setup Issues](#installation-and-setup-issues)
- [Configuration Problems](#configuration-problems)
- [Network and Connectivity Issues](#network-and-connectivity-issues)
- [Authentication and Authorization](#authentication-and-authorization)
- [Performance Issues](#performance-issues)
- [Data Synchronization Problems](#data-synchronization-problems)
- [Report Generation Issues](#report-generation-issues)
- [MCP Protocol Issues](#mcp-protocol-issues)
- [Deployment and Production Issues](#deployment-and-production-issues)
- [Error Codes and Messages](#error-codes-and-messages)
- [Frequently Asked Questions](#frequently-asked-questions)
- [Debugging Tools and Techniques](#debugging-tools-and-techniques)
- [Getting Help](#getting-help)

## Quick Start Troubleshooting

### First Steps When Something Goes Wrong

1. **Check the Basics**
   ```bash
   # Check if services are running
   ps aux | grep -E "(python|node|fastapi|http)"
   
   # Check port availability
   netstat -tlnp | grep -E ":8010|:8020|:8030|:8040"
   
   # Check disk space
   df -h
   ```

2. **Verify Environment Variables**
   ```bash
   # Check required environment variables
   echo $OPENPROJECT_URL
   echo $OPENPROJECT_API_KEY
   echo $PORT
   ```

3. **Test Basic Connectivity**
   ```bash
   # Test OpenProject connection
   curl -I "$OPENPROJECT_URL/api/v3/projects" \
     -H "Authorization: Bearer $OPENPROJECT_API_KEY"
   
   # Test local service
   curl -I "http://localhost:$PORT/health"
   ```

4. **Check Logs**
   ```bash
   # View recent logs
   tail -f logs/error.log
   tail -f logs/access.log
   
   # Check for errors
   grep -i error logs/error.log | tail -20
   ```

## Installation and Setup Issues

### Python Environment Issues

#### Problem: Virtual Environment Not Activating

**Symptoms:**
- `python` command not found after activating venv
- Module import errors
- Wrong Python version being used

**Solutions:**
```bash
# Check if venv exists
ls -la venv/

# Recreate venv if needed
python -m venv venv

# Activate correctly
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate    # Windows

# Verify Python path
which python
python --version
```

#### Problem: Dependencies Installation Fails

**Symptoms:**
- `pip install` fails with error messages
- Permission denied errors
- SSL certificate errors

**Solutions:**
```bash
# Update pip first
pip install --upgrade pip

# Install with specific Python version
python -m pip install -r requirements.txt

# Try with --user flag (if permission issues)
pip install --user -r requirements.txt

# For SSL issues
pip install --trusted-host pypi.org --trusted-host pypi.python.org -r requirements.txt

# Clear pip cache
pip cache purge
```

### Node.js Environment Issues

#### Problem: Node.js Version Compatibility

**Symptoms:**
- `npm install` fails with version errors
- TypeScript compilation errors
- Module resolution issues

**Solutions:**
```bash
# Check Node.js version
node --version
npm --version

# Use nvm to manage versions
nvm install 18
nvm use 18

# Clear npm cache
npm cache clean --force

# Install with --legacy-peer-deps if needed
npm install --legacy-peer-deps
```

## Configuration Problems

### Environment Configuration Issues

#### Problem: Missing Required Environment Variables

**Symptoms:**
- Application fails to start
- "Required environment variable not found" errors
- Configuration validation failures

**Solutions:**
```bash
# Check .env file exists
ls -la .env

# Create .env file if missing
cat > .env << EOF
OPENPROJECT_URL=https://your-openproject.com
OPENPROJECT_API_KEY=your-api-key-here
PORT=8010
LOG_LEVEL=INFO
EOF

# Verify environment variables are set
export $(cat .env | xargs)
env | grep -E "(OPENPROJECT|PORT|LOG_LEVEL)"
```

#### Problem: Invalid OpenProject Configuration

**Symptoms:**
- Connection timeouts to OpenProject
- 401 Unauthorized errors
- Invalid URL format errors

**Solutions:**
```bash
# Test OpenProject URL
curl -I "$OPENPROJECT_URL/api/v3/projects"

# Test API key
curl -X GET "$OPENPROJECT_URL/api/v3/projects" \
  -H "Authorization: Bearer $OPENPROJECT_API_KEY"

# Verify URL format (no trailing slash)
echo $OPENPROJECT_URL | grep -v '/$'
```

### Database Configuration Issues

#### Problem: Database Connection Fails

**Symptoms:**
- Database connection timeout errors
- Authentication failures
- Database not found errors

**Solutions:**
```bash
# Test database connectivity
python -c "
import psycopg2
try:
    conn = psycopg2.connect(
        dbname='openproject',
        user='openproject',
        password='your-password',
        host='localhost',
        port='5432'
    )
    print('Database connection successful')
    conn.close()
except Exception as e:
    print(f'Database connection failed: {e}')
"

# Check if database is running
sudo systemctl status postgresql
# or
docker ps | grep postgres
```

## Network and Connectivity Issues

### Port Conflicts

#### Problem: Port Already in Use

**Symptoms:**
- "Address already in use" errors
- Service fails to start
- Port binding errors

**Solutions:**
```bash
# Find process using the port
lsof -i :8010
# or
netstat -tlnp | grep :8010

# Kill the process if needed
kill -9 <PID>

# Change port in .env
echo "PORT=8011" >> .env

# Verify port is available
netstat -tlnp | grep :8011
```

### Firewall and Security Issues

#### Problem: Firewall Blocking Connections

**Symptoms:**
- Connection timeout errors
- Connection refused errors
- Service not accessible from outside

**Solutions:**
```bash
# Check firewall status
sudo ufw status
# or
sudo firewall-cmd --list-all

# Allow port through firewall
sudo ufw allow 8010
# or
sudo firewall-cmd --permanent --add-port=8010/tcp
sudo firewall-cmd --reload

# Test external connectivity
curl -I http://your-server-ip:8010/health
```

### Proxy Configuration Issues

#### Problem: Corporate Proxy Blocking Requests

**Symptoms:**
- Connection timeout to external services
- SSL handshake failures
- Proxy authentication required

**Solutions:**
```bash
# Set proxy environment variables
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
export NO_PROXY=localhost,127.0.0.1

# Test proxy connectivity
curl -x http://proxy.company.com:8080 -I https://api.github.com

# Configure pip to use proxy
pip install --proxy http://proxy.company.com:8080 package-name
```

## Authentication and Authorization

### API Key Issues

#### Problem: Invalid or Expired API Key

**Symptoms:**
- 401 Unauthorized errors
- "Invalid API key" messages
- Authentication failures

**Solutions:**
```bash
# Test API key validity
curl -X GET "$OPENPROJECT_URL/api/v3/projects" \
  -H "Authorization: Bearer $OPENPROJECT_API_KEY"

# Generate new API key in OpenProject
# Navigate to: OpenProject → My account → API access

# Update .env with new key
sed -i "s/OPENPROJECT_API_KEY=.*/OPENPROJECT_API_KEY=new-key-here/" .env
```

### Permission Issues

#### Problem: Insufficient Permissions

**Symptoms:**
- 403 Forbidden errors
- "Access denied" messages
- Missing data in responses

**Solutions:**
```bash
# Check user permissions in OpenProject
curl -X GET "$OPENPROJECT_URL/api/v3/users/me" \
  -H "Authorization: Bearer $OPENPROJECT_API_KEY"

# Verify user has required permissions
# - View projects
# - View work packages
# - Create reports

# Contact OpenProject administrator if needed
```

## Performance Issues

### Memory Issues

#### Problem: High Memory Usage

**Symptoms:**
- Service becomes unresponsive
- Out of memory errors
- Slow performance

**Solutions:**
```bash
# Check memory usage
free -h
# or
docker stats

# Monitor memory usage over time
top -p $(pgrep -f "python.*main.py")

# Restart service if needed
sudo systemctl restart mcp-http
# or
docker-compose restart

# Optimize memory usage
export MAX_CONNECTIONS=50
export WORKER_TIMEOUT=30
```

### CPU Performance Issues

#### Problem: High CPU Usage

**Symptoms:**
- High CPU utilization
- Slow response times
- Service unresponsiveness

**Solutions:**
```bash
# Check CPU usage
top -p $(pgrep -f "python.*main.py")
# or
htop

# Monitor CPU usage
ps aux --sort=-%cpu | grep -E "(python|node)"

# Profile CPU usage
python -m cProfile -o profile.prof app/main.py
python -m pstats profile.prof

# Optimize worker configuration
export GUNICORN_WORKERS=2
export MAX_REQUESTS=1000
```

### Database Performance Issues

#### Problem: Slow Database Queries

**Symptoms:**
- Slow API responses
- Database timeout errors
- High database load

**Solutions:**
```bash
# Monitor database queries
# Enable query logging in your configuration

# Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

# Add database indexes
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_work_packages_project ON work_packages(project_id);

# Optimize database connection pool
export DATABASE_POOL_SIZE=20
export DATABASE_MAX_OVERFLOW=30
```

## Data Synchronization Problems

### OpenProject Sync Issues

#### Problem: Data Not Syncing with OpenProject

**Symptoms:**
- Stale data in responses
- Missing new projects or work packages
- Data inconsistency

**Solutions:**
```bash
# Test OpenProject connection
curl -X GET "$OPENPROJECT_URL/api/v3/projects" \
  -H "Authorization: Bearer $OPENPROJECT_API_KEY"

# Check last sync time
curl -X GET "http://localhost:$PORT/admin/sync-status"

# Manually trigger sync
curl -X POST "http://localhost:$PORT/admin/sync" \
  -H "Authorization: Bearer $OPENPROJECT_API_KEY"

# Clear cache and restart
rm -rf cache/*
sudo systemctl restart mcp-http
```

### Cache Issues

#### Problem: Cache Serving Stale Data

**Symptoms:**
- Old data being returned
- Inconsistent responses
- Cache not invalidating properly

**Solutions:**
```bash
# Clear cache directory
rm -rf cache/*
# or
redis-cli FLUSHALL

# Disable cache temporarily for testing
export CACHE_ENABLED=false

# Check cache configuration
export CACHE_TTL=300
export CACHE_MAX_SIZE=1000
```

## Report Generation Issues

### Template Issues

#### Problem: Report Templates Not Found

**Symptoms:**
- "Template not found" errors
- Failed report generation
- Missing template files

**Solutions:**
```bash
# Check template directory
ls -la templates/reports/

# Verify template files exist
find templates/ -name "*.yaml" -o -name "*.html"

# Check template permissions
chmod 644 templates/reports/*.yaml

# Restart service after adding templates
sudo systemctl restart mcp-http
```

### PDF Generation Issues

#### Problem: PDF Generation Fails

**Symptoms:**
- PDF generation timeout
- Corrupted PDF files
- Missing dependencies

**Solutions:**
```bash
# Check PDF generation dependencies
which wkhtmltopdf
which pandoc

# Install missing dependencies
# Ubuntu/Debian
sudo apt-get install wkhtmltopdf pandoc

# CentOS/RHEL
sudo yum install wkhtmltopdf pandoc

# Test PDF generation manually
wkhtmltopdf --version
pandoc --version
```

## MCP Protocol Issues

### JSON-RPC Errors

#### Problem: Invalid JSON-RPC Requests

**Symptoms:**
- JSON parse errors
- Invalid request format
- Method not found errors

**Solutions:**
```bash
# Test MCP request format
curl -X POST "http://localhost:$PORT/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_projects",
      "arguments": {}
    },
    "id": "test-123"
  }'

# Validate JSON format
python -c "import json; json.loads('''your-json-here''')"

# Check MCP logs
tail -f logs/mcp.log
```

### Tool Registration Issues

#### Problem: MCP Tools Not Registered

**Symptoms:**
- Tools not appearing in MCP client
- "Tool not found" errors
- Missing tool definitions

**Solutions:**
```bash
# Check registered tools
curl -X GET "http://localhost:$PORT/admin/tools"

# Verify tool definitions
curl -X POST "http://localhost:$PORT/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "params": {},
    "id": "list-tools"
  }'

# Restart MCP service
sudo systemctl restart mcp-http
```

## Deployment and Production Issues

### Docker Deployment Issues

#### Problem: Docker Container Fails to Start

**Symptoms:**
- Container exits immediately
- Health check failures
- Port mapping issues

**Solutions:**
```bash
# Check container logs
docker logs mcp-http
docker logs mcp-fastapi

# Check container status
docker ps -a

# Inspect container
docker inspect mcp-http

# Start container in interactive mode for debugging
docker run -it --rm mcp-http bash

# Check Docker Compose configuration
docker-compose config
```

### Kubernetes Deployment Issues

#### Problem: Pods Not Starting

**Symptoms:**
- Pods in CrashLoopBackOff
- Image pull failures
- Resource limit issues

**Solutions:**
```bash
# Check pod status
kubectl get pods -n mcp
kubectl describe pod <pod-name> -n mcp

# Check pod logs
kubectl logs <pod-name> -n mcp

# Check events
kubectl get events -n mcp

# Check resource usage
kubectl top pods -n mcp

# Edit pod for debugging
kubectl edit deployment mcp-http -n mcp
```

### SSL/TLS Issues

#### Problem: SSL Certificate Errors

**Symptoms:**
- SSL handshake failures
- Certificate validation errors
- HTTPS connection issues

**Solutions:**
```bash
# Test SSL certificate
openssl s_client -connect your-domain.com:443
openssl x509 -in /path/to/cert.pem -text -noout

# Check certificate expiration
openssl x509 -enddate -noout -in /path/to/cert.pem

# Renew Let's Encrypt certificate
certbot renew --dry-run

# Test HTTPS connection
curl -I https://your-domain.com/health
```

## Error Codes and Messages

### Common HTTP Error Codes

| Code | Name | Description | Common Causes |
|------|------|-------------|---------------|
| 400 | Bad Request | Invalid request format | Malformed JSON, missing parameters |
| 401 | Unauthorized | Authentication failed | Invalid API key, expired token |
| 403 | Forbidden | Insufficient permissions | User lacks required permissions |
| 404 | Not Found | Resource not found | Invalid project ID, missing endpoint |
| 422 | Unprocessable Entity | Validation failed | Invalid data format, constraint violations |
| 429 | Too Many Requests | Rate limit exceeded | Too many requests in time period |
| 500 | Internal Server Error | Server error | Unexpected server failure |
| 502 | Bad Gateway | Gateway error | Upstream service unavailable |
| 503 | Service Unavailable | Service down | Maintenance, overload |
| 504 | Gateway Timeout | Timeout | Upstream service timeout |

### MCP Error Codes

| Code | Name | Description |
|------|------|-------------|
| -32700 | Parse error | Invalid JSON |
| -32600 | Invalid Request | Invalid JSON-RPC request |
| -32601 | Method not found | Requested method not available |
| -32602 | Invalid params | Invalid method parameters |
| -32603 | Internal error | Internal server error |
| -32001 | Unauthorized | Authentication failed |
| -32002 | Forbidden | Insufficient permissions |
| -32003 | Not found | Resource not found |
| -32004 | Rate limited | Too many requests |

### Database Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| 28000 | Invalid authorization | Check database credentials |
| 3D000 | Database does not exist | Create database |
| 28000 | Role does not exist | Create database user |
| 53300 | Insufficient resources | Increase database resources |
| 57014 | Statement timeout | Optimize query or increase timeout |

## Frequently Asked Questions

### General Questions

#### Q: What is the difference between the four solution types?

**A:** Each solution is optimized for different use cases:
- **HTTP Solution**: Production-ready, synchronous, stable
- **FastAPI Solution**: Development-friendly, async, auto-docs
- **FastMCP Solution**: MCP-native, streaming support
- **TypeScript Solution**: Frontend integration, type-safe

#### Q: Which solution should I use?

**A:** Choose based on your needs:
- Production deployments: HTTP Solution
- Development and API-first: FastAPI Solution
- Real-time updates: FastMCP Solution
- Frontend integration: TypeScript Solution

#### Q: Can I run multiple solutions simultaneously?

**A:** Yes, but use different ports:
- HTTP: 8010
- FastAPI: 8020
- FastMCP: 8030
- TypeScript: 8040

### Installation and Setup

#### Q: How do I get an OpenProject API key?

**A:** In OpenProject:
1. Go to My account → API access
2. Click "Generate new token"
3. Copy the token and set it as `OPENPROJECT_API_KEY`

#### Q: Do I need to install OpenProject locally?

**A:** No, you can use any OpenProject instance:
- Self-hosted
- OpenProject Cloud
- OpenProject.com

#### Q: What are the minimum system requirements?

**A:** Minimum requirements:
- CPU: 1 core
- RAM: 512MB
- Storage: 1GB
- Network: Internet connection

### Configuration

#### Q: How do I configure multiple OpenProject instances?

**A:** You can configure multiple instances:
```bash
# Primary instance
OPENPROJECT_URL=https://primary.openproject.com
OPENPROJECT_API_KEY=primary-key

# Secondary instance (if supported)
SECONDARY_OPENPROJECT_URL=https://secondary.openproject.com
SECONDARY_OPENPROJECT_API_KEY=secondary-key
```

#### Q: Can I use environment-specific configurations?

**A:** Yes, use multiple .env files:
```bash
# .env.development
OPENPROJECT_URL=http://localhost:8080
LOG_LEVEL=DEBUG

# .env.production
OPENPROJECT_URL=https://production.openproject.com
LOG_LEVEL=INFO
```

### Performance and Scaling

#### Q: How many concurrent users can the system handle?

**A:** It depends on the solution and configuration:
- HTTP Solution: ~100 concurrent users
- FastAPI Solution: ~500 concurrent users
- FastMCP Solution: ~1000 concurrent connections
- TypeScript Solution: ~200 concurrent users

#### Q: How do I improve performance?

**A:** Performance optimization tips:
- Use Redis for caching
- Enable gzip compression
- Use load balancer
- Optimize database queries
- Use CDN for static assets

### Security

#### Q: Is the API key secure?

**A:** API keys are secure if:
- Stored in environment variables (not code)
- Used over HTTPS
- Rotated regularly
- Have limited permissions

#### Q: How do I secure the deployment?

**A:** Security best practices:
- Use HTTPS with valid certificates
- Configure firewall rules
- Use non-root user
- Enable audit logging
- Regular security updates

### Integration

#### Q: How do I integrate with Claude Desktop?

**A:** Configure Claude Desktop:
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

#### Q: Can I use this with other AI assistants?

**A:** Yes, the MCP protocol is supported by:
- Claude Desktop
- Continue.dev
- Other MCP-compatible clients

### Troubleshooting

#### Q: Why am I getting "Connection refused" errors?

**A:** Common causes:
- Service not running
- Wrong port number
- Firewall blocking
- Port already in use

#### Q: Why am I getting 401 Unauthorized errors?

**A:** Common causes:
- Invalid API key
- Expired API key
- Missing Authorization header
- Insufficient permissions

### Deployment

#### Q: How do I update to the latest version?

**A:** Update process:
1. Backup current deployment
2. Pull latest changes
3. Update dependencies
4. Restart services
5. Verify functionality

#### Q: Can I deploy on cloud platforms?

**A:** Yes, supported platforms:
- AWS (EC2, ECS, Lambda)
- Google Cloud (Compute Engine, Cloud Run)
- Azure (VMs, Container Instances)
- Heroku
- DigitalOcean

## Debugging Tools and Techniques

### Logging Configuration

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Configure structured logging
export LOG_FORMAT=json
export LOG_FILE=/var/log/mcp/debug.log

# Enable specific module logging
export LOG_MODULES=mcp.adapters.openproject,mcp.services.reports
```

### Debug Mode

```python
# Enable debug mode in Python
import logging
logging.basicConfig(level=logging.DEBUG)

# Debug OpenProject adapter
from mcp.adapters.openproject import OpenProjectAdapter
adapter = OpenProjectAdapter(debug=True)
```

### Performance Profiling

```bash
# Profile Python application
python -m cProfile -o profile.prof app/main.py
python -m pstats profile.prof

# Profile with memory usage
python -m memory_profiler app/main.py

# Monitor real-time performance
htop
# or
glances
```

### Network Debugging

```bash
# Monitor network traffic
tcpdump -i any port 8010
# or
ngrep -d any port 8010

# Test connectivity
telnet localhost 8010
nc -z localhost 8010

# Trace route
traceroute your-openproject.com
```

## Getting Help

### Community Support

- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share experiences
- **Documentation**: Check latest documentation
- **Examples**: Review implementation examples

### Professional Support

- **Email Support**: support@example.com
- **Priority Support**: Available for enterprise customers
- **Consulting**: Custom implementation and integration
- **Training**: On-site and remote training options

### Bug Reports

When reporting bugs, include:
1. Environment details (OS, Python version, etc.)
2. Complete error messages and stack traces
3. Steps to reproduce the issue
4. Expected vs. actual behavior
5. Configuration files (remove sensitive data)

### Feature Requests

When requesting features:
1. Clear description of the feature
2. Use case and benefits
3. Proposed implementation
4. Alternatives considered
5. Priority level

This troubleshooting guide should help resolve most common issues. For additional support, please refer to the community resources or contact professional support.