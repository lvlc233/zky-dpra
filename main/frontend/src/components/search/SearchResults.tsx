'use client';

import React from 'react';
import { FileText, User, Calendar, Sparkles, AlertCircle, CheckCircle, Clock, FolderInput, Trash2, Bookmark } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { cn } from '@/lib/utils';
import { Paper } from '@/types/models';
import { format } from 'date-fns';
import * as Popover from '@radix-ui/react-popover';
import { toast } from 'sonner';
import { collectionService } from '@/services/collection.service';
import { paperService } from '@/services/paper.service';
import { PaperStatusBadge } from './PaperStatusBadge';

interface Collection {
  id: string;
  label: string;
  count: number;
}

interface SearchResultsProps {
  results: Paper[];
  className?: string;
  onToggleBookmark?: (id: string) => void;
  aiEnabled?: boolean;
  collections?: Collection[];
  onPaperUpdate?: () => void;
}

export const SearchResults: React.FC<SearchResultsProps> = ({ 
  results, 
  className, 
  onToggleBookmark, 
  aiEnabled,
  collections,
  onPaperUpdate
}) => {
  const router = useRouter();

  const handleOpenPaper = React.useCallback(
    (paperId: string) => {
      router.push(`/reader/${paperId}`);
    },
    [router]
  );

  const handleMove = async (paper: Paper, targetCollectionId: string) => {
    try {
      // If paper_id is missing (external search result), import it first
      if (!paper.paper_id) {
        if (paper.url) {
           const toastId = toast.loading('正在导入并移动论文...');
           try {
              await paperService.uploadWeb([paper.url], targetCollectionId);
              toast.success('已添加到收藏夹并开始处理', { id: toastId });
              onPaperUpdate?.();
           } catch (err: any) {
              toast.error(err.message || '导入失败', { id: toastId });
           }
           return;
        } else {
           toast.error('无法移动：缺少文件链接');
           return;
        }
      }

      await collectionService.movePaper(targetCollectionId, paper.paper_id);
      toast.success('移动成功');
      onPaperUpdate?.();
    } catch (error: any) {
      toast.error(error.message || '移动失败');
    }
  };

  const handleDelete = async (paperId: string) => {
    if (!confirm('确定要删除这篇论文吗？此操作不可恢复。')) return;
    
    try {
      await paperService.delete(paperId);
      toast.success('删除成功');
      onPaperUpdate?.();
    } catch (error: any) {
      toast.error(error.message || '删除失败');
    }
  };

  if (!results || results.length === 0) return null;

  return (
    <div className={cn("w-full max-w-6xl animate-in fade-in slide-in-from-bottom-8 duration-700", className)}>
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-gray-100 dark:border-slate-800 shadow-sm overflow-hidden">
        {/* Table Header */}
        <div className="grid grid-cols-12 gap-4 p-4 bg-gray-50/50 dark:bg-slate-800/50 border-b border-gray-100 dark:border-slate-800 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider items-center">
          <div className="col-span-3 pl-2">标题</div>
          <div className="col-span-2">作者</div>
          <div className="col-span-3">摘要</div>
          <div className="col-span-1">发布时间</div>
          <div className="col-span-1">来源</div>
          <div className="col-span-1">状态</div>
          <div className="col-span-1 text-right pr-2">操作</div>
        </div>

        {/* Table Body */}
        <div className="divide-y divide-gray-50 dark:divide-slate-800">
          {results.map((paper, index) => (
            <div 
              key={paper.paper_id || paper.url || index} 
              className="grid grid-cols-12 gap-4 p-4 hover:bg-gray-50/50 dark:hover:bg-slate-800/50 transition-colors group cursor-pointer items-start"
              onClick={() => paper.paper_id ? handleOpenPaper(paper.paper_id) : toast.info("请先添加到收藏夹以阅读")}
            >
              {/* Title Column */}
              <div className="col-span-3 pl-2">
                <div className="flex items-start gap-2">
                  <div className="mt-0.5 p-1.5 bg-indigo-50 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400 rounded-lg flex-shrink-0">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 leading-snug group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors line-clamp-2" title={paper.title}>
                      {paper.title}
                    </h3>
                    {aiEnabled && (paper as any).aiScore && (
                        <span className={cn(
                          "mt-1 inline-flex px-1.5 py-0.5 rounded text-[10px] font-bold border",
                          (paper as any).aiScore >= 90 ? "bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-400 border-green-200 dark:border-green-800" :
                          (paper as any).aiScore >= 80 ? "bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 border-blue-200 dark:border-blue-800" :
                          "bg-yellow-50 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 border-yellow-200 dark:border-yellow-800"
                        )}>
                          AI {(paper as any).aiScore}
                        </span>
                      )}
                  </div>
                </div>
              </div>

              {/* Authors Column */}
              <div className="col-span-2">
                <div className="flex flex-wrap gap-1">
                  {paper.authors && paper.authors.length > 0 ? (
                      paper.authors.slice(0, 2).map((author, i) => (
                          <div key={i} className="flex items-center gap-1 text-[10px] text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-slate-800 px-1.5 py-0.5 rounded border border-gray-100 dark:border-slate-700">
                              <User className="w-3 h-3 text-gray-400 dark:text-gray-500" />
                              <span className="truncate max-w-[80px]">{author}</span>
                          </div>
                      ))
                  ) : (
                      <span className="text-xs text-gray-400 italic">未知作者</span>
                  )}
                  {paper.authors && paper.authors.length > 2 && (
                      <span className="text-[10px] text-gray-400 dark:text-gray-500 self-center">+{paper.authors.length - 2}</span>
                  )}
                </div>
              </div>

              {/* Summary Column */}
              <div className="col-span-3">
                 <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-3 leading-relaxed" title={paper.summary || (paper as any).abstract}>
                    {paper.summary || (paper as any).abstract || "暂无摘要..."}
                 </p>
                 {aiEnabled && (paper as any).aiReason && (
                    <div className="mt-1 flex items-start gap-1 text-[10px] text-indigo-600 dark:text-indigo-400 bg-indigo-50/50 dark:bg-indigo-900/20 p-1 rounded">
                       <Sparkles className="w-3 h-3 flex-shrink-0 mt-0.5" />
                       <span className="line-clamp-2">{(paper as any).aiReason}</span>
                    </div>
                 )}
              </div>

              {/* Published At Column */}
              <div className="col-span-1 text-xs text-gray-600 dark:text-gray-400 flex items-center gap-1">
                 <Calendar className="w-3 h-3 text-gray-400" />
                 <span>
                   {paper.published_at 
                     ? format(new Date(paper.published_at), 'yyyy-MM-dd') 
                     : (paper as any).year || "-"}
                 </span>
              </div>

              {/* Source Column */}
              <div className="col-span-1">
                 {paper.source && (
                    <span className="text-[10px] px-2 py-0.5 bg-gray-100 dark:bg-slate-800 text-gray-500 dark:text-gray-400 rounded-full border border-gray-200 dark:border-slate-700 inline-block truncate max-w-full" title={paper.source}>
                        {paper.source}
                    </span>
                 )}
              </div>

              {/* Status Column */}
              <div className="col-span-1 text-xs">
                 <PaperStatusBadge status={paper.analysis_status || paper.status} jobId={paper.job_id} />
              </div>

              {/* Actions Column */}
              <div className="col-span-1 flex items-center justify-end gap-1">
                  <Popover.Root>
                    <Popover.Trigger asChild>
                      <button 
                        onClick={(e) => e.stopPropagation()}
                        className={cn(
                          "p-1.5 rounded-md transition-colors",
                          paper.is_bookmarked 
                            ? "text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/30 hover:bg-indigo-100 dark:hover:bg-indigo-900/50" 
                            : "text-gray-400 dark:text-gray-500 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/30"
                        )}
                        title={paper.is_bookmarked ? "已收藏 (点击移动)" : "添加到收藏夹"}
                      >
                        <Bookmark className={cn("w-3.5 h-3.5", paper.is_bookmarked && "fill-current")} />
                      </button>
                    </Popover.Trigger>
                    <Popover.Portal>
                      <Popover.Content className="w-48 bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-gray-100 dark:border-slate-700 p-1 z-50 animate-in zoom-in-95 duration-200" side="left" align="start" sideOffset={5}>
                        <div className="px-2 py-1.5 text-xs font-semibold text-gray-400 dark:text-gray-500 border-b border-gray-50 dark:border-slate-700 mb-1">
                          移动到...
                        </div>
                        <div className="max-h-48 overflow-y-auto">
                          {collections && collections.length > 0 ? (
                            collections.map(collection => (
                              <button
                                key={collection.id}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleMove(paper, collection.id);
                                }}
                                className="flex items-center justify-between w-full px-2 py-1.5 text-xs text-gray-600 dark:text-gray-300 hover:bg-indigo-50 dark:hover:bg-slate-700 hover:text-indigo-600 dark:hover:text-indigo-400 rounded text-left"
                              >
                                <span className="truncate">{collection.label}</span>
                                {collection.count > 0 && <span className="text-[10px] text-gray-400">{collection.count}</span>}
                              </button>
                            ))
                          ) : (
                            <div className="px-2 py-2 text-xs text-gray-400 text-center">无可用收藏夹</div>
                          )}
                        </div>
                      </Popover.Content>
                    </Popover.Portal>
                  </Popover.Root>

                  {paper.paper_id && (
                   <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(paper.paper_id!);
                    }}
                    className="p-1.5 text-gray-400 dark:text-gray-500 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md transition-colors"
                    title="删除论文"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                  )}
              </div>

            </div>
          ))}
        </div>
        
        {/* Footer */}
        <div className="p-3 border-t border-gray-100 dark:border-slate-800 bg-gray-50/30 dark:bg-slate-800/30 text-center text-xs text-gray-400 dark:text-gray-500">
          显示 {results.length} 条结果
        </div>
      </div>
    </div>
  );
};
