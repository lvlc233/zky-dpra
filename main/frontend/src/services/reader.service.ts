import request from '@/lib/request';
import { Layer, Annotation } from '@/types/models';
import { SummaryResponse, GraphResponse } from '@/types/api';

export const readerService = {
  // Summary
  getSummary: async (paperId: string, type = 'default'): Promise<SummaryResponse> => {
    return request.get(`/papers/${paperId}/summary`, { params: { summary_type: type } });
  },

  generateSummary: async (paperId: string, type = 'default'): Promise<SummaryResponse> => {
    return request.post(`/papers/${paperId}/summary`, { summary_type: type });
  },

  // Layers
  getLayers: async (paperId: string): Promise<{ layers: Layer[] }> => {
    return request.get(`/papers/${paperId}/layers`);
  },

  createLayer: async (paperId: string, name: string, type: 'system' | 'user'): Promise<Layer> => {
    return request.post(`/papers/${paperId}/layers`, { name, type });
  },

  updateLayer: async (layerId: string, data: Partial<Layer>): Promise<Layer> => {
    return request.put(`/layers/${layerId}`, data);
  },

  deleteLayer: async (layerId: string): Promise<void> => {
    return request.delete(`/layers/${layerId}`);
  },

  // Annotations
  addAnnotation: async (layerId: string, annotation: Omit<Annotation, 'id'>): Promise<Annotation> => {
    return request.post(`/layers/${layerId}/annotations`, annotation);
  },

  updateAnnotation: async (annoId: string, data: Partial<Annotation>): Promise<Annotation> => {
    return request.put(`/annotations/${annoId}`, data);
  },

  deleteAnnotation: async (annoId: string): Promise<void> => {
    return request.delete(`/annotations/${annoId}`);
  },

  // Notes
  getNotes: async (paperId: string): Promise<any[]> => {
    return request.get(`/papers/${paperId}/notes`);
  },

  createNote: async (paperId: string, content: string): Promise<any> => {
    return request.post(`/papers/${paperId}/notes`, { content });
  },

  // Graph
  getGraph: async (paperId: string): Promise<GraphResponse> => {
    return request.get(`/papers/${paperId}/graph`);
  }
};
