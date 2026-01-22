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
