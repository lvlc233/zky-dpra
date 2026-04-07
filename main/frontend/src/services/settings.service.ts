import request from '@/lib/request';
import { 
  SystemSettings, 
  SearchSettings, 
  AIReaderSettingsResponse, 
  AIReaderSettingsRequest,
  AgentSettings,
  SearchApiConfigInfo,
  SearchApiConfigUpdate,
  SystemStatsResponse,
  SystemModelConfig,
  SystemModelConfigUpdate
} from '@/types/settings';

export const settingsService = {
  // System Settings
  getSystemSettings: async (): Promise<SystemSettings> => {
    const res = await (request.get('/settings/system') as any);
    return res.system_settings;
  },

  updateSystemSettings: async (settings: SystemSettings): Promise<void> => {
    const res = await (request.patch('/settings/system', { system_settings: settings }) as any);
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
  },

  // Agent Settings
  getAgentSettings: async (): Promise<AgentSettings> => {
    const res = await (request.get('/settings/agent') as any);
    return res.agent_settings;
  },

  updateAgentSettings: async (settings: AgentSettings): Promise<void> => {
    const res = await (request.patch('/settings/agent', { agent_settings: settings }) as any);
    return res.agent_settings;
  },

  // Admin Search APIs
  getSearchApiConfigs: async (): Promise<SearchApiConfigInfo[]> => {
    const res = await (request.get('/settings/search-api-configs') as any);
    return res.configs;
  },

  updateSearchApiConfig: async (data: SearchApiConfigUpdate): Promise<SearchApiConfigInfo> => {
    return request.post<any>('/settings/search-api-configs', data);
  },

  deleteSearchApiConfig: async (apiName: string): Promise<boolean> => {
    return request.delete<any>(`/settings/search-api-configs/${apiName}`);
  },

  // System Stats
  getSystemStats: async (): Promise<SystemStatsResponse> => {
    return request.get<SystemStatsResponse>('/settings/system/stats');
  },

  // Admin Model Configs
  getSystemModelConfigs: async (): Promise<SystemModelConfig[]> => {
    return (await request.get('/admin/models')) as any;
  },

  updateSystemModelConfig: async (id: string, data: SystemModelConfigUpdate): Promise<SystemModelConfig> => {
    return (await request.patch(`/admin/models/${id}`, data)) as any;
  },

  createSystemModelConfig: async (type: string, data: SystemModelConfigUpdate): Promise<SystemModelConfig> => {
    return (await request.post(`/admin/models?config_type=${type}`, data)) as any;
  }
};
