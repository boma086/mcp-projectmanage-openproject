#!/usr/bin/env python3
"""
Script to generate configuration documentation from environment variables and config files
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Any
import json

def extract_env_variables():
    """Extract environment variables from .env files and source code"""
    print("Extracting environment variables...")
    
    env_vars = {}
    
    # Check for .env files
    env_files = [
        '.env',
        '.env.example',
        '.env.development',
        '.env.production'
    ]
    
    for env_file in env_files:
        if Path(env_file).exists():
            print(f"Processing {env_file}...")
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key] = {
                            'value': value,
                            'source': env_file,
                            'description': ''
                        }
    
    # Extract from source code
    source_dirs = [
        'solution-http/src',
        'solution-fastapi/app',
        'mcp-core/src'
    ]
    
    for source_dir in source_dirs:
        if Path(source_dir).exists():
            print(f"Scanning {source_dir}...")
            for py_file in Path(source_dir).rglob('*.py'):
                with open(py_file, 'r') as f:
                    content = f.read()
                    
                # Find os.environ.get calls
                matches = re.findall(r'os\.environ\.get\([\'"]([^\'"]+)[\'"]', content)
                for match in matches:
                    if match not in env_vars:
                        env_vars[match] = {
                            'value': '',
                            'source': py_file,
                            'description': ''
                        }
    
    return env_vars

def generate_config_reference(env_vars: Dict[str, Any]):
    """Generate configuration reference documentation"""
    print("Generating configuration reference...")
    
    config_content = f"""# Configuration Reference

This document provides a comprehensive reference for all configuration options available in the OpenProject MCP integration solutions.

## Environment Variables

The following environment variables can be configured in `.env` files or set directly in your environment.

### Required Variables

These variables are required for the application to function:

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
"""
    
    # Required variables
    required_vars = [
        'OPENPROJECT_URL',
        'OPENPROJECT_API_KEY'
    ]
    
    for var in required_vars:
        info = env_vars.get(var, {})
        config_content += f"| `{var}` | URL of your OpenProject instance | Required | `https://your.openproject.com` |\n"
    
    config_content += """
### Server Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
"""
    
    server_vars = [
        ('PORT', 'Server port number', '8010', '8010'),
        ('HOST', 'Server host address', '0.0.0.0', '0.0.0.0'),
        ('ENVIRONMENT', 'Environment (development/production)', 'development', 'production'),
        ('LOG_LEVEL', 'Logging level', 'INFO', 'DEBUG'),
        ('DEBUG', 'Debug mode', 'false', 'true')
    ]
    
    for var, desc, default, example in server_vars:
        config_content += f"| `{var}` | {desc} | `{default}` | `{example}` |\n"
    
    config_content += """
### Database Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
"""
    
    db_vars = [
        ('DATABASE_URL', 'Database connection string', 'sqlite:///app.db', 'postgresql://user:pass@localhost/db'),
        ('DATABASE_POOL_SIZE', 'Database connection pool size', '10', '20'),
        ('DATABASE_MAX_OVERFLOW', 'Maximum overflow connections', '20', '30'),
        ('DATABASE_POOL_TIMEOUT', 'Connection pool timeout (seconds)', '30', '60')
    ]
    
    for var, desc, default, example in db_vars:
        config_content += f"| `{var}` | {desc} | `{default}` | `{example}` |\n"
    
    config_content += """
### Cache Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
"""
    
    cache_vars = [
        ('CACHE_ENABLED', 'Enable caching', 'true', 'true'),
        ('CACHE_TYPE', 'Cache type', 'simple', 'redis'),
        ('CACHE_REDIS_URL', 'Redis connection URL', '', 'redis://localhost:6379/0'),
        ('CACHE_DEFAULT_TIMEOUT', 'Default cache timeout (seconds)', '300', '3600')
    ]
    
    for var, desc, default, example in cache_vars:
        config_content += f"| `{var}` | {desc} | `{default}` | `{example}` |\n"
    
    config_content += """
