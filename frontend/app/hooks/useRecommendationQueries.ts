import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { useEffect, useRef, useState, useCallback } from 'react';
import { toast } from 'sonner';
import { apiClient } from '../services/api';
import type { RecommendationRequest, HttpError } from '../types/index';

// Type for progress data
type ProgressData = {
  stage: string;
  progress: number;
  status: string;
  result?: unknown;
  error?: string;
};

// Custom hook for SSE connections
export const useSSEConnection = (
  url: string | null,
  onMessage: (data: unknown) => void,
  onError?: (error: Event) => void,
  enabled: boolean = true
) => {
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const keepAliveIntervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!enabled || !url) return;

    console.log('🔌 Establishing SSE connection to:', url);

    const connect = () => {
      const eventSource = new EventSource(url);
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        console.log('🔌 SSE connection opened successfully');
        // Start keep-alive ping
        keepAliveIntervalRef.current = setInterval(() => {
          if (eventSource.readyState === EventSource.OPEN) {
            console.log('🔄 SSE keep-alive ping');
          }
        }, 30000); // Ping every 30 seconds
      };

      eventSource.onmessage = event => {
        try {
          console.log('📨 SSE message received:', event.data);
          const data = JSON.parse(event.data);
          onMessage(data);
        } catch (error) {
          console.error(
            '❌ Failed to parse SSE message:',
            error,
            'Raw data:',
            event.data
          );
        }
      };

      eventSource.onerror = error => {
        console.error('❌ SSE connection error:', error);
        console.log('SSE ready state:', eventSource.readyState);

        // Clear keep-alive
        if (keepAliveIntervalRef.current) {
          clearInterval(keepAliveIntervalRef.current);
          keepAliveIntervalRef.current = null;
        }

        // Only call onError if the connection is actually closed
        if (eventSource.readyState === EventSource.CLOSED) {
          console.log('🔌 SSE connection closed, calling onError');
          if (onError) {
            onError(error);
          }
        }
      };
    };

    connect();

    return () => {
      console.log('🔌 Cleaning up SSE connection');
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (keepAliveIntervalRef.current) {
        clearInterval(keepAliveIntervalRef.current);
        keepAliveIntervalRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };
  }, [url, enabled, onMessage, onError]);

  const disconnect = useCallback(() => {
    console.log('🔌 Manually disconnecting SSE connection');
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (keepAliveIntervalRef.current) {
      clearInterval(keepAliveIntervalRef.current);
      keepAliveIntervalRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  return { disconnect };
};

// Simple SSE test hook
export const useSSETest = () => {
  const [messages, setMessages] = useState<string[]>([]);

  const testSSE = useCallback(() => {
    const eventSource = new EventSource('/api/test-sse');

    eventSource.onmessage = event => {
      try {
        const data = JSON.parse(event.data);
        console.log('SSE Test received:', data);
        setMessages(prev => [...prev, data.message]);
      } catch (error) {
        console.error('Failed to parse SSE test message:', error);
      }
    };

    eventSource.onerror = error => {
      console.error('SSE Test error:', error);
    };

    return () => {
      eventSource.close();
    };
  }, []);

  return { testSSE, messages };
};

// Hook for generating recommendation options (streaming)
export const useGenerateRecommendationOptionsStream = () => {
  const queryClient = useQueryClient();
  const [streamUrl, setStreamUrl] = useState<string | null>(null);
  const [activeOnProgress, setActiveOnProgress] = useState<
    ((progress: ProgressData) => void) | null
  >(null);
  const [activeOnError, setActiveOnError] = useState<
    ((error: string) => void) | null
  >(null);
  const [activeOnComplete, setActiveOnComplete] = useState<
    ((result: unknown) => void) | null
  >(null);
  const [currentRequest, setCurrentRequest] =
    useState<RecommendationRequest | null>(null);
  const disconnectRef = useRef<(() => void) | null>(null);
  const retryCountRef = useRef<number>(0);
  const maxRetries = 3;

  // Define callbacks
  const handleMessage = useCallback(
    (data: unknown) => {
      // Reset retry count on successful message
      retryCountRef.current = 0;

      if (!activeOnProgress) return;

      activeOnProgress(data as ProgressData);

      const progressData = data as {
        stage: string;
        progress: number;
        status: string;
        result?: unknown;
        error?: string;
      };

      if (
        progressData.status === 'complete' &&
        progressData.result &&
        activeOnComplete &&
        currentRequest
      ) {
        // Cache the result
        queryClient.setQueryData(
          ['recommendation-options', currentRequest.github_username],
          progressData.result
        );

        // Skip prefetch for now to avoid 401 issues after successful generation
        // TODO: Re-enable prefetch when token expiry issues are resolved
        console.log(
          '🔄 Skipping recommendation prefetch to avoid 401 logout issue'
        );

        activeOnComplete(progressData.result);
        toast.success('Recommendation options generated successfully!');
        disconnectRef.current?.();
      } else if (progressData.status === 'error' && activeOnError) {
        activeOnError(
          progressData.error || 'An error occurred during generation'
        );
        toast.error(
          progressData.error || 'Failed to generate recommendation options'
        );
        disconnectRef.current?.();
      }
    },
    [
      activeOnProgress,
      activeOnComplete,
      activeOnError,
      currentRequest,
      queryClient,
    ]
  );

  const handleError = useCallback(
    (errorEvent: Event) => {
      console.error('SSE connection error in generate:', errorEvent);
      console.log(
        'SSE ready state:',
        (errorEvent.target as EventSource)?.readyState
      );
      console.log('Retry count:', retryCountRef.current);

      // Don't immediately call onError - wait a bit to see if it's a temporary issue
      setTimeout(() => {
        const eventSource = errorEvent.target as EventSource;
        if (eventSource?.readyState === EventSource.CLOSED) {
          console.error('SSE connection permanently closed');

          // Try to reconnect if we haven't exceeded max retries
          if (retryCountRef.current < maxRetries && currentRequest) {
            retryCountRef.current += 1;
            console.log(
              `Attempting retry ${retryCountRef.current}/${maxRetries}`
            );

            // Reconnect after a delay
            setTimeout(() => {
              // Build the same URL for retry
              const params = new URLSearchParams({
                github_username: currentRequest.github_username,
                recommendation_type: currentRequest.recommendation_type,
                tone: currentRequest.tone,
                length: currentRequest.length,
              });

              if (currentRequest.custom_prompt) {
                params.append('custom_prompt', currentRequest.custom_prompt);
              }
              if (currentRequest.target_role) {
                params.append('target_role', currentRequest.target_role);
              }
              if (currentRequest.include_specific_skills?.length) {
                params.append(
                  'include_specific_skills',
                  currentRequest.include_specific_skills.join(',')
                );
              }

              const retryUrl = `/api/recommendations/generate-options/stream?${params.toString()}`;
              console.log('Retrying with URL:', retryUrl);

              // Set the retry URL to trigger reconnection
              setStreamUrl(retryUrl);
            }, 1000 * retryCountRef.current); // Exponential backoff
          } else {
            console.error('Max retries exceeded, giving up');
            if (activeOnError) {
              activeOnError('Connection failed after retries');
              toast.error('Connection failed. Please try again.');
            }
            disconnectRef.current?.();
          }
        }
      }, 2000); // Wait 2 seconds before declaring the connection dead
    },
    [activeOnError, currentRequest, maxRetries]
  );

  const { disconnect: actualDisconnect } = useSSEConnection(
    streamUrl,
    handleMessage,
    handleError,
    !!streamUrl
  );
  disconnectRef.current = actualDisconnect;

  const generate = useCallback(
    (
      request: RecommendationRequest,
      onProgress: (progress: {
        stage: string;
        progress: number;
        status: string;
        result?: unknown;
        error?: string;
      }) => void,
      onComplete: (result: unknown) => void,
      onError: (error: string) => void
    ) => {
      // Disconnect any existing connection
      disconnectRef.current?.();

      // Reset retry count for new generation
      retryCountRef.current = 0;

      // Set up new callbacks and request
      setActiveOnProgress(() => onProgress);
      setActiveOnComplete(() => onComplete);
      setActiveOnError(() => onError);
      setCurrentRequest(request);

      // Build query string for the streaming endpoint
      const params = new URLSearchParams({
        github_username: request.github_username,
        recommendation_type: request.recommendation_type,
        tone: request.tone,
        length: request.length,
      });

      if (request.custom_prompt) {
        params.append('custom_prompt', request.custom_prompt);
      }
      if (request.target_role) {
        params.append('target_role', request.target_role);
      }
      if (request.include_specific_skills?.length) {
        params.append(
          'include_specific_skills',
          request.include_specific_skills.join(',')
        );
      }
      if (request.exclude_keywords?.length) {
        params.append('exclude_keywords', request.exclude_keywords.join(','));
      }
      if (request.analysis_type) {
        params.append('analysis_type', request.analysis_type);
      }
      if (request.repository_url) {
        params.append('repository_url', request.repository_url);
      }

      const newStreamUrl = `/api/recommendations/generate-options/stream?${params.toString()}`;
      setStreamUrl(newStreamUrl);

      return () => disconnectRef.current?.();
    },
    []
  );

  return { generate, disconnect: () => disconnectRef.current?.() };
};

// Hook for generating recommendation options (legacy non-streaming)
export const useGenerateRecommendationOptions = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (request: RecommendationRequest) => {
      const response = await apiClient.generateRecommendationOptions(request);
      return response;
    },
    onSuccess: (data, variables) => {
      // Cache the generated options for this user
      queryClient.setQueryData(
        ['recommendation-options', variables.github_username],
        data
      );

      // Skip prefetch for now to avoid 401 issues after successful generation
      // TODO: Re-enable prefetch when token expiry issues are resolved
      console.log(
        '🔄 Skipping recommendation prefetch to avoid 401 logout issue'
      );

      toast.success('Recommendation options generated successfully!');
    },
    onError: (error: unknown) => {
      const httpError = error as HttpError;
      let errorMessage = 'Failed to generate recommendation. Please try again.';

      if (
        httpError.code === 'ECONNABORTED' ||
        httpError.message?.includes('timeout')
      ) {
        errorMessage =
          'Request timed out. The recommendation generation is taking longer than expected. Please try again.';
      } else if (httpError.response?.status === 429) {
        errorMessage =
          'Too many requests. Please wait a moment before trying again.';
      } else if (httpError.response?.status === 500) {
        errorMessage = 'Server error. Please try again in a few moments.';
      } else if (httpError.response?.status === 400) {
        errorMessage = errorMessage =
          httpError.response?.data?.detail ||
          'Invalid request. Please check your input.';
      } else if (!httpError.response) {
        errorMessage =
          'Network error. Please check your connection and try again.';
      } else if (httpError.response?.data?.detail) {
        errorMessage = httpError.response.data.detail;
      }

      toast.error(errorMessage);
    },
  });
};

