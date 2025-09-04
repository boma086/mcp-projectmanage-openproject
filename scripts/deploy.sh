#!/bin/bash

# Deployment automation script for all solutions
# Usage: ./deploy.sh [solution] [environment] [action]

set -e

SOLUTION=${1:-all}
ENVIRONMENT=${2:-staging}
ACTION=${3:-deploy}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Available solutions
SOLUTIONS=("solution-http" "solution-fastapi" "solution-fastmcp" "solution-typescript")

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

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking deployment prerequisites"
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed or not in PATH"
        return 1
    fi
    
    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        return 1
    fi
    
    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "Not in a git repository"
        return 1
    fi
    
    # Check Kubernetes cluster connectivity
    if ! kubectl cluster-info >/dev/null 2>&1; then
        print_error "Cannot connect to Kubernetes cluster"
        return 1
    fi
    
    print_success "All prerequisites checked"
}

# Function to prepare environment
prepare_environment() {
    local environment=$1
    
    print_status "Preparing $environment environment"
    
    # Create environment directory
    mkdir -p "deployment/$environment"
    
    # Create environment-specific configuration
    cat > "deployment/$environment/env-config.json" << EOF
{
  "environment": "$environment",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "commit": "$(git rev-parse HEAD)",
  "branch": "$(git rev-parse --abbrev-ref HEAD)",
  "solutions": []
}
EOF
    
    # Create Kubernetes namespace if it doesn't exist
    if ! kubectl get namespace "openproject-$environment" >/dev/null 2>&1; then
        kubectl create namespace "openproject-$environment"
        print_success "Created namespace: openproject-$environment"
    fi
    
    # Create environment-specific ConfigMap
    cat > "deployment/$environment/configmap.yaml" << EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: openproject-config
  namespace: openproject-$environment
data:
  ENVIRONMENT: "$environment"
  LOG_LEVEL: "INFO"
  MONITORING_ENABLED: "true"
  METRICS_ENABLED: "true"
EOF
    
    # Apply ConfigMap
    kubectl apply -f "deployment/$environment/configmap.yaml"
    
    print_success "Environment preparation completed for $environment"
}

# Function to deploy solution
deploy_solution() {
    local solution=$1
    local environment=$2
    
    print_status "Deploying $solution to $environment"
    
    # Check if solution directory exists
    if [ ! -d "$solution" ]; then
        print_error "Solution directory $solution does not exist"
        return 1
    fi
    
    # Check if Kubernetes manifests exist
    local manifest_dir="k8s"
    if [ ! -d "$solution/$manifest_dir" ]; then
        print_warning "Kubernetes manifests not found in $solution/$manifest_dir"
        # Create basic deployment manifest
        create_basic_deployment "$solution" "$environment"
    else
        # Apply existing manifests
        apply_kubernetes_manifests "$solution" "$environment"
    fi
    
    # Wait for deployment to be ready
    wait_for_deployment "$solution" "$environment"
    
    # Run health checks
    run_health_checks "$solution" "$environment"
    
    print_success "Successfully deployed $solution to $environment"
}

# Function to create basic deployment manifest
create_basic_deployment() {
    local solution=$1
    local environment=$2
    
    print_status "Creating basic deployment manifest for $solution"
    
    # Determine port and image
    local port=8010
    local image="$solution"
    
    case $solution in
        "solution-http")
            port=8010
            ;;
        "solution-fastapi")
            port=8020
            ;;
        "solution-fastmcp")
            port=8030
            ;;
        "solution-typescript")
            port=8040
            ;;
    esac
    
    # Create deployment manifest
    cat > "deployment/$environment/${solution}-deployment.yaml" << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $solution
  namespace: openproject-$environment
  labels:
    app: $solution
    environment: $environment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: $solution
  template:
    metadata:
      labels:
        app: $solution
        environment: $environment
    spec:
      containers:
      - name: $solution
        image: ghcr.io/\${GITHUB_REPOSITORY:-local}/$solution:develop
        ports:
        - containerPort: $port
        env:
        - name: ENVIRONMENT
          value: "$environment"
        - name: PORT
          value: "$port"
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
            port: $port
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: $port
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: $solution-service
  namespace: openproject-$environment
  labels:
    app: $solution
    environment: $environment
