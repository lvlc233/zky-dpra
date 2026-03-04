import React, { useEffect } from 'react';
import { FileText, CheckCircle2, AlertCircle, Trash2, Loader2, PlayCircle } from 'lucide-react';
import { useJobProgress } from '@/hooks/use-job-progress';
import { cn } from '@/lib/utils';
import type { FileItem } from './UploadModal';

export interface UploadFileItemProps {
  item: FileItem;
  onRemove: (id: string) => void;
  onStatusChange?: (id: string, status: FileItem['status'], progress: number) => void;
}

export const UploadFileItem: React.FC<UploadFileItemProps> = ({
  item,
  onRemove,
  onStatusChange
}) => {
  const { id, file, status: initialStatus, progress: initialProgress, jobId } = item;
  
  // Use the hook if we have a jobId and we are in processing state
  // We only enable the hook if we have a jobId and the item status is 'processing'
  const isProcessing = initialStatus === 'processing' && !!jobId;
  
  const { status: jobStatus, progress: jobProgress, stage: jobStage } = useJobProgress(
    isProcessing ? jobId : null,
    {
        enabled: isProcessing
    }
  );

  // Sync hook state to parent
  useEffect(() => {
    if (isProcessing && onStatusChange) {
       // Map job status to component status
       let newStatus: FileItem['status'] = 'processing';
       
       if (jobStatus === 'succeeded' || jobStatus === 'success' as any) {
           newStatus = 'success';
       } else if (jobStatus === 'failed') {
           newStatus = 'error';
       } else {
           newStatus = 'processing';
       }
       
       // Only update if changed significantly to avoid loops, though parent should handle identity
       // We pass the job progress
       if (newStatus !== initialStatus || jobProgress !== initialProgress) {
            onStatusChange(id, newStatus, jobProgress);
       }
    }
  }, [isProcessing, jobStatus, jobProgress, initialStatus, initialProgress, id, onStatusChange]);
  
  // Determine display values
  const displayStatus = isProcessing ? 
     ((jobStatus === 'succeeded' || jobStatus === 'success' as any) ? 'success' : jobStatus === 'failed' ? 'error' : 'processing') 
     : initialStatus;
     
  const displayProgress = isProcessing ? jobProgress : initialProgress;
  const displayStage = isProcessing ? jobStage : '';

  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-slate-800/50 rounded-lg border border-gray-100 dark:border-slate-800 group transition-all hover:border-indigo-100 dark:hover:border-slate-700">
      <div className="flex items-center gap-3 flex-1 min-w-0">
        <div className={cn(
          "p-2 rounded-lg transition-colors",
          displayStatus === 'success' ? "bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400" :
          displayStatus === 'error' ? "bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400" :
          displayStatus === 'processing' ? "bg-indigo-100 text-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-400" :
          "bg-gray-100 text-gray-500 dark:bg-slate-800 dark:text-slate-400"
        )}>
          {displayStatus === 'uploading' || displayStatus === 'processing' ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : displayStatus === 'success' ? (
            <CheckCircle2 className="w-5 h-5" />
          ) : displayStatus === 'error' ? (
            <AlertCircle className="w-5 h-5" />
          ) : (
            <FileText className="w-5 h-5" />
          )}
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <p className="text-sm font-medium text-gray-700 dark:text-gray-200 truncate pr-2" title={file.name}>
              {file.name}
            </p>
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
              {displayStatus === 'success' ? '完成' : 
               displayStatus === 'error' ? '失败' : 
               `${Math.round(displayProgress)}%`}
            </span>
          </div>
          
          <div className="h-1.5 w-full bg-gray-200 dark:bg-slate-700 rounded-full overflow-hidden">
            <div 
              className={cn(
                "h-full transition-all duration-300 ease-out rounded-full",
                displayStatus === 'success' ? "bg-green-500" :
                displayStatus === 'error' ? "bg-red-500" :
                "bg-indigo-500"
              )}
              style={{ width: `${Math.max(2, displayProgress)}%` }}
            />
          </div>
          
          {displayStage && displayStatus === 'processing' && (
              <p className="text-xs text-indigo-500 mt-1 truncate animate-pulse">
                  {displayStage}...
              </p>
          )}
        </div>
      </div>

      <button 
        onClick={() => onRemove(id)}
        className="ml-3 p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md transition-colors opacity-0 group-hover:opacity-100"
      >
        <Trash2 className="w-4 h-4" />
      </button>
    </div>
  );
};