// Hook for creating recommendation from option
export const useCreateRecommendationFromOption = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (params: {
      github_username: string;
      option: {
        id: number;
        name: string;
        content: string;
        title: string;
        word_count: number;
        focus: string;
        explanation: string;
        generation_parameters?: Record<string, unknown>;
      };
      options: Array<{
        id: number;
        name: string;
        content: string;
        title: string;
        word_count: number;
        focus: string;
        explanation: string;
        generation_parameters?: Record<string, unknown>;
      }>;
      analysis_type: string;
      repository_url?: string;
      recommendation_type: string;
      tone: string;
      length: string;
    }) => {
      const response = await apiClient.createFromOption({
        github_username: params.github_username,
        selected_option: {
          ...params.option,
          generation_parameters: params.option.generation_parameters || {},
        },
        all_options: params.options.map(opt => ({
          ...opt,
          generation_parameters: opt.generation_parameters || {},
        })),
        analysis_context_type: params.analysis_type,
        repository_url: params.repository_url,
      });
      return response;
    },
    onSuccess: (data, variables) => {
      // Add to user's recommendations cache
      queryClient.setQueryData(
        ['user-recommendations', variables.github_username],
        (
          oldData:
            | {
                recommendations: unknown[];
                total: number;
                page: number;
                page_size: number;
              }
            | undefined
        ) => {
          if (!oldData)
            return {
              recommendations: [data],
              total: 1,
              page: 1,
              page_size: 10,
            };
          return {
            ...oldData,
            recommendations: [data, ...oldData.recommendations].slice(
              0,
              oldData.page_size
            ),
            total: oldData.total + 1,
          };
        }
      );

      // Cache individual recommendation
      queryClient.setQueryData(['recommendation', data.id], data);

      toast.success('Recommendation created successfully!');
    },
    onError: (error: unknown) => {
      const httpError = error as HttpError;
      toast.error(
        httpError.response?.data?.detail ||
          'Failed to create recommendation from selected option'
      );
    },
  });
};

