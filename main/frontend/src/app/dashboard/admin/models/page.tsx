'use client';

import React, { useState, useEffect } from 'react';
import { Server, Edit2, X, Save, Activity, Plus, Shield } from 'lucide-react';
import { settingsService } from '@/services/settings.service';
import { SystemModelConfig, SystemModelConfigUpdate } from '@/types/settings';
import { toast } from 'sonner';

export default function AdminModelsPage() {
  const [configs, setConfigs] = useState<SystemModelConfig[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [editingConfig, setEditingConfig] = useState<{id: string, type: string, data: SystemModelConfigUpdate} | null>(null);
  const [isCreating, setIsCreating] = useState<string | null>(null); // type of config being created
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    loadConfigs();
  }, []);

  const loadConfigs = async () => {
    setIsLoading(true);
    try {
      const data = await settingsService.getSystemModelConfigs();
      setConfigs(data);
    } catch (error) {
      toast.error('加载系统模型配置失败');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEdit = (config: SystemModelConfig) => {
    setEditingConfig({
      id: config.id,
      type: config.type,
      data: {
        provider: config.provider,
        api_key: config.api_key,
        base_url: config.base_url,
        model_name: config.model_name,
        system_prompt: config.system_prompt,
        temperature: config.temperature,
        max_tokens: config.max_tokens,
        is_active: config.is_active
      }
    });
  };

  const handleSave = async () => {
    if (!editingConfig) return;
    setIsSaving(true);
    try {
      await settingsService.updateSystemModelConfig(editingConfig.id, editingConfig.data);
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

  const handleCreate = async (type: string) => {
    setIsSaving(true);
    try {
      const defaultData: SystemModelConfigUpdate = {
        provider: 'openai',
        api_key: '',
        base_url: '',
        model_name: type === 'embedding' ? 'text-embedding-3-small' : 'gpt-3.5-turbo',
        system_prompt: '',
        temperature: type === 'embedding' ? 0 : 0.7,
        max_tokens: 4096,
        is_active: true
      };
      await settingsService.createSystemModelConfig(type, defaultData);
      toast.success(`创建 ${type} 配置成功`);
      setIsCreating(null);
      await loadConfigs();
    } catch (error) {
      toast.error('创建失败');
      console.error(error);
    } finally {
      setIsSaving(false);
    }
  };

  const configTypes = ['chat', 'summary', 'mind_map', 'embedding', 'translate'];
  const existingTypes = Array.isArray(configs) ? configs.map(c => c.type) : [];
  const missingTypes = configTypes.filter(t => !existingTypes.includes(t));

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">模型与调度策略</h1>
          <p className="text-gray-500 dark:text-gray-400">配置全系统的模型默认值。用户未自定义时，将自动使用此处的配置。</p>
        </div>
        {missingTypes.length > 0 && (
          <div className="flex gap-2">
            {missingTypes.map(type => (
              <button
                key={type}
                onClick={() => handleCreate(type)}
                disabled={isSaving}
                className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-medium transition-all disabled:opacity-50"
              >
                <Plus className="w-4 h-4" />
                初始化 {type === 'embedding' ? 'Embedding' : type}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {isLoading ? (
          <div className="col-span-full py-20 text-center text-gray-400">加载中...</div>
        ) : configs.length === 0 ? (
          <div className="col-span-full py-20 text-center bg-white dark:bg-slate-800 rounded-2xl border border-dashed border-gray-200 dark:border-slate-700">
            <Shield className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
            <p className="text-gray-500">暂无系统模型配置，请点击右上角初始化。</p>
          </div>
        ) : (
          configs.map((config) => (
            <div 
              key={config.id} 
              className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-gray-100 dark:border-slate-700 overflow-hidden hover:shadow-md transition-shadow"
            >
              <div className="px-6 py-4 border-b border-gray-50 dark:border-slate-700/50 flex justify-between items-center bg-gray-50/50 dark:bg-slate-900/30">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
                    <Server className="w-4 h-4" />
                  </div>
                  <h3 className="font-bold text-gray-900 dark:text-white capitalize">{config.type} 配置</h3>
                </div>
                <div className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${config.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                  {config.is_active ? 'Active' : 'Disabled'}
                </div>
              </div>
              
              <div className="p-6 space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-500 dark:text-gray-400 text-xs mb-1">Provider</p>
                    <p className="font-medium text-gray-900 dark:text-white">{config.provider}</p>
                  </div>
                  <div>
                    <p className="text-gray-500 dark:text-gray-400 text-xs mb-1">Base URL</p>
                    <p className="font-medium text-gray-900 dark:text-white truncate">{config.base_url || 'Default'}</p>
                  </div>
                  <div>
                    <p className="text-gray-500 dark:text-gray-400 text-xs mb-1">Model Name</p>
                    <p className="font-medium text-gray-900 dark:text-white truncate">{config.model_name || 'Default'}</p>
                  </div>
                  <div>
                    <p className="text-gray-500 dark:text-gray-400 text-xs mb-1">API Key</p>
                    <p className="font-medium text-gray-900 dark:text-white truncate">
                      {config.api_key ? (config.api_key.length > 10 ? config.api_key.substring(0, 8) + '...' : '******') : 'Not Set'}
                    </p>
                  </div>
                  {config.type !== 'embedding' && (
                    <>
                      <div>
                        <p className="text-gray-500 dark:text-gray-400 text-xs mb-1">Temperature</p>
                        <p className="font-medium text-gray-900 dark:text-white">{config.temperature}</p>
                      </div>
                      <div>
                        <p className="text-gray-500 dark:text-gray-400 text-xs mb-1">Max Tokens</p>
                        <p className="font-medium text-gray-900 dark:text-white">{config.max_tokens}</p>
                      </div>
                    </>
                  )}
                </div>

                {config.system_prompt && (
                  <div>
                    <p className="text-gray-500 dark:text-gray-400 text-xs mb-1">System Prompt</p>
                    <p className="text-xs text-gray-600 dark:text-gray-300 line-clamp-2 bg-gray-50 dark:bg-slate-900 p-2 rounded-lg border border-gray-100 dark:border-slate-800 italic">
                      "{config.system_prompt}"
                    </p>
                  </div>
                )}

                <button 
                  onClick={() => handleEdit(config)}
                  className="w-full mt-2 py-2 px-4 rounded-xl border border-indigo-100 dark:border-indigo-900/30 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 text-sm font-medium transition-colors flex items-center justify-center gap-2"
                >
                  <Edit2 className="w-4 h-4" />
                  修改配置
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Edit Modal Overlay */}
      {editingConfig && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white dark:bg-slate-800 w-full max-w-lg rounded-3xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95">
            <div className="px-8 py-6 border-b border-gray-100 dark:border-slate-700 flex justify-between items-center">
              <div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                  编辑全局配置
                </h3>
                <p className="text-sm text-gray-500">ID: {editingConfig.id}</p>
              </div>
              <button 
                onClick={() => setEditingConfig(null)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors bg-gray-100 dark:bg-slate-700 p-2 rounded-full"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="p-8 space-y-5 max-h-[70vh] overflow-y-auto custom-scrollbar">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Provider</label>
                  <select 
                    value={editingConfig.data.provider}
                    onChange={e => setEditingConfig({
                      ...editingConfig, 
                      data: { ...editingConfig.data, provider: e.target.value }
                    })}
                    className="w-full px-4 py-2.5 border border-gray-200 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                  >
                    <option value="openai">OpenAI</option>
                    <option value="siliconflow">SiliconFlow</option>
                    <option value="ollama">Ollama</option>
                    <option value="anthropic">Anthropic</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Model Name (模型名称)</label>
                  <input 
                    type="text" 
                    value={editingConfig.data.model_name || ''}
                    onChange={e => setEditingConfig({
                      ...editingConfig, 
                      data: { ...editingConfig.data, model_name: e.target.value }
                    })}
                    className="w-full px-4 py-2.5 border border-gray-200 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                    placeholder={editingConfig.type === 'embedding' ? '例如: text-embedding-3-small' : '例如: gpt-4o, deepseek-chat'}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Base URL</label>
                  <input 
                    type="text" 
                    value={editingConfig.data.base_url || ''}
                    onChange={e => setEditingConfig({
                      ...editingConfig, 
                      data: { ...editingConfig.data, base_url: e.target.value }
                    })}
                    className="w-full px-4 py-2.5 border border-gray-200 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                    placeholder="接口基础地址, 例如: https://api.openai.com/v1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">API Key</label>
                  <input 
                    type="password" 
                    value={editingConfig.data.api_key || ''}
                    onChange={e => setEditingConfig({
                      ...editingConfig, 
                      data: { ...editingConfig.data, api_key: e.target.value }
                    })}
                    className="w-full px-4 py-2.5 border border-gray-200 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                    placeholder="输入该供应商的 API 密钥"
                  />
                </div>
              </div>
              
              {editingConfig.type !== 'embedding' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Temperature</label>
                    <div className="flex items-center gap-4">
                      <input 
                        type="range" 
                        min="0" 
                        max="2" 
                        step="0.1"
                        value={editingConfig.data.temperature ?? 0.7}
                        onChange={e => setEditingConfig({
                          ...editingConfig, 
                          data: { ...editingConfig.data, temperature: e.target.value === '' ? 0.7 : parseFloat(e.target.value) }
                        })}
                        className="flex-1 h-2 bg-gray-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                      />
                      <span className="w-12 text-center text-sm font-bold text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/30 px-2 py-1 rounded-lg">
                        {(editingConfig.data.temperature ?? 0.7).toFixed(1)}
                      </span>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Max Tokens</label>
                    <input 
                      type="number" 
                      value={editingConfig.data.max_tokens ?? 4096}
                      onChange={e => setEditingConfig({
                        ...editingConfig, 
                        data: { ...editingConfig.data, max_tokens: e.target.value === '' ? 4096 : parseInt(e.target.value) }
                      })}
                      className="w-full px-4 py-2.5 border border-gray-200 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">System Prompt</label>
                    <textarea 
                      rows={4}
                      value={editingConfig.data.system_prompt}
                      onChange={e => setEditingConfig({
                        ...editingConfig, 
                        data: { ...editingConfig.data, system_prompt: e.target.value }
                      })}
                      className="w-full px-4 py-2.5 border border-gray-200 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all resize-none"
                      placeholder="输入全局系统提示词..."
                    />
                  </div>
                </>
              )}

              <div className="flex items-center gap-3 p-4 bg-gray-50 dark:bg-slate-900/50 rounded-2xl border border-gray-100 dark:border-slate-800">
                <input 
                  type="checkbox" 
                  id="isActive"
                  checked={editingConfig.data.is_active}
                  onChange={e => setEditingConfig({
                    ...editingConfig, 
                    data: { ...editingConfig.data, is_active: e.target.checked }
                  })}
                  className="w-5 h-5 text-indigo-600 rounded-lg border-gray-300 focus:ring-indigo-500 transition-all"
                />
                <label htmlFor="isActive" className="text-sm font-bold text-gray-700 dark:text-gray-300 cursor-pointer">
                  启用此默认配置
                </label>
              </div>
            </div>

            <div className="px-8 py-6 bg-gray-50 dark:bg-slate-900/50 border-t border-gray-100 dark:border-slate-700 flex justify-end gap-3">
              <button 
                onClick={() => setEditingConfig(null)}
                className="px-6 py-2.5 text-sm font-bold text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-xl transition-all"
                disabled={isSaving}
              >
                取消
              </button>
              <button 
                onClick={handleSave}
                disabled={isSaving}
                className="px-8 py-2.5 text-sm font-bold text-white bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 rounded-xl shadow-lg shadow-indigo-200 dark:shadow-none transition-all flex items-center gap-2 disabled:opacity-50"
              >
                {isSaving ? <Activity className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                保存全局设置
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
