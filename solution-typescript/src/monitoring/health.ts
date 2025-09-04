/**
 * Health check module for TypeScript Solution
 */

import axios from 'axios';
import { HealthStatus, HealthCheckResult, HealthCheckSummary } from '../types';
import { logger } from '../utils/logger';
import { prometheusMetrics } from './metrics';

export class HealthChecker {
  private static instance: HealthChecker;
  private openprojectUrl: string;
  private openprojectApiKey: string;
  private cache: Map<string, { result: HealthCheckResult; timestamp: number }> = new Map();
  private readonly cacheTtl: number = 30000; // 30 seconds

  private constructor(openprojectUrl: string, openprojectApiKey: string) {
    this.openprojectUrl = openprojectUrl;
    this.openprojectApiKey = openprojectApiKey;
  }

  public static getInstance(openprojectUrl?: string, openprojectApiKey?: string): HealthChecker {
    if (!HealthChecker.instance) {
      if (!openprojectUrl || !openprojectApiKey) {
        throw new Error('OpenProject URL and API key are required for health checker initialization');
      }
      HealthChecker.instance = new HealthChecker(openprojectUrl, openprojectApiKey);
    }
    return HealthChecker.instance;
  }

  public async checkLiveness(): Promise<HealthCheckSummary> {
    const startTime = Date.now();
    const results: HealthCheckResult[] = [];

    // Basic service check
    results.push({
      name: 'service_liveness',
      status: HealthStatus.HEALTHY,
      durationMs: Date.now() - startTime,
      message: 'Service is running',
      timestamp: Date.now(),
    });

    return {
      overallStatus: HealthStatus.HEALTHY,
      totalChecks: 1,
      healthyChecks: 1,
      degradedChecks: 0,
      unhealthyChecks: 0,
      results,
      timestamp: Date.now(),
    };
  }

