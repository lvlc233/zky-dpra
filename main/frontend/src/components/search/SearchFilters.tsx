'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { UploadCloud, Check } from 'lucide-react';

interface SearchFiltersProps {
  className?: string;
  onUploadClick?: () => void;
  filters: {
    match_title: boolean;
    match_author: boolean;
    match_abstract: boolean;
    match_source: boolean;
    enable_web_search: boolean;
  };
  onChange: (filters: {
    match_title: boolean;
    match_author: boolean;
    match_abstract: boolean;
    match_source: boolean;
    enable_web_search: boolean;
  }) => void;
}

const FILTER_OPTIONS = [
  { id: 'match_title', label: '标题' },
  { id: 'match_author', label: '作者' },
  { id: 'match_abstract', label: '摘要' },
  { id: 'match_source', label: '来源' },
  { id: 'enable_web_search', label: '网络' },
] as const;

export const SearchFilters: React.FC<SearchFiltersProps> = ({ className, onUploadClick, filters, onChange }) => {
  const isAllSelected = Object.values(filters).every(Boolean);

  const toggleFilter = (key: keyof typeof filters | 'all') => {
    if (key === 'all') {
      if (isAllSelected) {
        onChange({
          match_title: false,
          match_author: false,
          match_abstract: false,
          match_source: false,
          enable_web_search: false,
        });
      } else {
        onChange({
          match_title: true,
          match_author: true,
          match_abstract: true,
          match_source: true,
          enable_web_search: true,
        });
      }
      return;
    }

    onChange({
      ...filters,
      [key]: !filters[key]
    });
  };

  return (
    <div className={cn("w-full max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 mt-6", className)}>
      {/* Filters List */}
      <div className="flex flex-wrap items-center justify-center gap-3">
        <button
          onClick={() => toggleFilter('all')}
          className={cn(
            "flex items-center gap-1.5 px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-200 border",
            isAllSelected
              ? "bg-gray-900 dark:bg-indigo-600 text-white border-gray-900 dark:border-indigo-600 shadow-md"
              : "bg-white dark:bg-slate-800 text-gray-600 dark:text-gray-300 border-gray-200 dark:border-slate-700 hover:border-gray-300 dark:hover:border-slate-600 hover:bg-gray-50 dark:hover:bg-slate-700"
          )}
        >
          {isAllSelected && <Check className="w-3 h-3" />}
          全部
        </button>

        {FILTER_OPTIONS.map((option) => {
          const isSelected = filters[option.id];
          return (
            <button
              key={option.id}
              onClick={() => toggleFilter(option.id)}
              className={cn(
                "flex items-center gap-1.5 px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-200 border",
                isSelected
                  ? "bg-gray-900 dark:bg-indigo-600 text-white border-gray-900 dark:border-indigo-600 shadow-md"
                  : "bg-white dark:bg-slate-800 text-gray-600 dark:text-gray-300 border-gray-200 dark:border-slate-700 hover:border-gray-300 dark:hover:border-slate-600 hover:bg-gray-50 dark:hover:bg-slate-700"
              )}
            >
              {isSelected && <Check className="w-3 h-3" />}
              {option.label}
            </button>
          );
        })}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3">
        <button 
          onClick={onUploadClick}
          className="flex items-center gap-2 text-sm font-medium text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 bg-indigo-50 dark:bg-indigo-900/30 hover:bg-indigo-100 dark:hover:bg-indigo-900/50 px-4 py-2 rounded-lg transition-colors"
        >
          <UploadCloud className="w-4 h-4" />
          <span>上传论文</span>
        </button>
      </div>
    </div>
  );
};
