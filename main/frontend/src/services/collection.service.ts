import request from '@/lib/request';
import { Collection, Paper } from '@/types/models';

const mapPaper = (paper: Paper & Record<string, unknown>): Paper => {
  const mappedId = (paper as { paper_id?: string }).paper_id ?? paper.id;
  return {
    ...paper,
    id: mappedId,
  };
};

const mapCollection = (collection: Collection & Record<string, unknown>): Collection => {
  const mappedId = (collection as { collection_id?: string }).collection_id ?? collection.id;
  const mappedCount = (collection as { total?: number }).total ?? collection.count;
  return {
    ...collection,
    id: mappedId,
    count: mappedCount,
  };
};

export const collectionService = {
  getAll: async (): Promise<Collection[]> => {
    const data = await request.get('/collections');
    const list = (data as Collection[]) ?? [];
    return list.map((item) => mapCollection(item));
  },

  getById: async (id: string): Promise<Collection & { papers: Paper[] }> => {
    const data = await request.get(`/collections/${id}`);
    const mapped = mapCollection(data as Collection);
    const papers = ((data as { papers?: Paper[] }).papers ?? []).map((paper) => mapPaper(paper));
    return { ...mapped, papers };
  },

  create: async (name: string): Promise<Collection> => {
    const data = await request.post('/collections', { name });
    return mapCollection(data as Collection);
  },

  update: async (id: string, name: string): Promise<Collection> => {
    const data = await request.patch(`/collections/${id}`, { new_name: name });
    return mapCollection(data as Collection);
  },

  delete: async (id: string): Promise<{ success: boolean }> => {
    return request.delete(`/collections/${id}`);
  },

  addPaper: async (collectionId: string, paperId: string): Promise<void> => {
    return request.patch(`/papers/move/${paperId}`, { collection_id: collectionId });
  },

  removePaper: async (paperId: string): Promise<void> => {
    return request.delete(`/papers/${paperId}`);
  }
};
