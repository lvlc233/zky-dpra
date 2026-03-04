import { useState, useEffect, useRef, useCallback } from 'react';
import { toast } from 'sonner';
import { logger } from '@/lib/logger';
import { paperService } from '@/services/paper.service';
import { useAuthStore } from '@/store/use-auth-store';

export interface JobProgressState {
  status: 'pending' | 'queued' | 'running' | 'succeeded' | 'failed';
  progress: number;
  stage: string;
  result?: any;
  error?: string;
}

interface UseJobProgressOptions {
  onSucceeded?: (result: any) => void;
  onFailed?: (error: string) => void;
  enabled?: boolean;
}

export const useJobProgress = (jobId: string | null, options: UseJobProgressOptions = {}) => {
  const [state, setState] = useState<JobProgressState>({
    status: 'pending',
    progress: 0,
    stage: '',
  });
  
  const eventSourceRef = useRef<EventSource | null>(null);
  const { enabled = true } = options;
  const token = useAuthStore(s => s.token);

  const closeConnection = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!jobId || !enabled || !token) {
      return;
    }

    // Close existing connection if any
    closeConnection();

    const url = paperService.getSSEUrl(jobId, token);
    logger.debug(`Connecting to SSE: ${url}`, null, 'useJobProgress');

    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      logger.debug('SSE Connected', { jobId }, 'useJobProgress');
    };

    eventSource.onerror = (error) => {
      logger.error('SSE Error', error, 'useJobProgress');
      // Typically EventSource will auto-reconnect, but if it's a fatal error (like 401/404), we might want to stop.
      // For now, let's leave it to auto-reconnect or close on component unmount.
      // If readyState is CLOSED (2), it means it won't retry.
      if (eventSource.readyState === EventSource.CLOSED) {
          setState(prev => ({ ...prev, status: 'failed', error: 'Connection closed' }));
      }
    };

    // Listen for specific events
    eventSource.addEventListener('start', (e: MessageEvent) => {
        const data = JSON.parse(e.data);
        setState(prev => ({
            ...prev,
            status: data.status,
            progress: data.progress,
            stage: data.stage || 'Starting...'
        }));
    });

    eventSource.addEventListener('progress', (e: MessageEvent) => {
        const data = JSON.parse(e.data);
        setState(prev => ({
            ...prev,
            status: data.status,
            progress: data.progress,
            stage: data.stage
        }));
    });

    eventSource.addEventListener('end', (e: MessageEvent) => {
        const data = JSON.parse(e.data);
        setState(prev => ({
            ...prev,
            status: data.status,
            progress: 100,
            stage: 'Completed',
            result: data.result
        }));
        
        closeConnection();
        
        if (data.status === 'succeeded' || data.status === 'success') {
            options.onSucceeded?.(data.result);
        } else {
            options.onFailed?.(data.error || 'Unknown error');
        }
    });

    eventSource.addEventListener('job_error', (e: MessageEvent) => {
        const data = JSON.parse(e.data);
        setState(prev => ({
           ...prev,
           status: 'failed',
           error: data.message
       }));
       closeConnection();
       options.onFailed?.(data.message);
   });

    return () => {
      closeConnection();
    };
  }, [jobId, enabled, token, closeConnection, options.onSucceeded, options.onFailed]);

  return state;
};
