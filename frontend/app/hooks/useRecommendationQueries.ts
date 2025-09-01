import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { apiClient } from '../services/api';
import type { RecommendationRequest, HttpError } from '../types/index';

// Hook for generating recommendation options
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

// Hook for regenerating recommendation
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
