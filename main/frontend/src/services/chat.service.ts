import request from '@/lib/request';

export interface ChatSession {
  id: string;
  title?: string; // Doc doesn't explicitly say title, but usually sessions have titles.
  agent_type: string;
  created_at?: string;
}

export interface ChatMessage {
  role: string;
  content: string;
}

export const chatService = {
  createSession: async (agentType: string, context?: any): Promise<ChatSession> => {
    const data = await request.post('/chat/sessions', { agent_type: agentType, context });
    const response = data as ChatSession & Record<string, unknown>;
    return {
      ...response,
      id: (response as { sessionId?: string; session_id?: string }).sessionId ?? (response as { session_id?: string }).session_id ?? response.id,
    };
  },

  getSessions: async (): Promise<ChatSession[]> => {
    const data = await request.get('/chat/sessions');
    const list = (data as ChatSession[]) ?? [];
    return list.map((session) => ({
      ...session,
      id: (session as { sessionId?: string; session_id?: string }).sessionId ?? (session as { session_id?: string }).session_id ?? session.id,
    }));
  },

  getSession: async (id: string): Promise<ChatSession> => {
    const data = await request.get(`/chat/sessions/${id}`);
    const session = data as ChatSession & Record<string, unknown>;
    return {
      ...session,
      id: (session as { sessionId?: string; session_id?: string }).sessionId ?? (session as { session_id?: string }).session_id ?? session.id,
    };
  },

  getMessages: async (sessionId: string): Promise<ChatMessage[]> => {
    return request.get(`/chat/sessions/${sessionId}/messages`);
  },

  // Note: Send Message is via SSE (POST /chat/sessions/{id}/message)
  // This service function might not be used if we use `fetch` or `EventSource` directly for SSE.
  // But if we need a standard POST:
  sendMessage: async (sessionId: string, content: string): Promise<void> => {
    // This endpoint returns text/event-stream, so axios might not be the best way to consume it
    // if we want to stream. But for sending, it's a POST.
    return request.post(`/chat/sessions/${sessionId}/message`, { content });
  }
};
