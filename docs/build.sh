#!/bin/bash

# Build script for OpenProject MCP documentation
# This script builds the documentation using MkDocs

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install dependencies
install_dependencies() {
    log "Installing documentation dependencies..."
    
    # Check if Python is available
    if ! command_exists python3; then
        error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Install dependencies
    if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        pip3 install -r "$SCRIPT_DIR/requirements.txt"
    else
        warn "requirements.txt not found, skipping dependency installation"
    fi
}

# Function to generate documentation
generate_documentation() {
    log "Generating documentation..."
    
    # Change to project directory
    cd "$PROJECT_DIR"
    
    # Run documentation generation scripts
    if [ -f "$SCRIPT_DIR/scripts/generate-api-docs.py" ]; then
        info "Generating API documentation..."
        python3 "$SCRIPT_DIR/scripts/generate-api-docs.py"
    fi
    
    if [ -f "$SCRIPT_DIR/scripts/generate-config-docs.py" ]; then
        info "Generating configuration documentation..."
        python3 "$SCRIPT_DIR/scripts/generate-config-docs.py"
    fi
}

# Function to build documentation
build_documentation() {
    log "Building documentation..."
    
    # Change to project directory
    cd "$PROJECT_DIR"
    
    # Build with MkDocs
    if command_exists mkdocs; then
        mkdocs build --verbose
        
        # Create versioned documentation if mike is available
        if command_exists mike; then
            info "Creating versioned documentation..."
            mike deploy --push --update-aliases latest
        fi
    else
        error "MkDocs is not installed. Please install it with: pip install mkdocs"
        exit 1
    fi
}

# Function to serve documentation locally
serve_documentation() {
    log "Starting local documentation server..."
    
    # Change to project directory
    cd "$PROJECT_DIR"
    
    # Serve with MkDocs
    if command_exists mkdocs; then
        mkdocs serve --dirtyreload
    else
        error "MkDocs is not installed. Please install it with: pip install mkdocs"
        exit 1
    fi
}

# Function to validate documentation
validate_documentation() {
    log "Validating documentation..."
    
    # Check for broken links
    if command_exists markdown-link-check; then
        info "Checking for broken links..."
        find "$SCRIPT_DIR" -name "*.md" -exec markdown-link-check {} \;
    fi
    
    # Check for broken internal links
    if command_exists htmlproofer; then
        info "Checking HTML links..."
        htmlproofer ./site --check-html --only-4xx --assume-extension
    fi
    
    # Validate MkDocs configuration
    if command_exists mkdocs; then
        info "Validating MkDocs configuration..."
        mkdocs build --strict
    fi
}

# Function to deploy documentation
deploy_documentation() {
    log "Deploying documentation..."
    
    # Change to project directory
    cd "$PROJECT_DIR"
    
    # Deploy to GitHub Pages
    if command_exists mkdocs; then
        mkdocs gh-deploy --force
    else
        error "MkDocs is not installed. Please install it with: pip install mkdocs"
        exit 1
    fi
}

# Function to clean build artifacts
clean_build() {
    log "Cleaning build artifacts..."
    
    # Remove site directory
    if [ -d "$PROJECT_DIR/site" ]; then
        rm -rf "$PROJECT_DIR/site"
    fi
    
    # Remove Python cache
    find "$PROJECT_DIR" -name "__pycache__" -type d -exec rm -rf {} +
    find "$PROJECT_DIR" -name "*.pyc" -delete
    
    # Remove Node.js cache
    if [ -d "$PROJECT_DIR/node_modules" ]; then
        rm -rf "$PROJECT_DIR/node_modules"
    fi
}

# Function to show help
show_help() {
    cat << EOF
OpenProject MCP Documentation Build Script

Usage: $0 [COMMAND]

COMMANDS:
    install         Install documentation dependencies
    generate        Generate documentation
    build           Build documentation
    serve           Serve documentation locally
    validate        Validate documentation
    deploy          Deploy documentation to GitHub Pages
    clean           Clean build artifacts
    all             Run all build steps
    help            Show this help message

EXAMPLES:
    $0 install          Install dependencies
    $0 build            Build documentation
    $0 serve            Serve documentation locally
    $0 all              Full build process

ENVIRONMENT VARIABLES:
    DOCS_DIR            Documentation directory (default: docs)
    SKIP_DEPS           Skip dependency installation (true/false)
    SKIP_GENERATE       Skip documentation generation (true/false)
    SKIP_VALIDATE       Skip validation (true/false)
    DEPLOY_BRANCH       Branch to deploy to (default: gh-pages)
    DEPLOY_REMOTE       Remote to deploy to (default: origin)

EOF
}

# Main function
main() {
    local command="${1:-}"
    
    case "$command" in
        install)
            install_dependencies
            ;;
        generate)
            generate_documentation
            ;;
        build)
            generate_documentation
            build_documentation
            ;;
        serve)
            serve_documentation
            ;;
        validate)
            validate_documentation
            ;;
        deploy)
            deploy_documentation
            ;;
        clean)
            clean_build
            ;;
        all)
            if [ "${SKIP_DEPS:-false}" != "true" ]; then
                install_dependencies
            fi
            if [ "${SKIP_GENERATE:-false}" != "true" ]; then
                generate_documentation
            fi
            build_documentation
            if [ "${SKIP_VALIDATE:-false}" != "true" ]; then
                validate_documentation
            fi
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"