spec:
  selector:
    app: $solution
  ports:
  - protocol: TCP
    port: 80
    targetPort: $port
  type: ClusterIP
EOF
    
    # Apply deployment
    kubectl apply -f "deployment/$environment/${solution}-deployment.yaml"
}

# Function to apply Kubernetes manifests
apply_kubernetes_manifests() {
    local solution=$1
    local environment=$2
    
    print_status "Applying Kubernetes manifests for $solution"
    
    local manifest_dir="$solution/k8s"
    
    # Apply all YAML files in the manifest directory
    for manifest in "$manifest_dir"/*.yaml; do
        if [ -f "$manifest" ]; then
            print_status "Applying $manifest"
            
            # Update namespace in manifest
            sed -i.bak "s/namespace: openproject-[^[:space:]]*/namespace: openproject-$environment/g" "$manifest"
            
            # Apply manifest
            kubectl apply -f "$manifest"
            
            # Restore original manifest
            mv "$manifest.bak" "$manifest"
        fi
    done
}

# Function to wait for deployment to be ready
wait_for_deployment() {
    local solution=$1
    local environment=$2
    local timeout=300
    local start_time=$(date +%s)
    
    print_status "Waiting for $solution deployment to be ready"
    
    while true; do
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))
        
        if [ $elapsed -gt $timeout ]; then
            print_error "Timeout waiting for $solution deployment to be ready"
            return 1
        fi
        
        # Check deployment status
        local ready_replicas=$(kubectl get deployment $solution -n "openproject-$environment" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
        local desired_replicas=$(kubectl get deployment $solution -n "openproject-$environment" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "1")
        
        if [ "$ready_replicas" = "$desired_replicas" ] && [ "$ready_replicas" != "0" ]; then
            print_success "$solution deployment is ready"
            break
        fi
        
        print_status "Waiting for $solution deployment... (${elapsed}s elapsed, ${ready_replicas}/${desired_replicas} replicas ready)"
        sleep 10
    done
}

# Function to run health checks
run_health_checks() {
    local solution=$1
    local environment=$2
    
    print_status "Running health checks for $solution"
    
    # Get service name and port
    local service_name="${solution}-service"
    local namespace="openproject-$environment"
    
    # Wait for service to be available
    kubectl wait --for=condition=ready pod -l app=$solution -n "$namespace" --timeout=60s
    
    # Port forward to local port for testing
    local local_port=$((8080 + RANDOM % 1000))
    kubectl port-forward service/$service_name $local_port:80 -n "$namespace" &
    local port_forward_pid=$!
    
    # Wait for port forward to be ready
    sleep 5
    
    # Test health endpoint
    if curl -f "http://localhost:$local_port/health" >/dev/null 2>&1; then
        print_success "Health check passed for $solution"
    else
        print_warning "Health check failed for $solution"
    fi
    
    # Test ready endpoint
    if curl -f "http://localhost:$local_port/health/ready" >/dev/null 2>&1; then
        print_success "Readiness check passed for $solution"
    else
        print_warning "Readiness check failed for $solution"
    fi
    
    # Clean up port forward
    kill $port_forward_pid 2>/dev/null || true
}

# Function to rollback deployment
rollback_deployment() {
    local solution=$1
    local environment=$2
    
    print_status "Rolling back $solution deployment in $environment"
    
    # Get current revision
    local current_revision=$(kubectl rollout history deployment/$solution -n "openproject-$environment" -o jsonpath='{.metadata.annotations.deployment.kubernetes.io/revision}' 2>/dev/null || echo "1")
    
    if [ "$current_revision" = "1" ]; then
        print_warning "Cannot rollback $solution - already at first revision"
        return 0
    fi
    
    # Rollback to previous revision
    kubectl rollout undo deployment/$solution -n "openproject-$environment"
    
    # Wait for rollback to complete
    kubectl rollout status deployment/$solution -n "openproject-$environment" --timeout=300s
    
    print_success "Successfully rolled back $solution deployment"
}

