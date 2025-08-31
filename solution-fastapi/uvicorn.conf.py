"""
Production-optimized Uvicorn configuration for async FastAPI MCP server

This configuration provides optimal settings for high-concurrency async operations,
connection pooling, and performance tuning for 1000+ concurrent users.
"""
import os
import multiprocessing
from typing import Dict, Any, Optional


def get_worker_count() -> int:
    """Calculate optimal worker count based on CPU cores and environment"""
    cpu_count = multiprocessing.cpu_count()
    
    # Get worker count from environment or calculate based on CPU
    workers = int(os.getenv("WORKERS", 0))
    if workers > 0:
        return min(workers, cpu_count * 2)
    
    # Production: Use 2x CPU cores, development: Use 1 worker
    environment = os.getenv("ENVIRONMENT", "development").lower()
    if environment == "production":
        return min(cpu_count * 2, 8)  # Cap at 8 workers for stability
    else:
        return 1  # Single worker for development


def get_worker_connections() -> int:
    """Calculate optimal worker connections based on expected load"""
    return int(os.getenv("WORKER_CONNECTIONS", 1000))


def get_max_requests() -> int:
    """Calculate max requests per worker before restart (memory management)"""
    return int(os.getenv("MAX_REQUESTS", 10000))


def get_max_requests_jitter() -> int:
    """Get jitter for max requests to prevent thundering herd"""
    return int(os.getenv("MAX_REQUESTS_JITTER", 1000))


def should_use_performance_optimizations() -> bool:
    """Check if we should use performance optimizations (uvloop, httptools)"""
    environment = os.getenv("ENVIRONMENT", "development").lower()
    return environment == "production"


# Core server configuration
bind = f"0.0.0.0:{os.getenv('PORT', '8020')}"
workers = get_worker_count()
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = get_worker_connections()

# Performance and stability settings
max_requests = get_max_requests()
max_requests_jitter = get_max_requests_jitter()
preload_app = True  # Load app before forking workers
keepalive = 2  # TCP keep-alive

# Timeout settings for high-concurrency scenarios
timeout = int(os.getenv("WORKER_TIMEOUT", "30"))
graceful_timeout = int(os.getenv("GRACEFUL_TIMEOUT", "30"))
worker_timeout = timeout

# Logging configuration
loglevel = os.getenv("LOG_LEVEL", "info").lower()
access_log = os.getenv("ACCESS_LOG", "true").lower() == "true"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
error_log = "-"  # Log to stdout
capture_output = True

# Process naming for monitoring
proc_name = "fastapi-mcp-async"

# Security settings
limit_request_line = int(os.getenv("LIMIT_REQUEST_LINE", "8192"))
limit_request_fields = int(os.getenv("LIMIT_REQUEST_FIELDS", "100"))
limit_request_field_size = int(os.getenv("LIMIT_REQUEST_FIELD_SIZE", "8192"))

# SSL configuration (if enabled)
keyfile = os.getenv("SSL_KEYFILE")
certfile = os.getenv("SSL_CERTFILE")
ssl_version = 5  # TLS 1.2+
ciphers = "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS"

# Advanced async configuration
if should_use_performance_optimizations():
    # Use uvloop for better async performance on Unix systems
    worker_class = "uvicorn.workers.UvicornWorker"
    # Note: uvloop and httptools are configured in the FastAPI app itself


def when_ready(server):
    """Hook called when server is ready to receive requests"""
    server.log.info("FastAPI MCP server is ready for async operations")
    server.log.info(f"Configuration: {workers} workers, {worker_connections} connections per worker")
    server.log.info(f"Performance optimizations: {should_use_performance_optimizations()}")


def worker_int(worker):
    """Hook called when worker receives SIGINT"""
    worker.log.info(f"Worker {worker.pid} received SIGINT, shutting down gracefully")


def worker_abort(worker):
    """Hook called when worker is aborted"""
    worker.log.error(f"Worker {worker.pid} was aborted")


def pre_fork(server, worker):
    """Hook called before worker fork"""
    server.log.info(f"Worker {worker.pid} about to fork")


def post_fork(server, worker):
    """Hook called after worker fork"""
    server.log.info(f"Worker {worker.pid} spawned")


def post_worker_init(worker):
    """Hook called after worker initialization"""
    worker.log.info(f"Worker {worker.pid} initialized for async operations")


