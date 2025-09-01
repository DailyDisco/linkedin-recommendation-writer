import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef } from 'react';
import { toast } from 'sonner';
import { apiClient } from '../services/api';
import type { RecommendationRequest, HttpError } from '../types/index';

// Custom hook for SSE connections
export const useSSEConnection = (
  url: string,
  onMessage: (data: unknown) => void,
  onError?: (error: Event) => void,
  enabled: boolean = true
) => {
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!enabled || !url) return;

    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    eventSource.onmessage = event => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error('Failed to parse SSE message:', error);
      }
    };

    eventSource.onerror = error => {
      console.error('SSE connection error:', error);
      if (onError) {
        onError(error);
      }
    };

    return () => {
      eventSource.close();
      eventSourceRef.current = null;
    };
  }, [url, enabled, onMessage, onError]);

  const disconnect = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  };

  return { disconnect };
};

// Hook for generating recommendation options (streaming)
export const useGenerateRecommendationOptionsStream = () => {
  const queryClient = useQueryClient();

  const generate = (
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

    const url = `${apiClient.baseURL}/recommendations/generate-options/stream?${params.toString()}`;

    // Create SSE connection directly without using a hook
    const eventSource = new EventSource(url);
    let isComplete = false;

    const disconnect = () => {
      if (eventSource && eventSource.readyState !== EventSource.CLOSED) {
        eventSource.close();
      }
    };

    eventSource.onmessage = event => {
      try {
        const data = JSON.parse(event.data);
        onProgress(data);

        if (data.status === 'complete' && data.result && !isComplete) {
          isComplete = true;
          // Cache the result
          queryClient.setQueryData(
            ['recommendation-options', request.github_username],
            data.result,
            { staleTime: 5 * 60 * 1000 }
          );

          // Prefetch recommendations
          queryClient.prefetchQuery({
            queryKey: ['user-recommendations', request.github_username],
            queryFn: () =>
              apiClient.getRecommendations({
                github_username: request.github_username,
              }),
            staleTime: 2 * 60 * 1000,
          });

          onComplete(data.result);
          toast.success('Recommendation options generated successfully!');
          disconnect();
        } else if (data.status === 'error') {
          onError(data.error || 'An error occurred during generation');
          toast.error(
            data.error || 'Failed to generate recommendation options'
          );
          disconnect();
        }
      } catch (error) {
        console.error('Failed to parse SSE message:', error);
        onError('Failed to parse server response');
        disconnect();
      }
    };

    eventSource.onerror = error => {
      console.error('SSE connection error:', error);
      if (!isComplete) {
        onError('Connection failed');
        toast.error('Connection failed. Please try again.');
        disconnect();
      }
    };

    return { disconnect };
  };

  return { generate };
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
        data,
        {
          staleTime: 5 * 60 * 1000, // 5 minutes
        }
      );

      // Prefetch recommendations for this user
      queryClient.prefetchQuery({
        queryKey: ['user-recommendations', variables.github_username],
        queryFn: () =>
          apiClient.getRecommendations({
            github_username: variables.github_username,
          }),
        staleTime: 2 * 60 * 1000, // 2 minutes
      });

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
      const response = await apiClient.createFromOption(
        params.github_username,
        {
          ...params.option,
          generation_parameters: params.option.generation_parameters || {},
        },
        params.options.map(opt => ({
          ...opt,
          generation_parameters: opt.generation_parameters || {},
        })),
        params.analysis_type,
        params.repository_url,
        params.recommendation_type,
        params.tone,
        params.length
      );
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

  const regenerate = (
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
    // Note: SSE doesn't support POST body directly, so we're not using requestBody
    // In a real implementation, you might need to establish the SSE connection first,
    // then send the POST request to trigger the streaming

    const url = `${apiClient.baseURL}/recommendations/regenerate/stream`;

    // Create SSE connection directly without using a hook
    const eventSource = new EventSource(url);
    let isComplete = false;

    const disconnect = () => {
      if (eventSource && eventSource.readyState !== EventSource.CLOSED) {
        eventSource.close();
      }
    };

    eventSource.onmessage = event => {
      try {
        const data = JSON.parse(event.data);
        onProgress(data);

        if (data.status === 'complete' && data.result && !isComplete) {
          isComplete = true;
          // Update cached recommendation
          queryClient.setQueryData(
            ['recommendation', data.result.id],
            data.result
          );

          // Update in user's recommendations list
          queryClient.setQueryData(
            ['user-recommendations', params.github_username],
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
                  recommendations: [data.result],
                  total: 1,
                  page: 1,
                  page_size: 10,
                };

              return {
                ...oldData,
                recommendations: oldData.recommendations.map(
                  (rec: { id: unknown }) =>
                    rec.id === (data.result as { id: unknown }).id
                      ? data.result
                      : rec
                ),
              };
            }
          );

          onComplete(data.result);
          toast.success('Recommendation refined successfully!');
          disconnect();
        } else if (data.status === 'error') {
          onError(data.error || 'An error occurred during refinement');
          toast.error(data.error || 'Failed to refine recommendation');
          disconnect();
        }
      } catch (error) {
        console.error('Failed to parse SSE message:', error);
        onError('Failed to parse server response');
        disconnect();
      }
    };

    eventSource.onerror = error => {
      console.error('SSE connection error:', error);
      if (!isComplete) {
        onError('Connection failed');
        toast.error('Connection failed. Please try again.');
        disconnect();
      }
    };

    // Note: SSE doesn't support POST body directly, so we're not using requestBody
    // In a real implementation, you might need to establish the SSE connection first,
    // then send the POST request to trigger the streaming

    return { disconnect };
  };

  return { regenerate };
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
    staleTime: 2 * 60 * 1000, // 2 minutes
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
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled: enabled && !!recommendationId,
  });
};
