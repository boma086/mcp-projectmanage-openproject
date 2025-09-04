#!/bin/bash

# Dockerfile Validation Script
# This script validates Dockerfiles for syntax and best practices

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Function to log messages
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Function to check if Docker is available
check_docker() {
    if ! command -v docker >/dev/null 2>&1; then
        error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        error "Unable to connect to Docker daemon. Please start Docker."
        exit 1
    fi
    
    log "Docker is available and running"
}

# Function to validate Dockerfile syntax
validate_dockerfile() {
    local dockerfile="$1"
    local context="$2"
    local solution_name="$3"
    
    info "Validating $solution_name Dockerfile..."
    
    if [[ ! -f "$dockerfile" ]]; then
        error "Dockerfile not found: $dockerfile"
        return 1
    fi
    
    # Check Dockerfile syntax with docker build
    local temp_image="mcp-${solution_name}-validation"
    local build_log="/tmp/docker-build-${solution_name}.log"
    
    if docker build -f "$dockerfile" -t "$temp_image" "$context" > "$build_log" 2>&1; then
        log "$solution_name Dockerfile validation successful"
        
        # Clean up test image
        docker rmi "$temp_image" >/dev/null 2>&1 || true
        rm -f "$build_log"
        return 0
    else
        error "$solution_name Dockerfile validation failed"
        error "Build log:"
        cat "$build_log"
        rm -f "$build_log"
        return 1
    fi
}

# Function to check Dockerfile best practices
check_dockerfile_best_practices() {
    local dockerfile="$1"
    local solution_name="$2"
    
    info "Checking $solution_name Dockerfile best practices..."
    
    local issues=0
    
    # Check for multi-stage builds
    if ! grep -q "FROM.*as.*builder" "$dockerfile"; then
        warn "$solution_name: No multi-stage build detected"
        ((issues++))
    fi
    
    # Check for non-root user
    if ! grep -q "USER.*[0-9]" "$dockerfile" && ! grep -q "useradd\|adduser\|groupadd" "$dockerfile"; then
        warn "$solution_name: No non-root user configured"
        ((issues++))
    fi
    
    # Check for health checks
    if ! grep -q "HEALTHCHECK" "$dockerfile"; then
        warn "$solution_name: No health check configured"
        ((issues++))
    fi
    
    # Check for exposed ports
    if ! grep -q "EXPOSE" "$dockerfile"; then
        warn "$solution_name: No ports exposed"
        ((issues++))
    fi
    
    # Check for specific security issues
    if grep -q "apt-get update.*&&.*apt-get install" "$dockerfile"; then
        warn "$solution_name: Consider combining apt-get update and install in single RUN command"
        ((issues++))
    fi
    
    if grep -q "rm -rf /var/lib/apt/lists" "$dockerfile"; then
        warn "$solution_name: apt-get cleanup should be in the same RUN command"
        ((issues++))
    fi
    
    if [[ $issues -eq 0 ]]; then
        log "$solution_name Dockerfile follows best practices"
        return 0
    else
        warn "$solution_name Dockerfile has $issues best practice issues"
        return 1
    fi
}

# Function to validate Docker Compose files
validate_docker_compose() {
    local compose_file="$1"
    local compose_name="$2"
    
    info "Validating $compose_name Docker Compose file..."
    
    if [[ ! -f "$compose_file" ]]; then
        error "Docker Compose file not found: $compose_file"
        return 1
    fi
    
    # Check YAML syntax
    if ! python3 -c "import yaml; yaml.safe_load(open('$compose_file', 'r'))" 2>/dev/null; then
        error "$compose_name: Invalid YAML syntax"
        return 1
    fi
    
    # Check Docker Compose schema
    if command -v docker-compose >/dev/null 2>&1; then
        if docker-compose -f "$compose_file" config >/dev/null 2>&1; then
            log "$compose_name Docker Compose configuration is valid"
            return 0
        else
            error "$compose_name: Invalid Docker Compose configuration"
            return 1
        fi
    else
        warn "docker-compose not available, skipping configuration validation"
        return 0
    fi
}

