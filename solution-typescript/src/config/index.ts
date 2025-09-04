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

  private loadConfig(): AppConfig {
    return {
      openproject: {
        url: this.getEnv('OPENPROJECT_URL', 'https://localhost:8080'),
        apiKey: this.getEnv('OPENPROJECT_API_KEY', ''),
      },
      server: {
        port: parseInt(this.getEnv('PORT', '8040')),
        host: this.getEnv('HOST', '0.0.0.0'),
        nodeEnv: this.getEnv('NODE_ENV', 'development'),
      },
      monitoring: {
        enabled: this.getEnv('ENABLE_METRICS', 'true') === 'true',
        metricsPath: this.getEnv('METRICS_PATH', '/metrics'),
        healthCheckEnabled: this.getEnv('HEALTH_CHECK_ENABLED', 'true') === 'true',
        healthCheckPath: this.getEnv('HEALTH_CHECK_PATH', '/health'),
        logLevel: this.getEnv('LOG_LEVEL', 'info'),
        structuredLogging: this.getEnv('STRUCTURED_LOGGING', 'true') === 'true',
        correlationIds: this.getEnv('CORRELATION_IDS', 'true') === 'true',
      },
      rateLimit: {
        enabled: this.getEnv('RATE_LIMIT_ENABLED', 'true') === 'true',
        windowMs: parseInt(this.getEnv('RATE_LIMIT_WINDOW_MS', '900000')),
        maxRequests: parseInt(this.getEnv('RATE_LIMIT_MAX_REQUESTS', '100')),
      },
      security: {
        corsEnabled: this.getEnv('CORS_ENABLED', 'true') === 'true',
        corsOrigin: this.getEnv('CORS_ORIGIN', '*'),
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

    return {
      isValid: errors.length === 0,
      errors,
    };
  }
}

export const config = Config.getInstance();
