/**
 * Prometheus metrics collection for TypeScript Solution
 */

import client from 'prom-client';
import { RequestMetrics } from '../types';
import { logger } from '../utils/logger';

export class PrometheusMetrics {
  private static instance: PrometheusMetrics;
  private registry: client.Registry;
  private appName: string;

  // HTTP Request Metrics
  private httpRequestsTotal: client.Counter<'method' | 'endpoint' | 'status_code' | 'service'>;
  private httpRequestDurationSeconds: client.Histogram<'method' | 'endpoint' | 'service'>;
  private httpResponseSizeBytes: client.Histogram<'method' | 'endpoint' | 'service'>;

  // Error Metrics
  private httpErrorsTotal: client.Counter<'method' | 'endpoint' | 'status_code' | 'error_type' | 'service'>;
  private mcpErrorsTotal: client.Counter<'error_type' | 'operation' | 'service'>;

  // Business Logic Metrics
  private mcpOperationsTotal: client.Counter<'operation' | 'tool' | 'status' | 'service'>;
  private mcpOperationDurationSeconds: client.Histogram<'operation' | 'tool' | 'service'>;

  // External Service Metrics
  private openprojectRequestsTotal: client.Counter<'method' | 'endpoint' | 'status_code' | 'service'>;
  private openprojectRequestDurationSeconds: client.Histogram<'method' | 'endpoint' | 'service'>;

  // Health Metrics
  private healthCheckStatus: client.Gauge<'check_type' | 'service'>;
  private openprojectConnectionStatus: client.Gauge<'service'>;

  // Performance Metrics
  private activeRequests: client.Gauge<'service'>;
  private requestQueueSize: client.Gauge<'service'>;

  // Node.js Metrics
  private nodejsMemoryHeapUsedBytes: client.Gauge<'service'>;
  private nodejsMemoryHeapTotalBytes: client.Gauge<'service'>;
  private nodejsMemoryExternalBytes: client.Gauge<'service'>;
  private nodejsCpuUsagePercent: client.Gauge<'service'>;

  // Application Info
  private appInfo: client.Info<'service'>;

  private constructor(appName: string = 'typescript-solution') {
    this.appName = appName;
    this.registry = new client.Registry();
    
    this.initializeMetrics();
    this.setupDefaultMetrics();
    this.setApplicationInfo();
  }

  public static getInstance(appName?: string): PrometheusMetrics {
    if (!PrometheusMetrics.instance) {
      PrometheusMetrics.instance = new PrometheusMetrics(appName);
    }
    return PrometheusMetrics.instance;
  }

  private initializeMetrics(): void {
    // HTTP Request Metrics
    this.httpRequestsTotal = new client.Counter({
      name: 'http_requests_total',
      help: 'Total HTTP requests',
      labelNames: ['method', 'endpoint', 'status_code', 'service'],
      registers: [this.registry],
    });

    this.httpRequestDurationSeconds = new client.Histogram({
      name: 'http_request_duration_seconds',
      help: 'HTTP request duration in seconds',
      labelNames: ['method', 'endpoint', 'service'],
      buckets: [0.1, 0.5, 1, 2, 5, 10],
      registers: [this.registry],
    });

    this.httpResponseSizeBytes = new client.Histogram({
      name: 'http_response_size_bytes',
      help: 'HTTP response size in bytes',
      labelNames: ['method', 'endpoint', 'service'],
      buckets: [1024, 4096, 16384, 65536, 262144],
      registers: [this.registry],
    });

    // Error Metrics
    this.httpErrorsTotal = new client.Counter({
      name: 'http_errors_total',
      help: 'Total HTTP errors',
      labelNames: ['method', 'endpoint', 'status_code', 'error_type', 'service'],
      registers: [this.registry],
    });

    this.mcpErrorsTotal = new client.Counter({
      name: 'mcp_errors_total',
      help: 'Total MCP processing errors',
      labelNames: ['error_type', 'operation', 'service'],
      registers: [this.registry],
    });

    // Business Logic Metrics
    this.mcpOperationsTotal = new client.Counter({
      name: 'mcp_operations_total',
      help: 'Total MCP operations',
      labelNames: ['operation', 'tool', 'status', 'service'],
      registers: [this.registry],
    });

    this.mcpOperationDurationSeconds = new client.Histogram({
      name: 'mcp_operation_duration_seconds',
      help: 'MCP operation duration in seconds',
      labelNames: ['operation', 'tool', 'service'],
      buckets: [0.1, 0.5, 1, 2, 5, 10],
      registers: [this.registry],
    });

    // External Service Metrics
    this.openprojectRequestsTotal = new client.Counter({
      name: 'openproject_requests_total',
      help: 'Total OpenProject API requests',
      labelNames: ['method', 'endpoint', 'status_code', 'service'],
      registers: [this.registry],
    });

    this.openprojectRequestDurationSeconds = new client.Histogram({
      name: 'openproject_request_duration_seconds',
      help: 'OpenProject API request duration in seconds',
      labelNames: ['method', 'endpoint', 'service'],
      buckets: [0.5, 1, 2, 5, 10, 30],
      registers: [this.registry],
    });

    // Health Metrics
    this.healthCheckStatus = new client.Gauge({
      name: 'health_check_status',
      help: 'Health check status (1=healthy, 0=unhealthy)',
      labelNames: ['check_type', 'service'],
      registers: [this.registry],
    });

    this.openprojectConnectionStatus = new client.Gauge({
      name: 'openproject_connection_status',
      help: 'OpenProject connection status (1=connected, 0=disconnected)',
      labelNames: ['service'],
      registers: [this.registry],
    });

    // Performance Metrics
    this.activeRequests = new client.Gauge({
      name: 'active_requests',
      help: 'Number of active requests',
      labelNames: ['service'],
      registers: [this.registry],
    });

    this.requestQueueSize = new client.Gauge({
      name: 'request_queue_size',
      help: 'Request queue size',
      labelNames: ['service'],
      registers: [this.registry],
    });

    // Node.js Metrics
    this.nodejsMemoryHeapUsedBytes = new client.Gauge({
      name: 'nodejs_memory_heap_used_bytes',
      help: 'Node.js memory heap used bytes',
      labelNames: ['service'],
      registers: [this.registry],
    });

    this.nodejsMemoryHeapTotalBytes = new client.Gauge({
      name: 'nodejs_memory_heap_total_bytes',
      help: 'Node.js memory heap total bytes',
      labelNames: ['service'],
      registers: [this.registry],
    });

    this.nodejsMemoryExternalBytes = new client.Gauge({
      name: 'nodejs_memory_external_bytes',
      help: 'Node.js memory external bytes',
      labelNames: ['service'],
      registers: [this.registry],
    });

    this.nodejsCpuUsagePercent = new client.Gauge({
      name: 'nodejs_cpu_usage_percent',
      help: 'Node.js CPU usage percent',
      labelNames: ['service'],
      registers: [this.registry],
    });

    // Application Info
    this.appInfo = new client.Info({
      name: 'app_info',
      help: 'Application information',
      labelNames: ['service'],
      registers: [this.registry],
    });
  }

