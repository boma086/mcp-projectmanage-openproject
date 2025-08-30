"""
Gunicorn WSGI server configuration for HTTP MCP Solution
Production-ready configuration with performance optimizations
"""
import os
import multiprocessing
from pathlib import Path

# Server socket
bind = f"{os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', '8010')}"
backlog = 2048

# Worker processes
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = int(os.getenv('WORKER_CONNECTIONS', '1000'))
max_requests = int(os.getenv('MAX_REQUESTS', '1000'))
max_requests_jitter = int(os.getenv('MAX_REQUESTS_JITTER', '50'))
preload_app = True

# Timeout configuration
timeout = int(os.getenv('WORKER_TIMEOUT', '30'))
keepalive = int(os.getenv('KEEPALIVE', '2'))
graceful_timeout = int(os.getenv('GRACEFUL_TIMEOUT', '30'))

# Process naming
proc_name = 'mcp-http-server'

# User and group (if running as root)
user = os.getenv('USER', 'mcpuser')
group = os.getenv('GROUP', 'mcpuser')

# Directories
tmp_upload_dir = None
secure_scheme_headers = {
    'X-FORWARDED-PROTOCOL': 'ssl',
    'X-FORWARDED-PROTO': 'https',
    'X-FORWARDED-SSL': 'on'
}

# Logging configuration
log_level = os.getenv('LOG_LEVEL', 'info').lower()
access_log_format = (
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s '
    '"%(f)s" "%(a)s" %(D)s'
)

# Create logs directory if it doesn't exist
logs_dir = Path('/app/logs')
logs_dir.mkdir(exist_ok=True)

# Log files
accesslog = str(logs_dir / 'access.log') if os.getenv('ACCESS_LOG_FILE') != '-' else '-'
errorlog = str(logs_dir / 'error.log') if os.getenv('ERROR_LOG_FILE') != '-' else '-'
capture_output = True
enable_stdio_inheritance = True

# SSL Configuration (if certificates are provided)
keyfile = os.getenv('SSL_KEYFILE')
certfile = os.getenv('SSL_CERTFILE')
ssl_version = 2  # SSLv23
cert_reqs = 0    # ssl.CERT_NONE
ca_certs = os.getenv('SSL_CA_CERTS')
suppress_ragged_eofs = True

# Security headers
forwarded_allow_ips = os.getenv('FORWARDED_ALLOW_IPS', '127.0.0.1')
proxy_allow_ips = os.getenv('PROXY_ALLOW_IPS', '127.0.0.1')
proxy_protocol = os.getenv('PROXY_PROTOCOL', 'false').lower() == 'true'

# Memory and performance tuning
worker_tmp_dir = '/dev/shm' if os.path.exists('/dev/shm') else '/tmp'
limit_request_line = int(os.getenv('LIMIT_REQUEST_LINE', '4094'))
limit_request_fields = int(os.getenv('LIMIT_REQUEST_FIELDS', '100'))
limit_request_field_size = int(os.getenv('LIMIT_REQUEST_FIELD_SIZE', '8190'))

# Environment-specific overrides
if os.getenv('ENVIRONMENT') == 'development':
    # Development settings
    reload = True
    log_level = 'debug'
    workers = 1
    timeout = 60
    capture_output = False
elif os.getenv('ENVIRONMENT') == 'production':
    # Production settings
    reload = False
    preload_app = True
    max_requests = 1000
    max_requests_jitter = 50
    worker_connections = 1000

# Custom worker lifecycle hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Starting MCP HTTP Server with Gunicorn")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("Reloading MCP HTTP Server")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info(f"MCP HTTP Server ready. Listening on {bind}")
    server.log.info(f"Worker processes: {workers}")
    server.log.info(f"Worker class: {worker_class}")

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info(f"Worker {worker.pid} received INT or QUIT signal")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.debug(f"Worker {worker.pid} about to be forked")

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.debug(f"Worker {worker.pid} spawned")

def post_worker_init(worker):
    """Called just after a worker has initialized the application."""
    worker.log.info(f"Worker {worker.pid} initialized")

def worker_abort(worker):
    """Called when a worker received the SIGABRT signal."""
    worker.log.error(f"Worker {worker.pid} received SIGABRT signal")

def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("Forked child, re-executing")

def pre_request(worker, req):
    """Called just before a worker processes the request."""
    worker.log.debug(f"{req.method} {req.uri}")

def post_request(worker, req, environ, resp):
    """Called after a worker processes the request."""
    # Log slow requests
    if hasattr(req, 'start_time'):
        duration = time.time() - req.start_time
        if duration > 1.0:  # Log requests taking more than 1 second
            worker.log.warning(
                f"Slow request: {req.method} {req.uri} took {duration:.2f}s"
            )

# Custom error handling
def worker_connections_exceeded(worker):
    """Called when worker connections exceed limit."""
    worker.log.warning(f"Worker {worker.pid} connections exceeded")

# Import time for request timing
import time