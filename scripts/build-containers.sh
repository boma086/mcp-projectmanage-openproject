#!/bin/bash

# Container image building and publishing script
# Usage: ./build-containers.sh [solution] [environment] [registry]

set -e

SOLUTION=${1:-all}
ENVIRONMENT=${2:-development}
REGISTRY=${3:-ghcr.io}

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

# Function to build Docker image
build_image() {
    local solution=$1
    local environment=$2
    local registry=$3
    
    print_status "Building Docker image for $solution ($environment)"
    
    # Change to solution directory
    if [ ! -d "$solution" ]; then
        print_error "Solution directory $solution does not exist"
        return 1
    fi
    
    cd "$solution"
    
    # Determine image tags based on environment
    local tags=()
    local commit_hash=$(git rev-parse --short HEAD)
    local branch_name=$(git rev-parse --abbrev-ref HEAD)
    
    case $environment in
        "development")
            tags+=("develop")
            tags+=("$commit_hash")
            if [ "$branch_name" != "main" ]; then
                tags+=("$branch_name")
            fi
            ;;
        "staging")
            tags+=("staging")
            tags+=("candidate")
            tags+=("$commit_hash")
            ;;
        "production")
            tags+=("latest")
            tags+=("stable")
            tags+=("$commit_hash")
            if [ "$branch_name" = "main" ]; then
                tags+=("production")
            fi
            ;;
        *)
            print_error "Unknown environment: $environment"
            return 1
            ;;
    esac
    
    # Build Docker tags
    local docker_tags=()
    for tag in "${tags[@]}"; do
        docker_tags+=("-t" "$registry/${GITHUB_REPOSITORY:-$solution}/$solution:$tag")
    done
    
    # Check if Dockerfile exists
    if [ ! -f "Dockerfile" ]; then
        print_error "Dockerfile not found in $solution"
        cd ..
        return 1
    fi
    
    # Build the image
    print_status "Building $solution with tags: ${tags[*]}"
    
    if docker build \
        --platform linux/amd64,linux/arm64 \
        "${docker_tags[@]}" \
        --label "org.opencontainers.image.created=$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --label "org.opencontainers.image.revision=$(git rev-parse HEAD)" \
        --label "org.opencontainers.image.source=https://github.com/${GITHUB_REPOSITORY:-local}/$solution" \
        --label "environment=$environment" \
        --label "solution=$solution" \
        .; then
        print_success "Successfully built $solution Docker image"
    else
        print_error "Failed to build $solution Docker image"
        cd ..
        return 1
    fi
    
    cd ..
}

# Function to push Docker image
push_image() {
    local solution=$1
    local environment=$2
    local registry=$3
    
    print_status "Pushing Docker image for $solution ($environment)"
    
    # Determine image tags based on environment
    local tags=()
    local commit_hash=$(git rev-parse --short HEAD)
    local branch_name=$(git rev-parse --abbrev-ref HEAD)
    
    case $environment in
        "development")
            tags+=("develop")
            tags+=("$commit_hash")
            if [ "$branch_name" != "main" ]; then
                tags+=("$branch_name")
            fi
            ;;
        "staging")
            tags+=("staging")
            tags+=("candidate")
            tags+=("$commit_hash")
            ;;
        "production")
            tags+=("latest")
            tags+=("stable")
            tags+=("$commit_hash")
            if [ "$branch_name" = "main" ]; then
                tags+=("production")
            fi
            ;;
    esac
    
    # Push images
    for tag in "${tags[@]}"; do
        local image_name="$registry/${GITHUB_REPOSITORY:-$solution}/$solution:$tag"
        print_status "Pushing $image_name"
        
        if docker push "$image_name"; then
            print_success "Successfully pushed $image_name"
        else
            print_error "Failed to push $image_name"
            return 1
        fi
    done
}

# Function to scan image for vulnerabilities
scan_image() {
    local solution=$1
    local environment=$2
    local registry=$3
    
    print_status "Scanning $solution image for vulnerabilities"
    
    # Determine primary tag
    local primary_tag
    case $environment in
        "development")
            primary_tag="develop"
            ;;
        "staging")
            primary_tag="staging"
            ;;
        "production")
            primary_tag="latest"
            ;;
    esac
    
    local image_name="$registry/${GITHUB_REPOSITORY:-$solution}/$solution:$primary_tag"
    
    # Check if Trivy is available
    if ! command -v trivy &> /dev/null; then
        print_warning "Trivy not found, skipping vulnerability scan"
        return 0
    fi
    
    # Create scan directory
    mkdir -p "security-scans/$solution"
    
    # Run security scan
    if trivy image \
        --format json \
        --output "security-scans/$solution/scan-$(date +%Y%m%d_%H%M%S).json" \
        --severity CRITICAL,HIGH,MEDIUM \
        "$image_name"; then
        print_success "Vulnerability scan completed for $solution"
    else
        print_warning "Vulnerability scan failed for $solution"
    fi
}

