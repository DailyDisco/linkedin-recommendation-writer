import { useState, useEffect, useCallback, useRef } from 'react';

export interface GitHubAnalysisResult {
  user_data: Record<string, unknown>;
  repositories: Array<Record<string, unknown>>;
  languages: Array<Record<string, unknown>>;
  skills: Record<string, unknown>;
  commit_analysis: Record<string, unknown>;
  analyzed_at: string;
  analysis_context_type: string;
}

export interface GitHubAnalysisProgress {
  task_id: string;
  status:
    | 'queued'
    | 'processing'
    | 'completed'
    | 'failed'
    | 'not_found'
    | 'error';
  stage: string;
  progress: number;
  timestamp: string;
  result?: GitHubAnalysisResult;
}

export interface GitHubAnalysisResponse {
  task_id: string;
  status: string;
  message: string;
  stream_url: string;
}

export const useGitHubAnalysisStream = () => {
  const [progress, setProgress] = useState<GitHubAnalysisProgress | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const startAnalysis = useCallback(
    async (
      username: string,
      forceRefresh: boolean = false
    ): Promise<GitHubAnalysisResponse> => {
      try {
        const response = await fetch('/api/v1/github/analyze/stream', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            username,
            force_refresh: forceRefresh,
          }),
        });

        if (!response.ok) {
          throw new Error(`Failed to start analysis: ${response.statusText}`);
        }

        const data: GitHubAnalysisResponse = await response.json();
        return data;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Unknown error';
        setError(errorMessage);
        throw new Error(errorMessage);
      }
    },
    []
  );

  const streamProgress = useCallback(
    (
      taskId: string,
      onComplete?: (result: GitHubAnalysisResult) => void,
      onError?: (error: string) => void
    ) => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      setIsStreaming(true);
      setError(null);

      const eventSource = new EventSource(
        `/api/v1/github/analyze/stream/${taskId}`
      );
      eventSourceRef.current = eventSource;

      eventSource.onmessage = event => {
        try {
          const data: GitHubAnalysisProgress = JSON.parse(event.data);
          setProgress(data);

          // Handle completion
          if (data.status === 'completed' && data.result && onComplete) {
            onComplete(data.result);
            eventSource.close();
            setIsStreaming(false);
          }

          // Handle errors
          if (
            data.status === 'failed' ||
            data.status === 'error' ||
            data.status === 'not_found'
          ) {
            const errorMessage = data.stage || 'Analysis failed';
            setError(errorMessage);
            if (onError) {
              onError(errorMessage);
            }
            eventSource.close();
            setIsStreaming(false);
          }
        } catch (err) {
          console.error('Error parsing SSE data:', err);
          setError('Failed to parse progress data');
          eventSource.close();
          setIsStreaming(false);
        }
      };

      eventSource.onerror = event => {
        console.error('SSE connection error:', event);
        setError('Connection lost');
        setIsStreaming(false);
        eventSource.close();
      };

      return () => {
        eventSource.close();
        setIsStreaming(false);
      };
    },
    []
  );

  const stopStreaming = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  return {
    progress,
    isStreaming,
    error,
    startAnalysis,
    streamProgress,
    stopStreaming,
  };
};
