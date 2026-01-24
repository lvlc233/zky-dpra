import React from 'react';
import { CheckCircle, Clock, AlertCircle } from 'lucide-react';
import { useJobProgress } from '@/hooks/use-job-progress';

interface PaperStatusBadgeProps {
  status?: string;
  jobId?: string;
  className?: string;
}

export const PaperStatusBadge: React.FC<PaperStatusBadgeProps> = ({ status: initialStatus, jobId, className = '' }) => {
  const isProcessing = (initialStatus === 'processing' || initialStatus === 'pending') && !!jobId;

  const { status: jobStatus, progress } = useJobProgress(
    isProcessing ? jobId : null,
    {
      enabled: isProcessing
    }
  );

  // If we have a real-time status update, use it, otherwise fallback to initial
  // But if initial is success/error, we usually stick to it unless jobId is active (which shouldn't happen if success)
  // Actually, if we just uploaded, initial might be 'processing' and jobId is present.
  
  const finalStatus = jobStatus || initialStatus;
  
  // Logic to determine display
  const isSuccess = finalStatus === 'success' || finalStatus === 'completed' || finalStatus === 'processed' || finalStatus === 'succeeded';
  const isError = finalStatus === 'error' || finalStatus === 'failed';
  const isRunning = finalStatus === 'processing' || finalStatus === 'pending' || finalStatus === 'queued' || finalStatus === 'running';

  if (isSuccess) {
    return (
      <div className={`flex items-center gap-1 text-green-600 dark:text-green-400 ${className}`}>
        <CheckCircle className="w-3 h-3" />
        <span>已完成</span>
      </div>
    );
  }

  if (isError) {
    return (
      <div className={`flex items-center gap-1 text-red-600 dark:text-red-400 ${className}`}>
        <AlertCircle className="w-3 h-3" />
        <span>异常</span>
      </div>
    );
  }

  if (isRunning) {
    return (
      <div className={`flex items-center gap-1 text-blue-600 dark:text-blue-400 ${className}`}>
        <Clock className="w-3 h-3 animate-spin" />
        <span>{progress > 0 ? `处理中 ${Math.round(progress)}%` : '处理中'}</span>
      </div>
    );
  }

  // Default / Unprocessed
  return (
    <div className={`flex items-center gap-1 text-gray-400 ${className}`}>
      <Clock className="w-3 h-3" />
      <span>未处理</span>
    </div>
  );
};
