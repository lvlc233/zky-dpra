import request from '@/lib/request';
import { Paper } from '@/types/models';
import { SearchConfig } from '@/types/api';

export interface SearchParams {
  query: string;
  page?: number;
  page_size?: number;
  filters?: Record<string, any>;
}

export const searchService = {
  search: async (params: SearchParams): Promise<Paper[]> => {
    return request.post('/search', params);
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