# Function to validate Kubernetes manifests
validate_kubernetes_manifests() {
    local manifest_dir="$1"
    
    info "Validating Kubernetes manifests..."
    
    if [[ ! -d "$manifest_dir" ]]; then
        error "Kubernetes manifests directory not found: $manifest_dir"
        return 1
    fi
    
    local total_issues=0
    
    # Find all YAML files
    while IFS= read -r -d '' yaml_file; do
        info "Validating $(basename "$yaml_file")..."
        
        # Check YAML syntax
        if ! python3 -c "import yaml; yaml.safe_load_all(open('$yaml_file', 'r'))" 2>/dev/null; then
            error "$(basename "$yaml_file"): Invalid YAML syntax"
            ((total_issues++))
            continue
        fi
        
        # Check Kubernetes manifests with kubectl if available
        if command -v kubectl >/dev/null 2>&1; then
            if ! kubectl apply --dry-run=client -f "$yaml_file" >/dev/null 2>&1; then
                error "$(basename "$yaml_file"): Invalid Kubernetes manifest"
                ((total_issues++))
            else
                log "$(basename "$yaml_file"): Kubernetes manifest is valid"
            fi
        else
            warn "kubectl not available, skipping Kubernetes validation"
        fi
    done < <(find "$manifest_dir" -name "*.yaml" -print0)
    
    if [[ $total_issues -eq 0 ]]; then
        log "All Kubernetes manifests are valid"
        return 0
    else
        error "Found $total_issues issues in Kubernetes manifests"
        return 1
    fi
}

# Function to validate environment files
validate_environment_files() {
    info "Validating environment configuration files..."
    
    local env_files=(
        "$PROJECT_DIR/.env"
        "$PROJECT_DIR/.env.development"
        "$PROJECT_DIR/.env.production"
        "$PROJECT_DIR/.env.test"
    )
    
    local total_issues=0
    
    for env_file in "${env_files[@]}"; do
        if [[ -f "$env_file" ]]; then
            info "Validating $(basename "$env_file")..."
            
            # Check for syntax issues
            if grep -q "^[^#]*export.*=" "$env_file"; then
                warn "$(basename "$env_file"): Contains export statements (not needed in .env files)"
                ((total_issues++))
            fi
            
            # Check for missing required variables in production
            if [[ "$env_file" == *".production" ]]; then
                local required_vars=("OPENPROJECT_URL" "OPENPROJECT_API_KEY" "SECRET_KEY")
                for var in "${required_vars[@]}"; do
                    if grep -q "^$var=" "$env_file" && grep -q "^$var=your-" "$env_file"; then
                        warn "$(basename "$env_file"): $var contains placeholder value"
                        ((total_issues++))
                    fi
                done
            fi
            
            log "$(basename "$env_file"): Environment file is valid"
        else
            warn "$(basename "$env_file"): Environment file not found"
        fi
    done
    
    if [[ $total_issues -eq 0 ]]; then
        log "All environment files are valid"
        return 0
    else
        warn "Found $total_issues issues in environment files"
        return 1
    fi
}