# Function to generate SBOM
generate_sbom() {
    local solution=$1
    local environment=$2
    local registry=$3
    
    print_status "Generating SBOM for $solution"
    
    # Determine primary tag
    local primary_tag
    case $environment in
        "development")
            primary_tag="develop"
            ;;
        "staging")
            primary_tag="staging"
            ;;
        "production")
            primary_tag="latest"
            ;;
    esac
    
    local image_name="$registry/${GITHUB_REPOSITORY:-$solution}/$solution:$primary_tag"
    
    # Create SBOM directory
    mkdir -p "sbom/$solution"
    
    # Generate SBOM using Syft if available
    if command -v syft &> /dev/null; then
        if syft "$image_name" \
            --output cyclonedx-json \
            --file "sbom/$solution/sbom-$(date +%Y%m%d_%H%M%S).json"; then
            print_success "SBOM generated for $solution"
        else
            print_warning "Failed to generate SBOM for $solution"
        fi
    else
        print_warning "Syft not found, skipping SBOM generation"
    fi
}

# Function to validate image
validate_image() {
    local solution=$1
    local environment=$2
    local registry=$3
    
    print_status "Validating $solution image"
    
    # Determine primary tag
    local primary_tag
    case $environment in
        "development")
            primary_tag="develop"
            ;;
        "staging")
            primary_tag="staging"
            ;;
        "production")
            primary_tag="latest"
            ;;
    esac
    
    local image_name="$registry/${GITHUB_REPOSITORY:-$solution}/$solution:$primary_tag"
    
    # Test if image can be pulled
    if docker pull "$image_name" >/dev/null 2>&1; then
        print_success "Image validation successful for $solution"
        
        # Test if image can run basic command
        if docker run --rm "$image_name" echo "Container validation successful" >/dev/null 2>&1; then
            print_success "Container runtime validation successful for $solution"
        else
            print_warning "Container runtime validation failed for $solution"
        fi
    else
        print_error "Image validation failed for $solution"
        return 1
    fi
}

# Main execution
main() {
    print_status "Starting container build process"
    print_status "Solution: $SOLUTION"
    print_status "Environment: $ENVIRONMENT"
    print_status "Registry: $REGISTRY"
    
    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "Not in a git repository"
        exit 1
    fi
    
    # Build specific solution or all solutions
    if [ "$SOLUTION" = "all" ]; then
        print_status "Building all solutions"
        
        for solution in "${SOLUTIONS[@]}"; do
            if [ -d "$solution" ]; then
                print_status "Processing $solution"
                
                # Build image
                if build_image "$solution" "$ENVIRONMENT" "$REGISTRY"; then
                    # Push image
                    if push_image "$solution" "$ENVIRONMENT" "$REGISTRY"; then
                        # Scan image
                        scan_image "$solution" "$ENVIRONMENT" "$REGISTRY"
                        
                        # Generate SBOM
                        generate_sbom "$solution" "$ENVIRONMENT" "$REGISTRY"
                        
                        # Validate image
                        validate_image "$solution" "$ENVIRONMENT" "$REGISTRY"
                        
                        print_success "Successfully processed $solution"
                    else
                        print_error "Failed to process $solution"
                    fi
                else
                    print_error "Failed to build $solution"
                fi
            else
                print_warning "Solution directory $solution does not exist, skipping"
            fi
        done
    else
        # Build specific solution
        if [[ " ${SOLUTIONS[@]} " =~ " ${SOLUTION} " ]]; then
            print_status "Processing $SOLUTION"
            
            # Build image
            if build_image "$SOLUTION" "$ENVIRONMENT" "$REGISTRY"; then
                # Push image
                if push_image "$SOLUTION" "$ENVIRONMENT" "$REGISTRY"; then
                    # Scan image
                    scan_image "$SOLUTION" "$ENVIRONMENT" "$REGISTRY"
                    
                    # Generate SBOM
                    generate_sbom "$SOLUTION" "$ENVIRONMENT" "$REGISTRY"
                    
                    # Validate image
                    validate_image "$SOLUTION" "$ENVIRONMENT" "$REGISTRY"
                    
                    print_success "Successfully processed $SOLUTION"
                else
                    print_error "Failed to process $SOLUTION"
                fi
            else
                print_error "Failed to build $SOLUTION"
            fi
        else
            print_error "Invalid solution: $SOLUTION"
            print_status "Available solutions: ${SOLUTIONS[*]}"
            exit 1
        fi
    fi
    
    print_success "Container build process completed"
}

# Show help
show_help() {
    echo "Usage: $0 [SOLUTION] [ENVIRONMENT] [REGISTRY]"
    echo ""
    echo "Arguments:"
    echo "  SOLUTION     Solution to build (default: all)"
    echo "              Available: solution-http, solution-fastapi, solution-fastmcp, solution-typescript"
    echo "  ENVIRONMENT  Target environment (default: development)"
    echo "              Available: development, staging, production"
    echo "  REGISTRY    Container registry (default: ghcr.io)"
    echo ""
    echo "Examples:"
    echo "  $0                           # Build all solutions for development"
    echo "  $0 solution-fastapi          # Build FastAPI solution for development"
    echo "  $0 solution-http production  # Build HTTP solution for production"
    echo "  $0 all staging docker.io     # Build all solutions for staging on Docker Hub"
    echo ""
    echo "Environment Variables:"
    echo "  GITHUB_REPOSITORY           GitHub repository name (for registry path)"
    echo ""
}

# Parse command line arguments
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_help
    exit 0
fi

# Run main function
main "$@"