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
}

export const ReaderSidebar: React.FC<ReaderSidebarProps> = ({ 
  className,
  isCollapsed = false,
  onNavigate,
  onToggleCollapse,
  toc = [],
}) => {

  if (isCollapsed) return null;

  return (
    <aside className={cn(
      "w-64 bg-white border-r border-gray-200 flex flex-col h-full",
      className
    )}>
      {/* Header */}
      <div className="flex p-3 border-b border-gray-100 items-center gap-2 text-gray-700 font-medium text-sm">
        <List className="w-4 h-4" />
        <span>目录</span>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-3">
        <OutlineView toc={toc} onNavigate={onNavigate} />
      </div>
    </aside>
  );
};

// Outline Component
const OutlineView = ({ toc, onNavigate }: { toc: any[], onNavigate?: (page: number) => void }) => {
  if (!toc || toc.length === 0) {
      return <div className="text-xs text-gray-400 p-2">暂无目录</div>;
  }

  return (
    <div className="space-y-1">
      {toc.map((item, idx) => (
        <button 
          key={idx}
          onClick={() => onNavigate?.(item.page)}
          className="w-full text-left px-2 py-1.5 text-xs text-gray-600 hover:bg-gray-50 rounded-md truncate transition-colors"
          title={item.title}
        >
          <span className="mr-2 text-gray-400">{item.page}</span>
          {item.title}
        </button>
      ))}
    </div>
  );
};