# Function to scale deployment
scale_deployment() {
    local solution=$1
    local environment=$2
    local replicas=$3
    
    print_status "Scaling $solution deployment to $replicas replicas in $environment"
    
    kubectl scale deployment/$solution -n "openproject-$environment" --replicas=$replicas
    
    # Wait for scale to complete
    kubectl rollout status deployment/$solution -n "openproject-$environment" --timeout=300s
    
    print_success "Successfully scaled $solution deployment to $replicas replicas"
}

# Function to get deployment status
get_deployment_status() {
    local solution=$1
    local environment=$2
    
    print_status "Getting deployment status for $solution in $environment"
    
    # Get deployment information
    echo "Deployment Information:"
    kubectl get deployment $solution -n "openproject-$environment" -o wide
    
    echo ""
    echo "Pod Status:"
    kubectl get pods -l app=$solution -n "openproject-$environment"
    
    echo ""
    echo "Service Information:"
    kubectl get service $solution-service -n "openproject-$environment"
    
    echo ""
    echo "Recent Events:"
    kubectl get events -n "openproject-$environment" --sort-by='.metadata.creationTimestamp' | tail -10
}

# Main execution
main() {
    print_status "Starting deployment automation"
    print_status "Solution: $SOLUTION"
    print_status "Environment: $ENVIRONMENT"
    print_status "Action: $ACTION"
    
    # Check prerequisites
    check_prerequisites
    
    # Prepare environment
    prepare_environment "$ENVIRONMENT"
    
    # Execute action
    case $ACTION in
        "deploy")
            if [ "$SOLUTION" = "all" ]; then
                print_status "Deploying all solutions to $ENVIRONMENT"
                for solution in "${SOLUTIONS[@]}"; do
                    if [ -d "$solution" ]; then
                        deploy_solution "$solution" "$ENVIRONMENT"
                    else
                        print_warning "Solution directory $solution does not exist, skipping"
                    fi
                done
            else
                if [[ " ${SOLUTIONS[@]} " =~ " ${SOLUTION} " ]]; then
                    deploy_solution "$SOLUTION" "$ENVIRONMENT"
                else
                    print_error "Invalid solution: $SOLUTION"
                    print_status "Available solutions: ${SOLUTIONS[*]}"
                    exit 1
                fi
            fi
            ;;
        "rollback")
            if [ "$SOLUTION" = "all" ]; then
                print_error "Cannot rollback all solutions at once"
                exit 1
            else
                rollback_deployment "$SOLUTION" "$ENVIRONMENT"
            fi
            ;;
        "scale")
            if [ "$SOLUTION" = "all" ]; then
                print_error "Cannot scale all solutions at once"
                exit 1
            else
                scale_deployment "$SOLUTION" "$ENVIRONMENT" 3
            fi
            ;;
        "status")
            if [ "$SOLUTION" = "all" ]; then
                print_error "Cannot get status for all solutions at once"
                exit 1
            else
                get_deployment_status "$SOLUTION" "$ENVIRONMENT"
            fi
            ;;
        *)
            print_error "Invalid action: $ACTION"
            print_status "Available actions: deploy, rollback, scale, status"
            exit 1
            ;;
    esac
    
    print_success "Deployment automation completed"
}

# Show help
show_help() {
    echo "Usage: $0 [SOLUTION] [ENVIRONMENT] [ACTION]"
    echo ""
    echo "Arguments:"
    echo "  SOLUTION     Solution to deploy (default: all)"
    echo "              Available: solution-http, solution-fastapi, solution-fastmcp, solution-typescript"
    echo "  ENVIRONMENT  Target environment (default: staging)"
    echo "              Available: development, staging, production"
    echo "  ACTION       Action to perform (default: deploy)"
    echo "              Available: deploy, rollback, scale, status"
    echo ""
    echo "Examples:"
    echo "  $0                           # Deploy all solutions to staging"
    echo "  $0 solution-fastapi          # Deploy FastAPI solution to staging"
    echo "  $0 solution-http production  # Deploy HTTP solution to production"
    echo "  $0 solution-fastapi staging rollback  # Rollback FastAPI solution in staging"
    echo ""
    echo "Environment Variables:"
    echo "  GITHUB_REPOSITORY           GitHub repository name (for image path)"
    echo ""
}

# Parse command line arguments
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_help
    exit 0
fi

# Run main function
main "$@"