'use client';

import React, { useState, useEffect } from 'react';
import { X, Monitor, Search, BookOpen, Save, Loader2 } from 'lucide-react';
import * as Dialog from '@radix-ui/react-dialog';
import { cn } from '@/lib/utils';
import { Switch } from '@/components/ui/switch';
import { toast } from 'sonner';
import { settingsService } from '@/services/settings.service';
import { useTheme } from '@/components/providers/ThemeProvider';
import { 
  SystemSettings, 
  SearchSettings, 
  AIReaderSettings, 
  AIReaderType,
  AgentSettings
} from '@/types/settings';
import { Bot } from 'lucide-react';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSettingsChanged?: () => void;
}

type SettingsTab = 'system' | 'search' | 'reader';

export const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose, onSettingsChanged }) => {
  const { setTheme } = useTheme();
  const [activeTab, setActiveTab] = useState<SettingsTab>('system');
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // State for each section
  const [systemSettings, setSystemSettings] = useState<SystemSettings | null>(null);
  const [searchSettings, setSearchSettings] = useState<SearchSettings | null>(null);
  const [readerSettings, setReaderSettings] = useState<AIReaderSettings[]>([]);

  // Fetch data when tab changes
  useEffect(() => {
    if (!isOpen) return;

    const loadData = async () => {
      setIsLoading(true);
      try {
        if (activeTab === 'system') {
          const data = await settingsService.getSystemSettings();
          setSystemSettings(data);
        } else if (activeTab === 'search') {
          const data = await settingsService.getSearchSettings();
          setSearchSettings(data);
        } else if (activeTab === 'reader') {
          const res = await settingsService.getAIReaderSettings();
          // Ensure we have all types or at least what comes back
          setReaderSettings(res.items || []);
        }
      } catch (error) {
        console.error('Failed to load settings:', error);
        toast.error('加载设置失败');
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [isOpen, activeTab]);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      if (activeTab === 'system' && systemSettings) {
        await settingsService.updateSystemSettings(systemSettings);
        toast.success('系统设置已保存');
        // Apply theme immediately if needed (optional side effect)
        if (systemSettings.system_colour === 'dark') {
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.remove('dark');
        }
      } else if (activeTab === 'search' && searchSettings) {
        await settingsService.updateSearchSettings(searchSettings);
        toast.success('搜索设置已保存');
      } else if (activeTab === 'reader') {
        await settingsService.updateAIReaderSettings({ items: readerSettings });
        toast.success('Agent设置已保存');
      }
      // onClose(); // Optional: close on save? Usually better to stay.
      if (onSettingsChanged) {
        onSettingsChanged();
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
      toast.error('保存失败');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Dialog.Root open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/20 backdrop-blur-sm z-50 animate-in fade-in duration-200" />
        <Dialog.Content className="fixed left-[50%] top-[50%] z-50 w-full max-w-4xl translate-x-[-50%] translate-y-[-50%] outline-none animate-in zoom-in-95 slide-in-from-bottom-4 duration-300">
          <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl overflow-hidden border border-gray-100 dark:border-gray-800 flex h-[650px] transition-colors duration-300">
            
            {/* Left Sidebar */}
            <div className="w-64 bg-gray-50/50 dark:bg-gray-800/50 border-r border-gray-100 dark:border-gray-800 p-6 flex flex-col">
              <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-6 px-2">设置</h2>
              
              <nav className="space-y-1 flex-1">
                <TabButton 
                  active={activeTab === 'system'} 
                  onClick={() => setActiveTab('system')}
                  icon={<Monitor className="w-4 h-4" />}
                  label="系统设置"
                />
                <TabButton 
                  active={activeTab === 'search'} 
                  onClick={() => setActiveTab('search')}
                  icon={<Search className="w-4 h-4" />}
                  label="搜索设置"
                />
                <TabButton 
                  active={activeTab === 'reader'} 
                  onClick={() => setActiveTab('reader')}
                  icon={<Bot className="w-4 h-4" />}
                  label="Agent 设置"
                />
              </nav>

              <div className="text-xs text-gray-400 px-2">
                Version 1.1.0
              </div>
            </div>

            {/* Right Content Area */}
            <div className="flex-1 flex flex-col min-w-0 bg-white dark:bg-gray-900">
              {/* Header */}
              <div className="h-16 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between px-8">
                <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">
                  {activeTab === 'system' && "系统设置"}
                  {activeTab === 'search' && "搜索配置"}
                  {activeTab === 'reader' && "Agent 配置 (LLM)"}
                </h3>
                <button 
                  onClick={onClose}
                  className="p-2 -mr-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Content Scrollable */}
              <div className="flex-1 overflow-y-auto p-8">
                {isLoading ? (
                  <div className="flex h-full items-center justify-center text-gray-400">
                    <Loader2 className="w-8 h-8 animate-spin" />
                  </div>
                ) : (
                  <>
                    {activeTab === 'system' && systemSettings && (
                      <SystemSettingsForm 
                        settings={systemSettings} 
                        onChange={setSystemSettings} 
                      />
                    )}
                    {activeTab === 'search' && searchSettings && (
                      <SearchSettingsForm 
                        settings={searchSettings} 
                        onChange={setSearchSettings} 
                      />
                    )}
                    {activeTab === 'reader' && (
                      <ReaderSettingsForm 
                        settings={readerSettings} 
                        onChange={setReaderSettings} 
                      />
                    )}
                  </>
                )}
              </div>

              {/* Footer Actions */}
              <div className="p-6 border-t border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-800/50 flex justify-end gap-3">
                <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                  取消
                </button>
                <button 
                  onClick={handleSave} 
                  disabled={isLoading || isSaving}
                  className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600 rounded-lg shadow-sm shadow-indigo-200 dark:shadow-none transition-colors flex items-center gap-2 disabled:opacity-50"
                >
                  {isSaving && <Loader2 className="w-4 h-4 animate-spin" />}
                  保存更改
                </button>
              </div>
            </div>

          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};

const TabButton = ({ active, onClick, icon, label }: { active: boolean; onClick: () => void; icon: React.ReactNode; label: string }) => (
  <button
    onClick={onClick}
    className={cn(
      "w-full flex items-center gap-3 px-3 py-2.5 text-sm font-medium rounded-xl transition-all duration-200",
      active 
        ? "bg-white dark:bg-slate-800 text-indigo-600 dark:text-indigo-400 shadow-sm border border-gray-100 dark:border-slate-700" 
        : "text-gray-600 dark:text-gray-400 hover:bg-white/50 dark:hover:bg-slate-800/50 hover:text-gray-900 dark:hover:text-gray-200"
    )}
  >
    <span className={cn(active ? "text-indigo-600 dark:text-indigo-400" : "text-gray-400 dark:text-gray-500")}>{icon}</span>
    {label}
  </button>
);

// Reader components

// --- Sub-components ---

const SystemSettingsForm = ({ settings, onChange }: { settings: SystemSettings, onChange: (s: SystemSettings) => void }) => {
  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 border-b border-gray-100 dark:border-gray-800 pb-2">界面外观</h4>
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <div className="text-sm font-medium text-gray-700 dark:text-gray-300">深色模式</div>
            <div className="text-xs text-gray-500 dark:text-gray-400">切换应用的主题颜色为深色</div>
          </div>
          <Switch 
            checked={settings.system_colour === 'dark'} 
            onCheckedChange={(checked) => onChange({ ...settings, system_colour: checked ? 'dark' : 'light' })} 
          />
        </div>
      </div>
    </div>
  );
};
import { DatePicker } from '@/components/ui/date-picker';

const SearchSettingsForm = ({ settings, onChange }: { settings: SearchSettings, onChange: (s: SearchSettings) => void }) => {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-6">
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">最小日期 (Min Date)</label>
          <DatePicker 
            date={settings.min_date ? new Date(settings.min_date) : undefined}
            setDate={(date) => onChange({ ...settings, min_date: date ? date.toISOString() : '' })}
            placeholder="选择开始日期"
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">最大日期 (Max Date)</label>
          <DatePicker 
            date={settings.max_date ? new Date(settings.max_date) : undefined}
            setDate={(date) => onChange({ ...settings, max_date: date ? date.toISOString() : '' })}
            placeholder="选择结束日期"
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">每页限制 (Limit)</label>
          <input 
            type="number" 
            className="w-full text-sm border-gray-200 dark:border-slate-700 rounded-lg focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50 dark:bg-slate-800 dark:text-gray-200 p-2"
            value={settings.limit}
            onChange={(e) => onChange({ ...settings, limit: parseInt(e.target.value) || 10 })}
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">分析状态</label>
          <select 
            className="w-full text-sm border-gray-200 dark:border-slate-700 rounded-lg focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50 dark:bg-slate-800 dark:text-gray-200 p-2"
            value={settings.match_analysis_status || ''}
            onChange={(e) => onChange({ ...settings, match_analysis_status: e.target.value as any })}
          >
            <option value="">全部 (All)</option>
            <option value="unprocessed">未处理 (Unprocessed)</option>
            <option value="processing">处理中 (Processing)</option>
            <option value="processed">已处理 (Processed)</option>
            <option value="error">错误 (Error)</option>
          </select>
        </div>
      </div>
    </div>
  );
};

const ReaderSettingsForm = ({ settings, onChange }: { settings: AIReaderSettings[], onChange: (s: AIReaderSettings[]) => void }) => {
  const [activeType, setActiveType] = useState<AIReaderType>('chat');

  // Helper to get or create setting for a type
  const getSetting = (type: AIReaderType): AIReaderSettings => {
    return settings.find(s => s.type === type) || {
      type,
      llm_name: '',
      provider: 'openai',
      api_key: '',
      base_url: '',
      config: {}
    };
  };

  const updateSetting = (type: AIReaderType, updates: Partial<AIReaderSettings>) => {
    const current = getSetting(type);
    const updated = { ...current, ...updates };
    
    // Replace or append
    const others = settings.filter(s => s.type !== type);
    onChange([...others, updated]);
  };

  const currentSetting = getSetting(activeType);

  return (
    <div className="space-y-6">
      {/* Sub-tabs */}
      <div className="flex space-x-2 border-b border-gray-100 dark:border-gray-800 pb-2">
        {(['chat', 'summary', 'mind_map'] as AIReaderType[]).map((type) => (
          <button
            key={type}
            onClick={() => setActiveType(type)}
            className={cn(
              "px-4 py-2 text-sm font-medium rounded-lg transition-colors capitalize",
              activeType === type 
                ? "bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-400" 
                : "text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800"
            )}
          >
            {type === 'chat' && 'AI 对话 (Chat)'}
            {type === 'summary' && '总结助手 (Summary)'}
            {type === 'mind_map' && '脑图助手 (MindMap)'}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 animate-in fade-in duration-300">
        <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">供应商 (Provider)</label>
            <input 
                type="text" 
                placeholder="e.g. openai, anthropic"
                className="w-full text-sm border-gray-200 dark:border-slate-700 rounded-lg focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50 dark:bg-slate-800 dark:text-gray-200 p-2"
                value={currentSetting.provider}
                onChange={(e) => updateSetting(activeType, { provider: e.target.value })}
            />
            </div>
            <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">模型名称 (Model Name)</label>
            <input 
                type="text" 
                placeholder="e.g. gpt-4o"
                className="w-full text-sm border-gray-200 dark:border-slate-700 rounded-lg focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50 dark:bg-slate-800 dark:text-gray-200 p-2"
                value={currentSetting.llm_name}
                onChange={(e) => updateSetting(activeType, { llm_name: e.target.value })}
            />
            </div>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Base URL</label>
          <input 
            type="text" 
            placeholder="https://api.openai.com/v1"
            className="w-full text-sm border-gray-200 dark:border-slate-700 rounded-lg focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50 dark:bg-slate-800 dark:text-gray-200 p-2"
            value={currentSetting.base_url}
            onChange={(e) => updateSetting(activeType, { base_url: e.target.value })}
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">API Key</label>
          <input 
            type="password" 
            placeholder="sk-..."
            className="w-full text-sm border-gray-200 dark:border-slate-700 rounded-lg focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50 dark:bg-slate-800 dark:text-gray-200 p-2"
            value={currentSetting.api_key}
            onChange={(e) => updateSetting(activeType, { api_key: e.target.value })}
          />
          <p className="text-xs text-gray-400 dark:text-gray-500">密钥将加密存储，不会在前端明文显示</p>
        </div>

        {/* Chat Specific Config */}
        {activeType === 'chat' && (
          <div className="pt-4 border-t border-gray-100 dark:border-gray-800 space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <div className="text-sm font-medium text-gray-700 dark:text-gray-300">启用向量搜索</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">允许 AI 在对话中检索相关论文片段</div>
              </div>
              <Switch 
                checked={currentSetting.config?.enable_vector_search || false} 
                onCheckedChange={(checked) => updateSetting(activeType, { 
                  config: { ...currentSetting.config, enable_vector_search: checked } 
                })} 
              />
            </div>

            {/* Vector Search Configuration */}
            {currentSetting.config?.enable_vector_search && (
              <div className="pl-4 border-l-2 border-indigo-100 dark:border-indigo-900/30 space-y-4 animate-in slide-in-from-top-2 duration-200">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Embedding Provider</label>
                    <select 
                        className="w-full text-sm border-gray-200 dark:border-slate-700 rounded-lg focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50 dark:bg-slate-800 dark:text-gray-200 p-2 outline-none"
                        value={currentSetting.config?.embedding_provider || 'openai'}
                        onChange={(e) => updateSetting(activeType, { 
                            config: { ...currentSetting.config, embedding_provider: e.target.value } 
                        })}
                    >
                        <option value="openai">OpenAI Compatible</option>
                        <option value="siliconflow">SiliconFlow</option>
                        <option value="local">Local</option>
                    </select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Embedding Model</label>
                    <input 
                        type="text" 
                        placeholder="e.g. text-embedding-3-small"
                        className="w-full text-sm border-gray-200 dark:border-slate-700 rounded-lg focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50 dark:bg-slate-800 dark:text-gray-200 p-2 outline-none"
                        value={currentSetting.config?.embedding_model || ''}
                        onChange={(e) => updateSetting(activeType, { 
                            config: { ...currentSetting.config, embedding_model: e.target.value } 
                        })}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Embedding Base URL</label>
                  <input 
                    type="text" 
                    placeholder="https://api.openai.com/v1"
                    className="w-full text-sm border-gray-200 dark:border-slate-700 rounded-lg focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50 dark:bg-slate-800 dark:text-gray-200 p-2 outline-none"
                    value={currentSetting.config?.embedding_base_url || ''}
                    onChange={(e) => updateSetting(activeType, { 
                        config: { ...currentSetting.config, embedding_base_url: e.target.value } 
                    })}
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Embedding API Key</label>
                  <input 
                    type="password" 
                    placeholder="sk-..."
                    className="w-full text-sm border-gray-200 dark:border-slate-700 rounded-lg focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50 dark:bg-slate-800 dark:text-gray-200 p-2 outline-none"
                    value={currentSetting.config?.embedding_api_key || ''}
                    onChange={(e) => updateSetting(activeType, { 
                        config: { ...currentSetting.config, embedding_api_key: e.target.value } 
                    })}
                  />
                  <p className="text-xs text-gray-400 dark:text-gray-500">密钥将加密存储，不会在前端明文显示</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
