#!/bin/bash

# Environment-specific deployment automation
# Usage: ./deploy-env.sh [environment] [action]

set -e

ENVIRONMENT=${1:-staging}
ACTION=${2:-deploy}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Environment-specific configurations
declare -A ENV_CONFIGS=(
    ["development"]="develop|1|256Mi|250m|512Mi|500m"
    ["staging"]="staging|2|512Mi|500m|1Gi|1"
    ["production"]="production|3|1Gi|1|2Gi|2"
)

# Solution-specific configurations
declare -A SOLUTION_PORTS=(
    ["solution-http"]=8010
    ["solution-fastapi"]=8020
    ["solution-fastmcp"]=8030
    ["solution-typescript"]=8040
)

# Function to validate environment
validate_environment() {
    if [[ ! -v ENV_CONFIGS[$ENVIRONMENT] ]]; then
        print_error "Invalid environment: $ENVIRONMENT"
        print_status "Available environments: ${!ENV_CONFIGS[@]}"
        exit 1
    fi
}

# Function to parse environment configuration
parse_env_config() {
    local config="${ENV_CONFIGS[$ENVIRONMENT]}"
    IFS='|' read -r env_tag replicas request_mem request_cpu limit_mem limit_cpu <<< "$config"
    
    export ENV_TAG="$env_tag"
    export REPLICAS="$replicas"
    export REQUEST_MEMORY="$request_mem"
    export REQUEST_CPU="$request_cpu"
    export LIMIT_MEMORY="$limit_mem"
    export LIMIT_CPU="$limit_cpu"
}

# Function to create environment-specific namespace
create_namespace() {
    print_status "Creating namespace for $ENVIRONMENT environment"
    
    cat > "deployment/namespace-$ENVIRONMENT.yaml" << EOF
apiVersion: v1
kind: Namespace
metadata:
  name: openproject-$ENVIRONMENT
  labels:
    environment: $ENVIRONMENT
    app: openproject-mcp
EOF
    
    kubectl apply -f "deployment/namespace-$ENVIRONMENT.yaml"
}

# Function to create environment-specific ConfigMap
create_configmap() {
    print_status "Creating ConfigMap for $ENVIRONMENT environment"
    
    cat > "deployment/configmap-$ENVIRONMENT.yaml" << EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: openproject-config
  namespace: openproject-$ENVIRONMENT
  labels:
    environment: $ENVIRONMENT
data:
  ENVIRONMENT: "$ENVIRONMENT"
  LOG_LEVEL: "$([ "$ENVIRONMENT" = "production" ] && echo "WARN" || echo "INFO")"
  MONITORING_ENABLED: "true"
  METRICS_ENABLED: "true"
  DEBUG_MODE: "$([ "$ENVIRONMENT" = "development" ] && echo "true" || echo "false")"
  HEALTH_CHECK_INTERVAL: "30"
  READINESS_CHECK_INTERVAL: "10"
EOF
    
    kubectl apply -f "deployment/configmap-$ENVIRONMENT.yaml"
}

# Function to create environment-specific Secret
create_secret() {
    print_status "Creating Secret for $ENVIRONMENT environment"
    
    # Check if secret already exists
    if kubectl get secret openproject-secrets -n "openproject-$ENVIRONMENT" >/dev/null 2>&1; then
        print_status "Secret already exists, updating..."
    fi
    
    # Create secret from environment variables or .env file
    if [ -f ".env.$ENVIRONMENT" ]; then
        kubectl create secret generic openproject-secrets \
            --namespace "openproject-$ENVIRONMENT" \
            --from-env-file=".env.$ENVIRONMENT" \
            --dry-run=client -o yaml | kubectl apply -f -
    else
        print_warning "No .env.$ENVIRONMENT file found, creating empty secret"
        kubectl create secret generic openproject-secrets \
            --namespace "openproject-$ENVIRONMENT" \
            --from-literal=OPENPROJECT_URL="" \
            --from-literal=OPENPROJECT_API_KEY="" \
            --dry-run=client -o yaml | kubectl apply -f -
    fi
}