  public async checkReadiness(): Promise<HealthCheckSummary> {
    const startTime = Date.now();
    const results: HealthCheckResult[] = [];

    try {
      // Check if monitoring is working
      const metrics = prometheusMetrics.getMetrics();
      if (metrics) {
        results.push({
          name: 'service_readiness',
          status: HealthStatus.HEALTHY,
          durationMs: Date.now() - startTime,
          message: 'Service is ready to handle traffic',
          timestamp: Date.now(),
        });
      } else {
        results.push({
          name: 'service_readiness',
          status: HealthStatus.DEGRADED,
          durationMs: Date.now() - startTime,
          message: 'Service monitoring not available',
          timestamp: Date.now(),
        });
      }
    } catch (error) {
      results.push({
        name: 'service_readiness',
        status: HealthStatus.UNHEALTHY,
        durationMs: Date.now() - startTime,
        message: `Service not ready: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: Date.now(),
      });
    }

    return this.summarizeResults(results);
  }

  public async checkDeepHealth(): Promise<HealthCheckSummary> {
    const startTime = Date.now();
    const results: HealthCheckResult[] = [];

    // Service health
    results.push(await this.checkServiceHealth());

    // OpenProject connection
    results.push(await this.checkOpenprojectConnection());

    // Resource health
    results.push(await this.checkResourceHealth());

    return this.summarizeResults(results);
  }

  private async checkServiceHealth(): Promise<HealthCheckResult> {
    const startTime = Date.now();

    try {
      // Check if monitoring is working
      const metrics = prometheusMetrics.getMetrics();
      let status: HealthStatus;
      let message: string;

      if (metrics) {
        status = HealthStatus.HEALTHY;
        message = 'Service monitoring is active';
      } else {
        status = HealthStatus.DEGRADED;
        message = 'Service monitoring not available';
      }

      const result: HealthCheckResult = {
        name: 'service_health',
        status,
        durationMs: Date.now() - startTime,
        message,
        timestamp: Date.now(),
      };

      // Update Prometheus metrics
      prometheusMetrics.updateHealthStatus('service', status === HealthStatus.HEALTHY);

      return result;
    } catch (error) {
      const result: HealthCheckResult = {
        name: 'service_health',
        status: HealthStatus.UNHEALTHY,
        durationMs: Date.now() - startTime,
        message: `Service health check failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: Date.now(),
      };

      // Update Prometheus metrics
      try {
        prometheusMetrics.updateHealthStatus('service', false);
      } catch {
        // Ignore errors during metrics update
      }

      return result;
    }
  }

  private async checkOpenprojectConnection(): Promise<HealthCheckResult> {
    const startTime = Date.now();
    const cacheKey = 'openproject_connection';

    // Check cache first
    const cachedResult = this.getCachedResult(cacheKey);
    if (cachedResult) {
      return cachedResult;
    }

    try {
      const headers = {
        'Authorization': `Bearer ${this.openprojectApiKey}`,
        'Content-Type': 'application/json',
      };

      const response = await axios.get(`${this.openprojectUrl}/api/v3/projects`, {
        headers,
        timeout: 10000,
      });

      let status: HealthStatus;
      let message: string;
      let details: any;

      if (response.status === 200) {
        status = HealthStatus.HEALTHY;
        message = 'OpenProject API connection successful';
        details = {
          responseTimeMs: Date.now() - startTime,
          statusCode: response.status,
          projectsCount: response.data._embedded?.elements?.length || 0,
        };
      } else if (response.status === 401) {
        status = HealthStatus.UNHEALTHY;
        message = 'OpenProject API authentication failed';
        details = {
          statusCode: response.status,
          error: 'Invalid API key',
        };
      } else {
        status = HealthStatus.DEGRADED;
        message = `OpenProject API returned status ${response.status}`;
        details = {
          statusCode: response.status,
          responseTimeMs: Date.now() - startTime,
        };
      }

      const result: HealthCheckResult = {
        name: 'openproject_connection',
        status,
        durationMs: Date.now() - startTime,
        message,
        details,
        timestamp: Date.now(),
      };

      // Update Prometheus metrics
      const connected = status === HealthStatus.HEALTHY;
      try {
        prometheusMetrics.updateOpenprojectConnectionStatus(connected);
      } catch {
        // Ignore errors during metrics update
      }

      // Cache result
      this.cacheResult(cacheKey, result);

      return result;
    } catch (error) {
      let status: HealthStatus;
      let message: string;
      let details: any;

      if (axios.isAxiosError(error) && error.code === 'ECONNABORTED') {
        status = HealthStatus.UNHEALTHY;
        message = 'OpenProject API connection timeout';
        details = { error: 'timeout' };
      } else {
        status = HealthStatus.UNHEALTHY;
        message = `OpenProject API connection failed: ${error instanceof Error ? error.message : 'Unknown error'}`;
        details = { error: error instanceof Error ? error.message : 'Unknown error' };
      }

      const result: HealthCheckResult = {
        name: 'openproject_connection',
        status,
        durationMs: Date.now() - startTime,
        message,
        details,
        timestamp: Date.now(),
      };

      // Update Prometheus metrics
      try {
        prometheusMetrics.updateOpenprojectConnectionStatus(false);
      } catch {
        // Ignore errors during metrics update
      }

      return result;
    }
  }

  private async checkResourceHealth(): Promise<HealthCheckResult> {
    const startTime = Date.now();
    const cacheKey = 'resource_health';

    // Check cache first
    const cachedResult = this.getCachedResult(cacheKey);
    if (cachedResult) {
      return cachedResult;
    }

    try {
      // Get system resource usage
      const memUsage = process.memoryUsage();
      const cpuUsage = process.cpuUsage();
      const totalCpuTime = cpuUsage.user + cpuUsage.system;
      const elapsedMs = Date.now() - startTime;
      const cpuUsagePercent = (totalCpuTime / 1000) / (elapsedMs / 1000) * 100;

      // Determine health status based on resource usage
      let status: HealthStatus = HealthStatus.HEALTHY;
      const issues: string[] = [];

      const memoryUsagePercent = (memUsage.heapUsed / memUsage.heapTotal) * 100;
      
      if (memoryUsagePercent > 90) {
        status = HealthStatus.UNHEALTHY;
        issues.push(`High memory usage: ${memoryUsagePercent.toFixed(1)}%`);
      } else if (memoryUsagePercent > 80) {
        if (status !== HealthStatus.UNHEALTHY) {
          status = HealthStatus.DEGRADED;
        }
        issues.push(`Elevated memory usage: ${memoryUsagePercent.toFixed(1)}%`);
      }

      if (cpuUsagePercent > 90) {
        status = HealthStatus.UNHEALTHY;
        issues.push(`High CPU usage: ${cpuUsagePercent.toFixed(1)}%`);
      } else if (cpuUsagePercent > 80) {
        if (status !== HealthStatus.UNHEALTHY) {
          status = HealthStatus.DEGRADED;
        }
        issues.push(`Elevated CPU usage: ${cpuUsagePercent.toFixed(1)}%`);
      }

      const message = issues.length === 0 ? 'Resource usage normal' : `Resource issues: ${issues.join('; ')}`;

      const details = {
        memoryPercent: Math.round(memoryUsagePercent * 100) / 100,
        memoryUsedMb: Math.round(memUsage.heapUsed / 1024 / 1024 * 100) / 100,
        memoryTotalMb: Math.round(memUsage.heapTotal / 1024 / 1024 * 100) / 100,
        memoryExternalMb: Math.round(memUsage.external / 1024 / 1024 * 100) / 100,
        cpuUsagePercent: Math.round(cpuUsagePercent * 100) / 100,
      };

      const result: HealthCheckResult = {
        name: 'resource_health',
        status,
        durationMs: Date.now() - startTime,
        message,
        details,
        timestamp: Date.now(),
      };

      // Update Node.js metrics
      prometheusMetrics.updateNodejsMetrics();

      // Cache result
      this.cacheResult(cacheKey, result);

      return result;
    } catch (error) {
      const result: HealthCheckResult = {
        name: 'resource_health',
        status: HealthStatus.UNKNOWN,
        durationMs: Date.now() - startTime,
        message: `Resource health check failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: Date.now(),
      };

      return result;
    }
  }

  private summarizeResults(results: HealthCheckResult[]): HealthCheckSummary {
    const healthyChecks = results.filter(r => r.status === HealthStatus.HEALTHY).length;
    const degradedChecks = results.filter(r => r.status === HealthStatus.DEGRADED).length;
    const unhealthyChecks = results.filter(r => r.status === HealthStatus.UNHEALTHY).length;

    let overallStatus: HealthStatus;
    if (unhealthyChecks > 0) {
      overallStatus = HealthStatus.UNHEALTHY;
    } else if (degradedChecks > 0) {
      overallStatus = HealthStatus.DEGRADED;
    } else {
      overallStatus = HealthStatus.HEALTHY;
    }

    return {
      overallStatus,
      totalChecks: results.length,
      healthyChecks,
      degradedChecks,
      unhealthyChecks,
      results,
      timestamp: Date.now(),
    };
  }

  private getCachedResult(cacheKey: string): HealthCheckResult | undefined {
    const cached = this.cache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < this.cacheTtl) {
      return cached.result;
    } else if (cached) {
      // Remove expired cache entry
      this.cache.delete(cacheKey);
    }
    return undefined;
  }

  private cacheResult(cacheKey: string, result: HealthCheckResult): void {
    this.cache.set(cacheKey, { result, timestamp: Date.now() });
  }

  public clearCache(): void {
    this.cache.clear();
  }

  public updateConfig(openprojectUrl: string, openprojectApiKey: string): void {
    this.openprojectUrl = openprojectUrl;
    this.openprojectApiKey = openprojectApiKey;
    this.clearCache();
  }
}

export const healthChecker = HealthChecker.getInstance();