// Hook for regenerating recommendation (streaming)
export const useRegenerateRecommendationStream = () => {
  const queryClient = useQueryClient();
  const [streamUrl, setStreamUrl] = useState<string | null>(null);
  const [activeOnProgress, setActiveOnProgress] = useState<
    ((progress: ProgressData) => void) | null
  >(null);
  const [activeOnError, setActiveOnError] = useState<
    ((error: string) => void) | null
  >(null);
  const [activeOnComplete, setActiveOnComplete] = useState<
    ((result: unknown) => void) | null
  >(null);
  const [currentParams, setCurrentParams] = useState<{
    original_content: string;
    refinement_instructions: string;
    github_username: string;
    recommendation_type?: string;
    tone?: string;
    length?: string;
    dynamic_tone?: string;
    dynamic_length?: string;
    include_keywords?: string[];
    exclude_keywords?: string[];
  } | null>(null);
  const disconnectRef = useRef<(() => void) | null>(null);

  // Define callbacks
  const handleMessage = useCallback(
    (data: unknown) => {
      if (!activeOnProgress) return;

      activeOnProgress(data as ProgressData);

      const progressData = data as {
        stage: string;
        progress: number;
        status: string;
        result?: unknown;
        error?: string;
      };

      if (
        progressData.status === 'complete' &&
        progressData.result &&
        activeOnComplete &&
        currentParams
      ) {
        // Update cached recommendation
        queryClient.setQueryData(
          ['recommendation', (progressData.result as { id: number }).id],
          progressData.result
        );

        // Update in user's recommendations list
        queryClient.setQueryData(
          ['user-recommendations', currentParams.github_username],
          (
            oldData:
              | {
                  recommendations: unknown[];
                  total: number;
                  page: number;
                  page_size: number;
                }
              | undefined
          ) => {
            if (!oldData)
              return {
                recommendations: [progressData.result],
                total: 1,
                page: 1,
                page_size: 10,
              };

            return {
              ...oldData,
              recommendations: oldData.recommendations.map((rec: unknown) =>
                (rec as { id: unknown }).id ===
                (progressData.result as { id: unknown }).id
                  ? progressData.result
                  : rec
              ),
            };
          }
        );

        activeOnComplete(progressData.result);
        toast.success('Recommendation refined successfully!');
        disconnectRef.current?.();
      } else if (progressData.status === 'error' && activeOnError) {
        activeOnError(
          progressData.error || 'An error occurred during refinement'
        );
        toast.error(progressData.error || 'Failed to refine recommendation');
        disconnectRef.current?.();
      }
    },
    [
      activeOnProgress,
      activeOnComplete,
      activeOnError,
      currentParams,
      queryClient,
    ]
  );

  const handleError = useCallback(
    (errorEvent: Event) => {
      console.error('SSE connection error in regenerate:', errorEvent);
      if (activeOnError) {
        activeOnError('Connection failed');
        toast.error('Connection failed. Please try again.');
      }
      disconnectRef.current?.();
    },
    [activeOnError]
  );

  const { disconnect: actualDisconnect } = useSSEConnection(
    streamUrl,
    handleMessage,
    handleError,
    !!streamUrl
  );
  disconnectRef.current = actualDisconnect;

  const regenerate = useCallback(
    (
      params: {
        original_content: string;
        refinement_instructions: string;
        github_username: string;
        recommendation_type?: string;
        tone?: string;
        length?: string;
        dynamic_tone?: string;
        dynamic_length?: string;
        include_keywords?: string[];
        exclude_keywords?: string[];
      },
      onProgress: (progress: {
        stage: string;
        progress: number;
        status: string;
        result?: unknown;
        error?: string;
      }) => void,
      onComplete: (result: unknown) => void,
      onError: (error: string) => void
    ) => {
      // Disconnect any existing connection
      disconnectRef.current?.();

      // Set up new callbacks and params
      setActiveOnProgress(() => onProgress);
      setActiveOnComplete(() => onComplete);
      setActiveOnError(() => onError);
      setCurrentParams(params);

      // Note: SSE doesn't support POST body directly, so we're not using requestBody
      // In a real implementation, you might need to establish the SSE connection first,
      // then send the POST request to trigger the streaming
      const newStreamUrl = `/api/recommendations/regenerate/stream`;
      setStreamUrl(newStreamUrl);

      return () => disconnectRef.current?.();
    },
    []
  );

  return { regenerate, disconnect: () => disconnectRef.current?.() };
};