# Function to create solution-specific deployment
create_deployment() {
    local solution=$1
    local port=${SOLUTION_PORTS[$solution]}
    
    print_status "Creating deployment for $solution in $ENVIRONMENT"
    
    cat > "deployment/$solution-deployment-$ENVIRONMENT.yaml" << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $solution
  namespace: openproject-$ENVIRONMENT
  labels:
    app: $solution
    environment: $ENVIRONMENT
    version: $ENV_TAG
spec:
  replicas: $REPLICAS
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: $solution
      environment: $ENVIRONMENT
  template:
    metadata:
      labels:
        app: $solution
        environment: $ENVIRONMENT
        version: $ENV_TAG
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "$port"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: $solution
        image: ghcr.io/\${GITHUB_REPOSITORY:-local}/$solution:$ENV_TAG
        ports:
        - containerPort: $port
          name: http
        env:
        - name: ENVIRONMENT
          valueFrom:
            configMapKeyRef:
              name: openproject-config
              key: ENVIRONMENT
        - name: OPENPROJECT_URL
          valueFrom:
            secretKeyRef:
              name: openproject-secrets
              key: OPENPROJECT_URL
        - name: OPENPROJECT_API_KEY
          valueFrom:
            secretKeyRef:
              name: openproject-secrets
              key: OPENPROJECT_API_KEY
        - name: PORT
          value: "$port"
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: openproject-config
              key: LOG_LEVEL
        resources:
          requests:
            memory: "$REQUEST_MEMORY"
            cpu: "$REQUEST_CPU"
          limits:
            memory: "$LIMIT_MEMORY"
            cpu: "$LIMIT_CPU"
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health/ready
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
      restartPolicy: Always
      imagePullSecrets:
      - name: regcred
EOF
    
    kubectl apply -f "deployment/$solution-deployment-$ENVIRONMENT.yaml"
}

# Function to create solution-specific service
create_service() {
    local solution=$1
    local port=${SOLUTION_PORTS[$solution]}
    
    print_status "Creating service for $solution in $ENVIRONMENT"
    
    cat > "deployment/$solution-service-$ENVIRONMENT.yaml" << EOF
apiVersion: v1
kind: Service
metadata:
  name: $solution-service
  namespace: openproject-$ENVIRONMENT
  labels:
    app: $solution
    environment: $ENVIRONMENT
spec:
  selector:
    app: $solution
    environment: $ENVIRONMENT
  ports:
  - protocol: TCP
    port: 80
    targetPort: http
    name: http
  type: ClusterIP
EOF
    
    kubectl apply -f "deployment/$solution-service-$ENVIRONMENT.yaml"
}

# Function to create ingress for environment
create_ingress() {
    print_status "Creating ingress for $ENVIRONMENT environment"
    
    local ingress_host=""
    case $ENVIRONMENT in
        "development")
            ingress_host="dev.openproject-mcp.local"
            ;;
        "staging")
            ingress_host="staging.openproject-mcp.local"
            ;;
        "production")
            ingress_host="openproject-mcp.local"
            ;;
    esac
    
    cat > "deployment/ingress-$ENVIRONMENT.yaml" << EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: openproject-ingress
  namespace: openproject-$ENVIRONMENT
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "$([ "$ENVIRONMENT" = "production" ] && echo "true" || echo "false")"
    cert-manager.io/cluster-issuer: "$([ "$ENVIRONMENT" = "production" ] && echo "letsencrypt-prod" || echo "letsencrypt-staging")"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - $ingress_host
    secretName: openproject-tls
  rules:
  - host: $ingress_host
    http:
      paths:
      - path: /http
        pathType: Prefix
        backend:
          service:
            name: solution-http-service
            port:
              number: 80
      - path: /fastapi
        pathType: Prefix
        backend:
          service:
            name: solution-fastapi-service
            port:
              number: 80
      - path: /fastmcp
        pathType: Prefix
        backend:
          service:
            name: solution-fastmcp-service
            port:
              number: 80
      - path: /typescript
        pathType: Prefix
        backend:
          service:
            name: solution-typescript-service
            port:
              number: 80
EOF
    
    kubectl apply -f "deployment/ingress-$ENVIRONMENT.yaml"
}

# Function to create monitoring resources
create_monitoring() {
    print_status "Creating monitoring resources for $ENVIRONMENT"
    
    # Create ServiceMonitor for Prometheus
    cat > "deployment/servicemonitor-$ENVIRONMENT.yaml" << EOF
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: openproject-monitor
  namespace: openproject-$ENVIRONMENT
  labels:
    app: openproject-mcp
    environment: $ENVIRONMENT
spec:
  selector:
    matchLabels:
      app: openproject-mcp
  namespaceSelector:
    matchNames:
    - openproject-$ENVIRONMENT
  endpoints:
  - port: http
    interval: 30s
    path: /metrics
EOF
    
    # Create Horizontal Pod Autoscaler
    cat > "deployment/hpa-$ENVIRONMENT.yaml" << EOF
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: openproject-hpa
  namespace: openproject-$ENVIRONMENT
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: solution-fastapi  # Example for one solution
  minReplicas: $REPLICAS
  maxReplicas: $((REPLICAS * 3))
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
EOF
    
    kubectl apply -f "deployment/servicemonitor-$ENVIRONMENT.yaml"
    kubectl apply -f "deployment/hpa-$ENVIRONMENT.yaml"
}

