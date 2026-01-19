import request from '@/lib/request';
import { PaperListResponse, UploadResponse, PaperStatusResponse } from '@/types/api';
import { Paper } from '@/types/models';

export const paperService = {
  upload: async (file: File, collectionId?: string | null): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    if (collectionId) {
      formData.append('collection_id', collectionId);
    }
    return request.post('/papers/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  fetchFromUrl: async (url: string, source = 'arXiv'): Promise<any> => {
    return request.post('/papers/fetch', { url, source });
  },

  getList: async (page = 1, limit = 10): Promise<Paper[]> => {
    // API docs say: /papers/list?limit=10&offset=0
    // And response is: [ { "id": "...", ... } ] (Array of papers, not { items, total })
    // Wait, let me double check the docs provided in the prompt.
    // Doc 2.1: Response: [ { "id": "...", ... } ]
    // Doc 2.1: Params: limit, offset.
    const offset = (page - 1) * limit;
    return request.get('/papers/list', { params: { limit, offset } });
  },

  getById: async (id: string): Promise<Paper> => {
    // Note: The doc doesn't explicitly list "Get Detail" endpoint under /papers/
    // But typically it should be there. Assuming /papers/{id} exists or using list.
    // Let's assume standard REST for now, or use list to find.
    // Wait, Doc 2.4 is /papers/{id}/status which returns details + status.
    // Maybe we should use that for details too? Or assume standard GET /papers/{id} exists.
    // I will keep standard GET /papers/{id} but be aware it might not be documented.
    return request.get(`/papers/${id}`); 
  },

  getStatus: async (id: string): Promise<PaperStatusResponse> => {
    return request.get(`/papers/${id}/status`);
  },

  process: async (id: string): Promise<{ status: string }> => {
    return request.post(`/papers/${id}/process`);
  },

  delete: async (id: string): Promise<{ success: boolean }> => {
    // Not documented but standard.
    return request.delete(`/papers/${id}`);
  }
};
