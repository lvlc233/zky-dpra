'use client';

import React, { useRef, useEffect, useState, useCallback } from 'react';
import { GraphCanvas, GraphNode, GraphEdge, GraphCanvasRef } from 'reagraph';
import { RotateCcw, Focus, Loader2, RefreshCw } from 'lucide-react';
import { readerService } from '@/services/reader.service';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

// ----------------------------------------------------------------------
// Component
// ----------------------------------------------------------------------

interface GraphVizProps {
  paperId: string;
}

export default function GraphViz({ paperId }: GraphVizProps) {
  // 使用 useRef 确保容器引用
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<GraphCanvasRef | null>(null);
  const [isDark, setIsDark] = useState(false);
  
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState<string | null>(null);

  const fetchData = useCallback(async (isManual = false) => {
      if (!paperId) return;
      setLoading(true);
      try {
          const res = await readerService.getMindMap(paperId);
          if (res) {
              // 优先处理系统通知
              if (res.system_notification) {
                  setNotification(res.system_notification);
                  // 如果有通知，通常意味着正在生成，数据可能为空或不完整
                  // 但如果也有节点，我们还是可以显示（取决于业务逻辑，这里假设生成中就没有图）
                  setNodes([]);
                  setEdges([]);
                  if (isManual) toast.info(res.system_notification);
              } else {
                  setNotification(null);
                  setNodes(res.nodes.map(n => ({
                      id: n.id,
                      label: n.label || n.text, // Support both label and text
                      fill: (n.data?.type || n.type) === 'root' ? '#4F46E5' : ((n.data?.type || n.type) === 'sub' ? '#8B5CF6' : '#EC4899'),
                      size: (n.data?.type || n.type) === 'root' ? 25 : 15
                  })));
                  setEdges(res.edges.map(e => ({
                      id: e.id || `${e.source || e.from_id}-${e.target || e.to_id}`,
                      source: e.source || e.from_id,
                      target: e.target || e.to_id,
                      label: e.label
                  })));
                  if (isManual) toast.success("知识图谱已更新");
              }
          }
      } catch (error) {
          console.error("Failed to fetch mind map", error);
          if (isManual) toast.error("获取知识图谱失败");
      } finally {
          setLoading(false);
      }
  }, [paperId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    // Initial check
    const checkDark = () => document.documentElement.classList.contains('dark');
    setIsDark(checkDark());

    // Observe class changes on html element
    const observer = new MutationObserver(() => {
      setIsDark(checkDark());
    });

    observer.observe(document.documentElement, { 
      attributes: true, 
      attributeFilter: ['class'] 
    });

    return () => observer.disconnect();
  }, []);

  const handleReset = () => {
    if (graphRef.current) {
      graphRef.current.centerGraph();
    }
  };

  const handleFit = () => {
    if (graphRef.current) {
      graphRef.current.fitNodesInView();
    }
  };

  const theme = {
    canvas: { background: 'transparent' },
    node: { 
      fill: '#4F46E5',
      activeFill: '#4338ca',
      opacity: 1,
      selectedOpacity: 1,
      inactiveOpacity: 0.2,
      label: { 
        color: isDark ? '#e2e8f0' : '#1f2937', 
        stroke: isDark ? '#0f172a' : '#ffffff', 
        activeColor: isDark ? '#f8fafc' : '#1f2937' 
      }
    },
    edge: { 
      fill: isDark ? '#475569' : '#94a3b8',
      activeFill: isDark ? '#94a3b8' : '#64748b',
      opacity: 1,
      selectedOpacity: 1,
      inactiveOpacity: 0.2,
      label: { 
        color: isDark ? '#94a3b8' : '#64748b', 
        stroke: isDark ? '#0f172a' : '#ffffff', 
        activeColor: isDark ? '#cbd5e1' : '#64748b' 
      }
    },
    arrow: { 
      fill: isDark ? '#475569' : '#94a3b8', 
      activeFill: isDark ? '#94a3b8' : '#64748b' 
    },
    ring: { fill: '#818cf8', activeFill: '#4f46e5' },
    lasso: { 
      border: isDark ? '1px solid #94a3b8' : '1px solid #5c5c5c', 
      background: 'rgba(75, 160, 255, 0.1)' 
    }
  };

  if (loading && nodes.length === 0 && !notification) {
      return (
        <div className="h-full flex items-center justify-center bg-white dark:bg-slate-900">
            <div className="flex flex-col items-center gap-2">
            <div className="w-8 h-8 border-4 border-indigo-200 dark:border-indigo-900 border-t-indigo-600 dark:border-t-indigo-500 rounded-full animate-spin" />
            <span className="text-sm text-gray-500 dark:text-gray-400">正在加载知识图谱...</span>
            </div>
        </div>
      );
  }

  if (notification) {
      return (
        <div className="h-full flex flex-col items-center justify-center bg-white dark:bg-slate-900 p-8 text-center space-y-4">
             <div className="w-12 h-12 bg-indigo-50 dark:bg-indigo-900/20 rounded-full flex items-center justify-center">
                 <Loader2 className="w-6 h-6 text-indigo-600 dark:text-indigo-400 animate-spin" />
             </div>
             <div className="space-y-2">
                 <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">生成中</h3>
                 <p className="text-gray-500 dark:text-gray-400 max-w-sm">{notification}</p>
             </div>
             <button 
                onClick={() => fetchData(true)}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm transition-colors flex items-center gap-2"
             >
                 <RefreshCw className="w-4 h-4" />
                 刷新状态
             </button>
        </div>
      );
  }

  return (
    <div 
      ref={containerRef}
      className="w-full h-full relative bg-gray-50 dark:bg-slate-900"
      style={{ minHeight: '400px' }} // 确保最小高度，防止塌缩
    >
      <GraphCanvas
        ref={graphRef}
        nodes={nodes}
        edges={edges}
        layoutType="forceDirected2d"
        labelType="all"
        sizingType="centrality"
        cameraMode="rotate"
        // 显式设置背景透明，以便看到底色
        theme={theme}
      />
      
      {/* 简单的悬浮统计 */}
      <div className="absolute top-4 left-4 bg-white/90 dark:bg-slate-800/90 backdrop-blur px-3 py-1.5 rounded-full shadow-sm border border-gray-200 dark:border-slate-700 text-xs font-medium text-gray-600 dark:text-gray-400">
        {nodes.length} Nodes · {edges.length} Edges
      </div>

      {/* 控制按钮组 */}
      <div className="absolute top-4 right-4 flex gap-2">
        <button 
          onClick={() => fetchData(true)}
          className="p-2 bg-white/90 dark:bg-slate-800/90 backdrop-blur rounded-lg shadow-sm border border-gray-200 dark:border-slate-700 text-gray-600 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/50 transition-colors"
          title="刷新数据"
        >
            <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
        </button>
        <button
          onClick={handleFit}
          className="p-2 bg-white/90 dark:bg-slate-800/90 backdrop-blur rounded-lg shadow-sm border border-gray-200 dark:border-slate-700 text-gray-600 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/50 transition-colors"
          title="适应视图"
        >
          <Focus className="w-4 h-4" />
        </button>
        <button
          onClick={handleReset}
          className="p-2 bg-white/90 dark:bg-slate-800/90 backdrop-blur rounded-lg shadow-sm border border-gray-200 dark:border-slate-700 text-gray-600 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/50 transition-colors"
          title="重置视角"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
