'use client';

import React, { useState, useEffect } from 'react';
import { ReaderNavbar } from '@/components/reader/ReaderNavbar';
import { ReaderSidebar } from '@/components/reader/ReaderSidebar';
import { ReaderRightPanel } from '@/components/reader/ReaderRightPanel';
import { PDFViewer } from '@/components/reader/PDFViewer';
import { Layer, Annotation } from '@/types/reader';
import { paperService } from '@/services/paper.service';
import { readerService } from '@/services/reader.service';
import { Paper, PaperStatusResponse, PaperJobStatusResponse } from '@/types/api';
import { toast } from 'sonner';
import { Loader2 } from 'lucide-react';
import { logger } from '@/lib/logger';

interface ReaderPageProps {
  params: {
    id: string;
  };
}

export default function ReaderPage({ params }: ReaderPageProps) {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [paper, setPaper] = useState<Paper | null>(null);
  const [status, setStatus] = useState<PaperStatusResponse | null>(null);
  const [jobStatus, setJobStatus] = useState<PaperJobStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  // Layers State
  const [layers, setLayers] = useState<Layer[]>([]);
  const [activeViewId, setActiveViewId] = useState<string>('');

  useEffect(() => {
    const init = async () => {
        try {
            // 1. Get Paper Details
            const paperData = await paperService.getById(params.id);
            setPaper(paperData);

            // 2. Get Status
            const statusData = await paperService.getStatus(params.id);
            setStatus(statusData);

            // 2.1 Get Job Status
            try {
                const jobData = await paperService.getJobStatus(params.id);
                setJobStatus(jobData);
            } catch (e) {
                logger.warn('Failed to fetch initial job status', e);
            }

            if (statusData.status === 'completed') {
                 // 3. Get Layers (Views + Annotations) if completed
                 try {
                    const views = await readerService.getViews(params.id);
                    
                    if (views.length > 0) {
                        const layersData = await Promise.all(views.map(async (view) => {
                            try {
                                const annos = await readerService.getAnnotations(params.id, view.view_id);
                                return {
                                    view_id: view.view_id,
                                    name: view.name,
                                    type: (view.name.includes('Base') || view.name.includes('原文')) ? 'system' : 'user',
                                    visible: view.enable,
                                    annotations: annos.items || [],
                                    color: undefined
                                } as Layer;
                            } catch (e) {
                                logger.warn(`Failed to fetch annotations for view ${view.view_id}`, e);
                                return {
                                    view_id: view.view_id,
                                    name: view.name,
                                    type: 'user',
                                    visible: view.enable,
                                    annotations: [],
                                } as Layer;
                            }
                        }));
                        setLayers(layersData);
                        setActiveViewId(layersData[0].view_id);
                    } else {
                         // Create default system layer if none
                         const defaultView = await readerService.createView(params.id, '原文 (Base)');
                         const defaultLayer: Layer = {
                             view_id: defaultView.view_id,
                             name: defaultView.name,
                             type: 'system',
                             visible: defaultView.enable,
                             annotations: []
                         };
                         setLayers([defaultLayer]);
                         setActiveViewId(defaultLayer.view_id);
                    }
                 } catch (e) {
                     logger.error("Failed to fetch layers", e, 'ReaderPage');
                 }
            }

        } catch (error: any) {
            logger.error("Failed to init reader:", error, 'ReaderPage');
            toast.error(error.message || "无法加载论文信息");
        } finally {
            setIsLoading(false);
        }
    };

    init();
  }, [params.id]);

  // SSE for real-time status updates
  useEffect(() => {
    // Only connect if there is an active job or paper is processing
    const jobId = jobStatus?.job_id;
    const isPaperProcessing = status && (status.status === 'pending' || status.status === 'processing');
    const isJobActive = jobStatus && (jobStatus.status === 'running' || jobStatus.status === 'queued');

    if (!jobId || (!isPaperProcessing && !isJobActive)) {
      return;
    }

    const token = localStorage.getItem('token') || '';
    if (!token) return;

    const url = paperService.getSSEUrl(jobId, token);
    logger.debug(`Connecting to SSE for job ${jobId}`, null, 'ReaderPage');

    const eventSource = new EventSource(url);

    const handleMessage = (data: any) => {
        // Update job status
        setJobStatus(prev => ({
            ...prev!,
            status: data.status,
            progress: data.progress,
            stage: data.stage,
            error: data.error,
            result: data.result
        }));

        // If status changed to success/failed, we might need to refresh paper status
        if (data.status === 'succeeded' || data.status === 'failed') {
            paperService.getStatus(params.id).then(setStatus);
            
            if (data.status === 'succeeded' && status?.status !== 'completed') {
                // Fetch layers if just completed
                readerService.getLayers(params.id).then(layersData => {
                     const fetchedLayers = (layersData as any).layers || layersData;
                     setLayers(fetchedLayers);
                     if (fetchedLayers.length > 0) {
                       setActiveViewId(fetchedLayers[0].view_id);
                     } else {
                        // Create default view
                        readerService.createView(params.id, '原文 (Base)').then(defaultView => {
                             const defaultLayer: Layer = {
                                 view_id: defaultView.view_id,
                                 name: defaultView.name,
                                 type: 'system',
                                 visible: defaultView.enable,
                                 annotations: []
                             };
                             setLayers([defaultLayer]);
                             setActiveViewId(defaultLayer.view_id);
                        });
                     }
                }).catch(e => logger.error('Failed to fetch layers', e));
            }
        }
    };

    eventSource.onopen = () => {
        logger.debug('SSE Connected', { jobId }, 'ReaderPage');
    };

    eventSource.addEventListener('progress', (e) => {
        try {
            const data = JSON.parse(e.data);
            handleMessage(data);
        } catch (err) {
            logger.error('SSE Parse Error', err);
        }
    });

    eventSource.addEventListener('end', (e) => {
        try {
            const data = JSON.parse(e.data);
            handleMessage(data);
            eventSource.close();
        } catch (err) {
            logger.error('SSE Parse Error', err);
        }
    });

    eventSource.onerror = (e) => {
        logger.error('SSE Error', e);
        eventSource.close();
        // Fallback to polling if SSE fails
        // Or implement retry logic
    };

    return () => {
        eventSource.close();
    };
  }, [jobStatus?.job_id, params.id]); // Re-connect if job_id changes

  // Fallback Polling (keep it simple, 5s interval)
  useEffect(() => {
      const isPaperProcessing = status && (status.status === 'pending' || status.status === 'processing');
      const isJobActive = jobStatus && (jobStatus.status === 'running' || jobStatus.status === 'queued');
      
      if (isPaperProcessing || isJobActive) {
          const interval = setInterval(async () => {
             // ... polling logic ...
             // Simplified polling as backup
             try {
                  const newStatus = await paperService.getStatus(params.id);
                  setStatus(newStatus);
                  const newJobStatus = await paperService.getJobStatus(params.id);
                  setJobStatus(newJobStatus);
             } catch (e) {
                 // ignore
             }
          }, 5000); // Slower polling
          return () => clearInterval(interval);
      }
  }, [status?.status, jobStatus?.status, params.id]);


  // Layer Handlers
  // Views/Layers management removed from UI but kept logic for backend compatibility
  // Only Annotation handlers remain

  const handleAddAnnotation = async (annotation: Annotation) => {
      try {
          const { annotation_id, ...data } = annotation;
          await readerService.addAnnotation(params.id, activeViewId, data);
          
          // Re-fetch to get the real ID if needed, or just use optimistic with generated ID?
          // The backend might assign a different ID. Ideally we should get the response.
          // But addAnnotation returns void in current service definition.
          // Let's assume for now we might need to refresh or just keep using the generated ID if backend accepts it?
          // Actually, service.addAnnotation takes Omit<Annotation, 'annotation_id'>.
          // This implies backend generates ID.
          // If backend generates ID, we should update our local state with that ID.
          // But `addAnnotation` returns void. This is a potential issue.
          // Let's check reader.service.ts again. It returns void.
          // Recommendation: Update reader.service.ts to return the created annotation or at least the ID.
          // For now, I will use the generated ID and hope for the best, or trigger a refresh?
          // Refreshing is safer.
          
          const annos = await readerService.getAnnotations(params.id, activeViewId);
          setLayers(layers.map(l => {
            if (l.view_id === activeViewId) {
                return { ...l, annotations: annos.items || [] };
            }
            return l;
          }));
      } catch (e) {
          toast.error("添加标注失败");
      }
  };

  const handleUpdateAnnotation = async (annotation: Annotation) => {
    // Optimistic
    setLayers(layers.map(l => {
      if (l.annotations.some(a => a.annotation_id === annotation.annotation_id)) {
        return {
          ...l,
          annotations: l.annotations.map(a => a.annotation_id === annotation.annotation_id ? annotation : a)
        };
      }
      return l;
    }));

    try {
        const { annotation_id, ...data } = annotation;
        // We need to find which view this annotation belongs to.
        // It should be the active view usually, or the view it belongs to.
        const layer = layers.find(l => l.annotations.some(a => a.annotation_id === annotation_id));
        if (layer) {
            await readerService.updateAnnotation(params.id, layer.view_id, annotation_id, data);
        }
    } catch (e) {
        toast.error("更新标注失败");
        // Revert? Complex to revert without deep clone or history.
    }
  };

  const handleDeleteAnnotation = async (annotationId: string) => {
    // Optimistic
    const layer = layers.find(l => l.annotations.some(a => a.annotation_id === annotationId));
    
    setLayers(layers.map(l => ({
      ...l,
      annotations: l.annotations.filter(a => a.annotation_id !== annotationId)
    })));

    if (layer) {
        try {
            await readerService.deleteAnnotation(params.id, layer.view_id, annotationId);
        } catch (e) {
             toast.error("删除标注失败");
             // Revert logic needed ideally
        }
    }
  };
  
  if (isLoading) {
      return (
          <div className="h-screen w-full flex items-center justify-center bg-gray-50 dark:bg-slate-950">
              <div className="text-center">
                  <Loader2 className="w-10 h-10 animate-spin text-indigo-600 mx-auto mb-4" />
                  <p className="text-gray-600 dark:text-gray-400">正在加载论文...</p>
              </div>
          </div>
      );
  }

  if (!paper || !status) {
       return (
          <div className="h-screen w-full flex items-center justify-center bg-gray-50 dark:bg-slate-950">
              <div className="text-center">
                  <p className="text-red-600 dark:text-red-400">未找到论文信息</p>
              </div>
          </div>
      );
  }

  /*
   * 变更记录：FrontendAgent(react)｜2026-01-17 21:36:00
   * 使用位置：ReaderPage（src/app/reader/[id]/page.tsx），用于阅读页主渲染分支。
   * 实现说明：解析状态为 pending/processing 时，只要后端已提供 file_url（来自 status 或 paper），就直接渲染 PDF；
   *           同时以非阻塞的方式展示解析进度提示，避免“必须等 AI 解析完才能看论文”。
   */
  const pdfUrl = status.file_url || paper.file_url || '';
  const isProcessing = status.status === 'processing' || status.status === 'pending';
  const shouldBlockForProcessing = isProcessing && !pdfUrl;

  if (shouldBlockForProcessing) {
    // Stage Mapping
    let stageText = "正在解析...";
    if (jobStatus?.stage) {
        switch (jobStatus.stage) {
            case 'starting': stageText = "正在启动解析任务..."; break;
            case 'parsing_text': stageText = "正在提取文本内容..."; break;
            case 'extracting_metadata': stageText = "正在分析元数据与目录..."; break;
            case 'saving_to_db': stageText = "正在保存解析结果..."; break;
            case 'finished': stageText = "解析完成，即将跳转..."; break;
            case 'failed': stageText = "解析失败"; break;
            default: stageText = `正在处理: ${jobStatus.stage}`;
        }
    }

    return (
      <div className="h-screen w-full flex items-center justify-center bg-gray-50 dark:bg-slate-950">
        <div className="text-center max-w-md p-6 bg-white dark:bg-slate-900 rounded-xl shadow-lg border border-gray-100 dark:border-slate-800">
          <Loader2 className="w-12 h-12 animate-spin text-indigo-600 mx-auto mb-6" />
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">正在解析论文</h2>
          <p className="text-gray-500 dark:text-gray-400 mb-6">{stageText}</p>

          <div className="w-full bg-gray-100 dark:bg-slate-800 rounded-full h-2 mb-2">
            <div
              className="bg-indigo-600 h-2 rounded-full transition-all duration-500"
              style={{ width: `${jobStatus?.progress || status.progress || 0}%` }}
            ></div>
          </div>
          <p className="text-xs text-gray-400 dark:text-gray-500 text-right">{jobStatus?.progress || status.progress || 0}%</p>
          
          {/* Debug Info (Optional, can be hidden) */}
          <div className="mt-4 p-2 bg-gray-50 dark:bg-slate-800 rounded text-left text-xs text-gray-400 font-mono overflow-x-auto">
              <p>Job ID: {jobStatus?.job_id || 'Waiting...'}</p>
              <p>Status: {jobStatus?.status || status.status}</p>
              <p>Stage: {jobStatus?.stage || 'unknown'}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!pdfUrl) {
    return (
      <div className="h-screen w-full flex items-center justify-center bg-gray-50 dark:bg-slate-950">
        <div className="text-center max-w-md p-6 bg-white dark:bg-slate-900 rounded-xl shadow-lg border border-gray-100 dark:border-slate-800">
          <p className="text-gray-900 dark:text-white font-medium">未找到论文 PDF 资源</p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">请稍后重试，或返回重新打开该论文。</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-full flex flex-col bg-white dark:bg-slate-950 overflow-hidden">
      {/* 1. Top Navbar */}
      <ReaderNavbar 
        title={`Paper: ${paper.title}`}
        isBookmarked={!!paper.is_bookmarked}
        onSearch={setSearchQuery}
      />

      {/* 2. Main Workspace (Flex Row) */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar (TOC) */}
        <ReaderSidebar 
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
          toc={status.toc || []}
          isLoading={isProcessing}
          loadingStage={jobStatus?.stage}
          progress={jobStatus?.progress || status.progress}
          onNavigate={(page) => setCurrentPage(page)}
        />

        {/* Center PDF Viewer */}
        <div className="flex-1 h-full relative">
          <PDFViewer
            url={pdfUrl}
            className="h-full"
            initialPage={currentPage}
            onPageChange={setCurrentPage}
            searchQuery={searchQuery}
            layers={layers}
            activeViewId={activeViewId}
            onAddAnnotation={activeViewId ? handleAddAnnotation : undefined}
            onUpdateAnnotation={handleUpdateAnnotation}
            onDeleteAnnotation={handleDeleteAnnotation}
          />
        </div>

        {/* Right AI Panel */}
        <ReaderRightPanel 
          paperId={params.id} 
          isProcessing={isProcessing} 
          loadingStage={jobStatus?.stage}
          progress={jobStatus?.progress}
          jobStatus={jobStatus}
        />
      </div>
    </div>
  );
}
