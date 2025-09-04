/**
 * Configuration management for TypeScript MCP Solution
 */

import dotenv from 'dotenv';
import { AppConfig } from '../types';

dotenv.config();

export class Config {
  private static instance: Config;
  private config: AppConfig;

  private constructor() {
    this.config = this.loadConfig();
  }

  public static getInstance(): Config {
    if (!Config.instance) {
      Config.instance = new Config();
    }
    return Config.instance;
  }

  public get(): AppConfig {
    return this.config;
  }

  public getOpenProjectConfig() {
    return this.config.openproject;
  }

  public getServerConfig() {
    return this.config.server;
  }

  public getMonitoringConfig() {
    return this.config.monitoring;
  }

  public getRateLimitConfig() {
    return this.config.rateLimit;
  }

  public getSecurityConfig() {
    return this.config.security;
  }

  public getAppConfig() {
    return this.config.app;
  }

  public getPerformanceConfig() {
    return this.config.performance;
  }

  private loadConfig(): AppConfig {
    return {
      app: {
        name: this.getEnv('APP_NAME', 'typescript-mcp'),
        version: this.getEnv('APP_VERSION', '1.0.0'),
        environment: this.getEnv('ENVIRONMENT', 'development'),
        debug: this.getEnv('DEBUG', 'false') === 'true',
      },
      openproject: {
        url: this.getEnv('OPENPROJECT_URL', 'https://localhost:8080'),
        apiKey: this.getEnv('OPENPROJECT_API_KEY', ''),
        timeout: parseInt(this.getEnv('OPENPROJECT_TIMEOUT', '30')),
        maxRetries: parseInt(this.getEnv('OPENPROJECT_MAX_RETRIES', '3')),
      },
      server: {
        port: parseInt(this.getEnv('PORT', '8040')),
        host: this.getEnv('HOST', '0.0.0.0'),
        nodeEnv: this.getEnv('NODE_ENV', 'production'),
        maxConnections: parseInt(this.getEnv('MAX_CONNECTIONS', '100')),
        requestTimeout: parseInt(this.getEnv('REQUEST_TIMEOUT', '30000')),
        maxRequestSize: parseInt(this.getEnv('MAX_REQUEST_SIZE', '10485760')),
      },
      monitoring: {
        enabled: this.getEnv('ENABLE_METRICS', 'true') === 'true',
        metricsPath: this.getEnv('METRICS_PATH', '/metrics'),
        healthCheckEnabled: this.getEnv('HEALTH_CHECK_ENABLED', 'true') === 'true',
        healthCheckInterval: parseInt(this.getEnv('HEALTH_CHECK_INTERVAL', '30')),
        deepHealthCheckInterval: parseInt(this.getEnv('DEEP_HEALTH_CHECK_INTERVAL', '300')),
        logLevel: this.getEnv('LOG_LEVEL', 'info'),
        structuredLogging: this.getEnv('STRUCTURED_LOGGING', 'true') === 'true',
        correlationIds: this.getEnv('CORRELATION_IDS', 'true') === 'true',
      },
      performance: {
        maxConcurrentRequests: parseInt(this.getEnv('MAX_CONCURRENT_REQUESTS', '100')),
        cacheTtl: parseInt(this.getEnv('CACHE_TTL', '300')),
      },
      rateLimit: {
        enabled: this.getEnv('RATE_LIMIT_ENABLED', 'true') === 'true',
        windowMs: parseInt(this.getEnv('RATE_LIMIT_WINDOW_MS', '900000')),
        maxRequests: parseInt(this.getEnv('RATE_LIMIT_MAX_REQUESTS', '100')),
      },
      security: {
        corsEnabled: this.getEnv('CORS_ENABLED', 'true') === 'true',
        corsOrigin: this.getEnv('CORS_ORIGIN', 'http://localhost,http://127.0.0.1'),
        trustedHosts: this.getEnv('TRUSTED_HOSTS', 'localhost,127.0.0.1'),
        helmetEnabled: this.getEnv('HELMET_ENABLED', 'true') === 'true',
        compressionEnabled: this.getEnv('COMPRESSION_ENABLED', 'true') === 'true',
      },
    };
  }

  private getEnv(key: string, defaultValue: string): string {
    const value = process.env[key];
    if (value === undefined || value === '') {
      return defaultValue;
    }
    return value;
  }

  public validate(): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];

    if (!this.config.openproject.url) {
      errors.push('OPENPROJECT_URL is required');
    }

    if (!this.config.openproject.apiKey) {
      errors.push('OPENPROJECT_API_KEY is required');
    }

    if (this.config.server.port < 1 || this.config.server.port > 65535) {
      errors.push('PORT must be between 1 and 65535');
    }

    if (this.config.openproject.timeout <= 0) {
      errors.push('OPENPROJECT_TIMEOUT must be positive');
    }

    if (this.config.server.requestTimeout <= 0) {
      errors.push('REQUEST_TIMEOUT must be positive');
    }

    const validEnvironments = ['development', 'testing', 'production'];
    if (!validEnvironments.includes(this.config.app.environment)) {
      errors.push(`ENVIRONMENT must be one of: ${validEnvironments.join(', ')}`);
    }

    const validLogLevels = ['debug', 'info', 'warn', 'error'];
    if (!validLogLevels.includes(this.config.monitoring.logLevel.toLowerCase())) {
      errors.push(`LOG_LEVEL must be one of: ${validLogLevels.join(', ')}`);
    }

    return {
      isValid: errors.length === 0,
      errors,
    };
  }
}

export const config = Config.getInstance();
