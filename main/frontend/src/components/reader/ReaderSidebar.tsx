'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { List } from 'lucide-react';
import { Layer } from '@/types/reader';

interface ReaderSidebarProps {
  className?: string;
  isCollapsed?: boolean;
  onNavigate?: (page: number) => void;
  onToggleCollapse?: () => void;
  toc?: any[];
  isLoading?: boolean;
  loadingStage?: string;
  progress?: number;
}

export const ReaderSidebar: React.FC<ReaderSidebarProps> = ({ 
  className,
  isCollapsed = false,
  onNavigate,
  onToggleCollapse,
  toc = [],
  isLoading = false,
  loadingStage,
  progress,
}) => {

  if (isCollapsed) return null;

  return (
    <aside className={cn(
      "w-64 bg-white dark:bg-slate-900 border-r border-gray-200 dark:border-slate-800 flex flex-col h-full",
      className
    )}>
      {/* Header */}
      <div className="flex p-3 border-b border-gray-100 dark:border-slate-800 items-center gap-2 text-gray-700 dark:text-gray-200 font-medium text-sm">
        <List className="w-4 h-4" />
        <span>目录</span>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-3">
        <OutlineView 
            toc={toc} 
            onNavigate={onNavigate} 
            isLoading={isLoading} 
            loadingStage={loadingStage}
            progress={progress}
        />
      </div>
    </aside>
  );
};

// Outline Component
const OutlineView = ({ toc, onNavigate, isLoading, loadingStage, progress }: { 
    toc: any[], 
    onNavigate?: (page: number) => void, 
    isLoading?: boolean,
    loadingStage?: string,
    progress?: number
}) => {
  if (isLoading && (!toc || toc.length === 0)) {
    // Map stage to friendly message
    let message = "正在解析目录...";
    if (loadingStage) {
        if (loadingStage.includes('toc')) message = "正在提取目录结构...";
        else if (loadingStage.includes('text')) message = "正在解析文本内容...";
        else if (loadingStage.includes('figures')) message = "正在分析图表...";
        else message = `正在解析中 (${loadingStage})...`;
    }
    
    return (
      <div className="space-y-3 p-2">
        <div className="h-4 bg-gray-100 dark:bg-slate-800 rounded w-3/4 animate-pulse" />
        <div className="h-4 bg-gray-100 dark:bg-slate-800 rounded w-1/2 animate-pulse" />
        <div className="h-4 bg-gray-100 dark:bg-slate-800 rounded w-5/6 animate-pulse" />
        <div className="h-4 bg-gray-100 dark:bg-slate-800 rounded w-2/3 animate-pulse" />
        <div className="h-4 bg-gray-100 dark:bg-slate-800 rounded w-3/4 animate-pulse" />
        <div className="flex flex-col gap-1 mt-4">
            <div className="flex items-center gap-2 text-xs text-indigo-500">
                <div className="w-3 h-3 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                <span>{message}</span>
            </div>
            {progress !== undefined && progress > 0 && (
                <div className="w-full bg-gray-100 dark:bg-slate-800 rounded-full h-1 mt-1">
                    <div className="bg-indigo-500 h-1 rounded-full transition-all duration-300" style={{ width: `${progress}%` }} />
                </div>
            )}
        </div>
      </div>
    );
  }

  if (!toc || toc.length === 0) {
      return <div className="text-xs text-gray-400 dark:text-gray-500 p-2">暂无目录</div>;
  }

  // Normalize TOC items
  const items = toc.map(item => {
      if (Array.isArray(item) && item.length >= 3) {
          // Handle PyMuPDF format: [level, title, page, ...]
          return { level: item[0], title: item[1], page: item[2] };
      }
      return { level: 1, ...item };
  });

  return (
    <div className="space-y-1">
      {items.map((item, idx) => (
        <button 
          key={idx}
          onClick={() => onNavigate?.(item.page)}
          className="w-full text-left py-1.5 text-xs text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-slate-800 rounded-md truncate transition-colors"
          style={{ paddingLeft: `${(item.level ? item.level - 1 : 0) * 12 + 8}px`, paddingRight: '8px' }}
          title={item.title}
        >
          <span className="mr-2 text-gray-400 dark:text-gray-500">{item.page}</span>
          {item.title}
        </button>
      ))}
    </div>
  );
};

