/**
 * OpenProject API adapter for TypeScript Solution
 */

import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { OpenProjectConfig, Project, WorkPackage } from '../types';
import { logger } from '../utils/logger';
import { MonitorOpenprojectRequest } from '../monitoring/middleware';

export class OpenProjectAdapter {
  private static instance: OpenProjectAdapter;
  private client: AxiosInstance;
  private config: OpenProjectConfig;

  private constructor(config: OpenProjectConfig) {
    this.config = config;
    this.client = this.createAxiosClient();
  }

  public static getInstance(config?: OpenProjectConfig): OpenProjectAdapter {
    if (!OpenProjectAdapter.instance) {
      if (!config) {
        throw new Error('OpenProject configuration is required for initialization');
      }
      OpenProjectAdapter.instance = new OpenProjectAdapter(config);
    }
    return OpenProjectAdapter.instance;
  }

  private createAxiosClient(): AxiosInstance {
    return axios.create({
      baseURL: `${this.config.url}/api/v3`,
      timeout: this.config.timeout || 30000,
      headers: {
        'Authorization': `Bearer ${this.config.apiKey}`,
        'Content-Type': 'application/json',
      },
    });

    // Add response interceptor for logging
    this.client.interceptors.response.use(
      (response) => {
        logger.debug('OpenProject API request successful', {
          method: response.config.method?.toUpperCase(),
          url: response.config.url,
          status: response.status,
          duration: response.headers['x-response-time'],
        });
        return response;
      },
      (error) => {
        logger.error('OpenProject API request failed', {
          method: error.config?.method?.toUpperCase(),
          url: error.config?.url,
          status: error.response?.status,
          message: error.message,
        });
        return Promise.reject(error);
      }
    );

    // Add request interceptor for timing
    this.client.interceptors.request.use((config) => {
      config.metadata = { startTime: Date.now() };
      return config;
    });

    this.client.interceptors.response.use((response) => {
      const endTime = Date.now();
      const startTime = response.config.metadata?.startTime || endTime;
      response.headers['x-response-time'] = endTime - startTime;
      return response;
    });
  }