// Hook for regenerating recommendation (legacy non-streaming)
export const useRegenerateRecommendation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (params: {
      original_content: string;
      refinement_instructions: string;
      github_username: string;
      recommendation_type?: string;
      tone?: string;
      length?: string;
      include_keywords?: string[];
      exclude_keywords?: string[];
    }) => {
      const response = await apiClient.regenerateRecommendation(params);
      return response;
    },
    onSuccess: (data, variables) => {
      // Update cached recommendation
      queryClient.setQueryData(['recommendation', data.id], data);

      // Update in user's recommendations list
      queryClient.setQueryData(
        ['user-recommendations', variables.github_username],
        (
          oldData:
            | {
                recommendations: Array<{ id: number }>;
                total: number;
                page: number;
                page_size: number;
              }
            | undefined
        ) => {
          if (!oldData)
            return {
              recommendations: [data],
              total: 1,
              page: 1,
              page_size: 10,
            };

          return {
            ...oldData,
            recommendations: oldData.recommendations.map(rec =>
              rec.id === data.id ? data : rec
            ),
          };
        }
      );

      toast.success('Recommendation refined successfully!');
    },
    onError: (error: unknown) => {
      const httpError = error as HttpError;
      toast.error(
        httpError.response?.data?.detail ||
          'Failed to regenerate recommendation. Please try again.'
      );
    },
  });
};

// Hook for fetching user's recommendations (with caching)
export const useUserRecommendations = (
  githubUsername?: string,
  enabled: boolean = true
) => {
  return useQuery({
    queryKey: ['user-recommendations', githubUsername],
    queryFn: () =>
      apiClient.getRecommendations({
        github_username: githubUsername,
        page: 1,
        limit: 10,
      }),
    gcTime: 10 * 60 * 1000, // 10 minutes
    enabled: enabled && !!githubUsername,
  });
};

// Hook for fetching individual recommendation
export const useRecommendation = (
  recommendationId: number | null,
  enabled: boolean = true
) => {
  return useQuery({
    queryKey: ['recommendation', recommendationId],
    queryFn: () => apiClient.getRecommendation(recommendationId!),
    gcTime: 5 * 60 * 1000, // 5 minutes
    enabled: enabled && !!recommendationId,
  });
};
