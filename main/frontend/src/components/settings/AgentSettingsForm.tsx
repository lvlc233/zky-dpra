
import { AgentSettings } from '@/types/settings';

const AgentSettingsForm = ({ settings, onChange }: { settings: AgentSettings, onChange: (s: AgentSettings) => void }) => {
  return (
    <div className="space-y-8 pb-10">
      {/* Embedding Config */}
      <div className="space-y-4">
         <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 border-b border-gray-100 dark:border-gray-800 pb-2">
            Embedding Configuration (向量化配置)
         </h4>
         <div className="grid grid-cols-1 gap-4">
             <div className="space-y-2">
               <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Provider</label>
               <select 
                 className="w-full p-2 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                 value={settings.embedding_provider}
                 onChange={(e) => onChange({...settings, embedding_provider: e.target.value as any})}
               >
                 <option value="none">Disabled (Close)</option>
                 <option value="local">Local (ONNX)</option>
                 <option value="siliconflow">SiliconFlow</option>
                 <option value="openai">OpenAI Compatible</option>
               </select>
             </div>
             {settings.embedding_provider !== 'local' && settings.embedding_provider !== 'none' && (
               <>
                 <div className="space-y-2">
                   <label className="text-sm font-medium text-gray-700 dark:text-gray-300">API Key</label>
                   <input 
                      type="password"
                      className="w-full p-2 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                      value={settings.embedding_api_key}
                      onChange={(e) => onChange({...settings, embedding_api_key: e.target.value})}
                      placeholder="留空则使用系统默认 (Leave blank for system default)"
                   />
                 </div>
                  <div className="space-y-2">
                   <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Base URL</label>
                   <input 
                      type="text"
                      className="w-full p-2 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                      value={settings.embedding_base_url}
                      onChange={(e) => onChange({...settings, embedding_base_url: e.target.value})}
                      placeholder="留空则使用系统默认 (Leave blank for system default)"
                   />
                 </div>
                  <div className="space-y-2">
                   <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Model Name</label>
                   <input 
                      type="text"
                      className="w-full p-2 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                      value={settings.embedding_model}
                      onChange={(e) => onChange({...settings, embedding_model: e.target.value})}
                      placeholder="留空则使用系统默认 (Leave blank for system default)"
                   />
                 </div>
               </>
             )}
         </div>
      </div>

      {/* RAG Config */}
      <div className="space-y-4">
         <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 border-b border-gray-100 dark:border-gray-800 pb-2">
            Agent / RAG Configuration (生成模型配置)
         </h4>
          <div className="grid grid-cols-1 gap-4">
             <div className="space-y-2">
               <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Provider</label>
               <select 
                 className="w-full p-2 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                 value={settings.rag_provider}
                 onChange={(e) => onChange({...settings, rag_provider: e.target.value as any})}
               >
                 <option value="siliconflow">SiliconFlow</option>
                 <option value="openai">OpenAI Compatible</option>
                 <option value="ollama">Ollama</option>
               </select>
             </div>
             <div className="space-y-2">
               <label className="text-sm font-medium text-gray-700 dark:text-gray-300">API Key</label>
               <input 
                  type="password"
                  className="w-full p-2 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                  value={settings.rag_api_key}
                  onChange={(e) => onChange({...settings, rag_api_key: e.target.value})}
                  placeholder="留空则使用系统默认 (Leave blank for system default)"
               />
             </div>
              <div className="space-y-2">
               <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Base URL</label>
               <input 
                  type="text"
                  className="w-full p-2 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                  value={settings.rag_base_url}
                  onChange={(e) => onChange({...settings, rag_base_url: e.target.value})}
                  placeholder="留空则使用系统默认 (Leave blank for system default)"
               />
             </div>
              <div className="space-y-2">
               <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Model Name</label>
               <input 
                  type="text"
                  className="w-full p-2 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                  value={settings.rag_base_model}
                  onChange={(e) => onChange({...settings, rag_base_model: e.target.value})}
                  placeholder="留空则使用系统默认 (Leave blank for system default)"
               />
             </div>
             <div className="space-y-2">
               <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Temperature: {settings.rag_temperature}</label>
               <input 
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  className="w-full accent-indigo-600"
                  value={settings.rag_temperature}
                  onChange={(e) => onChange({...settings, rag_temperature: parseFloat(e.target.value)})}
               />
             </div>
         </div>
      </div>
    </div>
  );
}

export { AgentSettingsForm };