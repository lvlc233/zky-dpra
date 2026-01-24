import React, { useState, useRef, useEffect } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  BookOpen, 
  List, 
  Lightbulb, 
  ChevronDown, 
  ChevronUp, 
  Send,
  Sparkles,
  Bot,
  User,
  Loader2,
  FileText,
  RefreshCw,
  History,
  PlusCircle,
  MessageSquare,
  Trash2
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { readerService } from '@/services/reader.service';
import { agentService, AgentSession } from '@/services/agent.service';
import { toast } from 'sonner';
import { logger } from '@/lib/logger';
import { useUnifiedChat, ChatMessage } from '@/hooks/use-unified-chat';
import ReactMarkdown from 'react-markdown';
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { format } from "date-fns";

interface GuideTabProps {
  paperId: string;
  isProcessing?: boolean;
  loadingStage?: string;
  progress?: number;
}

export const GuideTab: React.FC<GuideTabProps> = ({ paperId, isProcessing, loadingStage, progress }) => {
  const [isSummaryOpen, setIsSummaryOpen] = useState(true);
  const [inputValue, setInputValue] = useState('');
  const [summaryData, setSummaryData] = useState<Record<string, string>>({});
  const [isGeneratingSummary, setIsGeneratingSummary] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // History State
  const [sessions, setSessions] = useState<AgentSession[]>([]);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);

  // Chat Hook
  const { messages, setMessages, sendMessage, isLoading: isSending, clearMessages, chatSessionId, setChatSessionId } = useUnifiedChat({
    agentType: 'paper_copilot',
    context: { paper_id: paperId },
    onError: (e) => toast.error("聊天服务连接失败"),
  });

  // History Functions
  const fetchSessions = async () => {
      if (!paperId) return;
      try {
          const list = await agentService.getSessions(paperId);
          setSessions(list);
      } catch (e) {
          logger.error("Failed to fetch sessions", e);
      }
  };

  const handleNewChat = () => {
      clearMessages(); // This generates new session ID
      setIsHistoryOpen(false);
      toast.success("已开启新对话");
  };

  const handleLoadSession = async (session: AgentSession) => {
      if (session.thread_id) {
           setChatSessionId(session.thread_id);
           setIsHistoryOpen(false);
           
           try {
               const history = await agentService.getHistory(session.thread_id);
               const loadedMessages: ChatMessage[] = history.map((m, idx) => ({
                   id: `hist-${idx}-${Date.now()}`,
                   role: m.role,
                   content: m.content,
                   timestamp: Date.now(),
                   status: 'completed'
               }));
               setMessages(loadedMessages);
               toast.success("已加载历史会话");
           } catch(e) {
               logger.error("Failed to load history", e);
               toast.error("加载历史失败");
           }
      }
  };

  const handleDeleteSession = async (e: React.MouseEvent, threadId: string) => {
      e.stopPropagation();
      if (!confirm("确定要删除这条对话记录吗？")) return;
      
      try {
          await agentService.deleteSession(threadId);
          toast.success("会话已删除");
          fetchSessions();
          if (chatSessionId === threadId) {
              handleNewChat();
          }
      } catch (e) {
          logger.error("Failed to delete session", e);
          toast.error("删除失败");
      }
  };

  // Scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Init Summary
  const fetchSummary = async (isManual = false) => {
      if (!paperId) return;

      // 1. Get Summary
      setIsGeneratingSummary(true);
      try {
          const res = await readerService.getSummary(paperId);
          if (res && res.summary_config && Object.keys(res.summary_config).length > 0) {
              setSummaryData(res.summary_config);
              if (isManual) toast.success("导读已更新");
          } else {
              if (isManual) toast.info("暂无最新导读内容");
          }
      } catch (e) {
          logger.error("Failed to get summary", e, 'GuideTab');
          if (isManual) toast.error("获取导读失败");
      } finally {
          setIsGeneratingSummary(false);
      }
  };

  useEffect(() => {
      fetchSummary();
  }, [paperId]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isSending) return;
    const content = inputValue.trim();
    setInputValue('');
    await sendMessage(content);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Helper to render summary sections
  const renderSummarySection = (title: string, content: string, icon: React.ReactNode) => (
    <div className="space-y-2" key={title}>
      <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400">
        {icon}
        <h4 className="text-sm font-medium">{title}</h4>
      </div>
      <div className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed bg-gray-50 dark:bg-slate-800 p-3 rounded-lg prose dark:prose-invert max-w-none">
        <ReactMarkdown>{content}</ReactMarkdown>
      </div>
    </div>
  );

  return (
    <div className="h-full flex flex-col bg-gray-50/30 dark:bg-slate-800/30">
      {/* 1. Collapsible Summary Section */}
      <div className="flex-shrink-0 bg-white dark:bg-slate-900 border-b border-gray-200 dark:border-slate-800 shadow-sm transition-all duration-300 ease-in-out">
        <button 
          onClick={() => setIsSummaryOpen(!isSummaryOpen)}
          className="w-full flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
        >
          <div className="flex flex-col items-start">
            <h3 className="font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-500 dark:text-indigo-400" />
              论文导读
              <div 
                role="button"
                onClick={(e) => {
                    e.stopPropagation();
                    fetchSummary(true);
                }}
                className="p-1 hover:bg-gray-200 dark:hover:bg-slate-700 rounded-full transition-colors ml-1 cursor-pointer"
                title="刷新导读"
              >
                 <RefreshCw className={cn("w-3.5 h-3.5 text-gray-400 hover:text-indigo-500", isGeneratingSummary && "animate-spin")} />
              </div>
            </h3>
            {isSummaryOpen && Object.keys(summaryData).length === 0 && !isGeneratingSummary && (
                <span className="text-xs text-gray-400 mt-1">暂无导读内容</span>
            )}
            {isSummaryOpen && isGeneratingSummary && (
                <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 mt-2 text-sm">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>正在生成导读...</span>
                </div>
            )}
          </div>
          {isSummaryOpen ? (
            <ChevronUp className="w-4 h-4 text-gray-400 dark:text-gray-500" />
          ) : (
            <div className="flex items-center gap-2 text-xs text-gray-400 dark:text-gray-500">
              <span>展开摘要</span>
              <ChevronDown className="w-4 h-4" />
            </div>
          )}
        </button>
        
        {isSummaryOpen && (
          <div className="p-4 space-y-4 max-h-[50vh] overflow-y-auto scrollbar-thin scrollbar-thumb-gray-200 dark:scrollbar-thumb-slate-700">
            {isGeneratingSummary || (isProcessing && Object.keys(summaryData).length === 0) ? (
              <div className="flex flex-col items-center justify-center py-8 text-center space-y-3">
                <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
                <div className="space-y-1">
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {loadingStage?.includes('summary') ? '正在生成导读...' : '正在解析论文...'}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {progress ? `当前进度: ${progress}%` : 'DeepPaper 正在深度阅读并总结全文'}
                  </p>
                </div>
              </div>
            ) : (
              <>
                {Object.keys(summaryData).length > 0 ? (
                  <div className="space-y-4">
                    {summaryData['系统通知'] && (
                         <div className="p-3 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 text-sm rounded-lg flex items-center gap-2">
                             <Loader2 className="w-4 h-4 animate-spin" />
                             {summaryData['系统通知']}
                         </div>
                    )}
                    {summaryData['summary'] && renderSummarySection('导读概览', summaryData['summary'], <Sparkles className="w-4 h-4" />)}
                    {summaryData['abstract'] && renderSummarySection('摘要', summaryData['abstract'], <BookOpen className="w-4 h-4" />)}
                    {summaryData['highlights'] && renderSummarySection('亮点', summaryData['highlights'], <Lightbulb className="w-4 h-4" />)}
                    {summaryData['conclusion'] && renderSummarySection('结论', summaryData['conclusion'], <List className="w-4 h-4" />)}
                  </div>
                ) : (
                  <div className="text-center py-4 text-gray-500 dark:text-gray-400 text-sm">
                    暂无导读内容
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
      
      {/* 2. Chat Section */}
      <div className="flex-1 flex flex-col overflow-hidden min-h-0">
        <div className="p-2 border-b border-gray-100 dark:border-slate-800 bg-gray-50/50 dark:bg-slate-800/50 flex justify-between items-center">
           <div className="flex items-center gap-2">
               <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider pl-2">对话助手</span>
               <Popover open={isHistoryOpen} onOpenChange={setIsHistoryOpen}>
                   <PopoverTrigger asChild>
                       <button 
                           onClick={() => {
                               setIsHistoryOpen(true);
                               fetchSessions();
                           }}
                           className="p-1 hover:bg-gray-200 dark:hover:bg-slate-700 rounded transition-colors text-gray-400"
                           title="历史记录"
                       >
                           <History className="w-3.5 h-3.5" />
                       </button>
                   </PopoverTrigger>
                   <PopoverContent className="w-64 p-0" align="start">
                       <div className="flex flex-col">
                           <div className="flex items-center justify-between p-3 border-b bg-gray-50/50">
                               <span className="text-sm font-medium">历史会话</span>
                               <Button variant="ghost" size="sm" className="h-6 px-2 text-xs" onClick={handleNewChat}>
                                   <PlusCircle className="w-3 h-3 mr-1" />
                                   新对话
                               </Button>
                           </div>
                           <div className="max-h-60 overflow-y-auto p-1 space-y-0.5">
                               {sessions.map(s => (
                                   <div key={s.record_id} className="group flex items-center gap-1 w-full hover:bg-gray-100 dark:hover:bg-slate-800 rounded-md pr-1 transition-colors">
                                       <button
                                           onClick={() => handleLoadSession(s)}
                                           className={cn(
                                               "flex-1 text-left px-3 py-2 text-sm truncate flex items-center gap-3",
                                               chatSessionId === s.thread_id && "text-indigo-600 dark:text-indigo-400"
                                           )}
                                       >
                                           <MessageSquare className="w-3.5 h-3.5 flex-shrink-0 text-gray-400" />
                                           <div className="flex flex-col flex-1 min-w-0">
                                                <span className="truncate font-medium">{s.title || "未命名会话"}</span>
                                                <span className="text-[10px] text-gray-400">{format(new Date(s.created_at), "MM-dd HH:mm")}</span>
                                           </div>
                                       </button>
                                       <button
                                           onClick={(e) => handleDeleteSession(e, s.thread_id)}
                                           className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-100 dark:hover:bg-red-900/30 text-gray-400 hover:text-red-500 rounded transition-all"
                                           title="删除会话"
                                       >
                                           <Trash2 className="w-3.5 h-3.5" />
                                       </button>
                                   </div>
                               ))}
                               {sessions.length === 0 && (
                                   <div className="text-center py-8 text-xs text-gray-400">暂无历史记录</div>
                               )}
                           </div>
                       </div>
                   </PopoverContent>
               </Popover>
           </div>
           <button 
             onClick={clearMessages} 
             className="text-xs text-gray-400 dark:text-gray-500 hover:text-red-500 dark:hover:text-red-400 px-2 py-1 rounded hover:bg-red-50 dark:hover:bg-red-900/50 transition-colors"
           >
             清空当前
           </button>
        </div>

        <ScrollArea className="flex-1 p-4">
          <div className="space-y-6 pb-4">
            {messages.length === 0 && (
                <div className="text-center text-gray-400 text-sm mt-10">
                    <Bot className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p>你好！我是你的 AI 阅读助手。</p>
                    <p>关于这篇论文，你想了解什么？</p>
                </div>
            )}
            {messages.map((msg) => (
              <div key={msg.id} className={cn(
                "flex gap-3",
                msg.role === 'user' ? "flex-row-reverse" : "flex-row"
              )}>
                <div className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
                  msg.role === 'user' ? "bg-indigo-100 text-indigo-600 dark:bg-indigo-900 dark:text-indigo-300" : "bg-emerald-100 text-emerald-600 dark:bg-emerald-900 dark:text-emerald-300"
                )}>
                  {msg.role === 'user' ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
                </div>
                
                <div className={cn(
                  "flex flex-col max-w-[85%]",
                  msg.role === 'user' ? "items-end" : "items-start"
                )}>
                  <div className={cn(
                    "rounded-2xl px-4 py-2 text-sm shadow-sm",
                    msg.role === 'user' 
                      ? "bg-indigo-600 text-white rounded-tr-sm" 
                      : "bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 text-gray-800 dark:text-gray-200 rounded-tl-sm"
                  )}>
                    {/* Tool Calls Status */}
                    {msg.toolCalls && msg.toolCalls.length > 0 && (
                      <div className="mb-2 flex flex-col gap-1 border-b border-gray-100 dark:border-slate-800 pb-2">
                        {msg.toolCalls.map((tool, idx) => (
                          <div key={idx} className="text-xs flex items-center gap-2 text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-slate-800/50 px-2 py-1 rounded">
                            {tool.status === 'start' ? (
                              <Loader2 className="w-3 h-3 animate-spin text-indigo-500" />
                            ) : (
                              <FileText className="w-3 h-3 text-emerald-500" />
                            )}
                            <span>
                              {tool.tool_name === 'retrieve_paper_tool' ? '正在阅读论文...' : `调用工具: ${tool.tool_name}`}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}

                    {msg.role === 'assistant' ? (
                        <div className="prose prose-sm dark:prose-invert max-w-none">
                            <ReactMarkdown>{msg.content || (msg.status === 'streaming' ? '...' : '')}</ReactMarkdown>
                        </div>
                    ) : (
                        msg.content
                    )}
                  </div>
                  
                  {/* Citations */}
                  {msg.citations && msg.citations.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-2">
                          {msg.citations.map((citation, idx) => (
                              <div key={idx} className="text-xs bg-gray-100 dark:bg-slate-800 text-gray-600 dark:text-gray-400 px-2 py-1 rounded border border-gray-200 dark:border-slate-700 max-w-full truncate">
                                  Reference: {citation.text.substring(0, 30)}...
                              </div>
                          ))}
                      </div>
                  )}

                  <span className="text-[10px] text-gray-400 mt-1 px-1">
                    {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    {msg.status === 'error' && <span className="text-red-500 ml-2">发送失败</span>}
                  </span>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {/* Input Area */}
        <div className="p-4 bg-white dark:bg-slate-900 border-t border-gray-200 dark:border-slate-800">
          <div className="relative flex items-end gap-2 bg-gray-50 dark:bg-slate-800 rounded-xl border border-gray-200 dark:border-slate-700 p-2 focus-within:ring-2 focus-within:ring-indigo-500/20 focus-within:border-indigo-500 transition-all">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="问点什么..."
              className="flex-1 bg-transparent border-none focus:ring-0 text-sm max-h-32 min-h-[40px] resize-none py-2 px-1 text-gray-900 dark:text-gray-100 placeholder:text-gray-400"
              rows={1}
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isSending}
              className={cn(
                "p-2 rounded-lg transition-all flex-shrink-0",
                inputValue.trim() && !isSending
                  ? "bg-indigo-600 text-white shadow-md hover:bg-indigo-700 active:scale-95"
                  : "bg-gray-200 dark:bg-slate-700 text-gray-400 cursor-not-allowed"
              )}
            >
              {isSending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </button>
          </div>
          <div className="text-center mt-2">
             <p className="text-[10px] text-gray-400">AI 可能会产生错误，请仔细甄别。</p>
          </div>
        </div>
      </div>
    </div>
  );
};
