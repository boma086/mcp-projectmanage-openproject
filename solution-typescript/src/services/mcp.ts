/**
 * MCP (Model Context Protocol) service implementation
 */

import { MCPRequest, MCPResponse, Project, WorkPackage } from '../types';
import { openprojectAdapter } from '../adapters/openproject';
import { logger } from '../utils/logger';
import { MonitorMcpOperation } from '../monitoring/middleware';

export class MCPService {
  private static instance: MCPService;

  private constructor() {}

  public static getInstance(): MCPService {
    if (!MCPService.instance) {
      MCPService.instance = new MCPService();
    }
    return MCPService.instance;
  }

  @MonitorMcpOperation('list_projects', 'mcp')
  public async listProjects(params?: Record<string, any>): Promise<MCPResponse> {
    try {
      const projects = await openprojectAdapter.getProjects();
      
      return {
        jsonrpc: '2.0',
        id: params?.id || 1,
        result: {
          projects,
          count: projects.length,
        },
      };
    } catch (error) {
      logger.error('Failed to list projects', { error: error instanceof Error ? error.message : 'Unknown error' });
      return {
        jsonrpc: '2.0',
        id: params?.id || 1,
        error: {
          code: -32000,
          message: `Failed to list projects: ${error instanceof Error ? error.message : 'Unknown error'}`,
        },
      };
    }
  }

  @MonitorMcpOperation('get_project', 'mcp')
  public async getProject(params: Record<string, any>): Promise<MCPResponse> {
    try {
      const projectId = parseInt(params.projectId);
      if (isNaN(projectId)) {
        throw new Error('Invalid project ID');
      }

      const project = await openprojectAdapter.getProject(projectId);
      
      return {
        jsonrpc: '2.0',
        id: params.id,
        result: project,
      };
    } catch (error) {
      logger.error('Failed to get project', { projectId: params.projectId, error: error instanceof Error ? error.message : 'Unknown error' });
      return {
        jsonrpc: '2.0',
        id: params.id,
        error: {
          code: -32000,
          message: `Failed to get project: ${error instanceof Error ? error.message : 'Unknown error'}`,
        },
      };
    }
  }

  @MonitorMcpOperation('list_work_packages', 'mcp')
  public async listWorkPackages(params: Record<string, any>): Promise<MCPResponse> {
    try {
      const filters: Record<string, any> = {};
      
      if (params.projectId) filters.projectId = parseInt(params.projectId);
      if (params.status) filters.status = params.status;
      if (params.type) filters.type = params.type;
      if (params.assigneeId) filters.assigneeId = parseInt(params.assigneeId);

      const workPackages = await openprojectAdapter.getWorkPackages(filters);
      
      return {
        jsonrpc: '2.0',
        id: params.id,
        result: {
          workPackages,
          count: workPackages.length,
        },
      };
    } catch (error) {
      logger.error('Failed to list work packages', { error: error instanceof Error ? error.message : 'Unknown error' });
      return {
        jsonrpc: '2.0',
        id: params.id,
        error: {
          code: -32000,
          message: `Failed to list work packages: ${error instanceof Error ? error.message : 'Unknown error'}`,
        },
      };
    }
  }

  @MonitorMcpOperation('get_work_package', 'mcp')
  public async getWorkPackage(params: Record<string, any>): Promise<MCPResponse> {
    try {
      const workPackageId = parseInt(params.workPackageId);
      if (isNaN(workPackageId)) {
        throw new Error('Invalid work package ID');
      }

      const workPackage = await openprojectAdapter.getWorkPackage(workPackageId);
      
      return {
        jsonrpc: '2.0',
        id: params.id,
        result: workPackage,
      };
    } catch (error) {
      logger.error('Failed to get work package', { workPackageId: params.workPackageId, error: error instanceof Error ? error.message : 'Unknown error' });
      return {
        jsonrpc: '2.0',
        id: params.id,
        error: {
          code: -32000,
          message: `Failed to get work package: ${error instanceof Error ? error.message : 'Unknown error'}`,
        },
      };
    }
  }

  @MonitorMcpOperation('create_work_package', 'mcp')
  public async createWorkPackage(params: Record<string, any>): Promise<MCPResponse> {
    try {
      const { projectId, subject, description, type, status, priority, assigneeId } = params;
      
      if (!projectId || !subject) {
        throw new Error('Project ID and subject are required');
      }

      const workPackageData: Partial<WorkPackage> = {
        project: { id: parseInt(projectId) },
        subject,
        description,
        type,
        status,
        priority,
        assignee: assigneeId ? { id: parseInt(assigneeId) } : undefined,
      };

      const workPackage = await openprojectAdapter.createWorkPackage(workPackageData);
      
      return {
        jsonrpc: '2.0',
        id: params.id,
        result: workPackage,
      };
    } catch (error) {
      logger.error('Failed to create work package', { error: error instanceof Error ? error.message : 'Unknown error' });
      return {
        jsonrpc: '2.0',
        id: params.id,
        error: {
          code: -32000,
          message: `Failed to create work package: ${error instanceof Error ? error.message : 'Unknown error'}`,
        },
      };
    }
  }

