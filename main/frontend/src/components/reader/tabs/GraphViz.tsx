'use client';

import React, { useRef, useEffect, useState, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { forceCollide } from 'd3-force';
import { RotateCcw, Focus, Loader2, RefreshCw } from 'lucide-react';
import { readerService } from '@/services/reader.service';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

const ForceGraph2D = dynamic(
  () => import('react-force-graph-2d').then(mod => mod.default),
  { 
    ssr: false,
    loading: () => (
      <div className="h-full flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-indigo-200 dark:border-indigo-900 border-t-indigo-600 dark:border-t-indigo-500 rounded-full animate-spin" />
      </div>
    )
  }
);

interface GraphNode {
  id: string;
  label?: string;
  text?: string;
  type?: string;
  data?: { type?: string; [key: string]: any };
}

interface GraphEdge {
  id?: string;
  source?: string;
  target?: string;
  from_id?: string;
  to_id?: string;
  label?: string;
}

interface MindMapResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
  system_notification?: string;
}

interface GraphData {
  nodes: { id: string; label: string; color: string; size: number }[];
  links: { source: string; target: string; label?: string }[];
}

export default function GraphViz({ paperId, jobStatus }: { paperId: string; jobStatus?: any }) {
  const graphRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isDark, setIsDark] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState<string | null>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    const checkDark = () => document.documentElement.classList.contains('dark');
    setIsDark(checkDark());

    const observer = new MutationObserver(() => {
      setIsDark(checkDark());
    });

    observer.observe(document.documentElement, { 
      attributes: true, 
      attributeFilter: ['class'] 
    });

    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight
        });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  const fetchData = useCallback(async (isManual = false) => {
    if (!paperId) return;
    setLoading(true);
    try {
      const res: MindMapResponse = await readerService.getMindMap(paperId);
      if (res) {
        if (res.system_notification) {
          setNotification(res.system_notification);
          setGraphData({ nodes: [], links: [] });
          if (isManual) toast.info(res.system_notification);
        } else {
          setNotification(null);
          const nodes = res.nodes.map(n => ({
            id: n.id,
            label: n.label || n.text || n.id,
            color: (n.data?.type || n.type) === 'root' ? '#4F46E5' : 
                   (n.data?.type || n.type) === 'sub' ? '#8B5CF6' : '#EC4899',
            size: (n.data?.type || n.type) === 'root' ? 12 : 8
          }));
          const links = res.edges.map(e => ({
            source: e.source || e.from_id || '',
            target: e.target || e.to_id || '',
            label: e.label
          }));
          setGraphData({ nodes, links });
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
  }, [paperId, fetchData]);

  // Auto-refresh when background job succeeds
  useEffect(() => {
    if (jobStatus?.type === 'mind_map' && jobStatus.status === 'succeeded') {
      fetchData();
    }
  }, [jobStatus?.status, jobStatus?.type, fetchData]);

  useEffect(() => {
    if (graphRef.current) {
        // 大幅增加节点间的排斥力
        graphRef.current.d3Force('charge').strength(-1500);
        // 增加连接的默认距离，并减弱连接强度让节点能推开
        graphRef.current.d3Force('link').distance(300).strength(0.1);
        // 增加碰撞力，防止节点重叠，考虑文字空间，半径加大到100
        graphRef.current.d3Force('collide', forceCollide(100));
        // 减小向心力
        graphRef.current.d3Force('center').strength(0.01);
        
        // 重启模拟，赋予足够的能量
        graphRef.current.d3Alpha(1);
        graphRef.current.d3ReheatSimulation();
    }
  }, [graphData]);

  const handleReset = () => {
    if (graphRef.current) {
      graphRef.current.zoomToFit(400);
    }
  };

  const handleFit = () => {
    if (graphRef.current) {
      graphRef.current.zoomToFit(400);
    }
  };

  const drawNode = useCallback((node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const rawLabel = node.label || node.id;
    // 只有在足够放大或者节点较少时显示全称，否则截断
    const label = rawLabel.length > 20 ? rawLabel.substring(0, 17) + '...' : rawLabel;
    
    const fontSize = Math.max(8, 12 / globalScale);
    const nodeSize = node.size || 8;
    
    // 绘制节点主体
    ctx.fillStyle = node.color || '#4F46E5';
    ctx.beginPath();
    ctx.arc(node.x, node.y, nodeSize, 0, 2 * Math.PI);
    ctx.fill();
    
    // 绘制阴影/发光效果
    ctx.shadowBlur = 5;
    ctx.shadowColor = node.color || '#4F46E5';
    
    // 只有在缩放比例大于一定程度时才显示文字，或者显示简略文字
    if (globalScale > 0.5) {
        ctx.shadowBlur = 0;
        const textWidth = ctx.measureText(label).width;
        const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2); // some padding

        // 绘制文字背景，增加可读性
        ctx.fillStyle = isDark ? 'rgba(15, 23, 42, 0.8)' : 'rgba(255, 255, 255, 0.8)';
        ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y + nodeSize + 2, bckgDimensions[0], bckgDimensions[1]);

        ctx.fillStyle = isDark ? '#e2e8f0' : '#1f2937';
        ctx.font = `${fontSize}px Sans-Serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.fillText(label, node.x, node.y + nodeSize + 4);
    }
  }, [isDark]);

  const drawLink = useCallback((link: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const fontSize = Math.max(8, 10 / globalScale);
    const startX = link.source.x;
    const startY = link.source.y;
    const endX = link.target.x;
    const endY = link.target.y;
    
    ctx.strokeStyle = isDark ? '#475569' : '#94a3b8';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(startX, startY);
    ctx.lineTo(endX, endY);
    ctx.stroke();
    
    if (link.label) {
      const midX = (startX + endX) / 2;
      const midY = (startY + endY) / 2;
      ctx.fillStyle = isDark ? '#94a3b8' : '#64748b';
      ctx.font = `${fontSize}px Sans-Serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(link.label, midX, midY);
    }
  }, [isDark]);

  if (!mounted) {
    return (
      <div className="h-full flex items-center justify-center bg-white dark:bg-slate-900">
        <div className="w-8 h-8 border-4 border-indigo-200 dark:border-indigo-900 border-t-indigo-600 dark:border-t-indigo-500 rounded-full animate-spin" />
      </div>
    );
  }

  if (loading && graphData.nodes.length === 0 && !notification) {
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
      style={{ minHeight: '400px' }}
    >
      <ForceGraph2D
        ref={graphRef}
        graphData={graphData}
        width={dimensions.width}
        height={dimensions.height}
        nodeCanvasObject={drawNode}
        linkCanvasObject={drawLink}
        nodeRelSize={6}
        linkDirectionalArrowLength={6}
        linkDirectionalArrowRelPos={1}
        linkDirectionalArrowColor={() => isDark ? '#475569' : '#94a3b8'}
        backgroundColor={isDark ? '#0f172a' : '#f8fafc'}
        cooldownTicks={100}
        onEngineStop={handleFit}
        d3AlphaDecay={0.02}
        d3VelocityDecay={0.3}
        onNodeClick={(node: any) => {
          if (graphRef.current) {
             graphRef.current.centerAt(node.x, node.y, 1000);
             graphRef.current.zoom(2, 1000);
          }
        }}
      />
      
      <div className="absolute top-4 left-4 bg-white/90 dark:bg-slate-800/90 backdrop-blur px-3 py-1.5 rounded-full shadow-sm border border-gray-200 dark:border-slate-700 text-xs font-medium text-gray-600 dark:text-gray-400">
        {graphData.nodes.length} Nodes · {graphData.links.length} Links
      </div>

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
