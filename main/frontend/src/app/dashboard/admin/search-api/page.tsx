'use client';

import React, { useState, useEffect } from 'react';
import { Database, Edit2, X, Save, Activity } from 'lucide-react';
import { settingsService } from '@/services/settings.service';
import { SearchApiConfigInfo, SearchApiConfigUpdate } from '@/types/settings';
import { toast } from 'sonner';

export default function SearchApiPage() {
  const [configs, setConfigs] = useState<SearchApiConfigInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [editingConfig, setEditingConfig] = useState<SearchApiConfigUpdate | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    loadConfigs();
  }, []);

  const loadConfigs = async () => {
    setIsLoading(true);
    try {
      const data = await settingsService.getSearchApiConfigs();
      setConfigs(data);
    } catch (error) {
      toast.error('加载API配置失败');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEdit = (config: SearchApiConfigInfo) => {
    setEditingConfig({
      api_name: config.api_name,
      api_key: config.api_key || '',
      weight: config.weight,
      is_active: config.is_active
    });
  };

  const handleCancelEdit = () => {
    setEditingConfig(null);
  };

  const handleSave = async () => {
    if (!editingConfig) return;
    setIsSaving(true);
    try {
      await settingsService.updateSearchApiConfig(editingConfig);
      toast.success('配置更新成功');
      setEditingConfig(null);
      await loadConfigs();
    } catch (error) {
      toast.error('配置更新失败');
      console.error(error);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <>
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">搜索数据源配置</h1>
          <p className="text-gray-500 dark:text-gray-400">配置外部 API 数据源，实现搜索的高可用调度与自动回退。</p>
        </div>
      </div>

      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-gray-100 dark:border-slate-700 overflow-hidden">
        <div className="px-6 py-5 border-b border-gray-100 dark:border-slate-700 flex justify-between items-center">
          <h2 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Database className="w-5 h-5 text-indigo-500" />
            外部 API 配置 (多源回退策略)
          </h2>
          <div className="flex gap-4">
            <button 
              onClick={loadConfigs}
              className="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 font-medium transition-colors"
            >
              {isLoading ? '加载中...' : '刷新'}
            </button>
          </div>
        </div>
        <div className="p-6">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-500 dark:text-gray-400">
              <thead className="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-slate-900/50 dark:text-gray-400">
                <tr>
                  <th className="px-4 py-3 rounded-l-lg">API 平台</th>
                  <th className="px-4 py-3">API Key (脱敏)</th>
                  <th className="px-4 py-3">权重</th>
                  <th className="px-4 py-3">状态</th>
                  <th className="px-4 py-3 rounded-r-lg text-right">操作</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr>
                    <td colSpan={5} className="text-center py-6 text-gray-400">加载中...</td>
                  </tr>
                ) : configs.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="text-center py-6 text-gray-400">暂无配置，请点击右上角添加。</td>
                  </tr>
                ) : (
                  configs.map((api, i) => (
                    <tr key={api.api_name} className="border-b border-gray-50 dark:border-slate-700/50 last:border-0 hover:bg-gray-50/50 dark:hover:bg-slate-700/20">
                      <td className="px-4 py-4 font-medium text-gray-900 dark:text-white">{api.api_name}</td>
                      <td className="px-4 py-4 font-mono text-xs">
                        {api.api_key && api.api_key.length > 8 
                          ? `${api.api_key.substring(0, 4)}...${api.api_key.substring(api.api_key.length - 4)}` 
                          : api.api_key ? '***' : '未设置'}
                      </td>
                      <td className="px-4 py-4">
                        <span className="px-2 py-1 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 rounded-md text-xs font-bold">{api.weight}</span>
                      </td>
                      <td className="px-4 py-4">
                        <div className="flex items-center gap-2">
                          <div className={`w-2 h-2 rounded-full ${api.is_active ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'}`}></div>
                          <span>{api.is_active ? '运行中' : '已停用'}</span>
                        </div>
                      </td>
                      <td className="px-4 py-4 text-right flex justify-end gap-3 items-center">
                        <button 
                          onClick={() => handleEdit(api)}
                          className="text-indigo-600 hover:text-indigo-800 dark:text-indigo-400 dark:hover:text-indigo-300 font-medium flex items-center gap-1"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                          配置
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Edit Modal Overlay */}
      {editingConfig && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-800 w-full max-w-md rounded-2xl shadow-xl overflow-hidden animate-in fade-in zoom-in-95">
            <div className="px-6 py-4 border-b border-gray-100 dark:border-slate-700 flex justify-between items-center">
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                配置 API: {editingConfig.api_name}
              </h3>
              <button 
                onClick={handleCancelEdit}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">API Key</label>
                <input 
                  type="text" 
                  value={editingConfig.api_key || ''}
                  onChange={e => setEditingConfig({...editingConfig, api_key: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                  placeholder="输入新Key，留空则不修改"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">请求权重 (Weight)</label>
                <input 
                  type="number" 
                  value={editingConfig.weight}
                  onChange={e => setEditingConfig({...editingConfig, weight: parseInt(e.target.value) || 0})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                />
                <p className="text-xs text-gray-500 mt-1">权重越高，在请求回退策略中优先级越高。可设为0-100。</p>
              </div>

              <div className="flex items-center gap-2 pt-2">
                <input 
                  type="checkbox" 
                  id="isActive"
                  checked={editingConfig.is_active}
                  onChange={e => setEditingConfig({...editingConfig, is_active: e.target.checked})}
                  className="w-4 h-4 text-indigo-600 rounded border-gray-300 focus:ring-indigo-500"
                />
                <label htmlFor="isActive" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  状态启用
                </label>
              </div>
            </div>

            <div className="px-6 py-4 bg-gray-50 dark:bg-slate-900/50 border-t border-gray-100 dark:border-slate-700 flex justify-end gap-3">
              <button 
                onClick={handleCancelEdit}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                disabled={isSaving}
              >
                取消
              </button>
              <button 
                onClick={handleSave}
                disabled={isSaving}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50"
              >
                {isSaving ? <Activity className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                保存配置
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