# Main validation function
main() {
    log "Starting Docker and deployment validation..."
    
    # Check prerequisites
    check_docker
    
    local total_issues=0
    
    # Validate Dockerfiles
    info "=== Validating Dockerfiles ==="
    
    # HTTP Solution
    if ! validate_dockerfile "$PROJECT_DIR/solution-http/Dockerfile" "$PROJECT_DIR/solution-http" "http"; then
        ((total_issues++))
    fi
    if ! check_dockerfile_best_practices "$PROJECT_DIR/solution-http/Dockerfile" "http"; then
        ((total_issues++))
    fi
    
    # FastAPI Solution
    if ! validate_dockerfile "$PROJECT_DIR/solution-fastapi/Dockerfile" "$PROJECT_DIR/solution-fastapi" "fastapi"; then
        ((total_issues++))
    fi
    if ! check_dockerfile_best_practices "$PROJECT_DIR/solution-fastapi/Dockerfile" "fastapi"; then
        ((total_issues++))
    fi
    
    # FastMCP Solution
    if ! validate_dockerfile "$PROJECT_DIR/solution-fastmcp/Dockerfile" "$PROJECT_DIR/solution-fastmcp" "fastmcp"; then
        ((total_issues++))
    fi
    if ! check_dockerfile_best_practices "$PROJECT_DIR/solution-fastmcp/Dockerfile" "fastmcp"; then
        ((total_issues++))
    fi
    
    # TypeScript Solution
    if ! validate_dockerfile "$PROJECT_DIR/solution-typescript/Dockerfile" "$PROJECT_DIR/solution-typescript" "typescript"; then
        ((total_issues++))
    fi
    if ! check_dockerfile_best_practices "$PROJECT_DIR/solution-typescript/Dockerfile" "typescript"; then
        ((total_issues++))
    fi
    
    # Validate Docker Compose files
    info "=== Validating Docker Compose Files ==="
    
    if ! validate_docker_compose "$PROJECT_DIR/docker-compose.dev.yml" "Development"; then
        ((total_issues++))
    fi
    
    if ! validate_docker_compose "$PROJECT_DIR/docker-compose.prod.yml" "Production"; then
        ((total_issues++))
    fi
    
    # Validate Kubernetes manifests
    info "=== Validating Kubernetes Manifests ==="
    
    if ! validate_kubernetes_manifests "$PROJECT_DIR/k8s"; then
        ((total_issues++))
    fi
    
    # Validate environment files
    info "=== Validating Environment Files ==="
    
    if ! validate_environment_files; then
        ((total_issues++))
    fi
    
    # Summary
    info "=== Validation Summary ==="
    
    if [[ $total_issues -eq 0 ]]; then
        log "✅ All validations passed successfully!"
        return 0
    else
        error "❌ Found $total_issues validation issues"
        error "Please review and fix the issues before deployment"
        return 1
    fi
}

# Function to show help
show_help() {
    cat << EOF
Docker and Deployment Validation Script

USAGE:
    $0 [COMMAND]

COMMANDS:
    validate    Run full validation (default)
    docker     Validate Dockerfiles only
    compose    Validate Docker Compose files only
    k8s        Validate Kubernetes manifests only
    env        Validate environment files only
    help       Show this help message

EXAMPLES:
    $0 validate          # Full validation
    $0 docker           # Validate Dockerfiles only
    $0 compose          # Validate Docker Compose files only
    $0 k8s              # Validate Kubernetes manifests only
    $0 env              # Validate environment files only

NOTES:
    - Docker daemon must be running
    - kubectl is optional for Kubernetes validation
    - docker-compose is optional for Docker Compose validation
    - Python3 is required for YAML validation

EOF
}

# Parse command line arguments
case "${1:-validate}" in
    validate)
        main
        ;;
    docker)
        check_docker
        validate_dockerfile "$PROJECT_DIR/solution-http/Dockerfile" "$PROJECT_DIR/solution-http" "http"
        validate_dockerfile "$PROJECT_DIR/solution-fastapi/Dockerfile" "$PROJECT_DIR/solution-fastapi" "fastapi"
        validate_dockerfile "$PROJECT_DIR/solution-fastmcp/Dockerfile" "$PROJECT_DIR/solution-fastmcp" "fastmcp"
        validate_dockerfile "$PROJECT_DIR/solution-typescript/Dockerfile" "$PROJECT_DIR/solution-typescript" "typescript"
        ;;
    compose)
        validate_docker_compose "$PROJECT_DIR/docker-compose.dev.yml" "Development"
        validate_docker_compose "$PROJECT_DIR/docker-compose.prod.yml" "Production"
        ;;
    k8s)
        validate_kubernetes_manifests "$PROJECT_DIR/k8s"
        ;;
    env)
        validate_environment_files
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac