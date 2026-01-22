'use client';

import React, { useState, useCallback } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { X, Link as LinkIcon } from 'lucide-react';
import { toast } from 'sonner';
import { paperService } from '@/services/paper.service';
import { logger } from '@/lib/logger';
import { useUploadStore } from '@/store/upload.store';

interface UploadModalProps {
  // Compatibility props
  isOpen?: boolean;
  onClose?: () => void;
  onUploadSuccess?: () => void;
}

/**
 * UploadModal (Simplified / Web Only)
 * 
 * 阉割版上传组件：仅支持 Web URL 上传。
 * 完整版（包含本地上传）已备份至 UploadModalFull.tsx
 */
export const UploadModal: React.FC<UploadModalProps> = (props) => {
  const uploadStore = useUploadStore();
  
  // Use store state if props are not provided
  const isControlled = props.isOpen !== undefined;
  const show = isControlled ? props.isOpen : uploadStore.isOpen;
  
  const [webUrls, setWebUrls] = useState('');
  const [isWebUploading, setIsWebUploading] = useState(false);

  const handleClose = useCallback(() => {
    if (isControlled && props.onClose) {
        props.onClose();
    } else {
        uploadStore.close();
    }
    // Reset state on close
    setTimeout(() => {
        setWebUrls('');
    }, 300);
  }, [isControlled, props, uploadStore]);

  const handleSuccess = () => {
      uploadStore.triggerSuccess();
      if (isControlled && props.onUploadSuccess) {
          props.onUploadSuccess();
      }
  };

  const uploadWebUrls = async () => {
      if (!webUrls.trim()) return;
      
      const urls = webUrls.split('\n').map(u => u.trim()).filter(u => u);
      if (urls.length === 0) return;

      setIsWebUploading(true);
      try {
          await paperService.uploadWeb(urls, uploadStore.collectionId);
          toast.success(`成功提交 ${urls.length} 个链接进行处理`);
          setWebUrls('');
          handleSuccess();
          handleClose();
      } catch (error: any) {
          logger.error('Web upload failed:', error, 'UploadModal');
          toast.error(error.message || "链接上传失败");
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
            <Dialog.Title className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
              <LinkIcon className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              上传论文链接
            </Dialog.Title>
            <Dialog.Close asChild>
              <button onClick={handleClose} className="p-2 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 rounded-full hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors">
                <X className="w-5 h-5" />
              </button>
            </Dialog.Close>
          </div>

          {/* Content - Web Only */}
          <div className="p-6">
             <div className="flex flex-col gap-4">
                <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        PDF 链接地址
                    </label>
                    <textarea
                        value={webUrls}
                        onChange={(e) => setWebUrls(e.target.value)}
                        placeholder={`https://arxiv.org/pdf/2401.12345.pdf\nhttps://example.com/paper.pdf`}
                        className="w-full h-48 p-3 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-gray-900 dark:text-gray-100 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none resize-none text-sm leading-relaxed"
                    />
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                        每行一个链接，支持 arXiv 等常见学术网站的 PDF 链接。
                    </p>
                </div>
            </div>
          </div>

          <div className="p-6 pt-2 flex justify-end gap-3 border-t border-gray-50 dark:border-slate-800">
            <button
              onClick={handleClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
            >
              取消
            </button>
            
            <button
                onClick={uploadWebUrls}
                disabled={!webUrls.trim() || isWebUploading}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg shadow-sm shadow-indigo-200 dark:shadow-none transition-all"
            >
                {isWebUploading ? '处理中...' : '提交链接'}
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};
