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
  User
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface Message {
  id: string;
  role: 'ai' | 'user';
  content: string;
  timestamp: number;
}

export const GuideTab = () => {
  const [isSummaryOpen, setIsSummaryOpen] = useState(true);
  const [inputValue, setInputValue] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'ai',
      content: '你好！我是你的 AI 阅读助手。关于这篇论文，你想了解什么？你可以试着问我：\n1. 这篇论文的核心创新点是什么？\n2. 实验数据表现如何？',
      timestamp: Date.now()
    }
  ]);
  const scrollViewportRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    // Access the viewport element of Radix UI ScrollArea if possible, 
    // or just use a dummy div at bottom. 
    // For simplicity with standard ScrollArea, we might need a ref to the end.
    const viewport = document.querySelector('[data-radix-scroll-area-viewport]');
    if (viewport) {
      viewport.scrollTop = viewport.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = () => {
    if (!inputValue.trim()) return;

    const newUserMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue.trim(),
      timestamp: Date.now()
    };

    setMessages(prev => [...prev, newUserMsg]);
    setInputValue('');

    // Simulate AI response
    setTimeout(() => {
      const newAiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'ai',
        content: '这是一个模拟的 AI 回复。在实际应用中，这里会调用后端 API 基于 RAG 回答您的问题。',
        timestamp: Date.now()
      };
      setMessages(prev => [...prev, newAiMsg]);
    }, 1000);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="h-full flex flex-col bg-gray-50/30">
      {/* 1. Collapsible Summary Section */}
      <div className="flex-shrink-0 bg-white border-b border-gray-200 shadow-sm transition-all duration-300 ease-in-out">
        <button 
          onClick={() => setIsSummaryOpen(!isSummaryOpen)}
          className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
        >
          <div className="flex flex-col items-start">
            <h3 className="font-semibold text-gray-900 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-500" />
              论文导读
            </h3>
            {isSummaryOpen && (
               <p className="text-xs text-gray-500 mt-1">AI 自动生成的论文核心内容摘要</p>
            )}
          </div>
          {isSummaryOpen ? (
            <ChevronUp className="w-4 h-4 text-gray-400" />
          ) : (
            <div className="flex items-center gap-2 text-xs text-gray-400">
              <span>展开摘要</span>
              <ChevronDown className="w-4 h-4" />
            </div>
          )}
        </button>
        
        <div className={cn(
           "grid transition-all duration-500 ease-in-out bg-white",
           isSummaryOpen ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
         )}>
          <div className="overflow-hidden">
            <div className="px-4 pb-4">
             <ScrollArea className="h-[40vh] pr-4">
                <div className="space-y-6">
                  {/* Abstract Section */}
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-indigo-600">
                      <BookOpen className="w-4 h-4" />
                      <h4 className="text-sm font-medium">核心摘要</h4>
                    </div>
                    <p className="text-sm text-gray-600 leading-relaxed bg-gray-50 p-3 rounded-lg">
                      本文提出了一种基于 Agent 的深度论文研究系统 (DeepPaperResearcher)。
                      该系统利用大语言模型 (LLM) 和图数据库，实现了对海量学术论文的自动化检索、
                      阅读、分析和总结。实验结果表明，该系统在处理复杂科研任务时，效率比传统方法提升了 10 倍。
                    </p>
                  </div>

                  {/* Key Points Section */}
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-indigo-600">
                      <List className="w-4 h-4" />
                      <h4 className="text-sm font-medium">主要贡献</h4>
                    </div>
                    <ul className="space-y-2">
                      {[
                        "提出了基于图结构的论文知识表示方法",
                        "设计了多 Agent 协作的论文阅读与评分机制",
                        "实现了端到端的自动化科研报告生成流程"
                      ].map((point, index) => (
                        <li key={index} className="flex gap-2 text-sm text-gray-600">
                          <span className="text-indigo-400 font-bold">•</span>
                          <span>{point}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Insights Section */}
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-indigo-600">
                      <Lightbulb className="w-4 h-4" />
                      <h4 className="text-sm font-medium">创新点分析</h4>
                    </div>
                    <div className="bg-indigo-50 p-3 rounded-lg text-sm text-indigo-900 border border-indigo-100">
                      不同于传统的 RAG 方法，本文采用了动态知识图谱来增强上下文理解能力，
                      有效解决了跨文档推理的难题。
                    </div>
                  </div>
                </div>
             </ScrollArea>
             
             {/* Divider Gradient */}
             <div className="h-4 bg-gradient-to-t from-white to-transparent -mt-4 relative z-10 pointer-events-none" />
            </div>
           </div>
        </div>
      </div>
      
      {/* 2. Chat Section */}
      <div className="flex-1 flex flex-col overflow-hidden min-h-0">
        <div className="p-2 border-b border-gray-100 bg-gray-50/50 flex justify-between items-center">
           <span className="text-xs font-medium text-gray-500 uppercase tracking-wider pl-2">对话助手</span>
           <button 
             onClick={() => setMessages([])} 
             className="text-xs text-gray-400 hover:text-red-500 px-2 py-1 rounded hover:bg-red-50 transition-colors"
           >
             清空记录
           </button>
        </div>

        <ScrollArea className="flex-1 p-4">
          <div className="space-y-6 pb-4">
            {messages.map((msg) => (
              <div key={msg.id} className={cn(
                "flex gap-3",
                msg.role === 'user' ? "flex-row-reverse" : ""
              )}>
                {/* Avatar */}
                <div className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 shadow-sm",
                  msg.role === 'ai' 
                    ? "bg-indigo-100 text-indigo-600" 
                    : "bg-gray-200 text-gray-600"
                )}>
                  {msg.role === 'ai' ? <Bot className="w-4 h-4" /> : <User className="w-4 h-4" />}
                </div>

                {/* Bubble */}
                <div className={cn(
                  "p-3 rounded-2xl text-sm shadow-sm max-w-[85%] leading-relaxed whitespace-pre-wrap",
                  msg.role === 'ai' 
                    ? "bg-white border border-gray-100 text-gray-800 rounded-tl-none" 
                    : "bg-indigo-600 text-white rounded-tr-none"
                )}>
                  {msg.content}
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>

        {/* Input Area */}
        <div className="p-4 bg-white border-t border-gray-200">
           {/* Quick Actions (Optional placeholder) */}
           {messages.length < 2 && (
             <div className="flex gap-2 mb-3 overflow-x-auto pb-1 scrollbar-hide">
                {['深度思考', '解释方法', '总结结论'].map(tag => (
                  <button 
                    key={tag}
                    onClick={() => setInputValue(`请${tag}：`)}
                    className="flex-shrink-0 px-3 py-1 bg-gray-100 hover:bg-gray-200 text-gray-600 text-xs rounded-full transition-colors whitespace-nowrap"
                  >
                    {tag}
                  </button>
                ))}
             </div>
           )}

           <div className="relative">
             <textarea
               value={inputValue}
               onChange={(e) => setInputValue(e.target.value)}
               onKeyDown={handleKeyDown}
               placeholder="输入问题，Enter 发送..."
               className="w-full h-24 p-3 pr-10 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 resize-none bg-gray-50 focus:bg-white transition-all"
             />
             <button
               onClick={handleSendMessage}
               disabled={!inputValue.trim()}
               className="absolute bottom-3 right-3 p-1.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm"
             >
               <Send className="w-4 h-4" />
             </button>
           </div>
           <div className="text-[10px] text-gray-400 mt-2 text-center">
              AI 内容仅供参考，请核对原文
           </div>
        </div>
      </div>
    </div>
  );
};
