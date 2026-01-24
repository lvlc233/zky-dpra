'use client';

import React from 'react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { 
  ArrowLeft, 
  Bookmark, 
  Search, 
  Layers, 
  Plus,
  ChevronDown,
  Settings,
  Eye,
  EyeOff,
  Trash2,
  MoreHorizontal
} from 'lucide-react';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Button } from '@/components/ui/button';

interface ReaderNavbarProps {
  className?: string;
  title?: string;
  isBookmarked?: boolean;
  onToggleBookmark?: () => void;
  onSearch?: (query: string) => void;
  onViewManage?: () => void;
  showAnnotations?: boolean;
  onToggleAnnotations?: () => void;
  onClearAllAnnotations?: () => void;
}

export const ReaderNavbar: React.FC<ReaderNavbarProps> = ({
  className,
  title = "Untitled Paper",
  isBookmarked = false,
  onToggleBookmark,
  onSearch,
  onViewManage,
  showAnnotations = true,
  onToggleAnnotations,
  onClearAllAnnotations,
}) => {
  return (
    <header className={cn(
      "h-14 bg-white dark:bg-slate-900 border-b border-gray-200 dark:border-slate-800 flex items-center justify-between px-4 z-50",
      className
    )}>
      {/* Left: Back & Title */}
      <div className="flex items-center gap-4 w-1/4">
        <Link 
          href="/dashboard" 
          className="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
          title="返回主页"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <h1 className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate max-w-[200px]" title={title}>
          {title}
        </h1>
      </div>

      {/* Center: Toolbar */}
      <div className="flex-1 flex items-center justify-center max-w-2xl mx-auto">
        <div className="flex items-center bg-gray-100/50 dark:bg-slate-800/50 p-1 rounded-lg border border-gray-200 dark:border-slate-700 shadow-sm">
          {/* Search Input */}
          <div className="relative group w-80">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400 group-focus-within:text-indigo-500" />
            <input 
              type="text" 
              placeholder="文章内搜索..." 
              className="w-full h-8 pl-8 pr-3 bg-transparent text-xs text-gray-900 dark:text-gray-100 placeholder:text-gray-400 focus:outline-none focus:bg-white dark:focus:bg-slate-800 focus:rounded-md transition-all"
              onChange={(e) => onSearch?.(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center justify-end gap-2 w-1/4">
        <button
          onClick={onToggleBookmark}
          className={cn(
            "flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all",
            isBookmarked 
              ? "bg-indigo-50 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800" 
              : "text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-slate-800 border border-transparent"
          )}
        >
          <Bookmark className={cn("w-3.5 h-3.5", isBookmarked && "fill-current")} />
          <span>{isBookmarked ? '已收藏' : '收藏'}</span>
        </button>
        
        <Popover>
          <PopoverTrigger asChild>
            <button className="p-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-md">
              <Settings className="w-4 h-4" />
            </button>
          </PopoverTrigger>
          <PopoverContent className="w-56 p-2" align="end">
             <div className="space-y-1">
               <div className="px-2 py-1.5 text-xs font-semibold text-gray-500 dark:text-gray-400">
                 标注设置
               </div>
               
               {onToggleAnnotations && (
                 <button 
                    onClick={onToggleAnnotations}
                    className="w-full flex items-center gap-2 px-2 py-1.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-sm"
                 >
                    {showAnnotations ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                    <span>{showAnnotations ? '隐藏所有标注' : '显示所有标注'}</span>
                 </button>
               )}
               
               {onClearAllAnnotations && (
                 <button 
                    onClick={onClearAllAnnotations}
                    className="w-full flex items-center gap-2 px-2 py-1.5 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-sm"
                 >
                    <Trash2 className="w-4 h-4" />
                    <span>清空所有标注</span>
                 </button>
               )}
             </div>
          </PopoverContent>
        </Popover>
      </div>
    </header>
  );
};
