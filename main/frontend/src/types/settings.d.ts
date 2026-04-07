export type SystemTheme = 'light' | 'dark';

export interface SystemSettings {
  system_colour: SystemTheme;
}

export type MatchAnalysisStatus = 'unprocessed' | 'processing' | 'processed' | 'error';

export interface SearchSettings {
  match_analysis_status: MatchAnalysisStatus;
  min_date: string; // ISO date string
  max_date: string; // ISO date string
  limit: number;
}

export type AIReaderType = 'chat' | 'summary' | 'mind_map';

export interface AIReaderConfig {
  // Chat specific
  enable_vector_search?: boolean;
  // Generic config
  [key: string]: any;
}

export interface AIReaderSettings {
  type: AIReaderType;
  llm_name: string;
  provider: string;
  api_key: string;
  base_url: string;
  config: AIReaderConfig;
}

export interface AIReaderSettingsResponse {
  items: AIReaderSettings[];
}

export interface AIReaderSettingsRequest {
  items: AIReaderSettings[];
}

export interface AgentSettings {
  embedding_provider: 'none' | 'local' | 'siliconflow' | 'openai';
  embedding_model: string;
  embedding_api_key: string;
  embedding_base_url: string;
  
  rag_provider: 'siliconflow' | 'openai' | 'ollama';
  rag_base_model: string;
  rag_api_key: string;
  rag_base_url: string;
  rag_temperature: number;
}

export interface SearchApiConfigInfo {
  api_name: string;
  api_key: string;
  weight: number;
  is_active: boolean;
}

export interface SearchApiConfigUpdate {
  api_name: string;
  api_key?: string;
  weight: number;
  is_active: boolean;
}

export interface SearchApiConfigListResponse {
  configs: SearchApiConfigInfo[];
}

export interface ServiceStatus {
  name: string;
  status: boolean;
  latency: number;
}

export interface SystemStats {
  user_count: number;
  paper_count: number;
  api_request_count: number;
  system_load: number;
  service_statuses: ServiceStatus[];
}

export interface SystemStatsResponse {
  stats: SystemStats;
}

export interface SystemModelConfig {
  id: string;
  type: string;
  provider: string;
  model_name: string;
  base_url: string;
  api_key: string;
  system_prompt: string;
  temperature: number;
  max_tokens: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SystemModelConfigUpdate {
  provider?: string;
  model_name?: string;
  base_url?: string;
  api_key?: string;
  system_prompt?: string;
  temperature?: number;
  max_tokens?: number;
  is_active?: boolean;
}
