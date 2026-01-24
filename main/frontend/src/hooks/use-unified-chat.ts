import { useState, useCallback, useRef } from 'react';
import { createParser } from 'eventsource-parser';
import { useAuthStore } from '@/store/use-auth-store';
import { toast } from 'sonner';
import { logger } from '@/lib/logger';
import { chatService } from '@/services/chat.service';

export interface ChatMessage {
  id: string;
  role: 'user' | 'ai' | 'system';
  content: string;
  timestamp: number;
  citations?: Citation[];
  toolCalls?: ToolCall[];
  status?: 'sending' | 'streaming' | 'completed' | 'error';
}

export interface Citation {
  source_id: string;
  chunk_id: string;
  text: string;
  score: number;
}

export interface ToolCall {
  tool_name: string;
  args: any;
  status: 'start' | 'success' | 'failed';
  result?: any;
}

interface UseUnifiedChatOptions {
  agentType: string;
  context?: any;
  onError?: (error: any) => void;
  onFinish?: () => void;
}

export const useUnifiedChat = ({ agentType, context, onError, onFinish }: UseUnifiedChatOptions) => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const { token } = useAuthStore();
  const abortControllerRef = useRef<AbortController | null>(null);

  const initSession = useCallback(async () => {
    try {
      const session = await chatService.createSession(agentType, context);
      setSessionId(session.session_id);
      return session.session_id;
    } catch (e) {
      logger.error('Failed to init chat session', e);
      onError?.(e);
      return null;
    }
  }, [agentType, context, onError]);

  const sendMessage = useCallback(async (content: string, files: any[] = []) => {
    if (!content.trim()) return;

    let currentSessionId = sessionId;
    if (!currentSessionId) {
      currentSessionId = await initSession();
      if (!currentSessionId) return;
    }

    // Add User Message
    const userMsgId = Date.now().toString();
    const userMsg: ChatMessage = {
      id: userMsgId,
      role: 'user',
      content,
      timestamp: Date.now(),
      status: 'completed'
    };

    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    // Add AI Placeholder
    const aiMsgId = (Date.now() + 1).toString();
    const aiMsg: ChatMessage = {
      id: aiMsgId,
      role: 'ai',
      content: '',
      timestamp: Date.now(),
      status: 'streaming'
    };
    setMessages(prev => [...prev, aiMsg]);

    try {
      abortControllerRef.current = new AbortController();
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/chat/sessions/${currentSessionId}/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ content, files }),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        throw new Error(`Request failed: ${response.statusText}`);
      }

      if (!response.body) return;

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      const parser = createParser({
        onEvent: (event) => {
          if (event.type === 'event') {
            try {
              if (event.data === '[DONE]') return;
              
              const data = JSON.parse(event.data);
              
              // Handle different event types from backend
              // Based on doc: metadata, token, tool_call, tool_result, citation, finish, error
              
              // 1. Token (Content Delta)
              // Note: Backend doc says data: "content" directly for token event sometimes? 
              // API_DOCUMENTATION_v1.md says: event: token -> data: {"content": "..."}
              // FRONTEND_TO_BACKEND_API_REQ.md says: data: "这是" (string)
              // We need to handle both cases or see actual implementation.
              // Assuming JSON structure based on recent trends.
              
              // Let's assume standard format: { type, ...payload } or just payload based on event name
              // Actually createParser gives us `event.event` as the event name if present.
              // If backend sends `event: token\ndata: ...`, event.event will be 'token'.
              
              const eventType = event.event || 'token'; // Default to token if not specified?

              setMessages(prev => prev.map(msg => {
                if (msg.id !== aiMsgId) return msg;

                const updatedMsg = { ...msg };

                switch (eventType) {
                  case 'token':
                    // Handle both raw string and JSON object
                    const text = typeof data === 'string' ? data : (data.content || data.token || '');
                    updatedMsg.content += text;
                    break;
                  
                  case 'citation':
                    updatedMsg.citations = [...(updatedMsg.citations || []), data];
                    break;
                    
                  case 'tool_call':
                    updatedMsg.toolCalls = [...(updatedMsg.toolCalls || []), { ...data, status: 'start' }];
                    break;
                    
                  case 'tool_result':
                    // Find matching tool call and update
                    if (updatedMsg.toolCalls) {
                      updatedMsg.toolCalls = updatedMsg.toolCalls.map(tc => 
                        tc.tool_name === data.tool_name ? { ...tc, status: 'success', result: data.result } : tc
                      );
                    }
                    break;
                    
                  case 'error':
                    updatedMsg.status = 'error';
                    updatedMsg.content += `\n[Error: ${data.message || 'Unknown error'}]`;
                    break;
                }
                return updatedMsg;
              }));

              if (eventType === 'finish') {
                onFinish?.();
              }

            } catch (e) {
              console.error("Parse error", e);
            }
          }
        }
      });

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        parser.feed(chunk);
      }

      // Mark as completed
      setMessages(prev => prev.map(msg => 
        msg.id === aiMsgId ? { ...msg, status: 'completed' } : msg
      ));

    } catch (error: any) {
      if (error.name === 'AbortError') {
        console.log('Request aborted');
      } else {
        logger.error("Send message failed", error);
        toast.error("发送消息失败");
        setMessages(prev => prev.map(msg => 
            msg.id === aiMsgId 
            ? { ...msg, status: 'error', content: msg.content + "\n[发送失败，请重试]" } 
            : msg
        ));
      }
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  }, [sessionId, initSession, token, onFinish]);

  const stop = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsLoading(false);
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    sessionId,
    messages,
    isLoading,
    sendMessage,
    stop,
    clearMessages,
    setMessages // Allow manual setting if needed (e.g. for history)
  };
};
