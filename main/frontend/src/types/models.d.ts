/**
 * Data models matching the backend API documentation v1.1
 * Ref: PROJECT/DOCUMENTS/项目统一技术架构文档(重要).md
 */

export interface User {
  user_id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  settings?: any; // Define Settings type if needed
}

export interface Paper {
  paper_id?: string; // Optional for external search results
  title: string;
  url?: string; // Web URL or Proxy URL
  file_url?: string; // PDF file URL
  authors: string[];
  summary?: string; // Abstract/Summary
  published_at?: string;
  source: string; // 'arXiv', 'PDF', etc.
  tags: string[];
  references_number?: number;
  // Extra fields that might come from status or other contexts
  status?: 'processing' | 'success' | 'failed'; // From upload response
  analysis_status?: 'unprocessed' | 'processing' | 'processed' | 'error'; // From PaperMetaDTO
  is_bookmarked?: boolean;
  job_id?: string; // Active job ID for processing papers
  latest_job_type?: string;
  source_id?: string;
  arxiv_id?: string;
}

export interface Collection {
  collection_id: string;
  name: string;
  total: number;
}

export interface TocItem {
  title: string;
  page: number;
}

export interface Toc {
  items: TocItem[];
}

export interface Rect {
  x: number;
  y: number;
  width: number;
  height: number;
  page_index?: number;
  pageIndex?: number;
}

export interface Annotation {
  annotation_id: string;
  type: 'highlight' | 'translation' | 'note' | 'translate';
  rects: Rect[];
  content?: string;
  color?: string;
  createdAt?: number;
}

export interface View {
  view_id: string;
  name: string;
  enable: boolean;
  annotations: Annotation[];
}

export interface NoteMeta {
  id: string;
  title: string;
  page?: number;
  created_at: string;
  content?: string;
}

export interface Note extends NoteMeta {
  content: string; // Markdown
}

export interface MindMapNode {
  id: string;
  text: string;
  label?: string;
  type?: string;
  data?: { type?: string; [key: string]: any };
  meta?: Record<string, string>;
}

export interface MindMapEdge {
  id?: string;
  from_id: string;
  to_id: string;
  source?: string;
  target?: string;
  label?: string;
}

export interface MindMap {
  nodes: MindMapNode[];
  edges: MindMapEdge[];
  system_notification?: string;
}

export interface AISummary {
  summary_config: Record<string, string>;
}

export interface Job {
  id: string;
  type: 'parsing' | 'embedding' | 'summarizing' | 'tracking';
  status: 'pending' | 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled';
  progress: number;
  created_at: string;
  end_at?: string;
  error?: string;
  result?: any;
}
