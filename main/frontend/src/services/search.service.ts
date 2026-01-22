import request from '@/lib/request';
import { SearchedPaperMetaResponse } from '@/types/api';
import { MatchAnalysisStatus } from '@/types/settings';

export interface SearchParams {
  query: string;
  page: number;
  limit: number;
  
  // Text Match Filters
  match_title?: boolean;
  match_author?: boolean;
  match_abstract?: boolean;
  match_summary?: boolean;
  match_full_text?: boolean;
  
  // Advanced Settings
  match_analysis_status?: MatchAnalysisStatus;
  min_date?: string;
  max_date?: string;

  filters?: any;
}

export const searchService = {
  search: async (params: SearchParams): Promise<SearchedPaperMetaResponse> => {
    return request.post('/search', params);
  },
};
