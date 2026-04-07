'use client';

import React, { useEffect, useState } from 'react';
import { Users, Server, FileText, Settings, Activity, Check, Database, Shield, RefreshCw } from 'lucide-react';
import { settingsService } from '@/services/settings.service';
import { SystemStats } from '@/types/settings';
import { toast } from 'sonner';

import { useAuth } from '@/components/providers/AuthProvider';
import { useAuthStore } from '@/store/use-auth-store';
import { useRouter } from 'next/navigation';

export default function MonitoringPage() {
  const { isLoading: authLoading } = useAuth();
  const { isAuthenticated, user } = useAuthStore();
  const router = useRouter();
  
  const [statsData, setStatsData] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    if (!authLoading && (!isAuthenticated || user?.email !== 'admin@drap.com')) {
      // AdminLayout should handle this, but for extra safety:
      return;
    }
    
    if (!authLoading && isAuthenticated) {
      fetchStats();
      const interval = setInterval(() => fetchStats(true), 30000);
      return () => clearInterval(interval);
    }
  }, [authLoading, isAuthenticated, user]);

  const fetchStats = async (isRefresh = false) => {
    if (authLoading || !isAuthenticated) return;
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    
    try {
      const res = await settingsService.getSystemStats();
      setStatsData(res.stats);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
      toast.error('获取监控数据失败');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };


  const stats = [
    { 
      title: '总用户数', 
      value: statsData?.user_count.toLocaleString() ?? '...', 
      icon: <Users className="w-6 h-6 text-blue-500" />, 
      trend: statsData ? '实时' : '-' 
    },
    { 
      title: '处理文献数', 
      value: statsData?.paper_count.toLocaleString() ?? '...', 
      icon: <FileText className="w-6 h-6 text-green-500" />, 
      trend: statsData ? '累计' : '-' 
    },
    { 
      title: '后台任务量', 
      value: statsData?.api_request_count.toLocaleString() ?? '...', 
      icon: <Server className="w-6 h-6 text-purple-500" />, 
      trend: statsData ? '待处理/执行中' : '-' 
    },
    { 
      title: '系统负载 (CPU)', 
      value: statsData ? `${statsData.system_load.toFixed(1)}%` : '...', 
      icon: <Activity className="w-6 h-6 text-orange-500" />, 
      trend: statsData?.system_load && statsData.system_load > 80 ? '高负载' : '正常' 
    },
  ];

  return (
    <>
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">系统监控</h1>
          <p className="text-gray-500 dark:text-gray-400">实时监控 DeepPaper 系统资源、背景任务与核心服务状态。</p>
        </div>
        <button 
          onClick={() => fetchStats(true)}
          disabled={refreshing}
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white px-4 py-2 rounded-xl transition-colors font-medium text-sm shadow-sm ring-1 ring-indigo-500/20"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? '正在刷新...' : '立即刷新'}
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, i) => (
          <div key={i} className="bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-slate-700">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 bg-gray-50 dark:bg-slate-900 rounded-xl">
                {stat.icon}
              </div>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full bg-gray-100 dark:bg-slate-700 text-gray-500 dark:text-gray-400 uppercase tracking-wider`}>
                {stat.trend}
              </span>
            </div>
            <div>
              <h3 className="text-3xl font-bold text-gray-900 dark:text-white mb-1">{loading && !refreshing ? '...' : stat.value}</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 font-medium">{stat.title}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Monitoring Graphs */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white dark:bg-slate-800 rounded-3xl shadow-sm border border-gray-100 dark:border-slate-700 p-8 flex flex-col min-h-[400px] relative overflow-hidden group">
             <div className="flex justify-between items-center mb-8">
               <h3 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                 <Activity className="w-6 h-6 text-indigo-500" />
                 实时资源使用
               </h3>
             </div>
             
             {/* Simple visual replacement for charts since we don't have a library yet */}
             <div className="flex-1 flex flex-col items-center justify-center relative">
                <div className="absolute inset-0 bg-gradient-to-b from-indigo-50/20 to-transparent dark:from-indigo-950/10 rounded-2xl pointer-events-none" />
                <div className="w-full max-w-md space-y-8 z-10">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm font-medium">
                      <span className="text-gray-600 dark:text-gray-400">中央处理器 (CPU)</span>
                      <span className="text-indigo-600 dark:text-indigo-400 font-bold">{statsData?.system_load.toFixed(1)}%</span>
                    </div>
                    <div className="h-3 bg-gray-100 dark:bg-slate-700 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-indigo-500 transition-all duration-1000" 
                        style={{ width: `${statsData?.system_load ?? 0}%` }}
                      ></div>
                    </div>
                  </div>
                  
                  <div className="flex flex-col items-center gap-4 text-center mt-8">
                    <p className="text-gray-400 dark:text-slate-500 text-sm max-w-xs">
                      目前正在显示核心资源的即时快照。
                      <br />
                      历史趋势图表正在对接 Prometheus 采集引擎...
                    </p>
                  </div>
                </div>
             </div>
             
             {/* Decorative Background Elements */}
             <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/5 blur-[120px] rounded-full pointer-events-none" />
             <div className="absolute bottom-0 left-0 w-64 h-64 bg-purple-500/5 blur-[120px] rounded-full pointer-events-none" />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white dark:bg-slate-800 p-6 rounded-2xl border border-gray-100 dark:border-slate-700 flex items-center gap-4 md:col-span-2">
              <div className="w-12 h-12 rounded-xl bg-green-50 dark:bg-green-900/20 flex items-center justify-center">
                <Database className="w-6 h-6 text-green-500" />
              </div>
              <div className="flex-1 flex justify-between items-center">
                <div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 font-medium">PostgreSQL 核心数据库</p>
                  <p className="text-base font-bold text-gray-900 dark:text-white">
                    {statsData?.service_statuses.find(s => s.name === 'PostgreSQL')?.status ? '连接正常' : '连接失败'}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-500 dark:text-gray-400 font-medium">响应延迟</p>
                  <p className="text-base font-bold text-indigo-600 dark:text-indigo-400">
                    {statsData?.service_statuses.find(s => s.name === 'PostgreSQL')?.latency}ms
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* System Status Sidebar */}
        <div className="space-y-6">
          <div className="bg-white dark:bg-slate-800 rounded-3xl shadow-sm border border-gray-100 dark:border-slate-700 p-6 flex flex-col relative overflow-hidden">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                服务哨兵
                <span className="w-2 h-2 rounded-full bg-green-500 animate-ping"></span>
              </h3>
              <span className="text-[10px] bg-gray-100 dark:bg-slate-700 px-2 py-0.5 rounded text-gray-500 dark:text-gray-400 uppercase">Live</span>
            </div>
            
            <div className="space-y-5">
              {statsData?.service_statuses.map((svc, i) => (
                <div key={i} className="flex justify-between items-center group">
                  <div className="flex flex-col">
                    <span className="text-sm font-semibold text-gray-700 dark:text-gray-300 group-hover:text-indigo-500 transition-colors">{svc.name}</span>
                    <span className="text-[10px] text-gray-400 dark:text-slate-500">延迟: {svc.latency}ms</span>
                  </div>
                  <span className={`flex items-center gap-1.5 text-xs font-bold ${!svc.status ? 'text-red-500' : 'text-green-500'}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${!svc.status ? 'bg-red-500' : 'bg-green-500'}`}></span>
                    {svc.status ? '正常' : '故障'}
                  </span>
                </div>
              ))}
              {(!statsData || statsData.service_statuses.length === 0) && (
                <div className="text-center py-4 text-gray-400 text-xs">正在连接核心哨兵...</div>
              )}
            </div>
            
            <div className="mt-8 pt-6 border-t border-gray-100 dark:border-slate-700 space-y-3">
              <button 
                onClick={() => fetchStats(true)}
                className="w-full py-3 rounded-2xl bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-bold transition-all shadow-lg shadow-indigo-200 dark:shadow-none hover:scale-[1.02] active:scale-[0.98]"
              >
                全系统即时健康审计
              </button>
            </div>
          </div>
          
          <div className="bg-indigo-600 rounded-3xl p-6 text-white overflow-hidden relative group">
             <div className="relative z-10">
               <h4 className="font-bold mb-1 opacity-90">系统状态摘要</h4>
               <p className="text-xs opacity-75 leading-relaxed">
                 {statsData?.service_statuses.every(s => s.status) 
                   ? '所有核心微服务均处于在线健康状态。目前暂无待处理的主动维护警报。' 
                   : '部分服务出现连接延迟或中断，请及时检查网络配置或服务集群状态。'}
               </p>
             </div>
             <Shield className="absolute -right-4 -bottom-4 w-32 h-32 opacity-10 rotate-12 group-hover:rotate-0 transition-transform duration-500" />
          </div>
        </div>
      </div>

    </>
  );
}
