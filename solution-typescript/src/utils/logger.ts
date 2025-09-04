/**
 * Structured logging utility with correlation ID support
 */

import winston from 'winston';
import { LogContext } from '../types';
import { Config } from '../config';

const config = Config.getInstance();

export class Logger {
  private static instance: Logger;
  private logger: winston.Logger;
  private serviceName: string = 'typescript-solution';

  private constructor() {
    this.logger = winston.createLogger({
      level: config.get().monitoring.logLevel,
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
      ),
      defaultMeta: { service: this.serviceName },
      transports: [
        new winston.transports.Console({
          format: winston.format.combine(
            winston.format.colorize(),
            winston.format.simple()
          ),
        }),
        new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
        new winston.transports.File({ filename: 'logs/combined.log' }),
      ],
    });
  }

  public static getInstance(): Logger {
    if (!Logger.instance) {
      Logger.instance = new Logger();
    }
    return Logger.instance;
  }

  public info(message: string, context: Partial<LogContext> = {}): void {
    this.logger.info(message, this.formatContext(context));
  }

  public error(message: string, context: Partial<LogContext> = {}): void {
    this.logger.error(message, this.formatContext(context));
  }

  public warn(message: string, context: Partial<LogContext> = {}): void {
    this.logger.warn(message, this.formatContext(context));
  }

  public debug(message: string, context: Partial<LogContext> = {}): void {
    this.logger.debug(message, this.formatContext(context));
  }

  private formatContext(context: Partial<LogContext>): LogContext {
    return {
      timestamp: new Date().toISOString(),
      level: 'info',
      service: this.serviceName,
      ...context,
    } as LogContext;
  }

  public child(context: Partial<LogContext>): winston.Logger {
    return this.logger.child(context);
  }
}

export const logger = Logger.getInstance();
