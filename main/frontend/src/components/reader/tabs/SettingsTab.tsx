import React, { useState, useEffect } from 'react';
import { Switch } from '@/components/ui/switch';
import { Moon, Sun, Type, Monitor, Save, Loader2, Cpu, Key, Globe, Box } from 'lucide-react';
import { toast } from 'sonner';
import { settingsService } from '@/services/settings.service';
import { AIReaderSettings, AIReaderType, SystemSettings } from '@/types/settings';
import { cn } from '@/lib/utils';
import { useTheme } from '@/components/providers/ThemeProvider';

interface SettingsTabProps {
  paperId: string;
}

export const SettingsTab: React.FC<SettingsTabProps> = ({ paperId }) => {
  const { setTheme } = useTheme();
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  
  // Settings State
  const [systemSettings, setSystemSettings] = useState<SystemSettings | null>(null);
  const [readerSettings, setReaderSettings] = useState<AIReaderSettings[]>([]);
  const [activeAgentType, setActiveAgentType] = useState<AIReaderType>('chat');
  
  // Local Preferences (Mock state for now as they are not in backend types yet)
  // const [fontSize, setFontSize] = useState(16);
  // const [autoGuide, setAutoGuide] = useState(true);
  // const [showCitations, setShowCitations] = useState(true);
  // const [realtimeTrans, setRealtimeTrans] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setIsLoading(true);
    try {
      const [sys, reader] = await Promise.all([
        settingsService.getSystemSettings(),
        settingsService.getAIReaderSettings()
      ]);
      setSystemSettings(sys);
      setReaderSettings(reader.items || []);
    } catch (error) {
      console.error('Failed to load settings:', error);
      toast.error('加载设置失败');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      if (systemSettings) {
        await settingsService.updateSystemSettings(systemSettings);
        // Apply theme
        if (systemSettings.system_colour === 'dark') {
          setTheme('dark');
        } else {
          setTheme('light');
        }
      }
      
      await settingsService.updateAIReaderSettings({ items: readerSettings });
      toast.success('配置已保存');
    } catch (error) {
      console.error('Failed to save settings:', error);
      toast.error('保存失败');
    } finally {
      setIsSaving(false);
    }
  };

  const getAgentConfig = (type: AIReaderType): AIReaderSettings => {
    return readerSettings.find(s => s.type === type) || {
      type,
      llm_name: '',
      provider: 'openai',
      api_key: '',
      base_url: '',
      config: {}
    };
  };

  const updateAgentConfig = (type: AIReaderType, updates: Partial<AIReaderSettings>) => {
    const current = getAgentConfig(type);
    const updated = { ...current, ...updates };
    const others = readerSettings.filter(s => s.type !== type);
    setReaderSettings([...others, updated]);
  };

  const currentAgent = getAgentConfig(activeAgentType);

  if (isLoading && !systemSettings) {
    return (
      <div className="h-full flex items-center justify-center text-gray-400">
        <Loader2 className="w-6 h-6 animate-spin" />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-white dark:bg-slate-900">
      <div className="p-4 border-b border-gray-200 dark:border-slate-800 flex justify-between items-center">
        <h3 className="font-semibold text-gray-900 dark:text-gray-100">阅读设置</h3>
        <button 
          onClick={handleSave}
          disabled={isSaving}
          className="p-2 text-indigo-600 hover:bg-indigo-50 dark:text-indigo-400 dark:hover:bg-indigo-900/30 rounded-full transition-colors"
          title="保存设置"
        >
          {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
        </button>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-8">
        {/* Appearance Section */}
        <section className="space-y-3">
          <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider flex items-center gap-2">
            <Monitor className="w-3 h-3" /> 外观模式
          </h4>
          <div className="grid grid-cols-2 gap-2">
            <button 
              onClick={() => setSystemSettings(prev => prev ? { ...prev, system_colour: 'light' } : null)}
              className={cn(
                "flex items-center justify-center gap-2 p-2 rounded-lg border transition-all",
                systemSettings?.system_colour === 'light'
                  ? "border-indigo-600 bg-indigo-50 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-400"
                  : "border-gray-200 dark:border-slate-700 hover:bg-gray-50 dark:hover:bg-slate-800 text-gray-600 dark:text-gray-400"
              )}
            >
              <Sun className="w-4 h-4" />
              <span className="text-xs font-medium">浅色</span>
            </button>
            <button 
              onClick={() => setSystemSettings(prev => prev ? { ...prev, system_colour: 'dark' } : null)}
              className={cn(
                "flex items-center justify-center gap-2 p-2 rounded-lg border transition-all",
                systemSettings?.system_colour === 'dark'
                  ? "border-indigo-600 bg-indigo-50 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-400"
                  : "border-gray-200 dark:border-slate-700 hover:bg-gray-50 dark:hover:bg-slate-800 text-gray-600 dark:text-gray-400"
              )}
            >
              <Moon className="w-4 h-4" />
              <span className="text-xs font-medium">深色</span>
            </button>
          </div>
        </section>

        {/* AI Configuration Section */}
        <section className="space-y-4">
          <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider flex items-center gap-2">
            <Cpu className="w-3 h-3" /> AI 模型配置
          </h4>
          
          <div className="bg-gray-50 dark:bg-slate-800/50 rounded-lg p-3 space-y-4 border border-gray-100 dark:border-slate-800">
            {/* Agent Type Selector */}
            <div className="flex bg-white dark:bg-slate-900 rounded-md p-1 border border-gray-200 dark:border-slate-700">
              {(['chat', 'summary', 'mind_map'] as AIReaderType[]).map((type) => (
                <button
                  key={type}
                  onClick={() => setActiveAgentType(type)}
                  className={cn(
                    "flex-1 py-1.5 text-xs font-medium rounded transition-colors",
                    activeAgentType === type
                      ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-400 shadow-sm"
                      : "text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                  )}
                >
                  {type === 'chat' && '对话'}
                  {type === 'summary' && '总结'}
                  {type === 'mind_map' && '脑图'}
                </button>
              ))}
            </div>

            {/* Config Fields */}
            <div className="space-y-3 animate-in fade-in duration-200">
              <div className="space-y-1">
                <label className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                  <Box className="w-3 h-3" /> 供应商
                </label>
                <input 
                  type="text"
                  placeholder="openai / anthropic"
                  className="w-full text-xs border border-gray-200 dark:border-slate-700 rounded bg-white dark:bg-slate-900 px-2 py-1.5 focus:ring-1 focus:ring-indigo-500 outline-none"
                  value={currentAgent.provider}
                  onChange={(e) => updateAgentConfig(activeAgentType, { provider: e.target.value })}
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                  <Cpu className="w-3 h-3" /> 模型名称
                </label>
                <input 
                  type="text"
                  placeholder="gpt-4o"
                  className="w-full text-xs border border-gray-200 dark:border-slate-700 rounded bg-white dark:bg-slate-900 px-2 py-1.5 focus:ring-1 focus:ring-indigo-500 outline-none"
                  value={currentAgent.llm_name}
                  onChange={(e) => updateAgentConfig(activeAgentType, { llm_name: e.target.value })}
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                  <Globe className="w-3 h-3" /> Base URL
                </label>
                <input 
                  type="text"
                  placeholder="https://api.openai.com/v1"
                  className="w-full text-xs border border-gray-200 dark:border-slate-700 rounded bg-white dark:bg-slate-900 px-2 py-1.5 focus:ring-1 focus:ring-indigo-500 outline-none"
                  value={currentAgent.base_url}
                  onChange={(e) => updateAgentConfig(activeAgentType, { base_url: e.target.value })}
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                  <Key className="w-3 h-3" /> API Key
                </label>
                <input 
                  type="password"
                  placeholder="sk-..."
                  className="w-full text-xs border border-gray-200 dark:border-slate-700 rounded bg-white dark:bg-slate-900 px-2 py-1.5 focus:ring-1 focus:ring-indigo-500 outline-none"
                  value={currentAgent.api_key}
                  onChange={(e) => updateAgentConfig(activeAgentType, { api_key: e.target.value })}
                />
              </div>

              {activeAgentType === 'chat' && (
                 <div className="flex items-center justify-between pt-2 border-t border-gray-100 dark:border-slate-700/50">
                    <span className="text-xs font-medium text-gray-700 dark:text-gray-300">向量搜索</span>
                    <Switch 
                      checked={currentAgent.config?.enable_vector_search || false}
                      onCheckedChange={(checked) => updateAgentConfig(activeAgentType, { 
                        config: { ...currentAgent.config, enable_vector_search: checked }
                      })}
                      className="scale-75 origin-right"
                    />
                 </div>
              )}
            </div>
          </div>
        </section>

      </div>
    </div>
  );
};