### Security Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
"""
    
    security_vars = [
        ('SECRET_KEY', 'Application secret key', '', 'your-secret-key-here'),
        ('API_KEY_REQUIRED', 'Require API key for all endpoints', 'true', 'true'),
        ('CORS_ENABLED', 'Enable CORS', 'true', 'true'),
        ('CORS_ORIGINS', 'Allowed CORS origins', '*', 'http://localhost:3000'),
        ('RATE_LIMIT_ENABLED', 'Enable rate limiting', 'true', 'true'),
        ('RATE_LIMIT_REQUESTS', 'Rate limit requests per minute', '60', '1000')
    ]
    
    for var, desc, default, example in security_vars:
        config_content += f"| `{var}` | {desc} | `{default}` | `{example}` |\n"
    
    config_content += """
### Internationalization Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
"""
    
    i18n_vars = [
        ('DEFAULT_LANGUAGE', 'Default language', 'en', 'en'),
        ('SUPPORTED_LANGUAGES', 'Supported languages (comma-separated)', 'en', 'en,ja,de,fr,es'),
        ('I18N_DEBUG', 'Enable i18n debug mode', 'false', 'true'),
        'TRANSLATION_CACHE_ENABLED',
        'TRANSLATION_CACHE_TTL'
    ]
    
    for var in i18n_vars:
        if var in env_vars:
            info = env_vars[var]
            config_content += f"| `{var}` | Enable translation caching | `true` | `true` |\n"
    
    config_content += """
### Performance Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
"""
    
    perf_vars = [
        ('MAX_CONNECTIONS', 'Maximum database connections', '100', '200'),
        ('WORKER_TIMEOUT', 'Worker timeout (seconds)', '30', '60'),
        ('REQUEST_TIMEOUT', 'Request timeout (seconds)', '30', '60'),
        ('GUNICORN_WORKERS', 'Number of Gunicorn workers', '4', '8'),
        ('MAX_REQUESTS', 'Maximum requests per worker', '1000', '2000'),
        ('MAX_REQUESTS_JITTER', 'Request jitter', '50', '100')
    ]
    
    for var, desc, default, example in perf_vars:
        config_content += f"| `{var}` | {desc} | `{default}` | `{example}` |\n"
    
    config_content += f"""
### Monitoring Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
"""
    
    monitoring_vars = [
        ('METRICS_ENABLED', 'Enable metrics collection', 'true', 'true'),
        ('METRICS_PORT', 'Metrics port', '8090', '8090'),
        ('HEALTH_CHECK_ENABLED', 'Enable health checks', 'true', 'true'),
        ('HEALTH_CHECK_INTERVAL', 'Health check interval (seconds)', '30', '60')
    ]
    
    for var, desc, default, example in monitoring_vars:
        config_content += f"| `{var}` | {desc} | `{default}` | `{example}` |\n"
    
    config_content += """
## Configuration Files

### .env File

The `.env` file is used to store environment variables:

```bash
# OpenProject Configuration
OPENPROJECT_URL=https://your.openproject.com
OPENPROJECT_API_KEY=your-api-key-here

# Server Configuration
PORT=8010
HOST=0.0.0.0
ENVIRONMENT=production
LOG_LEVEL=INFO

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/openproject
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Cache Configuration
CACHE_ENABLED=true
CACHE_TYPE=redis
CACHE_REDIS_URL=redis://localhost:6379/0
CACHE_DEFAULT_TIMEOUT=3600

# Security Configuration
SECRET_KEY=your-secret-key-here
CORS_ENABLED=true
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Performance Configuration
MAX_CONNECTIONS=100
WORKER_TIMEOUT=30
GUNICORN_WORKERS=4
```

### Environment-specific Files

You can create environment-specific configuration files:

