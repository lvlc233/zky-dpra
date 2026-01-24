'use client';

import React from 'react';
import dynamic from 'next/dynamic';

const GraphViz = dynamic(() => import('./GraphViz'), {
  ssr: false,
  loading: () => (
    <div className="h-full flex items-center justify-center bg-white dark:bg-slate-900">
      <div className="flex flex-col items-center gap-2">
        <div className="w-8 h-8 border-4 border-indigo-200 dark:border-indigo-900 border-t-indigo-600 dark:border-t-indigo-500 rounded-full animate-spin" />
        <span className="text-sm text-gray-500 dark:text-gray-400">加载图谱组件...</span>
      </div>
    </div>
  )
});

interface GraphTabProps {
  paperId: string;
  isProcessing?: boolean;
  loadingStage?: string;
  progress?: number;
}

export const GraphTab: React.FC<GraphTabProps> = ({ paperId, isProcessing, loadingStage, progress }) => {
  if (isProcessing) {
    const message = loadingStage?.includes('graph') ? '正在生成知识图谱...' : '正在解析论文...';
    return (
      <div className="h-full flex items-center justify-center bg-white dark:bg-slate-900">
        <div className="flex flex-col items-center gap-2">
          <div className="w-8 h-8 border-4 border-indigo-200 dark:border-indigo-900 border-t-indigo-600 dark:border-t-indigo-500 rounded-full animate-spin" />
          <span className="text-sm text-gray-500 dark:text-gray-400">{message}</span>
          {progress && <span className="text-xs text-gray-400">{progress}%</span>}
        </div>
      </div>
    );
  }
  return <GraphViz paperId={paperId} />;
};
