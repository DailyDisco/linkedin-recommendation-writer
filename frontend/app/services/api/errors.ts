import { toast } from 'sonner';

/**
 * API error types for categorization
 */
export enum ApiErrorType {
  NETWORK_ERROR = 'network_error',
  AUTHENTICATION_ERROR = 'authentication_error',
  AUTHORIZATION_ERROR = 'authorization_error',
  VALIDATION_ERROR = 'validation_error',
  NOT_FOUND_ERROR = 'not_found_error',
  RATE_LIMIT_ERROR = 'rate_limit_error',
  SERVER_ERROR = 'server_error',
  SERVICE_UNAVAILABLE = 'service_unavailable',
  TIMEOUT_ERROR = 'timeout_error',
  UNKNOWN_ERROR = 'unknown_error',
}

/**
 * HTTP error interface for type safety
 */
export interface HttpError {
  response?: {
    status: number;
    data?: { detail?: string; message?: string };
  };
  request?: unknown;
  message?: string;
  code?: string;
  config?: {
    url?: string;
    method?: string;
  };
}

/**
 * Error mapping with user-friendly messages and recovery suggestions
 */
interface ErrorMapping {
  title: string;
  message: string;
  suggestions: string[];
  canRetry: boolean;
  showReportButton: boolean;
}

const ERROR_MAPPINGS: Record<ApiErrorType, ErrorMapping> = {
  [ApiErrorType.NETWORK_ERROR]: {
    title: 'Connection Problem',
    message:
      'Unable to connect to our servers. Please check your internet connection.',
    suggestions: [
      'Check your internet connection',
      'Try refreshing the page',
      'Wait a moment and try again',
    ],
    canRetry: true,
    showReportButton: false,
  },
  [ApiErrorType.AUTHENTICATION_ERROR]: {
    title: 'Authentication Required',
    message: 'Your session has expired or you need to log in.',
    suggestions: [
      'Log in again to continue',
      'Check if your account is active',
    ],
    canRetry: false,
    showReportButton: false,
  },
  [ApiErrorType.AUTHORIZATION_ERROR]: {
    title: 'Access Denied',
    message: "You don't have permission to perform this action.",
    suggestions: [
      'Contact your administrator',
      'Check your account permissions',
      'Try logging in with a different account',
    ],
    canRetry: false,
    showReportButton: true,
  },
  [ApiErrorType.VALIDATION_ERROR]: {
    title: 'Invalid Input',
    message: 'Please check your input and try again.',
    suggestions: [
      'Review the form fields',
      'Ensure all required fields are filled',
      'Check data formats (email, dates, etc.)',
    ],
    canRetry: true,
    showReportButton: false,
  },
  [ApiErrorType.NOT_FOUND_ERROR]: {
    title: 'Not Found',
    message: 'The requested resource could not be found.',
    suggestions: [
      'Check the URL or link',
      'Try searching for the content',
      'Go back to the previous page',
    ],
    canRetry: false,
    showReportButton: true,
  },
  [ApiErrorType.RATE_LIMIT_ERROR]: {
    title: 'Too Many Requests',
    message: "You've made too many requests. Please wait before trying again.",
    suggestions: [
      'Wait a few minutes',
      'Reduce the frequency of requests',
      'Contact support if you need higher limits',
    ],
    canRetry: true,
    showReportButton: false,
  },
  [ApiErrorType.SERVER_ERROR]: {
    title: 'Server Error',
    message: "Our servers encountered an error. We're working to fix this.",
    suggestions: [
      'Try again in a few minutes',
      'Refresh the page',
      'Contact support if the problem persists',
    ],
    canRetry: true,
    showReportButton: true,
  },
  [ApiErrorType.SERVICE_UNAVAILABLE]: {
    title: 'Service Unavailable',
    message: 'The service is temporarily unavailable. Please try again later.',
    suggestions: [
      'Check our status page',
      'Try again in 10-15 minutes',
      'Contact support for urgent issues',
    ],
    canRetry: true,
    showReportButton: true,
  },
  [ApiErrorType.TIMEOUT_ERROR]: {
    title: 'Request Timeout',
    message: 'The request took too long to complete.',
    suggestions: [
      'Check your internet connection',
      'Try again with less data',
      'Contact support if this persists',
    ],
    canRetry: true,
    showReportButton: true,
  },
  [ApiErrorType.UNKNOWN_ERROR]: {
    title: 'Unexpected Error',
    message: 'An unexpected error occurred. Our team has been notified.',
    suggestions: [
      'Try refreshing the page',
      'Clear your browser cache',
      'Contact support if this continues',
    ],
    canRetry: true,
    showReportButton: true,
  },
};

