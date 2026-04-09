import request from '@/lib/request';
import { 
  PaperReaderMetaResponse, TocResponse, ViewResponse, AnnotationResponse, 
  NoteMetaResponse, NoteResponse, AISummaryResponse, MindMapResponse, 
  RecordResponse, MessageResponse, Annotation
} from '@/types/api';
import { View } from '@/types/models';

export const readerService = {
  getMeta: async (paperId: string): Promise<PaperReaderMetaResponse> => {
    return request.get(`/papers/${paperId}/meta`);
  },

  getToc: async (paperId: string): Promise<TocResponse> => {
    return request.get(`/papers/${paperId}/toc`);
  },

  // Views (Mocked for now as backend doesn't support multi-views yet)
  getViews: async (paperId: string): Promise<ViewResponse[]> => {
    // Mock response
    return Promise.resolve([
      { view_id: 'default-view', name: '默认图层', enable: true, created_at: new Date().toISOString() }
    ]);
    // return request.get(`/papers/${paperId}/views`);
  },

  createView: async (paperId: string, name: string): Promise<ViewResponse> => {
    // Mock response
    return Promise.resolve({ 
      view_id: 'new-view-' + Date.now(), 
      name, 
      enable: true, 
      created_at: new Date().toISOString() 
    });
    // return request.post(`/papers/${paperId}/views`, { name });
  },

  updateView: async (paperId: string, viewId: string, enable: boolean): Promise<void> => {
    return Promise.resolve();
    // return request.patch(`/papers/${paperId}/views/${viewId}/enable`, { enable });
  },

  renameView: async (paperId: string, viewId: string, name: string): Promise<void> => {
    return Promise.resolve();
    // return request.patch(`/papers/${paperId}/views/${viewId}/rename`, { name });
  },

  deleteView: async (paperId: string, viewId: string): Promise<void> => {
    return Promise.resolve();
    // return request.delete(`/papers/${paperId}/views/${viewId}`);
  },

  // Annotations
  getAnnotations: async (paperId: string, viewId: string): Promise<AnnotationResponse> => {
    // Ignore viewId for now
    return request.get(`/papers/${paperId}/annotations`);
  },

  addAnnotation: async (paperId: string, viewId: string, data: Annotation): Promise<void> => {
     // Ignore viewId for now
     // Map annotation_id to id for backend
     const payload = {
         ...data,
         id: data.annotation_id
     };
    return request.post(`/papers/${paperId}/annotations`, payload);
  },

  updateAnnotation: async (paperId: string, viewId: string, annotationId: string, data: Omit<Annotation, 'annotation_id'>): Promise<void> => {
    return request.put(`/papers/${paperId}/annotations/${annotationId}`, data);
  },

  deleteAnnotation: async (paperId: string, viewId: string, annotationId: string): Promise<void> => {
    return request.delete(`/papers/${paperId}/annotations/${annotationId}`);
  },

  // Notes
  getNotes: async (paperId: string): Promise<NoteMetaResponse> => {
    return request.get(`/papers/${paperId}/notes`);
  },

  getNote: async (paperId: string, noteId: string): Promise<NoteResponse> => {
    return request.get(`/papers/${paperId}/notes/${noteId}`);
  },

  createNote: async (paperId: string, data: { title: string; content: string; page?: number }): Promise<NoteResponse> => {
    return request.post(`/papers/${paperId}/notes`, data);
  },

  updateNote: async (paperId: string, noteId: string, data: { title?: string; content?: string }): Promise<NoteResponse> => {
    return request.put(`/papers/${paperId}/notes/${noteId}`, data);
  },

  deleteNote: async (paperId: string, noteId: string): Promise<void> => {
    return request.delete(`/papers/${paperId}/notes/${noteId}`);
  },

  // AI
  getSummary: async (paperId: string): Promise<AISummaryResponse> => {
    return request.get(`/papers/${paperId}/ai/summary`);
  },

  getMindMap: async (paperId: string): Promise<MindMapResponse> => {
    return request.get(`/papers/${paperId}/ai/mind_map`);
  },

  getHistory: async (paperId: string): Promise<RecordResponse[]> => {
    return request.get(`/papers/${paperId}/ai/history`);
  },

  getRecord: async (paperId: string, recordId: string): Promise<MessageResponse> => {
    return request.get(`/papers/${paperId}/ai/record/${recordId}`);
  },

  translateText: async (paperId: string, text: string): Promise<{ translated_text: string }> => {
    return request.post(`/papers/${paperId}/ai/translate`, { text });
  },

  // Helper to get full layers (views + annotations)
  getLayers: async (paperId: string): Promise<{ layers: any[] }> => {
    // This aggregates views and their annotations
    const views = await readerService.getViews(paperId);
    if (!views || views.length === 0) return { layers: [] };

    const layers = await Promise.all(views.map(async (view) => {
        try {
            const annos = await readerService.getAnnotations(paperId, view.view_id);
            return {
                view_id: view.view_id,
                name: view.name,
                type: (view.name.includes('Base') || view.name.includes('原文')) ? 'system' : 'user',
                visible: view.enable,
                annotations: (annos.items || []).map((a: any) => ({
                    ...a,
                    annotation_id: a.annotation_id || a.id,
                    rects: a.rects || (a.rect ? [a.rect] : [])
                })),
                color: undefined
            };
        } catch (e) {
            return {
                view_id: view.view_id,
                name: view.name,
                type: 'user',
                visible: view.enable,
                annotations: [],
            };
        }
    }));
    return { layers };
  }
};