  @MonitorMcpOperation('update_work_package', 'mcp')
  public async updateWorkPackage(params: Record<string, any>): Promise<MCPResponse> {
    try {
      const workPackageId = parseInt(params.workPackageId);
      if (isNaN(workPackageId)) {
        throw new Error('Invalid work package ID');
      }

      const { subject, description, type, status, priority, assigneeId } = params;
      const updates: Partial<WorkPackage> = {};

      if (subject) updates.subject = subject;
      if (description) updates.description = description;
      if (type) updates.type = type;
      if (status) updates.status = status;
      if (priority) updates.priority = priority;
      if (assigneeId) updates.assignee = { id: parseInt(assigneeId) };

      const workPackage = await openprojectAdapter.updateWorkPackage(workPackageId, updates);
      
      return {
        jsonrpc: '2.0',
        id: params.id,
        result: workPackage,
      };
    } catch (error) {
      logger.error('Failed to update work package', { workPackageId: params.workPackageId, error: error instanceof Error ? error.message : 'Unknown error' });
      return {
        jsonrpc: '2.0',
        id: params.id,
        error: {
          code: -32000,
          message: `Failed to update work package: ${error instanceof Error ? error.message : 'Unknown error'}`,
        },
      };
    }
  }

  @MonitorMcpOperation('search_work_packages', 'mcp')
  public async searchWorkPackages(params: Record<string, any>): Promise<MCPResponse> {
    try {
      const { query, projectId, status, type } = params;
      
      const filters: Record<string, any> = {};
      if (projectId) filters.projectId = parseInt(projectId);
      if (status) filters.status = status;
      if (type) filters.type = type;

      let workPackages = await openprojectAdapter.getWorkPackages(filters);

      // Filter by query if provided
      if (query) {
        const lowercaseQuery = query.toLowerCase();
        workPackages = workPackages.filter(wp => 
          wp.subject.toLowerCase().includes(lowercaseQuery) ||
          (wp.description && wp.description.toLowerCase().includes(lowercaseQuery))
        );
      }

      return {
        jsonrpc: '2.0',
        id: params.id,
        result: {
          workPackages,
          count: workPackages.length,
          query,
        },
      };
    } catch (error) {
      logger.error('Failed to search work packages', { query: params.query, error: error instanceof Error ? error.message : 'Unknown error' });
      return {
        jsonrpc: '2.0',
        id: params.id,
        error: {
          code: -32000,
          message: `Failed to search work packages: ${error instanceof Error ? error.message : 'Unknown error'}`,
        },
      };
    }
  }

  @MonitorMcpOperation('get_server_info', 'mcp')
  public async getServerInfo(params: Record<string, any>): Promise<MCPResponse> {
    try {
      return {
        jsonrpc: '2.0',
        id: params.id,
        result: {
          name: 'OpenProject MCP Server',
          version: '1.0.0',
          protocol: 'Model Context Protocol',
          architecture: 'TypeScript/Node.js',
          capabilities: [
            'list_projects',
            'get_project',
            'list_work_packages',
            'get_work_package',
            'create_work_package',
            'update_work_package',
            'search_work_packages',
          ],
        },
      };
    } catch (error) {
      logger.error('Failed to get server info', { error: error instanceof Error ? error.message : 'Unknown error' });
      return {
        jsonrpc: '2.0',
        id: params.id,
        error: {
          code: -32000,
          message: `Failed to get server info: ${error instanceof Error ? error.message : 'Unknown error'}`,
        },
      };
    }
  }

  public async handleRequest(request: MCPRequest): Promise<MCPResponse> {
    const { method, params } = request;

    logger.info('Processing MCP request', {
      method,
      requestId: request.id,
      correlationId: params?.correlationId,
    });

    switch (method) {
      case 'list_projects':
        return this.listProjects(params || {});
      case 'get_project':
        return this.getProject(params || {});
      case 'list_work_packages':
        return this.listWorkPackages(params || {});
      case 'get_work_package':
        return this.getWorkPackage(params || {});
      case 'create_work_package':
        return this.createWorkPackage(params || {});
      case 'update_work_package':
        return this.updateWorkPackage(params || {});
      case 'search_work_packages':
        return this.searchWorkPackages(params || {});
      case 'get_server_info':
        return this.getServerInfo(params || {});
      default:
        logger.warn('Unknown MCP method', { method });
        return {
          jsonrpc: '2.0',
          id: request.id,
          error: {
            code: -32601,
            message: `Method not found: ${method}`,
          },
        };
    }
  }
}

export const mcpService = MCPService.getInstance();
