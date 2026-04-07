import React from 'react';
import { CheckCircle, Clock, AlertCircle } from 'lucide-react';
import { useJobProgress } from '@/hooks/use-job-progress';

interface PaperStatusBadgeProps {
  status?: string;
  jobId?: string;
  latestJobType?: string;
  className?: string;
}

export const PaperStatusBadge: React.FC<PaperStatusBadgeProps> = ({ status, jobId, latestJobType, className = '' }) => {
  const isProcessingLive = (status === 'processing' || status === 'parsing' || status === 'pending') && !!jobId;
  
  const { status: jobStatus, progress, stage } = useJobProgress(
    isProcessingLive ? jobId : null,
    {
      enabled: isProcessingLive
    }
  );

  // Status mapping
  const finalStatus = (jobStatus && jobStatus !== 'pending' ? jobStatus : status) as string;
  const currentStage = stage || latestJobType;
  
  const isSuccess = finalStatus === 'completed' || finalStatus === 'processed' || finalStatus === 'succeeded' || finalStatus === 'success';
  const isError = finalStatus === 'failed' || finalStatus === 'error';
  
  // Stages
  const isParsing = currentStage === 'parsing' || currentStage === 'process_pdf' || latestJobType === 'process_pdf';
  const isEmbedding = currentStage === 'embedding' || currentStage === 'vectorizing' || currentStage === 'vectorize' || latestJobType === 'vectorize';

  const handleRetry = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!jobId) return;
    try {
      const { paperService } = await import('@/services/paper.service');
      await paperService.retryJob(jobId);
      window.location.reload(); 
    } catch (err: any) {
      console.error('Retry failed:', err);
    }
  };

  if (!status && !jobId) {
    return (
      <div className={`flex items-center gap-1 text-gray-400 ${className}`}>
        <AlertCircle className="w-3 h-3" />
        <span>未入库</span>
      </div>
    );
  }

  if (isSuccess) {
    return (
      <div className={`flex items-center gap-1 text-green-600 dark:text-green-400 ${className}`}>
        <CheckCircle className="w-3 h-3" />
        <span>已入库</span>
      </div>
    );
  }

  if (isError) {
    const errorLabel = isEmbedding ? '向量化失败' : '解析失败';
    return (
      <div className={`flex flex-col gap-1 ${className}`}>
        <div className="flex items-center gap-1 text-red-600 dark:text-red-400">
          <AlertCircle className="w-3 h-3" />
          <span>{errorLabel}</span>
        </div>
        {jobId && (
          <button 
            onClick={handleRetry}
            className="text-[10px] text-indigo-600 hover:underline text-left pl-4"
          >
            重试
          </button>
        )}
      </div>
    );
  }

  if (finalStatus === 'parsed') {
    return (
      <div className={`flex items-center gap-1 text-yellow-600 dark:text-yellow-400 ${className}`}>
        <Clock className="w-3 h-3" />
        <span>等待向量化</span>
      </div>
    );
  }

  if (finalStatus === 'parsing' || (finalStatus === 'processing' && isParsing) || finalStatus === 'pending') {
    return (
      <div className={`flex items-center gap-1 text-blue-600 dark:text-blue-400 ${className}`}>
        <Clock className="w-3 h-3 animate-spin" />
        <span>{progress > 0 && progress < 100 ? `解析中 ${Math.round(progress)}%` : '解析中'}</span>
      </div>
    );
  }

  if (finalStatus === 'processing' || isEmbedding) {
    return (
      <div className={`flex items-center gap-1 text-blue-600 dark:text-blue-400 ${className}`}>
        <Clock className="w-3 h-3 animate-spin" />
        <span>{progress > 0 ? `向量化中 ${Math.round(progress)}%` : '向量化中'}</span>
      </div>
    );
  }

  // Default
  return (
    <div className={`flex items-center gap-1 text-gray-400 ${className}`}>
      <Clock className="w-3 h-3" />
      <span>未入库</span>
    </div>
  );
};
