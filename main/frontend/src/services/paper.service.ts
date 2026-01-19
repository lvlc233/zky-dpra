import request from '@/lib/request';
import { UploadResponse, PaperStatusResponse } from '@/types/api';
import { Paper } from '@/types/models';

const mapPaper = (paper: Paper & Record<string, unknown>): Paper => {
  const mappedId = (paper as { paper_id?: string }).paper_id ?? paper.id;
  return {
    ...paper,
    id: mappedId,
  };
};

export const paperService = {
  upload: async (file: File, collectionId?: string | null): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('files', file);
    if (collectionId) {
      formData.append('collection_id', collectionId);
    }
    return request.post('/papers/upload/local', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  fetchFromUrl: async (url: string, collectionId?: string | null): Promise<UploadResponse[]> => {
    const payload: { urls: string[]; collection_id?: string | null } = { urls: [url] };
    if (collectionId !== undefined) {
      payload.collection_id = collectionId;
    }
    return request.post('/papers/upload/web', payload);
  },

  getList: async (page = 1, limit = 10): Promise<Paper[]> => {
    const data = await request.get('/papers', { params: { page, limit, sort: 'created_at' } });
    const items = (data as { items?: Paper[] }).items ?? (data as Paper[]);
    return items.map((paper) => mapPaper(paper));
  },

  getById: async (id: string): Promise<Paper> => {
    const data = await request.get(`/papers/${id}`);
    return mapPaper(data as Paper);
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
