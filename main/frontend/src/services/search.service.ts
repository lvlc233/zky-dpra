import request from '@/lib/request';
import { Paper } from '@/types/models';
import { SearchConfig } from '@/types/api';

export interface SearchParams {
  query: string;
  page?: number;
  limit?: number;
  filters?: Record<string, any>;
}

export const searchService = {
  search: async (params: SearchParams): Promise<Paper[]> => {
    const data = await request.post('/search', params);
    const items = (data as { items?: Paper[] }).items ?? (data as Paper[]);
    return items.map((paper) => ({ ...paper, id: (paper as { paper_id?: string }).paper_id ?? paper.id }));
  },

  getHistory: async (): Promise<string[]> => {
    return request.get('/search/history');
  },

  clearHistory: async (): Promise<void> => {
    return request.delete('/search/history');
  },

  getConfig: async (): Promise<SearchConfig> => {
    return request.get('/search/config');
  },

  updateConfig: async (config: Partial<SearchConfig>): Promise<SearchConfig> => {
    return request.put('/search/config', config);
  }
};
