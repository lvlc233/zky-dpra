export interface User {
  id: string;
  email: string;
  full_name?: string;
  avatar_url?: string;
  created_at: string;
  is_active: boolean;
}

export interface Paper {
  id: string;
  title: string;
  authors: string[];
  abstract?: string;
  file_url?: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  is_bookmarked?: boolean;
  // Extended properties for search/dashboard
  year?: number;
  source?: string;
  citations?: number;
  aiScore?: number;
  aiReason?: string;
}

export interface Collection {
  id: string;
  name: string;
  description?: string;
  count?: number;
  created_at: string;
}

export interface Annotation {
  id: string;
  type: 'highlight' | 'note' | 'translate';
  rects: {
    x: number;
    y: number;
    width: number;
    height: number;
    pageIndex: number;
  }[];
  content?: string;
  color?: string;
  createdAt: number;
}

export interface Layer {
  id: string;
  name: string;
  type: 'system' | 'user';
  visible: boolean;
  annotations: Annotation[];
}
