import { useState, useCallback, useRef } from 'react';
import { createParser } from 'eventsource-parser';
import { useAuthStore } from '@/store/use-auth-store';
import { toast } from 'sonner';
import { logger } from '@/lib/logger';
import { chatService } from '@/services/chat.service';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system'; // Aligned with backend expected roles
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
  context?: { paper_id: string; [key: string]: any };
  onError?: (error: any) => void;
  onFinish?: () => void;
}

export const useUnifiedChat = ({ agentType, context, onError, onFinish }: UseUnifiedChatOptions) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const { token } = useAuthStore();
  const abortControllerRef = useRef<AbortController | null>(null);
  const [chatSessionId, setChatSessionId] = useState<string>("");

  // Initialize session ID if not present
  if (!chatSessionId) {
      // Simple UUID generation for frontend session
      const newSessionId = crypto.randomUUID();
      setChatSessionId(newSessionId);
  }

  // Clear messages function
  const clearMessages = useCallback(() => {
    setMessages([]);
    // Reset session ID when clearing messages to start fresh context
    setChatSessionId(crypto.randomUUID());
  }, []);
  
  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim()) return;

    // Add User Message
    const userMsgId = Date.now().toString();
    const userMsg: ChatMessage = {
      id: userMsgId,
      role: 'user',
      content,
      timestamp: Date.now(),
      status: 'completed'
    };

    // Optimistically add user message
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setIsLoading(true);

    // Add AI Placeholder
    const aiMsgId = (Date.now() + 1).toString();
    const aiMsg: ChatMessage = {
      id: aiMsgId,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      status: 'streaming'
    };
    setMessages(prev => [...prev, aiMsg]);

    try {
      abortControllerRef.current = new AbortController();
      
      let url = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/chat/message`; // Default/Fallback
      let body: any = { content };

      // Specialized logic for PaperChatAgent (Agentic RAG)
      if (agentType === 'paper_copilot' && context?.paper_id) {
        url = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/agent/paper_chat/stream`;
        
        // For persistent sessions (LangGraph + Checkpointer), we only send the NEW message.
        // The backend/graph will append it to the existing history.
        // Sending full history would cause duplication.
        const inputMessages = [{
            role: 'user',
            content: content
        }];

        body = {
          paper_id: context.paper_id,
          messages: inputMessages,
          chat_session_id: chatSessionId
        };
      }

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(body),
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
          try {
            if (event.data === '[DONE]') return;
            
            const eventType = event.event;
            const data = event.data ? JSON.parse(event.data) : {};

            setMessages(prev => prev.map(msg => {
              if (msg.id !== aiMsgId) return msg;

              const updatedMsg = { ...msg };

              switch (eventType) {
                case 'message':
                  // data: { content: "..." }
                  updatedMsg.content += (data.content || '');
                  break;
                
                case 'tool_start':
                  // data: { tool: "...", input: ... }
                  updatedMsg.toolCalls = [
                    ...(updatedMsg.toolCalls || []),
                    { 
                      tool_name: data.tool, 
                      args: data.input, 
                      status: 'start' 
                    }
                  ];
                  break;
                  
                case 'tool_end':
                  // data: { tool: "...", output: ... }
                  // Find the last matching tool call that is in 'start' status
                  if (updatedMsg.toolCalls) {
                    const toolIndex = updatedMsg.toolCalls.findLastIndex(
                      tc => tc.tool_name === data.tool && tc.status === 'start'
                    );
                    
                    if (toolIndex !== -1) {
                        const newToolCalls = [...updatedMsg.toolCalls];
                        newToolCalls[toolIndex] = {
                            ...newToolCalls[toolIndex],
                            status: 'success',
                            result: data.output
                        };
                        updatedMsg.toolCalls = newToolCalls;
                    }
                  }
                  break;

                case 'error':
                   updatedMsg.status = 'error';
                   // Backend sends { error: "..." } but we were looking for { message: "..." }
                   updatedMsg.content += `\n[Error: ${data.error || data.message || 'Unknown error'}]`;
                   break;
              }
              return updatedMsg;
            }));

          } catch (e) {
            console.error("Parse error", e);
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
      
      onFinish?.();

    } catch (error: any) {
      if (error.name === 'AbortError') {
        console.log('Request aborted');
      } else {
        logger.error('Chat error', error);
        setMessages(prev => prev.map(msg => 
            msg.id === aiMsgId ? { ...msg, status: 'error', content: msg.content + '\n[Request Failed]' } : msg
        ));
        onError?.(error);
        toast.error("消息发送失败");
      }
    } finally {
      setIsLoading(false);
    }
  }, [agentType, context, messages, token, onError, onFinish, chatSessionId]);

  return {
    messages,
    setMessages, // Export setter
    sendMessage,
    isLoading,
    clearMessages,
    chatSessionId,
    setChatSessionId
  };
};
