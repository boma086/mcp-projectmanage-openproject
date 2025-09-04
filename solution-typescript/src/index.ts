/**
 * Main application entry point for TypeScript MCP Solution
 */

import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import morgan from 'morgan';
import rateLimit from 'express-rate-limit';
import { body, validationResult } from 'express-validator';
import { config } from './config';
import { mcpService } from './services/mcp';
import { monitoringEndpoints } from './monitoring/endpoints';
import { monitoringMiddleware } from './monitoring/middleware';
import { logger } from './utils/logger';
import { prometheusMetrics } from './monitoring/metrics';
import { healthChecker } from './monitoring/health';
import { openprojectAdapter } from './adapters/openproject';
import { MCPRequest, MCPResponse } from './types';

class Application {
  private app: express.Application;
  private server: any;

  constructor() {
    this.app = express();
    this.setupMiddleware();
    this.setupRoutes();
    this.setupErrorHandling();
    this.setupGracefulShutdown();
  }

  private setupMiddleware(): void {
    const configData = config.get();

    // Security middleware
    if (configData.security.helmetEnabled) {
      this.app.use(helmet());
    }

    if (configData.security.corsEnabled) {
      this.app.use(cors({
        origin: configData.security.corsOrigin,
        credentials: true,
      }));
    }

    if (configData.security.compressionEnabled) {
      this.app.use(compression());
    }

    // Rate limiting
    if (configData.rateLimit.enabled) {
      const limiter = rateLimit({
        windowMs: configData.rateLimit.windowMs,
        max: configData.rateLimit.maxRequests,
        message: {
          error: 'Too many requests',
          message: 'Rate limit exceeded',
        },
        standardHeaders: true,
        legacyHeaders: false,
      });
      this.app.use(limiter);
    }

    // Body parsing
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true, limit: '10mb' }));

    // Logging
    this.app.use(morgan('combined', {
      stream: {
        write: (message: string) => {
          logger.info('HTTP request', { message: message.trim() });
        },
      },
    }));

    // Monitoring middleware
    this.app.use(monitoringMiddleware.monitorRequest());

    // Request logging
    this.app.use((req, res, next) => {
      logger.info('Incoming request', {
        method: req.method,
        path: req.path,
        userAgent: req.get('user-agent'),
        ip: req.ip,
        requestId: (req as any).requestId,
        correlationId: (req as any).correlationId,
      });
      next();
    });
  }

  private setupRoutes(): void {
    const configData = config.get();

    // Health check endpoints
    this.app.get('/health', (req, res) => monitoringEndpoints.getHealth(req, res));
    this.app.get('/health/live', (req, res) => monitoringEndpoints.getHealthLive(req, res));
    this.app.get('/health/ready', (req, res) => monitoringEndpoints.getHealthReady(req, res));

    // Metrics endpoint
    if (configData.monitoring.enabled) {
      this.app.get(configData.monitoring.metricsPath, (req, res) => monitoringEndpoints.getMetrics(req, res));
    }

    // Server info endpoint
    this.app.get('/info', (req, res) => monitoringEndpoints.getServerInfo(req, res));

    // Node.js metrics endpoint
    this.app.get('/nodejs-metrics', (req, res) => monitoringEndpoints.getNodejsMetrics(req, res));

    // MCP endpoint
    this.app.post('/mcp', 
      [
        body('jsonrpc').equals('2.0').withMessage('JSON-RPC version must be 2.0'),
        body('id').notEmpty().withMessage('Request ID is required'),
        body('method').notEmpty().withMessage('Method is required'),
      ],
      async (req, res) => {
        try {
          const errors = validationResult(req);
          if (!errors.isEmpty()) {
            return res.status(400).json({
              jsonrpc: '2.0',
              id: req.body.id,
              error: {
                code: -32600,
                message: 'Invalid Request',
                data: errors.array(),
              },
            });
          }

          const mcpRequest: MCPRequest = req.body;
          const response = await mcpService.handleRequest(mcpRequest);

          res.json(response);
        } catch (error) {
          logger.error('MCP request processing failed', {
            error: error instanceof Error ? error.message : 'Unknown error',
            requestId: (req as any).requestId,
            correlationId: (req as any).correlationId,
          });

          res.status(500).json({
            jsonrpc: '2.0',
            id: req.body.id,
            error: {
              code: -32603,
              message: 'Internal error',
            },
          });
        }
      }
    );

    // Legacy MCP endpoint for backward compatibility
    this.app.post('/', 
      [
        body('jsonrpc').equals('2.0').withMessage('JSON-RPC version must be 2.0'),
        body('id').notEmpty().withMessage('Request ID is required'),
        body('method').notEmpty().withMessage('Method is required'),
      ],
      async (req, res) => {
        try {
          const errors = validationResult(req);
          if (!errors.isEmpty()) {
            return res.status(400).json({
              jsonrpc: '2.0',
              id: req.body.id,
              error: {
                code: -32600,
                message: 'Invalid Request',
                data: errors.array(),
              },
            });
          }

          const mcpRequest: MCPRequest = req.body;
          const response = await mcpService.handleRequest(mcpRequest);

          res.json(response);
        } catch (error) {
          logger.error('MCP request processing failed', {
            error: error instanceof Error ? error.message : 'Unknown error',
            requestId: (req as any).requestId,
            correlationId: (req as any).correlationId,
          });

          res.status(500).json({
            jsonrpc: '2.0',
            id: req.body.id,
            error: {
              code: -32603,
              message: 'Internal error',
            },
          });
        }
      }
    );

    // Root endpoint
    this.app.get('/', (req, res) => {
      res.json({
        name: 'OpenProject MCP Server - TypeScript',
        version: '1.0.0',
        documentation: '/info',
        endpoints: {
          mcp: '/mcp',
          health: '/health',
          metrics: configData.monitoring.enabled ? configData.monitoring.metricsPath : undefined,
          info: '/info',
        },
      });
    });

    // 404 handler
    this.app.use((req, res) => {
      logger.warn('Route not found', {
        method: req.method,
        path: req.path,
        requestId: (req as any).requestId,
        correlationId: (req as any).correlationId,
      });

      res.status(404).json({
        error: 'Not Found',
        message: `Route ${req.method} ${req.path} not found`,
      });
    });
  }

  private setupErrorHandling(): void {
    // Global error handler
    this.app.use((error: Error, req: express.Request, res: express.Response, next: express.NextFunction) => {
      logger.error('Unhandled error', {
        error: error.message,
        stack: error.stack,
        method: req.method,
        path: req.path,
        requestId: (req as any).requestId,
        correlationId: (req as any).correlationId,
      });

      res.status(500).json({
        error: 'Internal Server Error',
        message: 'An unexpected error occurred',
      });
    });

    // Handle unhandled promise rejections
    process.on('unhandledRejection', (reason, promise) => {
      logger.error('Unhandled promise rejection', {
        reason: reason instanceof Error ? reason.message : reason,
        promise: promise,
      });
    });

    // Handle uncaught exceptions
    process.on('uncaughtException', (error) => {
      logger.error('Uncaught exception', {
        error: error.message,
        stack: error.stack,
      });
      
      // Graceful shutdown
      this.gracefulShutdown();
    });
  }

  private setupGracefulShutdown(): void {
    const gracefulShutdown = () => {
      logger.info('Starting graceful shutdown...');

      this.server.close(() => {
        logger.info('Server closed');
        process.exit(0);
      });

      // Force shutdown after timeout
      setTimeout(() => {
        logger.error('Graceful shutdown timeout, forcing exit');
        process.exit(1);
      }, 10000);
    };

    process.on('SIGTERM', gracefulShutdown);
    process.on('SIGINT', gracefulShutdown);
  }

  private async initializeServices(): Promise<void> {
    try {
      const configData = config.get();
      
      // Initialize health checker with OpenProject config
      healthChecker.updateConfig(configData.openproject.url, configData.openproject.apiKey);
      
      // Initialize OpenProject adapter
      openprojectAdapter.updateConfig(configData.openproject);
      
      // Test OpenProject connection
      const connectionOk = await openprojectAdapter.testConnection();
      if (!connectionOk) {
        logger.warn('OpenProject connection test failed, but service will continue');
      } else {
        logger.info('OpenProject connection test successful');
      }

      // Start Node.js metrics collection
      setInterval(() => {
        prometheusMetrics.updateNodejsMetrics();
      }, 15000); // Update every 15 seconds

      logger.info('Services initialized successfully');
    } catch (error) {
      logger.error('Failed to initialize services', {
        error: error instanceof Error ? error.message : 'Unknown error',
      });
      throw error;
    }
  }

  public async start(): Promise<void> {
    try {
      const configData = config.get();
      const validation = config.validate();

      if (!validation.isValid) {
        logger.error('Configuration validation failed', { errors: validation.errors });
        throw new Error(`Configuration validation failed: ${validation.errors.join(', ')}`);
      }

      // Initialize services
      await this.initializeServices();

      // Start server
      this.server = this.app.listen(configData.server.port, configData.server.host, () => {
        logger.info('Server started', {
          host: configData.server.host,
          port: configData.server.port,
          environment: configData.server.nodeEnv,
          monitoring: configData.monitoring.enabled,
          metricsPath: configData.monitoring.enabled ? configData.monitoring.metricsPath : undefined,
        });
      });

      this.server.on('error', (error: Error) => {
        logger.error('Server error', { error: error.message });
        throw error;
      });

    } catch (error) {
      logger.error('Failed to start server', {
        error: error instanceof Error ? error.message : 'Unknown error',
      });
      process.exit(1);
    }
  }

  public gracefulShutdown(): void {
    if (this.server) {
      this.server.close(() => {
        logger.info('Server closed gracefully');
        process.exit(0);
      });
    }
  }
}

// Start the application
async function main() {
  try {
    const app = new Application();
    await app.start();
  } catch (error) {
    logger.error('Failed to start application', {
      error: error instanceof Error ? error.message : 'Unknown error',
    });
    process.exit(1);
  }
}

// Handle direct execution
if (require.main === module) {
  main();
}

export default Application;
