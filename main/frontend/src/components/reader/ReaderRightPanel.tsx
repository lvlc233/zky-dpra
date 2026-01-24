'use client';

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { 
  MessageSquare, 
  PenTool, 
  Network, 
  Settings, 
  Send
} from 'lucide-react';
import { GuideTab } from './tabs/GuideTab';
import { NotesTab } from './tabs/NotesTab';
import { GraphTab } from './tabs/GraphTab';
import { SettingsTab } from './tabs/SettingsTab';

import { PaperJobStatusResponse } from '@/types/api';
import { Loader2 } from 'lucide-react';

interface ReaderRightPanelProps {
  className?: string;
  paperId: string;
  isProcessing?: boolean;
  loadingStage?: string;
  progress?: number;
  jobStatus?: PaperJobStatusResponse | null;
}

type Tab = 'guide' | 'notes' | 'graph' | 'settings';

export const ReaderRightPanel: React.FC<ReaderRightPanelProps> = ({ className, paperId, isProcessing, loadingStage, progress, jobStatus }) => {
  const [activeTab, setActiveTab] = useState<Tab>('guide');
  const [input, setInput] = useState('');

  const TABS = [
    { id: 'guide', label: '导读', icon: MessageSquare },
    { id: 'notes', label: '笔记', icon: PenTool },
    { id: 'graph', label: '脑图', icon: Network },
    { id: 'settings', label: '设置', icon: Settings },
  ];
  
  // Determine if we should show a background job indicator
  const showJobIndicator = jobStatus && 
    (jobStatus.status === 'running' || jobStatus.status === 'queued') && 
    jobStatus.type !== 'parse_text';

  const getJobLabel = (type?: string) => {
    switch(type) {
      case 'vectorize': return '构建知识库索引';
      case 'summary': return '生成智能总结';
      case 'mind_map': return '生成思维导图';
      default: return '后台处理中';
    }
  };

  return (
    <aside className={cn(
      "w-[400px] bg-white dark:bg-slate-900 border-l border-gray-200 dark:border-slate-800 flex flex-col h-full",
      className
    )}>
      {/* Top Tabs */}
      <div className="flex items-center justify-between p-2 border-b border-gray-100 dark:border-slate-800 overflow-x-auto no-scrollbar">
        {TABS.map((tab) => {
           const Icon = tab.icon;
           return (
             <button
               key={tab.id}
               onClick={() => setActiveTab(tab.id as Tab)}
               className={cn(
                 "flex flex-col items-center gap-1 px-3 py-2 rounded-lg text-[10px] font-medium transition-all min-w-[60px]",
                 activeTab === tab.id 
                   ? "bg-indigo-50 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400" 
                   : "text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-slate-800 hover:text-gray-900 dark:hover:text-gray-100"
               )}
             >
               <Icon className="w-4 h-4" />
               <span>{tab.label}</span>
             </button>
           );
        })}
      </div>

      {/* Background Job Indicator */}
      {showJobIndicator && (
        <div className="bg-indigo-50 dark:bg-indigo-900/30 px-4 py-2 flex items-center gap-3 border-b border-indigo-100 dark:border-indigo-800/50">
          <Loader2 className="w-4 h-4 text-indigo-600 dark:text-indigo-400 animate-spin" />
          <div className="flex-1">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-medium text-indigo-700 dark:text-indigo-300">
                {getJobLabel(jobStatus.type)}...
              </span>
              <span className="text-[10px] text-indigo-500 dark:text-indigo-400">
                {Math.round(jobStatus.progress || 0)}%
              </span>
            </div>
            <div className="w-full bg-indigo-200 dark:bg-indigo-800 rounded-full h-1">
              <div 
                className="bg-indigo-600 dark:bg-indigo-400 h-1 rounded-full transition-all duration-300"
                style={{ width: `${jobStatus.progress || 0}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 overflow-hidden bg-gray-50/30 dark:bg-slate-800/30 flex flex-col">
        {activeTab === 'guide' && <GuideTab paperId={paperId} isProcessing={isProcessing} loadingStage={loadingStage} progress={progress} />}
        {activeTab === 'notes' && <NotesTab paperId={paperId} />}
        {activeTab === 'graph' && <GraphTab paperId={paperId} isProcessing={isProcessing} loadingStage={loadingStage} progress={progress} />}
        {activeTab === 'settings' && <SettingsTab paperId={paperId} />}
      </div>
    </aside>
  );
};