- `.env.development` - Development environment
- `.env.test` - Testing environment
- `.env.production` - Production environment

The application will automatically load the appropriate file based on the `ENVIRONMENT` variable.

## Configuration Validation

The application validates configuration on startup. Required variables must be present and properly formatted.

### Validation Rules

1. **Required Variables**: `OPENPROJECT_URL` and `OPENPROJECT_API_KEY` are required
2. **URL Format**: `OPENPROJECT_URL` must be a valid URL
3. **Port Range**: `PORT` must be between 1 and 65535
4. **API Key**: `OPENPROJECT_API_KEY` must not be empty

### Validation Commands

```bash
# Validate configuration
python -c "from src.config import validate_config; validate_config()"

# Test OpenProject connection
curl -I "$OPENPROJECT_URL/api/v3/projects" \\
  -H "Authorization: Bearer $OPENPROJECT_API_KEY"
```

## Configuration Best Practices

### Security

1. **Never commit .env files to version control**
2. **Use strong secret keys**
3. **Rotate API keys regularly**
4. **Use environment-specific configurations**
5. **Limit CORS origins to trusted domains**

### Performance

1. **Use connection pooling for databases**
2. **Enable caching for frequently accessed data**
3. **Configure appropriate timeouts**
4. **Monitor resource usage**
5. **Use production-ready settings in production**

### Deployment

1. **Use configuration management tools**
2. **Encrypt sensitive configuration**
3. **Use secret management services**
4. **Implement configuration validation**
5. **Document configuration changes**

### .env.example

Create a `.env.example` file to document required variables:

```bash
# OpenProject Configuration
OPENPROJECT_URL=https://your.openproject.com
OPENPROJECT_API_KEY=your-api-key-here

# Server Configuration
PORT=8010
HOST=0.0.0.0
ENVIRONMENT=development
LOG_LEVEL=INFO

# Database Configuration
DATABASE_URL=sqlite:///app.db

# Cache Configuration
CACHE_ENABLED=true
CACHE_TYPE=simple
CACHE_DEFAULT_TIMEOUT=300

# Security Configuration
SECRET_KEY=your-secret-key-here
CORS_ENABLED=true
CORS_ORIGINS=*

# Performance Configuration
MAX_CONNECTIONS=100
WORKER_TIMEOUT=30
```

## Dynamic Configuration

Some configuration options can be changed at runtime:

### Reloading Configuration

```bash
# Reload configuration (if supported)
curl -X POST http://localhost:8010/admin/reload \\
  -H "Authorization: Bearer your-api-key"
```

### Environment Overrides

You can override configuration at runtime:

```bash
# Override specific variables
OPENPROJECT_URL=https://staging.openproject.com python app/main.py
```

## Configuration Migration

When upgrading versions, review configuration changes:

### Migration Checklist

1. **Review release notes** for configuration changes
2. **Update .env files** with new variables
3. **Remove deprecated variables**
4. **Test configuration validation**
5. **Update documentation**

### Example Migration

```bash
# Backup current configuration
cp .env .env.backup

# Update configuration for new version
sed -i 's/OLD_VAR/NEW_VAR/g' .env

# Add new required variables
echo "NEW_REQUIRED_VAR=value" >> .env

# Validate configuration
python -c "from src.config import validate_config; validate_config()"
```

## Troubleshooting Configuration

### Common Issues

1. **Missing Required Variables**
   ```
   Error: Required environment variable OPENPROJECT_URL not found
   Solution: Set OPENPROJECT_URL in your .env file
   ```

2. **Invalid URL Format**
   ```
   Error: Invalid OpenProject URL format
   Solution: Ensure URL includes protocol (http:// or https://)
   ```

3. **Database Connection Failed**
   ```
   Error: Could not connect to database
   Solution: Check DATABASE_URL and database server status
   ```

4. **Port Already in Use**
   ```
   Error: Port 8010 already in use
   Solution: Change PORT variable or stop conflicting service
   ```

