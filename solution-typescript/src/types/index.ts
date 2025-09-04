/**
 * Type definitions for TypeScript MCP Solution
 */

export interface RequestMetrics {
  requestId: string;
  method: string;
  path: string;
  startTime: number;
  endTime?: number;
  durationMs?: number;
  statusCode?: number;
  responseSize?: number;
  error?: string;
  userAgent?: string;
  correlationId?: string;
}

export interface HealthCheckResult {
  name: string;
  status: HealthStatus;
  durationMs: number;
  message: string;
  details?: Record<string, any>;
  timestamp: number;
}

export interface HealthCheckSummary {
  overallStatus: HealthStatus;
  totalChecks: number;
  healthyChecks: number;
  degradedChecks: number;
  unhealthyChecks: number;
  results: HealthCheckResult[];
  timestamp: number;
}

export interface AppConfig {
  app: {
    name: string;
    version: string;
    environment: string;
    debug: boolean;
  };
  openproject: {
    url: string;
    apiKey: string;
    timeout: number;
    maxRetries: number;
  };
  server: {
    port: number;
    host: string;
    nodeEnv: string;
    maxConnections: number;
    requestTimeout: number;
    maxRequestSize: number;
  };
  monitoring: {
    enabled: boolean;
    metricsPath: string;
    healthCheckEnabled: boolean;
    healthCheckInterval: number;
    deepHealthCheckInterval: number;
    logLevel: string;
    structuredLogging: boolean;
    correlationIds: boolean;
  };
  performance: {
    maxConcurrentRequests: number;
    cacheTtl: number;
  };
  rateLimit: {
    enabled: boolean;
    windowMs: number;
    maxRequests: number;
  };
  security: {
    corsEnabled: boolean;
    corsOrigin: string;
    trustedHosts: string;
    helmetEnabled: boolean;
    compressionEnabled: boolean;
  };
}

export interface OpenProjectConfig {
  url: string;
  apiKey: string;
  timeout?: number;
}

export interface MCPRequest {
  jsonrpc: '2.0';
  id: string | number;
  method: string;
  params?: Record<string, any>;
}

export interface MCPResponse {
  jsonrpc: '2.0';
  id: string | number;
  result?: any;
  error?: {
    code: number;
    message: string;
    data?: any;
  };
}

export interface Project {
  id: number;
  name: string;
  identifier: string;
  description?: string;
  status: string;
  createdAt: string;
  updatedAt: string;
}

export interface WorkPackage {
  id: number;
  subject: string;
  description?: string;
  type: string;
  status: string;
  priority: string;
  assignee?: {
    id: number;
    name: string;
  };
  project: {
    id: number;
    name: string;
  };
  createdAt: string;
  updatedAt: string;
}

export enum HealthStatus {
  HEALTHY = 'healthy',
  DEGRADED = 'degraded',
  UNHEALTHY = 'unhealthy',
  UNKNOWN = 'unknown'
}

export interface LogContext {
  timestamp: string;
  level: string;
  correlationId?: string;
  requestId?: string;
  service: string;
  method?: string;
  path?: string;
  durationMs?: number;
  statusCode?: number;
  userAgent?: string;
  message: string;
  error?: string;
  [key: string]: any;
}

export interface MetricsData {
  name: string;
  type: 'counter' | 'gauge' | 'histogram' | 'summary';
  value: number;
  labels?: Record<string, string>;
  help?: string;
}