  @MonitorOpenprojectRequest('GET', '/projects')
  public async getProjects(): Promise<Project[]> {
    try {
      const response: AxiosResponse = await this.client.get('/projects');
      
      if (response.data._embedded?.elements) {
        return response.data._embedded.elements.map((project: any) => ({
          id: project.id,
          name: project.name,
          identifier: project.identifier,
          description: project.description?.raw,
          status: project.status,
          createdAt: project.createdAt,
          updatedAt: project.updatedAt,
        }));
      }
      
      return [];
    } catch (error) {
      logger.error('Failed to fetch projects', { error: error instanceof Error ? error.message : 'Unknown error' });
      throw new Error(`Failed to fetch projects: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  @MonitorOpenprojectRequest('GET', '/projects/{id}')
  public async getProject(id: number): Promise<Project> {
    try {
      const response: AxiosResponse = await this.client.get(`/projects/${id}`);
      
      return {
        id: response.data.id,
        name: response.data.name,
        identifier: response.data.identifier,
        description: response.data.description?.raw,
        status: response.data.status,
        createdAt: response.data.createdAt,
        updatedAt: response.data.updatedAt,
      };
    } catch (error) {
      logger.error('Failed to fetch project', { projectId: id, error: error instanceof Error ? error.message : 'Unknown error' });
      throw new Error(`Failed to fetch project ${id}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  @MonitorOpenprojectRequest('GET', '/work_packages')
  public async getWorkPackages(filters?: Record<string, any>): Promise<WorkPackage[]> {
    try {
      const params = new URLSearchParams();
      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            params.append(`filters[${key}]`, JSON.stringify([value]));
          }
        });
      }

      const response: AxiosResponse = await this.client.get('/work_packages', { params });
      
      if (response.data._embedded?.elements) {
        return response.data._embedded.elements.map((wp: any) => ({
          id: wp.id,
          subject: wp.subject,
          description: wp.description?.raw,
          type: wp.type?.name || 'Unknown',
          status: wp.status?.name || 'Unknown',
          priority: wp.priority?.name || 'Normal',
          assignee: wp.assignee ? {
            id: wp.assignee.id,
            name: wp.assignee.name,
          } : undefined,
          project: {
            id: wp.project.id,
            name: wp.project.name,
          },
          createdAt: wp.createdAt,
          updatedAt: wp.updatedAt,
        }));
      }
      
      return [];
    } catch (error) {
      logger.error('Failed to fetch work packages', { error: error instanceof Error ? error.message : 'Unknown error' });
      throw new Error(`Failed to fetch work packages: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  @MonitorOpenprojectRequest('GET', '/work_packages/{id}')
  public async getWorkPackage(id: number): Promise<WorkPackage> {
    try {
      const response: AxiosResponse = await this.client.get(`/work_packages/${id}`);
      
      return {
        id: response.data.id,
        subject: response.data.subject,
        description: response.data.description?.raw,
        type: response.data.type?.name || 'Unknown',
        status: response.data.status?.name || 'Unknown',
        priority: response.data.priority?.name || 'Normal',
        assignee: response.data.assignee ? {
          id: response.data.assignee.id,
          name: response.data.assignee.name,
        } : undefined,
        project: {
          id: response.data.project.id,
          name: response.data.project.name,
        },
        createdAt: response.data.createdAt,
        updatedAt: response.data.updatedAt,
      };
    } catch (error) {
      logger.error('Failed to fetch work package', { workPackageId: id, error: error instanceof Error ? error.message : 'Unknown error' });
      throw new Error(`Failed to fetch work package ${id}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  @MonitorOpenprojectRequest('POST', '/work_packages')
  public async createWorkPackage(workPackage: Partial<WorkPackage>): Promise<WorkPackage> {
    try {
      const payload = {
        subject: workPackage.subject,
        description: { raw: workPackage.description || '' },
        _links: {
          project: { href: `/api/v3/projects/${workPackage.project?.id}` },
          type: { href: `/api/v3/types/${this.getTypeId(workPackage.type)}` },
          status: { href: `/api/v3/statuses/${this.getStatusId(workPackage.status)}` },
          priority: { href: `/api/v3/priorities/${this.getPriorityId(workPackage.priority)}` },
        },
      };

      if (workPackage.assignee) {
        (payload._links as any).assignee = { href: `/api/v3/users/${workPackage.assignee.id}` };
      }

      const response: AxiosResponse = await this.client.post('/work_packages', payload);
      
      return {
        id: response.data.id,
        subject: response.data.subject,
        description: response.data.description?.raw,
        type: response.data.type?.name || 'Unknown',
        status: response.data.status?.name || 'Unknown',
        priority: response.data.priority?.name || 'Normal',
        assignee: response.data.assignee ? {
          id: response.data.assignee.id,
          name: response.data.assignee.name,
        } : undefined,
        project: {
          id: response.data.project.id,
          name: response.data.project.name,
        },
        createdAt: response.data.createdAt,
        updatedAt: response.data.updatedAt,
      };
    } catch (error) {
      logger.error('Failed to create work package', { error: error instanceof Error ? error.message : 'Unknown error' });
      throw new Error(`Failed to create work package: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  @MonitorOpenprojectRequest('PATCH', '/work_packages/{id}')
  public async updateWorkPackage(id: number, updates: Partial<WorkPackage>): Promise<WorkPackage> {
    try {
      const payload: any = {};

      if (updates.subject) payload.subject = updates.subject;
      if (updates.description) payload.description = { raw: updates.description };

      if (updates.type || updates.status || updates.priority || updates.assignee) {
        payload._links = {};

        if (updates.type) {
          payload._links.type = { href: `/api/v3/types/${this.getTypeId(updates.type)}` };
        }
        if (updates.status) {
          payload._links.status = { href: `/api/v3/statuses/${this.getStatusId(updates.status)}` };
        }
        if (updates.priority) {
          payload._links.priority = { href: `/api/v3/priorities/${this.getPriorityId(updates.priority)}` };
        }
        if (updates.assignee) {
          payload._links.assignee = { href: `/api/v3/users/${updates.assignee.id}` };
        }
      }

      const response: AxiosResponse = await this.client.patch(`/work_packages/${id}`, payload);
      
      return {
        id: response.data.id,
        subject: response.data.subject,
        description: response.data.description?.raw,
        type: response.data.type?.name || 'Unknown',
        status: response.data.status?.name || 'Unknown',
        priority: response.data.priority?.name || 'Normal',
        assignee: response.data.assignee ? {
          id: response.data.assignee.id,
          name: response.data.assignee.name,
        } : undefined,
        project: {
          id: response.data.project.id,
          name: response.data.project.name,
        },
        createdAt: response.data.createdAt,
        updatedAt: response.data.updatedAt,
      };
    } catch (error) {
      logger.error('Failed to update work package', { workPackageId: id, error: error instanceof Error ? error.message : 'Unknown error' });
      throw new Error(`Failed to update work package ${id}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  public async testConnection(): Promise<boolean> {
    try {
      const response = await this.client.get('/projects', { params: { pageSize: 1 } });
      return response.status === 200;
    } catch (error) {
      logger.error('OpenProject connection test failed', { error: error instanceof Error ? error.message : 'Unknown error' });
      return false;
    }
  }

  private getTypeId(typeName: string): number {
    // This is a simplified mapping. In a real implementation, you would fetch the actual type IDs
    const typeMap: Record<string, number> = {
      'Task': 1,
      'Bug': 2,
      'Feature': 3,
      'Milestone': 4,
    };
    return typeMap[typeName] || 1;
  }

  private getStatusId(statusName: string): number {
    // This is a simplified mapping. In a real implementation, you would fetch the actual status IDs
    const statusMap: Record<string, number> = {
      'New': 1,
      'In Progress': 2,
      'Resolved': 3,
      'Closed': 4,
      'Rejected': 5,
    };
    return statusMap[statusName] || 1;
  }

  private getPriorityId(priorityName: string): number {
    // This is a simplified mapping. In a real implementation, you would fetch the actual priority IDs
    const priorityMap: Record<string, number> = {
      'Low': 3,
      'Normal': 4,
      'High': 5,
      'Urgent': 6,
      'Immediate': 7,
    };
    return priorityMap[priorityName] || 4;
  }

  public updateConfig(config: OpenProjectConfig): void {
    this.config = config;
    this.client = this.createAxiosClient();
  }
}

export const openprojectAdapter = OpenProjectAdapter.getInstance();
