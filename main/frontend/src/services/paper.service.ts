import request from '@/lib/request';
import { PapersUploadResponse, PaperReaderMetaResponse, JobListResponse, JobResponse, SearchedPaperMetaResponse, PaperJobStatusResponse, PaperStatusResponse } from '@/types/api';
import { Paper, Job } from '@/types/models';

export const paperService = {
  uploadLocal: async (files: File[], collectionId?: string): Promise<PapersUploadResponse[]> => {
    const promises = files.map(file => {
      const formData = new FormData();
      formData.append('file', file);
      if (collectionId) {
        formData.append('collection_id', collectionId);
      }
      return request.post('/papers/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    });
    return Promise.all(promises);
  },

  uploadWeb: async (urls: string[], collectionId?: string, metadata?: { title?: string, authors?: string[], summary?: string, source?: string, published_at?: string, source_id?: string, arxiv_id?: string }): Promise<PapersUploadResponse[]> => {
    return request.post('/papers/upload/web', { 
      urls, 
      collection_id: collectionId,
      ...metadata
    });
  },

  // Get list of papers from backend
  getList: async (page = 1, limit = 10): Promise<Paper[]> => {
     const offset = (page - 1) * limit;
     const items: any[] = await request.get('/papers/list', { 
        params: { limit, offset } 
    });

    return items.map(item => ({
         paper_id: item.paper_id,
          title: item.title,
          url: item.file_url,
          authors: item.authors || [],
          summary: item.abstract,
          published_at: item.published_at || item.created_at,
          source: item.source || 'Upload',
          tags: [],
          status: item.status,
          job_id: item.job_id,
          latest_job_type: item.latest_job_type
      }));
  },

  getMeta: async (paperId: string): Promise<PaperReaderMetaResponse> => {
    return request.get(`/papers/${paperId}/meta`);
  },

  getJobs: async (paperId: string): Promise<JobListResponse> => {
    return request.get(`/papers/${paperId}/jobs`);
  },

  createJob: async (paperId: string, type: Job['type'], options?: any): Promise<JobResponse> => {
    return request.post(`/papers/${paperId}/jobs`, { type, options });
  },

  getJob: async (jobId: string): Promise<JobResponse> => {
    return request.get(`/jobs/${jobId}`);
  },

  retryJob: async (jobId: string): Promise<void> => {
    return request.post(`/jobs/${jobId}/retry`);
  },

  delete: async (id: string): Promise<void> => {
    return request.delete(`/papers/${id}`);
  },

  getById: async (id: string): Promise<Paper> => {
    if (id === 'mock-id-001') {
        return {
          paper_id: 'mock-id-001',
          title: 'DeepPaper: A Deep Learning Approach for Academic Paper Research',
          url: 'https://arxiv.org/pdf/2601.14047',
          file_url: 'https://arxiv.org/pdf/2601.14047',
          authors: ['Frontend Agent', 'User'],
          summary: '这是一个用于测试详情页面的模拟数据。它展示了 Agent 如何通过 Mock 数据来驱动前端开发。',
          published_at: '2026-01-21',
          source: 'Mock System',
          tags: ['Mock', 'Test', 'Agent'],
          status: 'success'
        } as unknown as Paper;
      }
      return request.get(`/papers/${id}`);
    },

    getStatus: async (id: string): Promise<PaperStatusResponse> => {
      if (id === 'mock-id-001') {
        return {
          paper_id: 'mock-id-001',
          status: 'completed',
          file_url: 'https://arxiv.org/pdf/2601.14047',
          progress: 100,
          step: 'done',
          toc: [
            { title: 'Abstract', page: 1 },
            { title: '1. Introduction', page: 1 },
            { title: '2. Methodology', page: 2 },
            { title: '3. Experiments', page: 3 },
            { title: '4. Conclusion', page: 4 }
          ],
          message: 'Mock processing complete'
        };
      }
    return request.get(`/papers/${id}/status`);
  },

  getJobStatus: async (paperId: string): Promise<PaperJobStatusResponse | null> => {
    return request.get(`/papers/${paperId}/job-status`);
  },

  getSSEUrl: (jobId: string, token: string) => {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    return `${baseUrl}/jobs/${jobId}/events?token=${token}`;
  },
};
