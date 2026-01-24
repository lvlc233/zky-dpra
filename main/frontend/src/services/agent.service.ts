import request from '@/lib/request';

export interface AgentSession {
  record_id: string;
  user_id: string;
  paper_id?: string;
  title: string;
  thread_id: string;
  created_at: string;
  updated_at: string;
  agent_type: string;
}

export const agentService = {
  getSessions: async (paperId: string): Promise<AgentSession[]> => {
    return request.get('/agent/paper_chat/sessions', { params: { paper_id: paperId } });
  },
  
  getHistory: async (threadId: string): Promise<any[]> => {
    return request.get('/agent/paper_chat/history', { params: { thread_id: threadId } });
  },
  
  deleteSession: async (threadId: string) => {
    return request.delete(`/agent/paper_chat/sessions/${threadId}`);
  }
};