# Function to deploy all solutions
deploy_all() {
    print_status "Deploying all solutions to $ENVIRONMENT"
    
    # Create namespace
    create_namespace
    
    # Create configmap and secret
    create_configmap
    create_secret
    
    # Deploy each solution
    for solution in "${!SOLUTION_PORTS[@]}"; do
        create_deployment "$solution"
        create_service "$solution"
    done
    
    # Create ingress and monitoring
    create_ingress
    create_monitoring
    
    print_success "All solutions deployed to $ENVIRONMENT"
}

# Function to verify deployment
verify_deployment() {
    print_status "Verifying deployment in $ENVIRONMENT"
    
    # Wait for deployments to be ready
    for solution in "${!SOLUTION_PORTS[@]}"; do
        print_status "Waiting for $solution deployment..."
        kubectl wait --for=condition=available deployment/$solution \
            --namespace "openproject-$ENVIRONMENT" \
            --timeout=300s
    done
    
    # Check pod status
    print_status "Checking pod status..."
    kubectl get pods -n "openproject-$ENVIRONMENT"
    
    # Check service status
    print_status "Checking service status..."
    kubectl get services -n "openproject-$ENVIRONMENT"
    
    # Run health checks
    print_status "Running health checks..."
    for solution in "${!SOLUTION_PORTS[@]}"; do
        local service_name="$solution-service"
        kubectl get endpoints "$service_name" -n "openproject-$ENVIRONMENT"
    done
    
    print_success "Deployment verification completed for $ENVIRONMENT"
}

# Function to rollback deployment
rollback_deployment() {
    local solution=${3:-all}
    
    print_status "Rolling back deployment in $ENVIRONMENT"
    
    if [ "$solution" = "all" ]; then
        for sol in "${!SOLUTION_PORTS[@]}"; do
            print_status "Rolling back $sol..."
            kubectl rollout undo deployment/$sol \
                --namespace "openproject-$ENVIRONMENT"
        done
    else
        print_status "Rolling back $solution..."
        kubectl rollout undo deployment/$solution \
            --namespace "openproject-$ENVIRONMENT"
    fi
    
    # Wait for rollback to complete
    verify_deployment
    
    print_success "Rollback completed for $ENVIRONMENT"
}

# Main execution
main() {
    print_status "Starting environment deployment automation"
    print_status "Environment: $ENVIRONMENT"
    print_status "Action: $ACTION"
    
    # Validate environment
    validate_environment
    
    # Parse environment configuration
    parse_env_config
    
    # Create deployment directory
    mkdir -p deployment
    
    # Execute action
    case $ACTION in
        "deploy")
            deploy_all
            verify_deployment
            ;;
        "verify")
            verify_deployment
            ;;
        "rollback")
            rollback_deployment "$@"
            ;;
        "config")
            create_namespace
            create_configmap
            create_secret
            ;;
        *)
            print_error "Invalid action: $ACTION"
            print_status "Available actions: deploy, verify, rollback, config"
            exit 1
            ;;
    esac
    
    print_success "Environment deployment automation completed"
}

# Show help
show_help() {
    echo "Usage: $0 [ENVIRONMENT] [ACTION] [SOLUTION]"
    echo ""
    echo "Arguments:"
    echo "  ENVIRONMENT  Target environment (default: staging)"
    echo "              Available: development, staging, production"
    echo "  ACTION       Action to perform (default: deploy)"
    echo "              Available: deploy, verify, rollback, config"
    echo "  SOLUTION     Solution to rollback (default: all, only for rollback)"
    echo ""
    echo "Examples:"
    echo "  $0                           # Deploy to staging"
    echo "  $0 production deploy         # Deploy to production"
    echo "  $0 staging verify            # Verify staging deployment"
    echo "  $0 production rollback       # Rollback all solutions in production"
    echo "  $0 production rollback solution-http  # Rollback specific solution"
    echo ""
}

# Parse command line arguments
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_help
    exit 0
fi

# Run main function
main "$@"