/**
 * Determine error type based on HTTP status and error details
 */
function determineErrorType(status: number, error: HttpError): ApiErrorType {
  const message =
    error.response?.data?.detail ||
    error.response?.data?.message ||
    error.message ||
    '';

  // Network errors
  if (status === 0 || !error.response) {
    return ApiErrorType.NETWORK_ERROR;
  }

  // Authentication/Authorization
  if (status === 401) return ApiErrorType.AUTHENTICATION_ERROR;
  if (status === 403) return ApiErrorType.AUTHORIZATION_ERROR;

  // Client errors
  if (status === 400) return ApiErrorType.VALIDATION_ERROR;
  if (status === 404) return ApiErrorType.NOT_FOUND_ERROR;
  if (status === 429) return ApiErrorType.RATE_LIMIT_ERROR;

  // Server errors
  if (status >= 500) {
    if (status === 502 || status === 503 || status === 504) {
      return ApiErrorType.SERVICE_UNAVAILABLE;
    }
    return ApiErrorType.SERVER_ERROR;
  }

  // Timeout detection
  if (
    message.toLowerCase().includes('timeout') ||
    error.code === 'ECONNABORTED'
  ) {
    return ApiErrorType.TIMEOUT_ERROR;
  }

  return ApiErrorType.UNKNOWN_ERROR;
}

/**
 * Structured API error result
 */
export interface ApiErrorResult {
  type: ApiErrorType;
  status: number;
  message: string;
  title: string;
  suggestions: string[];
  canRetry: boolean;
  showReportButton: boolean;
  errorId: string;
  data: unknown;
  originalError: unknown;
}

/**
 * Handle API errors with comprehensive mapping and recovery suggestions
 */
export function handleApiError(
  error: unknown,
  options: {
    showToast?: boolean;
    context?: string;
    onRetry?: () => void;
  } = {}
): ApiErrorResult {
  const { showToast = true, context = '', onRetry } = options;

  let errorType: ApiErrorType;
  let status = -1;
  let errorData: unknown = null;

  const httpError = error as HttpError;

  if (httpError.response) {
    status = httpError.response.status;
    errorData = httpError.response.data;
    errorType = determineErrorType(status, httpError);
  } else if (httpError.request) {
    errorType = ApiErrorType.NETWORK_ERROR;
    status = 0;
  } else {
    errorType = ApiErrorType.UNKNOWN_ERROR;
    status = -1;
  }

  const errorMapping = ERROR_MAPPINGS[errorType];
  const errorId = `api_error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

  // Log structured error in development
  if (import.meta.env.DEV) {
    console.group(`🚨 API Error - ${context || 'Unknown Context'}`);
    console.error('Error ID:', errorId);
    console.error('Type:', errorType);
    console.error('Status:', status);
    console.error('Message:', httpError?.message || 'Unknown error');
    console.error('Data:', errorData);
    console.groupEnd();
  }

  // Show toast notification
  if (showToast) {
    if (errorMapping.canRetry && onRetry) {
      toast.error(errorMapping.message, {
        description: errorMapping.title,
        action: {
          label: 'Retry',
          onClick: onRetry,
        },
        duration: 8000,
      });
    } else {
      toast.error(errorMapping.message, {
        description: errorMapping.title,
        duration: 6000,
      });
    }
  }

  return {
    type: errorType,
    status,
    message: errorMapping.message,
    title: errorMapping.title,
    suggestions: errorMapping.suggestions,
    canRetry: errorMapping.canRetry,
    showReportButton: errorMapping.showReportButton,
    errorId,
    data: errorData,
    originalError: error,
  };
}

/**
 * Legacy function for backward compatibility
 * @deprecated Use handleApiError with options object instead
 */
export function handleApiErrorLegacy(
  error: unknown,
  showToast = true
): ApiErrorResult {
  return handleApiError(error, { showToast });
}
