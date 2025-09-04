/**
 * Monitoring endpoints for TypeScript Solution
 */

import { Request, Response } from 'express';
import { prometheusMetrics } from './metrics';
import { healthChecker } from './health';
import { logger } from '../utils/logger';

export class MonitoringEndpoints {
  private static instance: MonitoringEndpoints;

  private constructor() {}

  public static getInstance(): MonitoringEndpoints {
    if (!MonitoringEndpoints.instance) {
      MonitoringEndpoints.instance = new MonitoringEndpoints();
    }
    return MonitoringEndpoints.instance;
  }

  public async getMetrics(req: Request, res: Response): Promise<void> {
    try {
      const metrics = prometheusMetrics.getMetrics();
      
      res.set('Content-Type', 'text/plain; version=0.0.4; charset=utf-8');
      res.send(metrics);
      
      logger.debug('Metrics endpoint accessed', {
        userAgent: req.get('user-agent'),
        correlationId: (req as any).correlationId,
      });
    } catch (error) {
      logger.error('Failed to serve metrics', { error: error instanceof Error ? error.message : 'Unknown error' });
      res.status(500).json({
        error: 'Failed to serve metrics',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  }

  public async getHealth(req: Request, res: Response): Promise<void> {
    try {
      const type = req.query.type as string || 'liveness';
      let healthSummary;

      switch (type) {
        case 'liveness':
          healthSummary = await healthChecker.checkLiveness();
          break;
        case 'readiness':
          healthSummary = await healthChecker.checkReadiness();
          break;
        case 'deep':
          healthSummary = await healthChecker.checkDeepHealth();
          break;
        default:
          res.status(400).json({
            error: 'Invalid health check type',
            validTypes: ['liveness', 'readiness', 'deep'],
          });
          return;
      }

      const statusCode = this.getHealthStatusCode(healthSummary.overallStatus);
      
      res.status(statusCode).json({
        status: healthSummary.overallStatus,
        timestamp: healthSummary.timestamp,
        checks: healthSummary.results,
        summary: {
          total: healthSummary.totalChecks,
          healthy: healthSummary.healthyChecks,
          degraded: healthSummary.degradedChecks,
          unhealthy: healthSummary.unhealthyChecks,
        },
      });

      logger.debug('Health check endpoint accessed', {
        type,
        status: healthSummary.overallStatus,
        correlationId: (req as any).correlationId,
      });
    } catch (error) {
      logger.error('Health check failed', { error: error instanceof Error ? error.message : 'Unknown error' });
      res.status(500).json({
        status: 'unhealthy',
        error: 'Health check failed',
        message: error instanceof Error ? error.message : 'Unknown error',
        timestamp: Date.now(),
      });
    }
  }

  public async getHealthLive(req: Request, res: Response): Promise<void> {
    try {
      const healthSummary = await healthChecker.checkLiveness();
      const statusCode = this.getHealthStatusCode(healthSummary.overallStatus);
      
      res.status(statusCode).json({
        status: healthSummary.overallStatus,
        timestamp: healthSummary.timestamp,
      });
    } catch (error) {
      logger.error('Liveness check failed', { error: error instanceof Error ? error.message : 'Unknown error' });
      res.status(500).json({
        status: 'unhealthy',
        error: 'Liveness check failed',
        timestamp: Date.now(),
      });
    }
  }

  public async getHealthReady(req: Request, res: Response): Promise<void> {
    try {
      const healthSummary = await healthChecker.checkReadiness();
      const statusCode = this.getHealthStatusCode(healthSummary.overallStatus);
      
      res.status(statusCode).json({
        status: healthSummary.overallStatus,
        timestamp: healthSummary.timestamp,
      });
    } catch (error) {
      logger.error('Readiness check failed', { error: error instanceof Error ? error.message : 'Unknown error' });
      res.status(500).json({
        status: 'unhealthy',
        error: 'Readiness check failed',
        timestamp: Date.now(),
      });
    }
  }

  public async getServerInfo(req: Request, res: Response): Promise<void> {
    try {
      const serverInfo = {
        name: 'OpenProject MCP Server - TypeScript',
        version: '1.0.0',
        architecture: 'TypeScript/Node.js',
        environment: process.env.NODE_ENV || 'development',
        uptime: process.uptime(),
        memory: process.memoryUsage(),
        nodeVersion: process.version,
        platform: process.platform,
        features: {
          monitoring: true,
          metrics: true,
          healthChecks: true,
          structuredLogging: true,
          correlationIds: true,
        },
        endpoints: {
          mcp: '/mcp',
          health: '/health',
          metrics: '/metrics',
          healthLive: '/health/live',
          healthReady: '/health/ready',
        },
      };

      res.json(serverInfo);

      logger.debug('Server info endpoint accessed', {
        correlationId: (req as any).correlationId,
      });
    } catch (error) {
      logger.error('Failed to get server info', { error: error instanceof Error ? error.message : 'Unknown error' });
      res.status(500).json({
        error: 'Failed to get server info',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  }

  public async getNodejsMetrics(req: Request, res: Response): Promise<void> {
    try {
      const memoryUsage = process.memoryUsage();
      const cpuUsage = process.cpuUsage();
      const uptime = process.uptime();
      
      const metrics = {
        memory: {
          rss: memoryUsage.rss,
          heapTotal: memoryUsage.heapTotal,
          heapUsed: memoryUsage.heapUsed,
          external: memoryUsage.external,
          arrayBuffers: memoryUsage.arrayBuffers,
        },
        cpu: {
          user: cpuUsage.user,
          system: cpuUsage.system,
        },
        uptime,
        pid: process.pid,
        version: process.version,
        platform: process.platform,
        arch: process.arch,
      };

      res.json(metrics);

      logger.debug('Node.js metrics endpoint accessed', {
        correlationId: (req as any).correlationId,
      });
    } catch (error) {
      logger.error('Failed to get Node.js metrics', { error: error instanceof Error ? error.message : 'Unknown error' });
      res.status(500).json({
        error: 'Failed to get Node.js metrics',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  }

  private getHealthStatusCode(status: string): number {
    switch (status) {
      case 'healthy':
        return 200;
      case 'degraded':
        return 200;
      case 'unhealthy':
        return 503;
      case 'unknown':
        return 500;
      default:
        return 500;
    }
  }
}

export const monitoringEndpoints = MonitoringEndpoints.getInstance();