### Debug Commands

```bash
# Check current environment variables
env | grep -E "(OPENPROJECT|PORT|DATABASE)"

# Test database connection
python -c "from src.database import test_connection; test_connection()"

# Validate OpenProject connection
curl -I "$OPENPROJECT_URL/api/v3/projects" \\
  -H "Authorization: Bearer $OPENPROJECT_API_KEY"

# Check configuration
python -c "from src.config import get_config; print(get_config())"
```

This configuration reference should help you configure the OpenProject MCP integration solutions for your specific needs.
"""
    
    output_path = Path('docs/reference/configuration.md')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(config_content)
    
    print(f"✅ Configuration reference saved to {output_path}")

def generate_env_reference(env_vars: Dict[str, Any]):
    """Generate environment variables reference"""
    print("Generating environment variables reference...")
    
    env_content = """# Environment Variables

This document provides a comprehensive list of all environment variables that can be used to configure the OpenProject MCP integration solutions.

## Environment Variables by Category

### OpenProject Integration

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
"""
    
    openproject_vars = [
        ('OPENPROJECT_URL', 'URL of your OpenProject instance', True, ''),
        ('OPENPROJECT_API_KEY', 'API key for OpenProject authentication', True, ''),
        ('OPENPROJECT_TIMEOUT', 'Timeout for OpenProject API requests (seconds)', False, '30'),
        ('OPENPROJECT_VERIFY_SSL', 'Verify SSL certificate for OpenProject', False, 'true')
    ]
    
    for var, desc, required, default in openproject_vars:
        req = "Yes" if required else "No"
        config_content += f"| `{var}` | {desc} | {req} | `{default}` |\n"
    
    env_content += """
### Server Configuration

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
"""
    
    server_vars = [
        ('PORT', 'Server port number', False, '8010'),
        ('HOST', 'Server host address', False, '0.0.0.0'),
        ('ENVIRONMENT', 'Environment (development/production/test)', False, 'development'),
        ('LOG_LEVEL', 'Logging level (DEBUG/INFO/WARNING/ERROR)', False, 'INFO'),
        ('DEBUG', 'Enable debug mode', False, 'false'),
        ('SECRET_KEY', 'Application secret key', False, ''),
        ('BASE_URL', 'Base URL for the application', False, '')
    ]
    
    for var, desc, required, default in server_vars:
        req = "Yes" if required else "No"
        env_content += f"| `{var}` | {desc} | {req} | `{default}` |\n"
    
    env_content += """
### Database Configuration

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
"""
    
    db_vars = [
        ('DATABASE_URL', 'Database connection string', False, 'sqlite:///app.db'),
        ('DATABASE_POOL_SIZE', 'Database connection pool size', False, '10'),
        ('DATABASE_MAX_OVERFLOW', 'Maximum overflow connections', False, '20'),
        ('DATABASE_POOL_TIMEOUT', 'Connection pool timeout (seconds)', False, '30'),
        ('DATABASE_ECHO', 'Log SQL queries', False, 'false')
    ]
    
    for var, desc, required, default in db_vars:
        req = "Yes" if required else "No"
        env_content += f"| `{var}` | {desc} | {req} | `{default}` |\n"
    
    env_content += """
### Cache Configuration

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
"""
    
    cache_vars = [
        ('CACHE_ENABLED', 'Enable caching', False, 'true'),
        ('CACHE_TYPE', 'Cache type (simple/redis)', False, 'simple'),
        ('CACHE_REDIS_URL', 'Redis connection URL', False, ''),
        ('CACHE_DEFAULT_TIMEOUT', 'Default cache timeout (seconds)', False, '300'),
        ('CACHE_KEY_PREFIX', 'Cache key prefix', False, 'mcp_')
    ]
    
    for var, desc, required, default in cache_vars:
        req = "Yes" if required else "No"
        env_content += f"| `{var}` | {desc} | {req} | `{default}` |\n"
    
    env_content += """
