import request from '@/lib/request';
import { 
  SystemSettings, 
  SearchSettings, 
  AIReaderSettingsResponse, 
  AIReaderSettingsRequest,
  AgentSettings
} from '@/types/settings';

export const settingsService = {
  // System Settings
  getSystemSettings: async (): Promise<SystemSettings> => {
    const res = await request.get<any>('/settings/system');
    return res.system_settings;
  },

  updateSystemSettings: async (settings: SystemSettings): Promise<void> => {
    const res = await request.patch<any>('/settings/system', { system_settings: settings });
    return res.system_settings;
  },

  // Search Settings
  getSearchSettings: async (): Promise<SearchSettings> => {
    const res = await request.get<any>('/settings/search');
    return res.search_settings;
  },

  updateSearchSettings: async (settings: SearchSettings): Promise<void> => {
    const res = await request.put<any>('/settings/search', { search_settings: settings });
    return res.search_settings;
  },

  // AI Reader Settings
  getAIReaderSettings: async (): Promise<AIReaderSettingsResponse> => {
    return request.get('/settings/reader/ai');
  },

  updateAIReaderSettings: async (data: AIReaderSettingsRequest): Promise<void> => {
    return request.patch('/settings/reader/ai', data);
  }
};
