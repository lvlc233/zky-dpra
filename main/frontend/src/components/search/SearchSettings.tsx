'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { Switch } from '@/components/ui/switch';
import { Calendar, FileText, BarChart, Zap, Layers, Filter } from 'lucide-react';
import { SearchSettings as SearchSettingsType, MatchAnalysisStatus } from '@/types/settings';

import { DatePicker } from '@/components/ui/date-picker';

interface SearchSettingsProps {
  className?: string;
  isOpen: boolean;
  onClose: () => void;
  settings: SearchSettingsType;
  onChange: (settings: SearchSettingsType) => void;
  onApply: () => void;
}

const STATUS_OPTIONS: { value: MatchAnalysisStatus; label: string }[] = [
  { value: 'unprocessed', label: '未处理' },
  { value: 'processing', label: '处理中' },
  { value: 'processed', label: '已处理' },
  { value: 'error', label: '错误' },
];

export const SearchSettings: React.FC<SearchSettingsProps> = ({ className, isOpen, onClose, settings, onChange, onApply }) => {
  if (!isOpen) return null;

  return (
    <div className={cn(
      "absolute right-0 top-16 w-80 bg-white dark:bg-slate-900 rounded-2xl shadow-xl border border-gray-100 dark:border-slate-800 z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-200 origin-top-right",
      className
    )}>
      <div className="p-4 space-y-6">
        
        {/* Filter Configuration Section */}
        <div className="space-y-3">
          <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider flex items-center gap-2">
            <Filter className="w-3 h-3" />
            高级筛选
          </h4>

          <div className="space-y-3">
            <div className="space-y-1.5">
               <div className="text-sm font-medium text-gray-700 dark:text-gray-300">解析状态</div>
               <select 
                 value={settings.match_analysis_status || ''}
                 onChange={(e) => onChange({ ...settings, match_analysis_status: e.target.value as MatchAnalysisStatus })}
                 className="w-full text-sm border-gray-200 dark:border-slate-700 rounded-lg focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50 dark:bg-slate-800 dark:text-gray-200 p-2"
               >
                   <option value="">全部</option>
                   {STATUS_OPTIONS.map(opt => (
                     <option key={opt.value} value={opt.value}>{opt.label}</option>
                   ))}
               </select>
           </div>

            <div className="space-y-1.5">
                <div className="text-sm font-medium text-gray-700 dark:text-gray-300">发表日期范围</div>
                <div className="flex flex-col gap-2">
                    <DatePicker 
                      date={settings.min_date ? new Date(settings.min_date) : undefined}
                      setDate={(date) => onChange({ ...settings, min_date: date ? date.toISOString() : '' })}
                      placeholder="开始日期"
                    />
                    <DatePicker 
                      date={settings.max_date ? new Date(settings.max_date) : undefined}
                      setDate={(date) => onChange({ ...settings, max_date: date ? date.toISOString() : '' })}
                      placeholder="结束日期"
                    />
                </div>
            </div>
            
            <div className="space-y-1.5">
                <div className="text-sm font-medium text-gray-700 dark:text-gray-300">每页显示数量</div>
                <input 
                  type="number" 
                  min={1}
                  max={100}
                  value={settings.limit}
                  onChange={(e) => onChange({ ...settings, limit: parseInt(e.target.value) || 10 })}
                  className="w-full text-sm bg-gray-50 dark:bg-slate-800 border-gray-200 dark:border-slate-700 dark:text-gray-200 rounded-md p-1.5" 
                />
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="p-3 bg-gray-50 dark:bg-slate-800 border-t border-gray-100 dark:border-slate-700 flex justify-between items-center">
        <button onClick={onClose} className="text-xs text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200">取消</button>
        <button onClick={() => { onApply(); onClose(); }} className="px-3 py-1.5 bg-gray-900 dark:bg-indigo-600 text-white text-xs font-medium rounded-lg hover:bg-gray-800 dark:hover:bg-indigo-700">
            确认应用
        </button>
      </div>
    </div>
  );
};
