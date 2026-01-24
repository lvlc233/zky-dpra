'use client';

import React, { useState, useRef, useCallback } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { X, UploadCloud, FileText, Trash2, CheckCircle2, AlertCircle, Link as LinkIcon, FileUp } from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import { paperService } from '@/services/paper.service';
import { logger } from '@/lib/logger';

import { useUploadStore } from '@/store/upload.store';

interface UploadModalProps {
  // Compatibility props, optional now
  isOpen?: boolean;
  onClose?: () => void;
  onUploadSuccess?: () => void;
}

export interface FileItem {
  id: string;
  file: File;
  status: 'pending' | 'uploading' | 'success' | 'error' | 'processing';
  progress: number;
  jobId?: string;
}

type UploadTab = 'local' | 'web';

export const UploadModal: React.FC<UploadModalProps> = (props) => {
  const uploadStore = useUploadStore();
  const [activeTab, setActiveTab] = useState<UploadTab>('local');
  
  // Use store state if props are not provided, otherwise use props (for backward compatibility if needed)
  const isControlled = props.isOpen !== undefined;
  const show = isControlled ? props.isOpen : uploadStore.isOpen;
  
  const handleClose = useCallback(() => {
    if (isControlled && props.onClose) {
        props.onClose();
    } else {
        uploadStore.close();
    }
    // Reset state on close
    setTimeout(() => {
        setFiles([]);
        setWebUrls('');
        setActiveTab('local');
    }, 300);
  }, [isControlled, props, uploadStore]);

  const handleSuccess = () => {
      // Trigger global success mechanism
      uploadStore.triggerSuccess();
      
      // If props provided, also call it (legacy support)
      if (isControlled && props.onUploadSuccess) {
          props.onUploadSuccess();
      }
  };

  const [files, setFiles] = useState<FileItem[]>([]);
  const [webUrls, setWebUrls] = useState('');
  const [isWebUploading, setIsWebUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files) {
      handleFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleFiles = (newFiles: File[]) => {
    const validFiles = newFiles.filter(file => file.type === 'application/pdf');
    
    if (validFiles.length < newFiles.length) {
        toast.warning("已过滤非 PDF 文件");
    }

    const newFileItems: FileItem[] = validFiles.map(file => ({
      id: Math.random().toString(36).substring(7),
      file,
      status: 'pending',
      progress: 0
    }));

    setFiles(prev => [...prev, ...newFileItems]);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(Array.from(e.target.files));
    }
    // Reset input so the same file can be selected again if needed
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id));
  };

  const uploadLocalFiles = async () => {
    const pendingFiles = files.filter(f => f.status === 'pending');
    
    if (pendingFiles.length === 0) return;

    // Mark as uploading
    setFiles(prev => prev.map(f => 
      f.status === 'pending' ? { ...f, status: 'uploading' } : f
    ));

    // Upload each file
    // Note: Ideally we should use Promise.all or a queue, but sequential is safer for progress tracking per file for now
    // Or we can modify paperService to accept multiple files at once which it does (uploadLocal takes files[])
    // But our UI shows per-file progress.
    // Let's stick to per-file upload for better UI feedback, although less efficient network-wise if many small files.
    // Wait, paperService.uploadLocal takes files: File[]. It uploads all at once.
    // If we use that, we get one success/fail for the batch.
    // Let's try to upload one by one to keep the current UI logic working easily, 
    // OR we can group them. 
    // Given the current UI structure `files.map`, let's do one by one for granular control.
    // Actually paperService.uploadLocal returns PapersUploadResponse[].
    
    // For better UX, let's upload one by one using a modified service call or just loop.
    // Since service.uploadLocal takes File[], we can pass [file].
    
    for (const fileItem of pendingFiles) {
        try {
            const responses = await paperService.uploadLocal([fileItem.file], uploadStore.collectionId);
            const response = responses[0];

            setFiles(prev => prev.map(f => 
                f.id === fileItem.id ? { 
                    ...f, 
                    status: response?.status === 'processing' ? 'processing' : 'success', 
                    progress: response?.status === 'processing' ? 0 : 100,
                    jobId: response?.job_id
                } : f
            ));
            
        } catch (error: any) {
            logger.error('Upload failed:', error, 'UploadModal');
            setFiles(prev => prev.map(f => 
                f.id === fileItem.id ? { ...f, status: 'error', progress: 0 } : f
            ));
            toast.error(`文件 ${fileItem.file.name} 上传失败: ${error.message || '未知错误'}`);
        }
    }
    
    // Check if any success
    if (files.some(f => f.status === 'success' || pendingFiles.some(pf => pf.id === f.id))) {
         handleSuccess();
         toast.success("上传处理完成");
    }
  };

  const uploadWebUrls = async () => {
      if (!webUrls.trim()) return;
      
      const urls = webUrls.split('\n').map(u => u.trim()).filter(u => u);
      if (urls.length === 0) return;

      setIsWebUploading(true);
      
      // Create mock file items for the URLs to track progress
      const newFileItems: FileItem[] = urls.map(url => ({
          id: Math.random().toString(36).substring(7),
          file: { name: url, size: 0, type: 'application/pdf' } as File,
          status: 'uploading',
          progress: 0
      }));

      // Add to list immediately
      setFiles(prev => [...prev, ...newFileItems]);
      // Switch to local tab to show the file list
      setActiveTab('local');
      setWebUrls('');

      try {
          const responses = await paperService.uploadWeb(urls, uploadStore.collectionId);
          
          // Update items with jobId from response
          setFiles(prev => {
              const updatedItems = [...prev];
              newFileItems.forEach((item, index) => {
                  const response = responses[index];
                  const itemIndex = updatedItems.findIndex(f => f.id === item.id);
                  
                  if (itemIndex !== -1) {
                      if (response && response.status !== 'failed') {
                          updatedItems[itemIndex] = {
                              ...updatedItems[itemIndex],
                              status: 'processing',
                              jobId: response.job_id
                          };
                      } else {
                          updatedItems[itemIndex] = {
                              ...updatedItems[itemIndex],
                              status: 'error'
                          };
                      }
                  }
              });
              return updatedItems;
          });
          
          const successCount = responses.filter(r => r.status !== 'failed').length;
          const failCount = responses.length - successCount;

          if (successCount > 0) {
            toast.success(`成功提交 ${successCount} 个链接进行处理`);
          }
          
          if (failCount > 0) {
            toast.error(`${failCount} 个链接提交失败`);
          }

          // Don't close immediately so user can see progress
          handleSuccess();
      } catch (error: any) {
          logger.error('Web upload failed:', error, 'UploadModal');
          toast.error(error.message || "链接上传失败");
          
          // Mark all new items as error
          setFiles(prev => prev.map(f => 
              newFileItems.some(nf => nf.id === f.id) 
                  ? { ...f, status: 'error' } 
                  : f
          ));
      } finally {
          setIsWebUploading(false);
      }
  };

  return (
    <Dialog.Root open={show} onOpenChange={(open) => !open && handleClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 animate-in fade-in" />
        <Dialog.Content className="fixed left-[50%] top-[50%] z-50 w-full max-w-lg translate-x-[-50%] translate-y-[-50%] bg-white dark:bg-slate-900 rounded-xl shadow-2xl outline-none animate-in fade-in zoom-in-95 duration-200 overflow-hidden">
          
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-100 dark:border-slate-800 bg-gray-50/50 dark:bg-slate-800/50">
            <Dialog.Title className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              上传论文
            </Dialog.Title>
            <Dialog.Close asChild>
              <button onClick={handleClose} className="p-2 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 rounded-full hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors">
                <X className="w-5 h-5" />
              </button>
            </Dialog.Close>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-gray-100 dark:border-slate-800">
              <button 
                onClick={() => setActiveTab('local')}
                className={cn(
                    "flex-1 py-3 text-sm font-medium transition-colors relative",
                    activeTab === 'local' ? "text-indigo-600 dark:text-indigo-400" : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
                )}
              >
                <div className="flex items-center justify-center gap-2">
                    <FileUp className="w-4 h-4" />
                    本地上传
                </div>
                {activeTab === 'local' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-600 dark:bg-indigo-400" />}
              </button>
              <button 
                onClick={() => setActiveTab('web')}
                className={cn(
                    "flex-1 py-3 text-sm font-medium transition-colors relative",
                    activeTab === 'web' ? "text-indigo-600 dark:text-indigo-400" : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
                )}
              >
                <div className="flex items-center justify-center gap-2">
                    <LinkIcon className="w-4 h-4" />
                    网络链接
                </div>
                {activeTab === 'web' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-600 dark:bg-indigo-400" />}
              </button>
          </div>

          {/* Content */}
          <div className="p-6">
            {activeTab === 'local' ? (
                <>
                    <div
                        onClick={() => fileInputRef.current?.click()}
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        onDrop={handleDrop}
                        className={cn(
                        "flex flex-col items-center justify-center w-full h-48 rounded-xl border-2 border-dashed transition-all duration-200 cursor-pointer",
                        isDragging 
                            ? "border-indigo-500 bg-indigo-50/50 dark:bg-indigo-900/20" 
                            : "border-gray-200 dark:border-slate-700 bg-gray-50/50 dark:bg-slate-800/30 hover:bg-gray-50 dark:hover:bg-slate-800/50 hover:border-gray-300 dark:hover:border-slate-600"
                        )}
                    >
                        <input 
                        ref={fileInputRef}
                        type="file" 
                        accept=".pdf"
                        multiple 
                        className="hidden" 
                        onChange={handleFileSelect}
                        />
                        <div className="flex flex-col items-center justify-center pt-5 pb-6">
                        <div className={cn(
                            "w-12 h-12 rounded-full flex items-center justify-center mb-3 transition-colors",
                            isDragging ? "bg-indigo-100 text-indigo-600 dark:bg-indigo-900 dark:text-indigo-400" : "bg-gray-100 dark:bg-slate-800 text-gray-400 dark:text-gray-500"
                        )}>
                            <UploadCloud className="w-6 h-6" />
                        </div>
                        <p className="mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">
                            <span className="text-indigo-600 dark:text-indigo-400 hover:underline">点击上传</span> 或拖拽文件到这里
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">支持 PDF 格式 (最大 20MB)</p>
                        </div>
                    </div>

                    {files.length > 0 && (
                        <div className="mt-4 space-y-3 max-h-[200px] overflow-y-auto pr-2 custom-scrollbar">
                        {files.map((file) => (
                            <UploadFileItem 
                                key={file.id} 
                                item={file} 
                                onRemove={removeFile}
                                onStatusChange={(id, status, progress) => {
                                    setFiles(prev => prev.map(f => f.id === id ? { ...f, status, progress } : f));
                                }}
                            />
                        ))}
                        </div>
                    )}
                </>
            ) : (
                <div className="flex flex-col gap-4">
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-700">
                            PDF 链接地址
                        </label>
                        <textarea
                            value={webUrls}
                            onChange={(e) => setWebUrls(e.target.value)}
                            placeholder={`https://arxiv.org/pdf/2401.12345.pdf\nhttps://example.com/paper.pdf`}
                            className="w-full h-48 p-3 rounded-xl border border-gray-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none resize-none text-sm leading-relaxed"
                        />
                        <p className="text-xs text-gray-500">
                            每行一个链接，支持 arXiv 等常见学术网站的 PDF 链接。
                        </p>
                    </div>
                </div>
            )}
          </div>

          <div className="p-6 pt-2 flex justify-end gap-3 border-t border-gray-50">
            <button
              onClick={handleClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              取消
            </button>
            
            {activeTab === 'local' ? (
                <button
                onClick={uploadLocalFiles}
                disabled={files.length === 0 || files.every(f => f.status === 'success') || files.some(f => f.status === 'uploading')}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg shadow-sm shadow-indigo-200 transition-all"
                >
                {files.some(f => f.status === 'uploading') ? '上传中...' : '开始上传'}
                </button>
            ) : (
                <button
                onClick={uploadWebUrls}
                disabled={!webUrls.trim() || isWebUploading}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg shadow-sm shadow-indigo-200 transition-all"
                >
                {isWebUploading ? '处理中...' : '提交链接'}
                </button>
            )}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};
