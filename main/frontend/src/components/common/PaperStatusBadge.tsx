import React from 'react';
import { CheckCircle, Clock, AlertCircle } from 'lucide-react';
import { useJobProgress } from '@/hooks/use-job-progress';
import { cn } from '@/lib/utils';

interface PaperStatusBadgeProps {
  status?: string;
  jobId?: string;
  className?: string;
}

export const PaperStatusBadge: React.FC<PaperStatusBadgeProps> = ({ 
  status: initialStatus, 
  jobId,
  className 
}) => {
  const isProcessing = (initialStatus === 'processing' || initialStatus === 'pending') && !!jobId;

  const { status: jobStatus, progress, stage } = useJobProgress(
    isProcessing ? jobId : null,
    { enabled: isProcessing }
  );

  // Determine current status to display
  // If we have a live job status, use it, otherwise fallback to initialStatus
  const displayStatus = isProcessing && jobStatus ? jobStatus : initialStatus;
  
  // Normalize status strings
  const normalizedStatus = React.useMemo(() => {
    if (!displayStatus) return 'unprocessed';
    if (['processed', 'success', 'succeeded', 'completed'].includes(displayStatus)) return 'success';
    if (['processing', 'running', 'queued', 'pending'].includes(displayStatus)) return 'processing';
    if (['error', 'failed'].includes(displayStatus)) return 'error';
    return 'unprocessed';
  }, [displayStatus]);

  const renderContent = () => {
    switch (normalizedStatus) {
      case 'success':
        return (
          <div className="flex items-center gap-1 text-green-600 dark:text-green-400">
            <CheckCircle className="w-3 h-3" />
            <span>已完成</span>
          </div>
        );
      case 'processing':
        return (
          <div className="flex items-center gap-1 text-blue-600 dark:text-blue-400">
            <Clock className="w-3 h-3 animate-spin" />
            <span>
                {stage === 'queued' ? '排队中' : 
                 stage === 'parsing' || stage === 'process_pdf' ? '解析中' : 
                 stage === 'embedding' || stage === 'vectorize' ? '向量化' : 
                 progress > 0 ? `${Math.round(progress)}%` : '处理中'}
            </span>
          </div>
        );
      case 'error':
        return (
          <div className="flex items-center gap-1 text-red-600 dark:text-red-400">
            <AlertCircle className="w-3 h-3" />
            <span>异常</span>
          </div>
        );
      default:
        return (
          <div className="flex items-center gap-1 text-gray-400">
            <Clock className="w-3 h-3" />
            <span>未处理</span>
          </div>
        );
    }
  };

  return (
    <div className={cn("text-xs", className)}>
      {renderContent()}
    </div>
  );
};
