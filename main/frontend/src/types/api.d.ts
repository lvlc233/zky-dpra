import { User, Paper } from './models';
export type { User, Paper };

// Generic API Response wrapper
export interface ApiResponse<T = any> {
  code: number;
  message: string;
  data: T;
}

// Auth
export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Papers
export interface PaperListResponse {
  items: Paper[];
  total: number;
  page: number;
  limit: number;
}

export interface UploadResponse {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
}

export interface PaperStatusResponse {
  paper_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  toc?: any[];
  file_url?: string;
}

// Search
export interface SearchConfig {
  engines: string[];
  max_results: number;
  // ... other config fields
}

// Reader
export interface SummaryResponse {
  content: string;
  summary_type: string;
}

export interface GraphResponse {
  nodes: any[];
  edges: any[];
}