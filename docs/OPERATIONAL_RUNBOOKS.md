# Operational Runbooks

This document provides comprehensive operational runbooks for managing and monitoring the OpenProject MCP integration solutions in production environments.

## 📋 Table of Contents

1. [Runbook Overview](#runbook-overview)
2. [System Management](#system-management)
3. [Monitoring and Alerting](#monitoring-and-alerting)
4. [Incident Management](#incident-management)
5. [Performance Management](#performance-management)
6. [Security Operations](#security-operations)
7. [Backup and Recovery](#backup-and-recovery)
8. [Scaling Operations](#scaling-operations)
9. [Maintenance Operations](#maintenance-operations)
10. [Disaster Recovery](#disaster-recovery)

## 📚 Runbook Overview

### Purpose
These runbooks provide step-by-step procedures for operating, monitoring, and maintaining the OpenProject MCP integration solutions in production environments.

### Scope
- All four solution types (HTTP, FastAPI, FastMCP, TypeScript)
- Production management and monitoring
- Incident response and recovery
- Performance optimization
- Security operations

### Audience
- System administrators
- DevOps engineers
- Site reliability engineers
- Operations teams

## 🖥️ System Management

### Runbook: System Startup

**ID**: OPS-001  
**Severity**: Normal  
**Estimated Time**: 5-10 minutes

#### Prerequisites
- System is properly installed and configured
- Required services are available (OpenProject, database, cache)
- Environment variables are set correctly

#### Procedure

1. **Verify System Status**
   ```bash
   # Check system resources
   free -h
   df -h
   uptime
   
   # Check network connectivity
   ping -c 4 8.8.8.8
   ```

2. **Start Services**
   ```bash
   # HTTP Solution
   sudo systemctl start mcp-http
   
   # FastAPI Solution
   sudo systemctl start mcp-fastapi
   
   # TypeScript Solution
   pm2 start typescript-mcp
   
   # FastMCP Solution
   pm2 start fastmcp-server
   ```

3. **Verify Service Health**
   ```bash
   # Check HTTP Solution
   curl -f http://localhost:8010/health
   
   # Check FastAPI Solution
   curl -f http://localhost:8020/health
   
   # Check TypeScript Solution
   curl -f http://localhost:3000/health
   ```

4. **Check Logs**
   ```bash
   # HTTP Solution logs
   sudo journalctl -u mcp-http -f
   
   # FastAPI Solution logs
   sudo journalctl -u mcp-fastapi -f
   
   # TypeScript Solution logs
   pm2 logs typescript-mcp
   ```

#### Verification
- All services are running
- Health endpoints return 200 OK
- No critical errors in logs
- Services are accessible via configured endpoints

#### Rollback
```bash
# Stop all services
sudo systemctl stop mcp-http mcp-fastapi
pm2 stop typescript-mcp fastmcp-server

# Check previous status
sudo systemctl status mcp-http mcp-fastapi
pm2 status
```

### Runbook: System Shutdown

**ID**: OPS-002  
**Severity**: Normal  
**Estimated Time**: 2-5 minutes

#### Procedure

1. **Graceful Shutdown**
   ```bash
   # HTTP Solution
   sudo systemctl stop mcp-http
   
   # FastAPI Solution
   sudo systemctl stop mcp-fastapi
   
   # TypeScript Solution
   pm2 stop typescript-mcp
   
   # FastMCP Solution
   pm2 stop fastmcp-server
   ```

2. **Verify Shutdown**
   ```bash
   # Check service status
   sudo systemctl status mcp-http mcp-fastapi
   pm2 status
   
   # Check port usage
   lsof -i :8010
   lsof -i :8020
   lsof -i :3000
   ```

3. **Backup Data (Optional)**
   ```bash
   # Run backup script
   /scripts/backup.sh
   ```

#### Verification
- All services are stopped
- No processes are running on configured ports
- All data is properly saved

### Runbook: Service Restart

**ID**: OPS-003  
**Severity**: Normal  
**Estimated Time**: 3-5 minutes

#### Procedure

1. **Graceful Restart**
   ```bash
   # HTTP Solution
   sudo systemctl restart mcp-http
   
   # FastAPI Solution
   sudo systemctl restart mcp-fastapi
   
   # TypeScript Solution
   pm2 restart typescript-mcp
   
   # FastMCP Solution
   pm2 restart fastmcp-server
   ```

2. **Health Check**
   ```bash
   # Wait 30 seconds, then check health
   sleep 30
   curl -f http://localhost:8010/health
   curl -f http://localhost:8020/health
   curl -f http://localhost:3000/health
   ```

3. **Monitor Logs**
   ```bash
   # Check for startup errors
   sudo journalctl -u mcp-http --since "5 minutes ago"
   sudo journalctl -u mcp-fastapi --since "5 minutes ago"
   pm2 logs typescript-mcp --lines 50
   ```

#### Verification
- Services restart successfully
- Health checks pass
- No startup errors in logs
- Normal response times

## 📊 Monitoring and Alerting

### Runbook: System Health Check

**ID**: MON-001  
**Severity**: Normal  
**Estimated Time**: 2-3 minutes  
**Frequency**: Every 5 minutes

#### Procedure

1. **Check Service Status**
   ```bash
   # System services
   sudo systemctl is-active mcp-http mcp-fastapi
   
   # PM2 services
   pm2 status
   
   # Docker containers
   docker ps
   ```

2. **Check Resource Usage**
   ```bash
   # CPU and memory
   top -bn1 | head -20
   free -h
   
   # Disk usage
   df -h
   du -sh /var/log/*
   ```

3. **Check Application Health**
   ```bash
   # Health endpoints
   curl -s http://localhost:8010/health | jq .
   curl -s http://localhost:8020/health | jq .
   curl -s http://localhost:3000/health | jq .
   ```

4. **Check Database Connectivity**
   ```bash
   # PostgreSQL
   pg_isready -h localhost -p 5432 -U openproject
   
   # Redis
   redis-cli ping
   ```

#### Expected Results
- All services are active
- CPU usage < 80%
- Memory usage < 85%
- Disk usage < 80%
- Health endpoints return healthy status
- Database connections are successful

#### Alert Thresholds
- **Critical**: Service down, CPU > 90%, Memory > 95%, Disk > 90%
- **Warning**: High response times, error rate > 5%, degraded performance

### Runbook: Performance Monitoring

**ID**: MON-002  
**Severity**: Normal  
**Estimated Time**: 5-10 minutes  
**Frequency**: Every 15 minutes

#### Procedure

1. **Check Response Times**
   ```bash
   # Measure response times
   time curl -s http://localhost:8010/health > /dev/null
   time curl -s http://localhost:8020/health > /dev/null
   time curl -s http://localhost:3000/health > /dev/null
   ```

2. **Check Error Rates**
   ```bash
   # Parse logs for errors
   sudo journalctl -u mcp-http --since "1 hour ago" | grep -i error | wc -l
   sudo journalctl -u mcp-fastapi --since "1 hour ago" | grep -i error | wc -l
   
   # Check HTTP status codes
   sudo journalctl -u mcp-http --since "1 hour ago" | grep -o 'HTTP/[0-9.]* [0-9]*' | sort | uniq -c
   ```

3. **Check Database Performance**
   ```bash
   # PostgreSQL queries
   psql -h localhost -U openproject -d openproject -c "SELECT count(*) FROM pg_stat_activity;"
   psql -h localhost -U openproject -d openproject -c "SELECT query, calls, total_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 5;"
   ```

4. **Check Network Performance**
   ```bash
   # Network connections
   netstat -an | grep :8010 | wc -l
   netstat -an | grep :8020 | wc -l
   netstat -an | grep :3000 | wc -l
   
   # Network latency
   ping -c 4 localhost
   ```

#### Expected Results
- Response times < 1 second
- Error rate < 1%
- Database connections < 100
- Network connections stable

#### Performance Baselines
- **HTTP Solution**: < 200ms response time, 100+ req/s
- **FastAPI Solution**: < 100ms response time, 1000+ req/s
- **TypeScript Solution**: < 150ms response time, 800+ req/s
- **FastMCP Solution**: < 50ms response time, 2000+ req/s

### Runbook: Log Analysis

**ID**: MON-003  
**Severity**: Normal  
**Estimated Time**: 10-15 minutes  
**Frequency**: Daily

#### Procedure

1. **Collect Log Files**
   ```bash
   # System logs
   sudo journalctl -u mcp-http --since yesterday > /tmp/mcp-http-logs.log
   sudo journalctl -u mcp-fastapi --since yesterday > /tmp/mcp-fastapi-logs.log
   
   # Application logs
   pm2 logs typescript-mcp --lines 1000 > /tmp/typescript-logs.log
   
   # Access logs
   sudo tail -n 1000 /var/log/nginx/access.log > /tmp/nginx-access.log
   ```

2. **Analyze Error Patterns**
   ```bash
   # Count errors by type
   grep -i error /tmp/mcp-http-logs.log | cut -d: -f5 | sort | uniq -c | sort -nr
   
   # Find frequent error messages
   grep -i error /tmp/mcp-http-logs.log | awk '{print $0}' | sort | uniq -c | sort -nr | head -10
   ```

3. **Analyze Performance Issues**
   ```bash
   # Find slow requests
   grep "slow request" /tmp/mcp-http-logs.log | tail -20
   
   # Check for timeouts
   grep -i timeout /tmp/mcp-http-logs.log | wc -l
   ```

4. **Generate Daily Report**
   ```bash
   # Create summary report
   echo "Daily Log Analysis Report - $(date)" > /tmp/daily-report.log
   echo "=================================" >> /tmp/daily-report.log
   echo "HTTP Solution Errors: $(grep -i error /tmp/mcp-http-logs.log | wc -l)" >> /tmp/daily-report.log
   echo "FastAPI Solution Errors: $(grep -i error /tmp/mcp-fastapi-logs.log | wc -l)" >> /tmp/daily-report.log
   echo "Total Requests: $(wc -l < /tmp/nginx-access.log)" >> /tmp/daily-report.log
   echo "Error Rate: $(echo "scale=2; $(grep -i error /tmp/mcp-http-logs.log | wc -l) / $(wc -l < /tmp/nginx-access.log) * 100" | bc)%" >> /tmp/daily-report.log
   ```

#### Expected Results
- Error rate < 1%
- No critical errors
- Performance within acceptable limits
- Log files are manageable in size

## 🚨 Incident Management

### Runbook: Service Outage

**ID**: INC-001  
**Severity**: Critical  
**Estimated Time**: 15-30 minutes

#### Detection
- Health checks failing
- Service not responding
- High error rates
- Alerts from monitoring system

#### Procedure

1. **Assess Impact**
   ```bash
   # Check service status
   sudo systemctl status mcp-http mcp-fastapi
   pm2 status
   
   # Check health endpoints
   curl -v http://localhost:8010/health
   curl -v http://localhost:8020/health
   curl -v http://localhost:3000/health
   
   # Check recent logs
   sudo journalctl -u mcp-http --since "10 minutes ago" | tail -50
   ```

2. **Identify Root Cause**
   ```bash
   # Check system resources
   top -bn1 | head -20
   free -h
   df -h
   
   # Check network connectivity
   netstat -tuln | grep -E ':8010|:8020|:3000'
   
   # Check database connectivity
   pg_isready -h localhost -p 5432 -U openproject
   redis-cli ping
   ```

3. **Restore Service**
   ```bash
   # Restart services
   sudo systemctl restart mcp-http mcp-fastapi
   pm2 restart all
   
   # If restart fails, check configuration
   sudo systemctl status mcp-http
   pm2 status
   
   # Check for configuration errors
   sudo journalctl -u mcp-http -p err --since "1 hour ago"
   ```

4. **Verify Restoration**
   ```bash
   # Test health endpoints
   curl -f http://localhost:8010/health
   curl -f http://localhost:8020/health
   curl -f http://localhost:3000/health
   
   # Test basic functionality
   curl -f http://localhost:8010/api/projects
   curl -f http://localhost:8020/api/v1/projects
   curl -f http://localhost:3000/api/v1/projects
   ```

#### Communication
- Notify stakeholders of outage
- Provide estimated resolution time
- Update incident status
- Document root cause

#### Post-Incident Review
- Document incident timeline
- Identify root cause
- Implement preventive measures
- Update runbooks if needed

### Runbook: Performance Degradation

**ID**: INC-002  
**Severity**: Warning  
**Estimated Time**: 30-60 minutes

#### Detection
- Response times exceeding thresholds
- High CPU/memory usage
- Increased error rates
- User complaints about slowness

#### Procedure

1. **Assess Performance**
   ```bash
   # Check response times
   time curl -s http://localhost:8010/health > /dev/null
   time curl -s http://localhost:8020/health > /dev/null
   
   # Check resource usage
   top -bn1 | head -20
   free -h
   
   # Check database performance
   psql -h localhost -U openproject -d openproject -c "SELECT count(*) FROM pg_stat_activity;"
   ```

2. **Identify Bottlenecks**
   ```bash
   # Check slow queries
   psql -h localhost -U openproject -d openproject -c "SELECT query, calls, total_time, mean_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
   
   # Check network connections
   netstat -an | grep :8010 | wc -l
   netstat -an | grep :8020 | wc -l
   
   # Check application logs for performance issues
   sudo journalctl -u mcp-http --since "1 hour ago" | grep -i "slow\|timeout"
   ```

3. **Optimize Performance**
   ```bash
   # Clear cache if needed
   redis-cli FLUSHDB
   
   # Restart services to clear memory
   sudo systemctl restart mcp-http mcp-fastapi
   pm2 restart all
   
   # Adjust worker processes if needed
   sudo systemctl edit mcp-http
   # Update worker count based on CPU cores
   ```

4. **Monitor Improvement**
   ```bash
   # Monitor response times
   for i in {1..10}; do
     echo "Check $i:"
     time curl -s http://localhost:8010/health > /dev/null
     sleep 5
   done
   ```

#### Verification
- Response times return to normal
- Resource usage within acceptable limits
- Error rates return to normal
- User complaints resolved

### Runbook: Database Connection Issues

**ID**: INC-003  
**Severity**: Critical  
**Estimated Time**: 20-40 minutes

#### Detection
- Database connection errors in logs
- Health checks failing with database errors
- Applications unable to connect to database

#### Procedure

1. **Assess Database Status**
   ```bash
   # Check PostgreSQL status
   sudo systemctl status postgresql
   
   # Check database connectivity
   pg_isready -h localhost -p 5432 -U openproject
   
   # Check database logs
   sudo tail -n 50 /var/log/postgresql/postgresql-15-main.log
   ```

2. **Check Database Resources**
   ```bash
   # Check database connections
   psql -h localhost -U openproject -d openproject -c "SELECT count(*) FROM pg_stat_activity;"
   
   # Check database size
   psql -h localhost -U openproject -d openproject -c "SELECT pg_size_pretty(pg_database_size('openproject'));"
   
   # Check table locks
   psql -h localhost -U openproject -d openproject -c "SELECT locktype, relation::regclass, mode FROM pg_locks WHERE granted = false;"
   ```

3. **Resolve Connection Issues**
   ```bash
   # Restart PostgreSQL if needed
   sudo systemctl restart postgresql
   
   # Check connection limits
   psql -h localhost -U openproject -d openproject -c "SHOW max_connections;"
   
   # Clear stale connections if needed
   psql -h localhost -U openproject -d openproject -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND now() - query_start > interval '5 minutes';"
   ```

4. **Verify Application Connectivity**
   ```bash
   # Test application database connections
   sudo systemctl restart mcp-http mcp-fastapi
   pm2 restart all
   
   # Check application logs
   sudo journalctl -u mcp-http --since "5 minutes ago" | tail -20
   ```

#### Verification
- Database service is running
- Applications can connect to database
- Health checks passing
- No database connection errors in logs

## ⚡ Performance Management

### Runbook: Performance Tuning

**ID**: PERF-001  
**Severity**: Normal  
**Estimated Time**: 30-60 minutes

#### Procedure

1. **Analyze Current Performance**
   ```bash
   # Check current response times
   ab -n 100 -c 10 http://localhost:8010/health
   
   # Check resource usage
   top -bn1 | head -20
   free -h
   
   # Check database performance
   psql -h localhost -U openproject -d openproject -c "SELECT query, calls, total_time, mean_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
   ```

2. **Optimize HTTP Solution**
   ```bash
   # Update Gunicorn configuration
   sudo nano /etc/systemd/system/mcp-http.service
   
   # Update worker count
   # workers = multiprocessing.cpu_count() * 2 + 1
   # worker_class = 'sync'
   # worker_connections = 1000
   
   # Restart service
   sudo systemctl daemon-reload
   sudo systemctl restart mcp-http
   ```

3. **Optimize FastAPI Solution**
   ```bash
   # Update Uvicorn configuration
   sudo nano /etc/systemd/system/mcp-fastapi.service
   
   # Update worker settings
   # workers = 4
   # worker_class = 'uvicorn.workers.UvicornWorker'
   # limit_concurrency = 1000
   
   # Restart service
   sudo systemctl daemon-reload
   sudo systemctl restart mcp-fastapi
   ```

4. **Optimize Database**
   ```bash
   # Update PostgreSQL configuration
   sudo nano /etc/postgresql/15/main/postgresql.conf
   
   # Update performance settings
   # shared_buffers = 256MB
   # effective_cache_size = 1GB
   # maintenance_work_mem = 64MB
   # checkpoint_completion_target = 0.9
   # wal_buffers = 16MB
   # default_statistics_target = 100
   
   # Restart PostgreSQL
   sudo systemctl restart postgresql
   ```

5. **Optimize Cache**
   ```bash
   # Update Redis configuration
   sudo nano /etc/redis/redis.conf
   
   # Update memory settings
   # maxmemory 512mb
   # maxmemory-policy allkeys-lru
   
   # Restart Redis
   sudo systemctl restart redis
   ```

#### Verification
- Improved response times
- Reduced resource usage
- Better database performance
- No performance degradation

### Runbook: Load Testing

**ID**: PERF-002  
**Severity**: Normal  
**Estimated Time**: 30-45 minutes

#### Procedure

1. **Prepare Load Test**
   ```bash
   # Install load testing tools
   sudo apt-get install apache2-utils
   
   # Create test script
   cat > /tmp/load-test.sh << 'EOF'
   #!/bin/bash
   echo "Starting load test at $(date)"
   
   # Test HTTP Solution
   echo "Testing HTTP Solution..."
   ab -n 1000 -c 50 http://localhost:8010/health > /tmp/http-load-test.log
   
   # Test FastAPI Solution
   echo "Testing FastAPI Solution..."
   ab -n 1000 -c 50 http://localhost:8020/health > /tmp/fastapi-load-test.log
   
   # Test TypeScript Solution
   echo "Testing TypeScript Solution..."
   ab -n 1000 -c 50 http://localhost:3000/health > /tmp/typescript-load-test.log
   
   echo "Load test completed at $(date)"
   EOF
   
   chmod +x /tmp/load-test.sh
   ```

2. **Run Load Test**
   ```bash
   # Execute load test
   /tmp/load-test.sh
   
   # Monitor system during test
   top -bn1 | head -20
   free -h
   
   # Check application logs
   sudo journalctl -u mcp-http --since "5 minutes ago" | tail -20
   ```

3. **Analyze Results**
   ```bash
   # Parse results
   echo "HTTP Solution Results:"
   grep "Requests per second" /tmp/http-load-test.log
   grep "Time per request" /tmp/http-load-test.log
   
   echo "FastAPI Solution Results:"
   grep "Requests per second" /tmp/fastapi-load-test.log
   grep "Time per request" /tmp/fastapi-load-test.log
   
   echo "TypeScript Solution Results:"
   grep "Requests per second" /tmp/typescript-load-test.log
   grep "Time per request" /tmp/typescript-load-test.log
   ```

4. **Generate Report**
   ```bash
   # Create performance report
   cat > /tmp/performance-report-$(date +%Y%m%d).log << EOF
   Performance Load Test Report - $(date)
   ========================================
   
   HTTP Solution:
   - Requests per second: $(grep "Requests per second" /tmp/http-load-test.log | awk '{print $4}')
   - Time per request: $(grep "Time per request" /tmp/http-load-test.log | awk '{print $4}')
   
   FastAPI Solution:
   - Requests per second: $(grep "Requests per second" /tmp/fastapi-load-test.log | awk '{print $4}')
   - Time per request: $(grep "Time per request" /tmp/fastapi-load-test.log | awk '{print $4}')
   
   TypeScript Solution:
   - Requests per second: $(grep "Requests per second" /tmp/typescript-load-test.log | awk '{print $4}')
   - Time per request: $(grep "Time per request" /tmp/typescript-load-test.log | awk '{print $4}')
   
   System Resources During Test:
   - CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')
   - Memory Usage: $(free -h | grep Mem | awk '{print $3 "/" $2}')
   
   EOF
   ```

#### Expected Results
- HTTP Solution: 100+ requests/second, <200ms response time
- FastAPI Solution: 1000+ requests/second, <100ms response time
- TypeScript Solution: 800+ requests/second, <150ms response time
- System resources within acceptable limits

## 🔒 Security Operations

### Runbook: Security Audit

**ID**: SEC-001  
**Severity**: Normal  
**Estimated Time**: 60-90 minutes  
**Frequency**: Monthly

#### Procedure

1. **Review Access Controls**
   ```bash
   # Check user accounts
   sudo cut -d: -f1,3 /etc/passwd | grep -E '^[^:]*:[0-9]{4}$'
   
   # Check sudo access
   sudo grep -i sudo /etc/group
   
   # Check SSH access
   sudo grep -i ssh /etc/passwd
   ```

2. **Review SSL/TLS Configuration**
   ```bash
   # Check SSL certificate expiration
   openssl x509 -in /etc/ssl/certs/mcp.yourdomain.com.crt -noout -dates
   
   # Test SSL configuration
   openssl s_client -connect mcp.yourdomain.com:443 -tls1_2
   
   # Check SSL protocols
   nmap --script ssl-enum-ciphers -p 443 mcp.yourdomain.com
   ```

3. **Review Firewall Rules**
   ```bash
   # Check iptables rules
   sudo iptables -L -n -v
   
   # Check ufw status
   sudo ufw status
   
   # Check open ports
   sudo netstat -tuln
   ```

4. **Review Application Security**
   ```bash
   # Check environment variables
   sudo grep -r "API_KEY\|PASSWORD" /etc/systemd/system/
   
   # Check file permissions
   sudo find /opt/mcp* -type f -name "*.env" -ls
   
   # Check log files for security issues
   sudo grep -i "authentication\|authorization\|security" /var/log/mcp*/*
   ```

5. **Review Dependencies**
   ```bash
   # Check for outdated packages
   sudo apt list --upgradable
   
   # Check Python packages for vulnerabilities
   pip-audit --requirement /opt/mcp-http/requirements.txt
   
   # Check Node.js packages for vulnerabilities
   npm audit --production
   ```

#### Security Checklist
- [ ] All user accounts have strong passwords
- [ ] SSL certificates are valid and not expired
- [ ] Firewall rules are restrictive
- [ ] No hardcoded secrets in configuration files
- [ ] All dependencies are up to date
- [ ] Log files are properly secured
- [ ] Backup procedures are in place
- [ ] Access controls are properly configured

### Runbook: Security Incident Response

**ID**: SEC-002  
**Severity**: Critical  
**Estimated Time**: Variable

#### Detection
- Security alerts from monitoring systems
- Unusual login attempts
- Suspicious network activity
- Data breach indicators

#### Procedure

1. **Assess Situation**
   ```bash
   # Check system logs for suspicious activity
   sudo grep -i "failed\|error\|attack" /var/log/auth.log | tail -50
   
   # Check network connections
   sudo netstat -tuln | grep -E ':8010|:8020|:3000'
   
   # Check running processes
   sudo ps aux | grep -E 'mcp|http|fastapi'
   ```

2. **Contain Incident**
   ```bash
   # Stop affected services
   sudo systemctl stop mcp-http mcp-fastapi
   pm2 stop all
   
   # Block suspicious IP addresses
   sudo iptables -A INPUT -s suspicious_ip -j DROP
   
   # Change passwords
   sudo passwd openproject_user
   ```

3. **Investigate Incident**
   ```bash
   # Collect evidence
   sudo tar -czf /tmp/security-incident-$(date +%Y%m%d).tar.gz \
     /var/log/mcp* \
     /var/log/auth.log \
     /var/log/nginx/access.log
   
   # Analyze logs
   sudo grep -i "attack\|breach\|unauthorized" /var/log/mcp*/*
   ```

4. **Recover and Restore**
   ```bash
   # Restore from backup if needed
   /scripts/restore.sh /backups/clean-backup.tar.gz
   
   # Restart services
   sudo systemctl start mcp-http mcp-fastapi
   pm2 start all
   
   # Verify functionality
   curl -f http://localhost:8010/health
   curl -f http://localhost:8020/health
   ```

#### Documentation
- Document incident timeline
- Preserve evidence
- Create incident report
- Implement preventive measures

## 💾 Backup and Recovery

### Runbook: Backup System

**ID**: BKP-001  
**Severity**: Normal  
**Estimated Time**: 15-30 minutes  
**Frequency**: Daily

#### Procedure

1. **Prepare Backup**
   ```bash
   # Create backup directory
   BACKUP_DIR="/backups/$(date +%Y%m%d)"
   mkdir -p "$BACKUP_DIR"
   
   # Check available disk space
   df -h
   ```

2. **Backup Application Data**
   ```bash
   # Backup configuration files
   sudo cp -r /etc/systemd/system/mcp* "$BACKUP_DIR/"
   sudo cp -r /opt/mcp* "$BACKUP_DIR/"
   
   # Backup environment files
   sudo cp -r /opt/mcp*/.env* "$BACKUP_DIR/"
   
   # Backup templates
   sudo cp -r /opt/mcp*/templates "$BACKUP_DIR/"
   ```

3. **Backup Database**
   ```bash
   # Backup PostgreSQL
   sudo pg_dump -h localhost -U openproject -d openproject > "$BACKUP_DIR/openproject.sql"
   
   # Backup Redis
   sudo docker exec redis redis-cli --rdb "$BACKUP_DIR/redis_dump.rdb"
   ```

4. **Backup Logs**
   ```bash
   # Backup application logs
   sudo cp -r /var/log/mcp* "$BACKUP_DIR/"
   sudo cp -r /var/log/nginx "$BACKUP_DIR/"
   
   # Backup system logs
   sudo journalctl -u mcp-http --since "1 week ago" > "$BACKUP_DIR/mcp-http-journal.log"
   sudo journalctl -u mcp-fastapi --since "1 week ago" > "$BACKUP_DIR/mcp-fastapi-journal.log"
   ```

5. **Compress and Verify**
   ```bash
   # Compress backup
   tar -czf "$BACKUP_DIR.tar.gz" -C "$(dirname "$BACKUP_DIR")" "$(basename "$BACKUP_DIR")"
   
   # Verify backup
   tar -tzf "$BACKUP_DIR.tar.gz" | head -10
   
   # Test restore (optional)
   mkdir -p /tmp/backup-test
   tar -xzf "$BACKUP_DIR.tar.gz" -C /tmp/backup-test
   ```

6. **Cleanup Old Backups**
   ```bash
   # Keep last 7 days of backups
   find /backups -name "*.tar.gz" -mtime +7 -delete
   
   # Check backup size
   du -sh /backups
   ```

#### Verification
- Backup files created successfully
- Backup files are not corrupted
- Backup size is reasonable
- Old backups are properly cleaned up

### Runbook: Restore System

**ID**: BKP-002  
**Severity**: Critical  
**Estimated Time**: 30-60 minutes

#### Procedure

1. **Prepare for Restore**
   ```bash
   # Stop services
   sudo systemctl stop mcp-http mcp-fastapi
   pm2 stop all
   
   # Identify backup file
   ls -la /backups/*.tar.gz | tail -5
   BACKUP_FILE="/backups/$(ls -t /backups/*.tar.gz | head -1)"
   ```

2. **Extract Backup**
   ```bash
   # Create restore directory
   RESTORE_DIR="/tmp/restore-$(date +%Y%m%d)"
   mkdir -p "$RESTORE_DIR"
   
   # Extract backup
   tar -xzf "$BACKUP_FILE" -C "$RESTORE_DIR"
   
   # Verify extracted files
   ls -la "$RESTORE_DIR"
   ```

3. **Restore Configuration**
   ```bash
   # Restore systemd services
   sudo cp "$RESTORE_DIR"/mcp*.service /etc/systemd/system/
   sudo systemctl daemon-reload
   
   # Restore application files
   sudo cp -r "$RESTORE_DIR"/mcp* /opt/
   sudo chown -R mcpuser:mcpuser /opt/mcp*
   
   # Restore environment files
   sudo cp "$RESTORE_DIR"/.env* /opt/mcp*/
   ```

4. **Restore Database**
   ```bash
   # Restore PostgreSQL
   sudo -u postgres dropdb openproject
   sudo -u postgres createdb openproject
   sudo -u postgres psql -d openproject < "$RESTORE_DIR/openproject.sql"
   
   # Restore Redis
   sudo docker cp "$RESTORE_DIR"/redis_dump.rdb redis:/data/dump.rdb
   sudo docker exec redis redis-cli BGSAVE
   ```

5. **Start Services**
   ```bash
   # Start services
   sudo systemctl start mcp-http mcp-fastapi
   pm2 start all
   
   # Wait for services to start
   sleep 30
   ```

6. **Verify Restoration**
   ```bash
   # Check service status
   sudo systemctl status mcp-http mcp-fastapi
   pm2 status
   
   # Test health endpoints
   curl -f http://localhost:8010/health
   curl -f http://localhost:8020/health
   
   # Test basic functionality
   curl -f http://localhost:8010/api/projects
   curl -f http://localhost:8020/api/v1/projects
   ```

#### Verification
- Services start successfully
- Health checks pass
- Data is restored correctly
- No errors in logs

## 📈 Scaling Operations

### Runbook: Scale Up Resources

**ID**: SCL-001  
**Severity**: Normal  
**Estimated Time**: 15-30 minutes

#### Procedure

1. **Assess Current Load**
   ```bash
   # Check current resource usage
   top -bn1 | head -20
   free -h
   
   # Check application performance
   curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8010/health
   
   # Check database performance
   psql -h localhost -U openproject -d openproject -c "SELECT count(*) FROM pg_stat_activity;"
   ```

2. **Scale Up HTTP Solution**
   ```bash
   # Update Gunicorn configuration
   sudo nano /etc/systemd/system/mcp-http.service
   
   # Increase worker count
   # Environment="GUNICORN_WORKERS=8"
   # Environment="WORKER_CONNECTIONS=2000"
   
   # Restart service
   sudo systemctl daemon-reload
   sudo systemctl restart mcp-http
   ```

3. **Scale Up FastAPI Solution**
   ```bash
   # Update Uvicorn configuration
   sudo nano /etc/systemd/system/mcp-fastapi.service
   
   # Increase worker count
   # Environment="UVICORN_WORKERS=8"
   # Environment="LIMIT_CONCURRENCY=2000"
   
   # Restart service
   sudo systemctl daemon-reload
   sudo systemctl restart mcp-fastapi
   ```

4. **Scale Database Resources**
   ```bash
   # Update PostgreSQL configuration
   sudo nano /etc/postgresql/15/main/postgresql.conf
   
   # Increase memory settings
   # shared_buffers = 512MB
   # effective_cache_size = 2GB
   # maintenance_work_mem = 128MB
   
   # Restart PostgreSQL
   sudo systemctl restart postgresql
   ```

5. **Monitor After Scaling**
   ```bash
   # Monitor resource usage
   top -bn1 | head -20
   free -h
   
   # Monitor performance
   for i in {1..10}; do
     curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8010/health
     sleep 5
   done
   ```

#### Verification
- Improved resource utilization
- Better performance under load
- Services remain stable
- No scaling-related errors

### Runbook: Scale Out (Multiple Instances)

**ID**: SCL-002  
**Severity**: Normal  
**Estimated Time**: 30-45 minutes

#### Procedure

1. **Prepare Load Balancer**
   ```bash
   # Update nginx configuration
   sudo nano /etc/nginx/nginx.conf
   
   # Add upstream blocks
   # upstream mcp_http_backend {
   #     server 10.0.1.10:8010;
   #     server 10.0.1.11:8010;
   #     server 10.0.1.12:8010;
   # }
   ```

2. **Deploy Additional Instances**
   ```bash
   # Clone configuration to new servers
   scp -r /opt/mcp-http user@new-server:/opt/
   scp -r /etc/systemd/system/mcp-http.service user@new-server:/etc/systemd/system/
   
   # Start services on new servers
   ssh user@new-server "sudo systemctl daemon-reload"
   ssh user@new-server "sudo systemctl start mcp-http"
   ```

3. **Configure Database for Multiple Instances**
   ```bash
   # Update PostgreSQL connection pool
   sudo nano /etc/postgresql/15/main/postgresql.conf
   
   # Increase max_connections
   # max_connections = 200
   
   # Restart PostgreSQL
   sudo systemctl restart postgresql
   ```

4. **Configure Load Balancer**
   ```bash
   # Update proxy configuration
   sudo nano /etc/nginx/sites-available/mcp-http
   
   # Configure load balancing
   # location / {
   #     proxy_pass http://mcp_http_backend;
   #     proxy_set_header Host $host;
   #     proxy_set_header X-Real-IP $remote_addr;
   #     proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
   # }
   
   # Restart nginx
   sudo systemctl restart nginx
   ```

5. **Verify Load Balancing**
   ```bash
   # Test load distribution
   for i in {1..10}; do
     curl -s http://load-balancer/health | grep -o "hostname"
     sleep 1
   done
   
   # Monitor individual instances
   curl -s http://10.0.1.10:8010/health
   curl -s http://10.0.1.11:8010/health
   curl -s http://10.0.1.12:8010/health
   ```

#### Verification
- Load balancer distributing traffic
- All instances healthy
- Improved overall performance
- No single point of failure

## 🔧 Maintenance Operations

### Runbook: System Update

**ID**: MAINT-001  
**Severity**: Normal  
**Estimated Time**: 60-120 minutes  
**Frequency**: Monthly

#### Procedure

1. **Prepare for Maintenance**
   ```bash
   # Notify users of maintenance
   echo "System maintenance starting at $(date)" | mail -s "Maintenance Notice" admin@yourdomain.com
   
   # Create backup
   /scripts/backup.sh
   
   # Check current system state
   sudo systemctl status mcp-http mcp-fastapi
   pm2 status
   ```

2. **Update System Packages**
   ```bash
   # Update package lists
   sudo apt update
   
   # Upgrade packages
   sudo apt upgrade -y
   
   # Check for broken packages
   sudo apt --fix-broken install -y
   ```

3. **Update Application Dependencies**
   ```bash
   # Update Python packages
   cd /opt/mcp-http
   sudo -u mcpuser pip install -r requirements.txt --upgrade
   sudo -u mcpuser pip install -r requirements.txt --upgrade --upgrade-strategy eager
   
   # Update Node.js packages
   cd /opt/mcp-typescript
   sudo -u nodeuser npm update --save
   ```

4. **Update Security Patches**
   ```bash
   # Install security updates
   sudo unattended-upgrade -d
   
   # Check for vulnerabilities
   sudo apt audit
   sudo pip-audit --requirement /opt/mcp-http/requirements.txt
   npm audit --production
   ```

5. **Restart Services**
   ```bash
   # Restart all services
   sudo systemctl restart mcp-http mcp-fastapi
   pm2 restart all
   
   # Wait for services to start
   sleep 30
   ```

6. **Verify System**
   ```bash
   # Check service status
   sudo systemctl status mcp-http mcp-fastapi
   pm2 status
   
   # Test health endpoints
   curl -f http://localhost:8010/health
   curl -f http://localhost:8020/health
   
   # Test basic functionality
   curl -f http://localhost:8010/api/projects
   curl -f http://localhost:8020/api/v1/projects
   ```

7. **Complete Maintenance**
   ```bash
   # Notify users of maintenance completion
   echo "System maintenance completed at $(date)" | mail -s "Maintenance Complete" admin@yourdomain.com
   
   # Document maintenance
   echo "Maintenance completed on $(date)" >> /var/log/maintenance.log
   ```

#### Verification
- All services running normally
- No functionality issues
- Performance within acceptable limits
- No security vulnerabilities

### Runbook: Log Rotation

**ID**: MAINT-002  
**Severity**: Normal  
**Estimated Time**: 5-10 minutes  
**Frequency**: Weekly

#### Procedure

1. **Check Log Sizes**
   ```bash
   # Check application logs
   du -sh /var/log/mcp*
   du -sh /opt/mcp*/logs/*
   
   # Check system logs
   du -sh /var/log/syslog
   du -sh /var/log/auth.log
   ```

2. **Rotate Application Logs**
   ```bash
   # Rotate HTTP Solution logs
   sudo logrotate -f /etc/logrotate.d/mcp-http
   
   # Rotate FastAPI Solution logs
   sudo logrotate -f /etc/logrotate.d/mcp-fastapi
   
   # Rotate TypeScript Solution logs
   pm2 logrotate
   ```

3. **Rotate System Logs**
   ```bash
   # Rotate system logs
   sudo logrotate -f /etc/logrotate.d/syslog
   sudo logrotate -f /etc/logrotate.d/auth.log
   ```

4. **Compress Old Logs**
   ```bash
   # Compress logs older than 7 days
   find /var/log/mcp* -name "*.log.*" -mtime +7 -exec gzip {} \;
   find /var/log -name "*.log.*" -mtime +7 -exec gzip {} \;
   ```

5. **Clean Up Old Logs**
   ```bash
   # Remove logs older than 30 days
   find /var/log/mcp* -name "*.gz" -mtime +30 -delete
   find /var/log -name "*.gz" -mtime +30 -delete
   ```

#### Verification
- Log files are rotated
- Old logs are compressed
- Disk space is freed
- No log rotation errors

## 🌋 Disaster Recovery

### Runbook: Complete System Recovery

**ID**: DR-001  
**Severity**: Critical  
**Estimated Time**: 2-4 hours

#### Procedure

1. **Assess Disaster Scope**
   ```bash
   # Check system status
   sudo systemctl status
   pm2 status
   
   # Check network connectivity
   ping -c 4 8.8.8.8
   
   # Check disk integrity
   sudo fsck -t ext4 /dev/sda1
   ```

2. **Boot into Recovery Mode**
   ```bash
   # Reboot into recovery mode
   sudo reboot
   
   # Select recovery mode from GRUB menu
   ```

3. **Restore from Backup**
   ```bash
   # Mount backup drive
   sudo mount /dev/sdb1 /mnt/backup
   
   # Restore system configuration
   sudo cp -r /mnt/backup/etc/systemd/system/mcp* /etc/systemd/system/
   sudo cp -r /mnt/backup/opt/mcp* /opt/
   
   # Restore data
   sudo cp -r /mnt/backup/var/lib/postgresql /var/lib/
   sudo cp -r /mnt/backup/var/lib/redis /var/lib/
   ```

4. **Rebuild Services**
   ```bash
   # Reinstall packages
   sudo apt update
   sudo apt install -y python3 python3-pip nodejs npm postgresql redis-server
   
   # Restore application dependencies
   cd /opt/mcp-http
   sudo -u mcpuser pip install -r requirements.txt
   
   cd /opt/mcp-typescript
   sudo -u nodeuser npm install --production
   ```

5. **Restore Database**
   ```bash
   # Start PostgreSQL
   sudo systemctl start postgresql
   
   # Restore database
   sudo -u postgres createdb openproject
   sudo -u postgres psql -d openproject < /mnt/backup/openproject.sql
   
   # Start Redis
   sudo systemctl start redis
   sudo docker cp /mnt/backup/redis_dump.rdb redis:/data/dump.rdb
   ```

6. **Start Services**
   ```bash
   # Start all services
   sudo systemctl daemon-reload
   sudo systemctl start mcp-http mcp-fastapi postgresql redis
   pm2 start all
   
   # Wait for services to start
   sleep 60
   ```

7. **Verify Recovery**
   ```bash
   # Check service status
   sudo systemctl status mcp-http mcp-fastapi
   pm2 status
   
   # Test health endpoints
   curl -f http://localhost:8010/health
   curl -f http://localhost:8020/health
   
   # Test full functionality
   curl -f http://localhost:8010/api/projects
   curl -f http://localhost:8020/api/v1/projects
   
   # Test database connectivity
   psql -h localhost -U openproject -d openproject -c "SELECT count(*) FROM projects;"
   ```

#### Verification
- All services running
- Data integrity verified
- Functionality restored
- Performance acceptable

#### Documentation
- Document recovery process
- Update disaster recovery plan
- Identify root cause
- Implement preventive measures

## 📋 Runbook Maintenance

### Runbook Updates
- Review runbooks monthly
- Update procedures based on incidents
- Add new runbooks for new features
- Test runbook procedures quarterly

### Runbook Testing
- Test critical runbooks quarterly
- Test disaster recovery annually
- Update runbooks based on test results
- Document runbook test results

### Runbook Distribution
- Ensure runbooks are accessible
- Train operations team on runbooks
- Maintain runbook version control
- Archive outdated runbooks

This comprehensive set of operational runbooks provides detailed procedures for managing, monitoring, and maintaining the OpenProject MCP integration solutions in production environments.