import { User, Paper, Collection, View, Annotation, NoteMeta, Note, MindMap, AISummary, RecordItem, Message, Job, TocItem } from './models';

export type { User, Paper, Collection, View, Annotation, NoteMeta, Note, MindMap, AISummary, RecordItem, Message, Job, TocItem };

export interface ApiResponse<T = any> {
  code: number;
  message: string;
  data: T;
}

// Auth
export interface LoginResponse extends User {
  access_token: string;
  refresh_token?: string;
  settings?: any;
}

export interface TokenPairResponse {
  access_token: string;
  refresh_token?: string;
}

// Papers
export interface PapersUploadResponse {
  paper_id: string;
  job_id?: string;
  title: string;
  status: 'processing' | 'success' | 'failed';
  message?: string;
}

export interface SearchedPaperMetaResponse {
  items: Paper[];
  total: number;
  message?: string;
}

export interface PaperReaderMetaResponse {
  paper_id: string;
  url: string;
  summary?: AISummary;
  toc?: { items: TocItem[] };
  views: View[];
  notes: NoteMeta[];
  mind_map?: MindMap;
  history: RecordItem[];
  jobs: Job[];
}

// Collections
export interface CollectionResponse extends Collection {}

export interface CollectionDetailResponse {
  items: Paper[];
}

// Views
export interface ViewResponse {
  view_id: string;
  name: string;
  enable: boolean;
}

export interface AnnotationResponse {
  items: Annotation[];
}

// Notes
export interface NoteMetaResponse {
  items: NoteMeta[];
}

export interface NoteResponse extends Note {}

// AI
export interface AISummaryResponse extends AISummary {}
export interface MindMapResponse extends MindMap {}
export interface RecordResponse extends RecordItem {}
export interface MessageResponse {
  items: Message[];
}
export interface JobListResponse {
  items: Job[];
}
export interface JobResponse {
  job: Job;
}

export interface PaperJobStatusResponse {
  job_id: string;
  status: 'pending' | 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled';
  stage: string;
  progress: number;
  error?: string;
  created_at: string;
  end_at?: string;
  result?: any;
  type?: string;
}

export interface PaperStatusResponse {
  paper_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  title: string;
  authors: string[];
  abstract: string;
  progress: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
  toc?: any[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
  file_url?: string;
  published_at?: string;
  source?: string;
}

// Admin User Management
export interface UserAdminResponse {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserAdminListResponse {
  users: UserAdminResponse[];
  total: number;
}