  private setupDefaultMetrics(): void {
    client.collectDefaultMetrics({
      register: this.registry,
      prefix: 'nodejs_',
      labels: { service: this.appName },
    });
  }

  private setApplicationInfo(): void {
    this.appInfo.set(
      {
        app_name: this.appName,
        version: '1.0.0',
        architecture: 'typescript-nodejs',
        node_version: process.version,
      },
      { service: this.appName }
    );
  }

  public recordRequest(metrics: RequestMetrics): void {
    const endpoint = metrics.path || 'unknown';
    const statusCode = metrics.statusCode || 500;

    // Record request count
    this.httpRequestsTotal.inc(
      {
        method: metrics.method,
        endpoint,
        status_code: statusCode,
        service: this.appName,
      }
    );

    // Record request duration
    if (metrics.durationMs !== undefined) {
      const durationSeconds = metrics.durationMs / 1000;
      this.httpRequestDurationSeconds.observe(
        {
          method: metrics.method,
          endpoint,
          service: this.appName,
        },
        durationSeconds
      );
    }

    // Record response size
    if (metrics.responseSize !== undefined) {
      this.httpResponseSizeBytes.observe(
        {
          method: metrics.method,
          endpoint,
          service: this.appName,
        },
        metrics.responseSize
      );
    }

    // Record errors
    if (statusCode >= 400) {
      const errorType = statusCode < 500 ? 'client_error' : 'server_error';
      this.httpErrorsTotal.inc(
        {
          method: metrics.method,
          endpoint,
          status_code: statusCode,
          error_type: errorType,
          service: this.appName,
        }
      );
    }
  }

  public recordMcpOperation(operation: string, tool: string, status: string, durationMs: number): void {
    const durationSeconds = durationMs / 1000;

    this.mcpOperationsTotal.inc(
      {
        operation,
        tool,
        status,
        service: this.appName,
      }
    );

    this.mcpOperationDurationSeconds.observe(
      {
        operation,
        tool,
        service: this.appName,
      },
      durationSeconds
    );
  }

  public recordMcpError(errorType: string, operation: string): void {
    this.mcpErrorsTotal.inc(
      {
        error_type: errorType,
        operation,
        service: this.appName,
      }
    );
  }

  public recordOpenprojectRequest(method: string, endpoint: string, statusCode: number, durationMs: number): void {
    const durationSeconds = durationMs / 1000;

    this.openprojectRequestsTotal.inc(
      {
        method,
        endpoint,
        status_code: statusCode,
        service: this.appName,
      }
    );

    this.openprojectRequestDurationSeconds.observe(
      {
        method,
        endpoint,
        service: this.appName,
      },
      durationSeconds
    );
  }

  public updateHealthStatus(checkType: string, status: boolean): void {
    this.healthCheckStatus.set(
      {
        check_type: checkType,
        service: this.appName,
      },
      status ? 1 : 0
    );
  }

  public updateOpenprojectConnectionStatus(connected: boolean): void {
    this.openprojectConnectionStatus.set(
      {
        service: this.appName,
      },
      connected ? 1 : 0
    );
  }

  public incrementActiveRequests(): void {
    this.activeRequests.inc({ service: this.appName });
  }

  public decrementActiveRequests(): void {
    this.activeRequests.dec({ service: this.appName });
  }

  public updateRequestQueueSize(size: number): void {
    this.requestQueueSize.set({ service: this.appName }, size);
  }

  public updateNodejsMetrics(): void {
    const memUsage = process.memoryUsage();
    
    this.nodejsMemoryHeapUsedBytes.set({ service: this.appName }, memUsage.heapUsed);
    this.nodejsMemoryHeapTotalBytes.set({ service: this.appName }, memUsage.heapTotal);
    this.nodejsMemoryExternalBytes.set({ service: this.appName }, memUsage.external);
  }

  public getMetrics(): string {
    return this.registry.metrics();
  }

  public getRegistry(): client.Registry {
    return this.registry;
  }

  public reset(): void {
    this.registry.reset();
    this.setApplicationInfo();
  }
}

export const prometheusMetrics = PrometheusMetrics.getInstance();
