import request from '@/lib/request';
import { Collection, Paper } from '@/types/models';

export const collectionService = {
  getAll: async (): Promise<Collection[]> => {
    return request.get('/collections');
  },

  getById: async (id: string): Promise<Collection & { papers: Paper[] }> => {
    return request.get(`/collections/${id}`);
  },

  create: async (name: string, description?: string): Promise<Collection> => {
    return request.post('/collections', { name, description });
  },

  update: async (id: string, data: Partial<Collection>): Promise<Collection> => {
    return request.put(`/collections/${id}`, data);
  },

  delete: async (id: string): Promise<{ success: boolean }> => {
    return request.delete(`/collections/${id}`);
  },

  addPaper: async (collectionId: string, paperId: string): Promise<void> => {
    return request.post(`/collections/${collectionId}/papers`, { paper_id: paperId });
  },

  removePaper: async (collectionId: string, paperId: string): Promise<void> => {
    return request.delete(`/collections/${collectionId}/papers/${paperId}`);
  }
};