def worker_exit(server, worker):
    """Hook called when worker exits"""
    server.log.info(f"Worker {worker.pid} exited")


def on_exit(server):
    """Hook called when server exits"""
    server.log.info("FastAPI MCP server shutting down")


def on_reload(server):
    """Hook called when server reloads (development only)"""
    server.log.info("FastAPI MCP server reloading")


# Environment-specific overrides
environment = os.getenv("ENVIRONMENT", "development").lower()

if environment == "development":
    # Development settings for debugging
    reload = True
    workers = 1
    loglevel = "debug"
    access_log = True
    max_requests = 0  # Disable worker restart in development
    
elif environment == "production":
    # Production settings for performance
    reload = False
    workers = get_worker_count()
    loglevel = "info"
    access_log = True
    preload_app = True
    
    # Enable prometheus metrics if available
    if os.getenv("ENABLE_METRICS", "true").lower() == "true":
        try:
            import prometheus_client
            # Enable multiprocess mode for Prometheus metrics
            os.environ["PROMETHEUS_MULTIPROC_DIR"] = "/tmp/prometheus_multiproc"
        except ImportError:
            pass

elif environment == "testing":
    # Testing settings
    reload = False
    workers = 1
    loglevel = "warning"
    access_log = False
    max_requests = 0


# Uvicorn-specific configuration for async optimizations
uvicorn_config: Dict[str, Any] = {
    # Event loop configuration
    "loop": "uvloop" if should_use_performance_optimizations() else "asyncio",
    
    # HTTP protocol configuration
    "http": "httptools" if should_use_performance_optimizations() else "h11",
    
    # WebSocket configuration
    "ws": "websockets",
    "ws_max_size": int(os.getenv("WEBSOCKET_MESSAGE_MAX_SIZE", str(1024 * 1024))),  # 1MB
    "ws_ping_interval": int(os.getenv("WEBSOCKET_HEARTBEAT_INTERVAL", "30")),
    "ws_ping_timeout": 10,
    
    # Lifespan configuration
    "lifespan": "on",
    
    # Header configuration
    "server_header": False,  # Don't expose server version
    "date_header": True,
    
    # Interface configuration
    "interface": "asgi3",
    
    # SSL configuration
    "ssl_keyfile": keyfile,
    "ssl_certfile": certfile,
    "ssl_version": ssl_version if keyfile and certfile else None,
    "ssl_ciphers": ciphers if keyfile and certfile else None,
}

# Performance monitoring configuration
def get_performance_config() -> Dict[str, Any]:
    """Get performance monitoring configuration"""
    return {
        "max_concurrent_requests": int(os.getenv("MAX_CONCURRENT_REQUESTS", "1000")),
        "request_timeout": int(os.getenv("REQUEST_TIMEOUT", "30")),
        "slow_request_threshold": float(os.getenv("SLOW_REQUEST_THRESHOLD", "1.0")),
        "worker_memory_limit": int(os.getenv("WORKER_MEMORY_LIMIT", "512")),  # MB
        "enable_gc_monitoring": os.getenv("ENABLE_GC_MONITORING", "false").lower() == "true",
    }


# Export configuration for external monitoring tools
def get_server_config_summary() -> Dict[str, Any]:
    """Get server configuration summary for monitoring and debugging"""
    return {
        "server": {
            "bind": bind,
            "workers": workers,
            "worker_class": worker_class,
            "worker_connections": worker_connections,
            "environment": environment,
        },
        "performance": {
            "max_requests": max_requests,
            "timeout": timeout,
            "graceful_timeout": graceful_timeout,
            "keepalive": keepalive,
            "preload_app": preload_app,
        },
        "async_optimizations": {
            "loop": uvicorn_config.get("loop"),
            "http": uvicorn_config.get("http"),
            "ws": uvicorn_config.get("ws"),
            "performance_mode": should_use_performance_optimizations(),
        },
        "logging": {
            "level": loglevel,
            "access_log": access_log,
            "capture_output": capture_output,
        },
        "limits": {
            "request_line": limit_request_line,
            "request_fields": limit_request_fields,
            "request_field_size": limit_request_field_size,
        }
    }


# Validate configuration on import
if __name__ == "__main__":
    import json
    config_summary = get_server_config_summary()
    print("Uvicorn Configuration Summary:")
    print(json.dumps(config_summary, indent=2))