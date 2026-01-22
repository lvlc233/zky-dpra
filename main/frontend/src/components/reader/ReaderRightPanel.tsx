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

interface ReaderRightPanelProps {
  className?: string;
  paperId: string;
}

type Tab = 'guide' | 'notes' | 'graph' | 'settings';

export const ReaderRightPanel: React.FC<ReaderRightPanelProps> = ({ className, paperId }) => {
  const [activeTab, setActiveTab] = useState<Tab>('guide');
  const [input, setInput] = useState('');

  const TABS = [
    { id: 'guide', label: '导读', icon: MessageSquare },
    { id: 'notes', label: '笔记', icon: PenTool },
    { id: 'graph', label: '脑图', icon: Network },
    { id: 'settings', label: '设置', icon: Settings },
  ];

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

      {/* Main Content Area */}
      <div className="flex-1 overflow-hidden bg-gray-50/30 dark:bg-slate-800/30 flex flex-col">
        {activeTab === 'guide' && <GuideTab paperId={paperId} />}
        {activeTab === 'notes' && <NotesTab paperId={paperId} />}
        {activeTab === 'graph' && <GraphTab paperId={paperId} />}
        {activeTab === 'settings' && <SettingsTab paperId={paperId} />}
      </div>
    </aside>
  );
};
