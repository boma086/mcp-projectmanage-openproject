/**
 * Request correlation ID management
 */

import { v4 as uuidv4 } from 'uuid';

export class RequestCorrelation {
  private static instance: RequestCorrelation;
  private correlationMap: Map<string, string> = new Map();

  private constructor() {}

  public static getInstance(): RequestCorrelation {
    if (!RequestCorrelation.instance) {
      RequestCorrelation.instance = new RequestCorrelation();
    }
    return RequestCorrelation.instance;
  }

  public generateCorrelationId(requestId: string): string {
    const correlationId = `corr_${uuidv4().replace(/-/g, '').substring(0, 12)}`;
    this.correlationMap.set(requestId, correlationId);
    return correlationId;
  }

  public getCorrelationId(requestId: string): string | undefined {
    return this.correlationMap.get(requestId);
  }

  public cleanupCorrelationId(requestId: string): void {
    this.correlationMap.delete(requestId);
  }

  public generateRequestId(): string {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 10);
    return `req_${timestamp}_${random}`;
  }

  public clear(): void {
    this.correlationMap.clear();
  }
}

export const correlation = RequestCorrelation.getInstance();
