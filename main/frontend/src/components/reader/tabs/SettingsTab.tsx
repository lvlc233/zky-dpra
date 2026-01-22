import React from 'react';
import { Switch } from '@/components/ui/switch';
import { Moon, Sun, Type, Monitor } from 'lucide-react';

interface SettingsTabProps {
  paperId: string;
}

export const SettingsTab: React.FC<SettingsTabProps> = ({ paperId }) => {
  return (
    <div className="h-full flex flex-col bg-white dark:bg-slate-900">
      <div className="p-4 border-b border-gray-200 dark:border-slate-800">
        <h3 className="font-semibold text-gray-900 dark:text-gray-100">阅读设置</h3>
      </div>
      
      <div className="flex-1 p-4 space-y-6">
        {/* Theme Section */}
        <div className="space-y-3">
          <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">外观模式</h4>
          <div className="grid grid-cols-3 gap-2">
            <button className="flex flex-col items-center gap-2 p-3 rounded-lg border-2 border-indigo-600 bg-indigo-50 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-400">
              <Sun className="w-5 h-5" />
              <span className="text-xs font-medium">浅色</span>
            </button>
            <button className="flex flex-col items-center gap-2 p-3 rounded-lg border border-gray-200 dark:border-slate-700 hover:bg-gray-50 dark:hover:bg-slate-800 text-gray-600 dark:text-gray-400 transition-colors">
              <Moon className="w-5 h-5" />
              <span className="text-xs font-medium">深色</span>
            </button>
            <button className="flex flex-col items-center gap-2 p-3 rounded-lg border border-gray-200 dark:border-slate-700 hover:bg-gray-50 dark:hover:bg-slate-800 text-gray-600 dark:text-gray-400 transition-colors">
              <Monitor className="w-5 h-5" />
              <span className="text-xs font-medium">跟随系统</span>
            </button>
          </div>
        </div>

        {/* Font Section */}
        <div className="space-y-3">
          <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">字体大小</h4>
          <div className="flex items-center justify-between bg-gray-50 dark:bg-slate-800 p-3 rounded-lg border border-gray-200 dark:border-slate-700">
            <Type className="w-4 h-4 text-gray-500 dark:text-gray-400" />
            <input type="range" min="12" max="24" defaultValue="16" className="w-32 h-1 bg-gray-300 dark:bg-slate-600 rounded-lg appearance-none cursor-pointer accent-indigo-600 dark:accent-indigo-500" />
            <Type className="w-6 h-6 text-gray-900 dark:text-gray-100" />
          </div>
        </div>

        {/* Analysis Preferences */}
        <div className="space-y-3">
          <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">分析偏好</h4>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <label className="text-sm font-medium text-gray-900 dark:text-gray-100">自动生成导读</label>
                <p className="text-xs text-gray-500 dark:text-gray-400">打开文件时自动分析摘要</p>
              </div>
              <Switch checked={true} onCheckedChange={() => {}} />
            </div>
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <label className="text-sm font-medium text-gray-900 dark:text-gray-100">显示引用链接</label>
                <p className="text-xs text-gray-500 dark:text-gray-400">在正文中高亮显示参考文献</p>
              </div>
              <Switch checked={true} onCheckedChange={() => {}} />
            </div>
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <label className="text-sm font-medium text-gray-900 dark:text-gray-100">实时翻译</label>
                <p className="text-xs text-gray-500 dark:text-gray-400">选中文字时显示翻译浮窗</p>
              </div>
              <Switch checked={false} onCheckedChange={() => {}} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
