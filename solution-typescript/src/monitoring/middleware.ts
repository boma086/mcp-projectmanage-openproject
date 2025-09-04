/**
 * Monitoring middleware for TypeScript Solution
 */

import { Request, Response, NextFunction } from 'express';
import { RequestMetrics } from '../types';
import { logger } from '../utils/logger';
import { correlation } from '../utils/correlation';
import { prometheusMetrics } from './metrics';

export interface MonitoringContext {
  metrics: RequestMetrics;
  startTime: number;
}

export class MonitoringMiddleware {
  private static instance: MonitoringMiddleware;
  private serviceName: string = 'typescript-solution';

  private constructor() {}

  public static getInstance(): MonitoringMiddleware {
    if (!MonitoringMiddleware.instance) {
      MonitoringMiddleware.instance = new MonitoringMiddleware();
    }
    return MonitoringMiddleware.instance;
  }

  public monitorRequest(): (req: Request, res: Response, next: NextFunction) => void {
    return (req: Request, res: Response, next: NextFunction) => {
      const requestId = correlation.generateRequestId();
      const correlationId = correlation.generateCorrelationId(requestId);

      const startTime = Date.now();
      const metrics: RequestMetrics = {
        requestId,
        method: req.method,
        path: req.path,
        startTime,
        userAgent: req.get('user-agent'),
        correlationId,
      };

      // Add correlation ID to request
      req.headers['x-request-id'] = requestId;
      req.headers['x-correlation-id'] = correlationId;
      (req as any).requestId = requestId;
      (req as any).correlationId = correlationId;

      // Increment active requests
      prometheusMetrics.incrementActiveRequests();

      // Store start time for response timing
      (res as any)._startTime = startTime;
      (res as any)._metrics = metrics;

      // Override res.end to capture response metrics
      const originalEnd = res.end;
      res.end = function(chunk?: any, encoding?: any): Response {
        const endTime = Date.now();
        const durationMs = endTime - startTime;

        // Update metrics
        metrics.endTime = endTime;
        metrics.durationMs = durationMs;
        metrics.statusCode = res.statusCode;
        metrics.responseSize = res.get('content-length') ? parseInt(res.get('content-length')!) : undefined;

        // Record metrics
        prometheusMetrics.recordRequest(metrics);

        // Log request
        logger.info('Request completed', {
          requestId: metrics.requestId,
          method: metrics.method,
          path: metrics.path,
          durationMs: metrics.durationMs,
          statusCode: metrics.statusCode,
          userAgent: metrics.userAgent,
          correlationId: metrics.correlationId,
        });

        // Decrement active requests
        prometheusMetrics.decrementActiveRequests();

        // Clean up correlation ID
        correlation.cleanupCorrelationId(requestId);

        // Call original end
        return originalEnd.call(this, chunk, encoding);
      };

      // Handle errors
      res.on('error', (error: Error) => {
        metrics.endTime = Date.now();
        metrics.durationMs = Date.now() - startTime;
        metrics.error = error.message;
        metrics.statusCode = 500;

        prometheusMetrics.recordRequest(metrics);

        logger.error('Request failed', {
          requestId: metrics.requestId,
          method: metrics.method,
          path: metrics.path,
          durationMs: metrics.durationMs,
          statusCode: metrics.statusCode,
          error: error.message,
          userAgent: metrics.userAgent,
          correlationId: metrics.correlationId,
        });

        prometheusMetrics.decrementActiveRequests();
        correlation.cleanupCorrelationId(requestId);
      });

      next();
    };
  }

  public monitorMcpOperation(operation: string, tool: string = 'unknown') {
    return (target: any, propertyKey: string, descriptor: PropertyDescriptor) => {
      const originalMethod = descriptor.value;

      descriptor.value = async function(...args: any[]) {
        const startTime = Date.now();
        let status = 'success';
        let error: any = null;

        try {
          return await originalMethod.apply(this, args);
        } catch (err) {
          status = 'error';
          error = err;
          prometheusMetrics.recordMcpError(err.constructor.name, operation);
          throw err;
        } finally {
          const durationMs = Date.now() - startTime;
          prometheusMetrics.recordMcpOperation(operation, tool, status, durationMs);
        }
      };

      return descriptor;
    };
  }

  public monitorOpenprojectRequest(method: string, endpoint: string) {
    return (target: any, propertyKey: string, descriptor: PropertyDescriptor) => {
      const originalMethod = descriptor.value;

      descriptor.value = async function(...args: any[]) {
        const startTime = Date.now();
        let statusCode = 200;

        try {
          const result = await originalMethod.apply(this, args);
          
          // Try to extract status code from result if available
          if (result && typeof result === 'object' && 'status' in result) {
            statusCode = result.status;
          }
          
          return result;
        } catch (error) {
          statusCode = 500;
          throw error;
        } finally {
          const durationMs = Date.now() - startTime;
          prometheusMetrics.recordOpenprojectRequest(method, endpoint, statusCode, durationMs);
        }
      };

      return descriptor;
    };
  }

  public logRequest(context: Partial<RequestMetrics>): void {
    logger.info('Request processed', context);
  }

  public logError(context: Partial<RequestMetrics>, error: Error): void {
    logger.error('Request failed', {
      ...context,
      error: error.message,
      stack: error.stack,
    });
  }
}

export const monitoringMiddleware = MonitoringMiddleware.getInstance();

// Decorator functions for method-level monitoring
export function MonitorMcpOperation(operation: string, tool: string = 'unknown') {
  return monitoringMiddleware.monitorMcpOperation(operation, tool);
}

export function MonitorOpenprojectRequest(method: string, endpoint: string) {
  return monitoringMiddleware.monitorOpenprojectRequest(method, endpoint);
}