### Security Configuration

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
"""
    
    security_vars = [
        ('API_KEY_REQUIRED', 'Require API key for all endpoints', False, 'true'),
        ('CORS_ENABLED', 'Enable CORS', False, 'true'),
        ('CORS_ORIGINS', 'Allowed CORS origins (comma-separated)', False, '*'),
        ('CORS_METHODS', 'Allowed CORS methods', False, 'GET,POST,PUT,DELETE'),
        ('CORS_HEADERS', 'Allowed CORS headers', False, 'Content-Type,Authorization'),
        ('RATE_LIMIT_ENABLED', 'Enable rate limiting', False, 'true'),
        ('RATE_LIMIT_REQUESTS', 'Rate limit requests per minute', False, '60'),
        ('RATE_LIMIT_WINDOW', 'Rate limit window (seconds)', False, '60')
    ]
    
    for var, desc, required, default in security_vars:
        req = "Yes" if required else "No"
        env_content += f"| `{var}` | {desc} | {req} | `{default}` |\n"
    
    env_content += """
### Performance Configuration

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
"""
    
    perf_vars = [
        ('MAX_CONNECTIONS', 'Maximum concurrent connections', False, '100'),
        ('WORKER_TIMEOUT', 'Worker timeout (seconds)', False, '30'),
        ('REQUEST_TIMEOUT', 'Request timeout (seconds)', False, '30'),
        ('GUNICORN_WORKERS', 'Number of Gunicorn workers', False, '4'),
        ('MAX_REQUESTS', 'Maximum requests per worker', False, '1000'),
        ('MAX_REQUESTS_JITTER', 'Request jitter', False, '50'),
        ('WORKER_CONNECTIONS', 'Maximum connections per worker', False, '1000')
    ]
    
    for var, desc, required, default in perf_vars:
        req = "Yes" if required else "No"
        env_content += f"| `{var}` | {desc} | {req} | `{default}` |\n"
    
    env_content += """
### Internationalization Configuration

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
"""
    
    i18n_vars = [
        ('DEFAULT_LANGUAGE', 'Default language code', False, 'en'),
        ('SUPPORTED_LANGUAGES', 'Supported languages (comma-separated)', False, 'en'),
        ('I18N_DEBUG', 'Enable i18n debug mode', False, 'false'),
        ('TRANSLATION_CACHE_ENABLED', 'Enable translation caching', False, 'true'),
        ('TRANSLATION_CACHE_TTL', 'Translation cache TTL (seconds)', False, '3600'),
        ('LOCALE_PATH', 'Path to translation files', False, 'locales')
    ]
    
    for var, desc, required, default in i18n_vars:
        req = "Yes" if required else "No"
        env_content += f"| `{var}` | {desc} | {req} | `{default}` |\n"
    
    env_content += """
### Monitoring and Logging

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
"""
    
    monitoring_vars = [
        ('METRICS_ENABLED', 'Enable metrics collection', False, 'true'),
        ('METRICS_PORT', 'Metrics port', False, '8090'),
        ('HEALTH_CHECK_ENABLED', 'Enable health checks', False, 'true'),
        ('HEALTH_CHECK_INTERVAL', 'Health check interval (seconds)', False, '30'),
        ('LOG_FILE', 'Log file path', False, ''),
        ('LOG_ROTATION', 'Enable log rotation', False, 'true'),
        ('LOG_MAX_SIZE', 'Maximum log file size (MB)', False, '10'),
        ('LOG_BACKUP_COUNT', 'Number of backup log files', False, '5')
    ]
    
    for var, desc, required, default in monitoring_vars:
        req = "Yes" if required else "No"
        env_content += f"| `{var}` | {desc} | {req} | `{default}` |\n"
    
    env_content += """

## Environment File Templates

### Development Environment (.env.development)

