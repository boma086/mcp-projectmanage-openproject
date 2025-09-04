# Production Deployment Guide

This guide provides comprehensive instructions for deploying MCP OpenProject solutions to production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Deployment Strategies](#deployment-strategies)
4. [Step-by-Step Deployment](#step-by-step-deployment)
5. [Monitoring and Alerting](#monitoring-and-alerting)
6. [Backup and Disaster Recovery](#backup-and-disaster-recovery)
7. [Security Hardening](#security-hardening)
8. [High Availability](#high-availability)
9. [Troubleshooting](#troubleshooting)
10. [Maintenance and Operations](#maintenance-and-operations)

## Prerequisites

### Infrastructure Requirements

- **Kubernetes Cluster**: v1.21+ with at least 10 nodes
- **Compute Resources**: 
  - Minimum 20 vCPUs
  - 40GB RAM
  - 500GB storage
- **Network**: Multi-AZ deployment with proper VPC configuration
- **Load Balancers**: ALB and NLB support
- **DNS**: Wildcard domain for applications

### Software Requirements

- **kubectl**: v1.21+
- **Helm**: v3.0+
- **AWS CLI**: v2.0+
- **Istio**: v1.12+ (optional, for advanced traffic management)
- **Docker**: v20.0+

### Access Requirements

- **AWS Account**: With appropriate IAM permissions
- **Kubernetes Access**: Admin access to the cluster
- **Domain Access**: Ability to manage DNS records
- **SSL Certificates**: Wildcard SSL certificate for the domain

## Architecture Overview

### Production Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Internet Gateway                             │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                      Load Balancer                               │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │           ALB (Application Load Balancer)                 │ │
│  │  - SSL Termination                                         │ │
│  │  - WAF Integration                                         │ │
│  │  - Rate Limiting                                            │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                      Ingress Controller                         │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │            NGINX Ingress Controller                         │ │
│  │  - Multi-host routing                                       │ │
│  │  - SSL configuration                                        │ │
│  │  - Path-based routing                                       │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                   Application Services                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │ HTTP Sol.   │ │ FastAPI Sol. │ │ FastMCP Sol.│ │ TypeScript  │ │
│  │             │ │             │ │             │ │    Sol.     │ │
│  │  - 3 replicas│ │  - 3 replicas│ │  - 3 replicas│ │  - 3 replicas│ │
│  │  - HPA       │ │  - HPA       │ │  - HPA       │ │  - HPA       │ │
│  │  - PDB       │ │  - PDB       │ │  - PDB       │ │  - PDB       │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                   Data Services                                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │ PostgreSQL  │ │    Redis    │ │ Prometheus  │ │  Grafana    │ │
│  │   Cluster   │ │   Cluster   │ │             │ │             │ │
│  │             │ │             │ │             │ │             │ │
│  │  - 3 nodes  │ │  - 6 nodes  │ │  - HA config │ │  - Dashboards│ │
│  │  - Replication│ │  - Sharding │ │  - Alerting  │ │  - Alerting │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

1. **Load Balancer**: Handles external traffic with SSL termination
2. **Ingress Controller**: Manages routing to different services
3. **Application Services**: Four solution types with auto-scaling
4. **Data Services**: High-availability database and cache clusters
5. **Monitoring**: Comprehensive monitoring and alerting system

## Deployment Strategies

### 1. Rolling Deployment

**When to use**: Standard deployments with minimal downtime
**Benefits**: Gradual rollout, easy rollback
**Commands**:
```bash
./scripts/production-deploy.sh --deployment-type rolling --solution all
```

### 2. Blue-Green Deployment

**When to use**: Critical updates requiring zero downtime
**Benefits**: Zero downtime, immediate rollback capability
**Commands**:
```bash
./scripts/production-deploy.sh --deployment-type blue-green --solution all
```

### 3. Canary Deployment

**When to use**: Testing new features with limited traffic
**Benefits**: Risk mitigation, gradual traffic increase
**Commands**:
```bash
./scripts/production-deploy.sh --deployment-type canary --solution all
```

## Step-by-Step Deployment

### Phase 1: Environment Preparation

1. **Create Kubernetes Cluster**
```bash
# Create EKS cluster
eksctl create cluster --name mcp-openproject-prod --region us-west-2 --node-type m5.large --nodes 10

# Update kubeconfig
aws eks update-kubeconfig --name mcp-openproject-prod --region us-west-2
```

2. **Install Required Tools**
```bash
# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install Istio (optional)
curl -L https://istio.io/downloadIstio | sh -
cd istio-*
export PATH=$PWD/bin:$PATH
istioctl install --set profile=demo
```

3. **Configure DNS**
```bash
# Create Route53 hosted zone
aws route53 create-hosted-zone --name mcp-openproject.example.com --caller-reference $(date +%s)
```

### Phase 2: Infrastructure Deployment

1. **Deploy Base Infrastructure**
```bash
# Apply namespace and configurations
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmaps.yaml

# Deploy infrastructure services
kubectl apply -f k8s/infrastructure.yaml
```

2. **Setup High Availability**
```bash
# Apply HA configurations
kubectl apply -f k8s/high-availability.yaml

# Wait for services to be ready
kubectl wait --for=condition=ready pod -l app=postgres-ha -n mcp-openproject --timeout=300s
```

### Phase 3: Security and Monitoring

1. **Apply Security Hardening**
```bash
# Apply security configurations
kubectl apply -f k8s/security-hardening.yaml
kubectl apply -f k8s/production-ingress.yaml
```

2. **Setup Monitoring**
```bash
# Deploy monitoring stack
kubectl apply -f k8s/production-monitoring.yaml

# Setup Grafana dashboards
kubectl apply -f monitoring/grafana/dashboards/
```

### Phase 4: Application Deployment

1. **Deploy Applications**
```bash
# Deploy all solutions
./scripts/production-automation.sh --skip-tests

# Or deploy specific solution
./scripts/production-deploy.sh --solution http --deployment-type rolling
```

2. **Setup Ingress and SSL**
```bash
# Setup certificates
./scripts/production-automation.sh setup-certificates

# Apply ingress configurations
kubectl apply -f k8s/production-ingress.yaml
```

### Phase 5: Testing and Validation

1. **Run Tests**
```bash
# Run smoke tests
./scripts/production-automation.sh run-smoke-tests

# Run performance tests
./scripts/production-automation.sh run-performance-tests
```

2. **Validate Deployment**
```bash
# Check all services are running
kubectl get pods -n mcp-openproject

# Check ingress endpoints
kubectl get ingress -n mcp-openproject

# Run health checks
./scripts/production-automation.sh health-check
```

## Monitoring and Alerting

### Prometheus Configuration

The production deployment includes a comprehensive Prometheus setup with:

- **Scraping**: All application and infrastructure metrics
- **Alerting**: Pre-configured alert rules
- **Storage**: 30-day retention with compression
- **High Availability**: Multi-replica deployment

### Key Metrics

1. **Application Metrics**
   - HTTP request rates and error rates
   - Response times (P50, P95, P99)
   - Resource usage (CPU, memory)
   - Custom business metrics

2. **Infrastructure Metrics**
   - Node resource usage
   - Pod health and restarts
   - Network traffic
   - Disk usage

3. **Database Metrics**
   - PostgreSQL performance metrics
   - Redis cache metrics
   - Connection pool usage

### Alerting Configuration

Alerts are configured for:

- **Critical**: Service downtime, database issues, security breaches
- **Warning**: High resource usage, slow queries, degraded performance
- **Info**: Routine maintenance, deployment notifications

### Grafana Dashboards

Pre-configured dashboards include:

- **System Overview**: Cluster health and resource usage
- **Application Performance**: Request metrics and response times
- **Database Health**: PostgreSQL and Redis metrics
- **Infrastructure**: Node and network metrics

## Backup and Disaster Recovery

### Backup Strategy

1. **Automated Backups**
   - Daily database backups
   - Configuration backups
   - S3 storage with 90-day retention

2. **Backup Schedule**
   - PostgreSQL: Daily at 2 AM UTC
   - Redis: Daily at 3 AM UTC
   - Configurations: Daily at 4 AM UTC

3. **Backup Storage**
   - Primary: S3 with versioning
   - Secondary: Local persistent volume
   - Retention: 90 days

### Disaster Recovery

1. **Recovery Procedures**
   - Database restoration from S3
   - Configuration restoration
   - Full cluster recovery

2. **Recovery Testing**
   - Monthly backup verification
   - Quarterly disaster recovery drills
   - Annual plan review

### Backup Commands

```bash
# Create manual backup
kubectl create job --from=cronjob/postgres-backup manual-postgres-backup -n mcp-openproject

# Restore from backup
kubectl exec -it disaster-recovery-pod -- /recovery/restore-postgres.sh /backup/postgres_backup_20231201_020000.sql
```

## Security Hardening

### Network Security

1. **Network Policies**
   - Isolated namespace communication
   - Restricted ingress/egress traffic
   - Pod-to-pod communication control

2. **Firewall Rules**
   - Security group configurations
   - VPC network ACLs
   - WAF rules for web applications

### Pod Security

1. **Security Contexts**
   - Non-root user execution
   - Read-only filesystems
   - Capability dropping

2. **Resource Limits**
   - CPU and memory limits
   - Pod disruption budgets
   - Resource quotas

### Access Control

1. **RBAC Configuration**
   - Role-based access control
   - Service account management
   - Audit logging

2. **Secrets Management**
   - Encrypted secrets
   - Automatic rotation
   - Access logging

## High Availability

### Multi-AZ Deployment

1. **Infrastructure HA**
   - Multi-AZ Kubernetes cluster
   - Cross-zone load balancing
   - Multi-AZ database clusters

2. **Application HA**
   - Multi-replica deployments
   - Horizontal pod autoscaling
   - Pod disruption budgets

### Failover Configuration

1. **Automatic Failover**
   - Database failover
   - Service failover
   - Load balancer failover

2. **Manual Failover**
   - Regional failover
   - Complete environment failover

### Scaling Configuration

1. **Horizontal Scaling**
   - CPU-based autoscaling
   - Memory-based autoscaling
   - Custom metric scaling

2. **Vertical Scaling**
   - Resource optimization
   - Performance tuning

## Troubleshooting

### Common Issues

1. **Pod Not Starting**
```bash
# Check pod status
kubectl describe pod <pod-name> -n mcp-openproject

# Check pod logs
kubectl logs <pod-name> -n mcp-openproject

# Check events
kubectl get events -n mcp-openproject
```

2. **Service Not Accessible**
```bash
# Check service endpoints
kubectl get endpoints -n mcp-openproject

# Check network policies
kubectl get networkpolicy -n mcp-openproject

# Check ingress configuration
kubectl describe ingress <ingress-name> -n mcp-openproject
```

3. **Database Issues**
```bash
# Check database connectivity
kubectl exec -it <pod-name> -n mcp-openproject -- pg_isready

# Check database logs
kubectl logs <postgres-pod> -n mcp-openproject

# Check database status
kubectl exec -it <postgres-pod> -n mcp-openproject -- psql -U mcpuser -d mcpdb -c "SELECT * FROM pg_stat_activity;"
```

### Performance Issues

1. **High CPU Usage**
```bash
# Check resource usage
kubectl top pods -n mcp-openproject

# Check HPA status
kubectl get hpa -n mcp-openproject

# Check node resources
kubectl top nodes
```

2. **High Memory Usage**
```bash
# Check memory usage
kubectl describe pod <pod-name> -n mcp-openproject | grep -i memory

# Check memory limits
kubectl get pod <pod-name> -n mcp-openproject -o yaml | grep -i limits
```

### Log Analysis

1. **Application Logs**
```bash
# Stream application logs
kubectl logs -f <pod-name> -n mcp-openproject

# Get logs from all pods
kubectl logs -l app=<app-name> -n mcp-openproject

# Get logs from previous container
kubectl logs <pod-name> -n mcp-openproject --previous
```

2. **System Logs**
```bash
# Get system logs
kubectl logs -n kube-system <system-pod>

# Get ingress controller logs
kubectl logs -n ingress-nginx <ingress-pod>
```

## Maintenance and Operations

### Regular Maintenance

1. **Daily Tasks**
   - Monitor system health
   - Check backup status
   - Review alert notifications

2. **Weekly Tasks**
   - Update security patches
   - Review resource usage
   - Optimize configurations

3. **Monthly Tasks**
   - Test backup restoration
   - Review security policies
   - Update documentation

### Rolling Updates

1. **Application Updates**
```bash
# Update application image
kubectl set image deployment/<deployment-name> <container-name>=<new-image> -n mcp-openproject

# Monitor rollout status
kubectl rollout status deployment/<deployment-name> -n mcp-openproject

# Rollback if needed
kubectl rollout undo deployment/<deployment-name> -n mcp-openproject
```

2. **Infrastructure Updates**
```bash
# Update Kubernetes version
eksctl upgrade cluster --name mcp-openproject-prod --region us-west-2

# Update node groups
eksctl upgrade nodegroup --cluster=mcp-openproject-prod --region us-west-2 --name=<nodegroup-name>
```

### Performance Optimization

1. **Resource Tuning**
```bash
# Update resource limits
kubectl set resources deployment/<deployment-name> --limits=cpu=2000m,memory=2Gi --requests=cpu=1000m,memory=1Gi -n mcp-openproject

# Update HPA configuration
kubectl autoscale deployment/<deployment-name> --min=3 --max=10 --cpu-percent=70 -n mcp-openproject
```

2. **Database Optimization**
```bash
# Update PostgreSQL configuration
kubectl edit configmap postgres-ha-config -n mcp-openproject

# Update Redis configuration
kubectl edit configmap redis-cluster-config -n mcp-openproject
```

## Emergency Procedures

### Service Outage

1. **Immediate Actions**
   - Check service status
   - Identify affected components
   - Initiate rollback if necessary

2. **Communication**
   - Notify stakeholders
   - Update status page
   - Document incident

### Security Incident

1. **Containment**
   - Isolate affected systems
   - Block malicious traffic
   - Preserve evidence

2. **Recovery**
   - Restore from backup
   - Apply security patches
   - Update access controls

### Data Loss

1. **Assessment**
   - Identify lost data
   - Determine recovery point
   - Choose recovery strategy

2. **Recovery**
   - Restore from backup
   - Validate data integrity
   - Update monitoring

## Conclusion

This production deployment guide provides a comprehensive framework for deploying and managing MCP OpenProject solutions in production environments. Following these guidelines ensures a secure, scalable, and maintainable deployment.

For additional support or questions, refer to the troubleshooting section or contact the operations team.

---

**Next Steps**:
1. Review the deployment checklist
2. Prepare your environment
3. Run the deployment automation
4. Validate the deployment
5. Configure monitoring and alerting