```bash
# OpenProject Configuration
OPENPROJECT_URL=http://localhost:8080
OPENPROJECT_API_KEY=dev-api-key

# Server Configuration
PORT=8010
HOST=0.0.0.0
ENVIRONMENT=development
LOG_LEVEL=DEBUG
DEBUG=true

# Database Configuration
DATABASE_URL=sqlite:///dev.db
DATABASE_ECHO=true

# Cache Configuration
CACHE_ENABLED=true
CACHE_TYPE=simple
CACHE_DEFAULT_TIMEOUT=300

# Security Configuration
API_KEY_REQUIRED=false
CORS_ENABLED=true
CORS_ORIGINS=*

# Performance Configuration
MAX_CONNECTIONS=50
WORKER_TIMEOUT=30
```

### Production Environment (.env.production)

```bash
# OpenProject Configuration
OPENPROJECT_URL=https://your.openproject.com
OPENPROJECT_API_KEY=your-production-api-key

# Server Configuration
PORT=8010
HOST=0.0.0.0
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/openproject
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Cache Configuration
CACHE_ENABLED=true
CACHE_TYPE=redis
CACHE_REDIS_URL=redis://localhost:6379/0
CACHE_DEFAULT_TIMEOUT=3600

# Security Configuration
SECRET_KEY=your-secret-key-here
API_KEY_REQUIRED=true
CORS_ENABLED=true
CORS_ORIGINS=https://yourdomain.com
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=1000

# Performance Configuration
MAX_CONNECTIONS=200
WORKER_TIMEOUT=60
GUNICORN_WORKERS=4
MAX_REQUESTS=2000

# Monitoring Configuration
METRICS_ENABLED=true
HEALTH_CHECK_ENABLED=true
LOG_FILE=/var/log/mcp/app.log
LOG_ROTATION=true
```

### Testing Environment (.env.test)

```bash
# OpenProject Configuration
OPENPROJECT_URL=http://localhost:8080
OPENPROJECT_API_KEY=test-api-key

# Server Configuration
PORT=8011
HOST=0.0.0.0
ENVIRONMENT=test
LOG_LEVEL=WARNING
DEBUG=false

# Database Configuration
DATABASE_URL=sqlite:///test.db

# Cache Configuration
CACHE_ENABLED=false

# Security Configuration
API_KEY_REQUIRED=false
CORS_ENABLED=true
CORS_ORIGINS=*
```

## Environment Variable Precedence

Environment variables are loaded in the following order (later values override earlier ones):

1. Default values in code
2. `.env` file
3. Environment-specific `.env.{environment}` file
4. System environment variables

This allows you to override configuration at different levels.

## Best Practices

### Security

1. **Never commit `.env` files to version control**
2. **Use strong secret keys in production**
3. **Use different API keys for different environments**
4. **Rotate API keys regularly**
5. **Use secret management services in production**

### Performance

1. **Use appropriate connection pool sizes**
2. **Enable caching in production**
3. **Configure appropriate timeouts**
4. **Use production-ready logging levels**
5. **Monitor resource usage**

### Deployment

1. **Use environment-specific configurations**
2. **Validate configuration before deployment**
3. **Document configuration changes**
4. **Use configuration management tools**
5. **Implement configuration validation"""
    
    output_path = Path('docs/reference/environment-variables.md')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(env_content)
    
    print(f"✅ Environment variables reference saved to {output_path}")

def main():
    """Main function to generate configuration documentation"""
    print("🚀 Starting configuration documentation generation...")
    
    # Extract environment variables
    env_vars = extract_env_variables()
    
    # Create necessary directories
    Path('docs/reference').mkdir(parents=True, exist_ok=True)
    
    # Generate documentation
    generate_config_reference(env_vars)
    generate_env_reference(env_vars)
    
    print("✅ Configuration documentation generation completed!")

if __name__ == '__main__':
    main()