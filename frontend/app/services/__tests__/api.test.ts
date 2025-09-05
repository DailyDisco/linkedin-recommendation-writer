/**
 * Tests for API Error Handling
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { handleApiError, ApiErrorType } from '../api';

// Mock toast
vi.mock('sonner', () => ({
  toast: {
    error: vi.fn(),
  },
}));

// Import the mocked toast for testing
import { toast } from 'sonner';
const mockToastError = vi.mocked(toast).error;

describe('API Error Handling', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Network Errors', () => {
    it('should handle network errors correctly', () => {
      const networkError = {
        request: {},
        message: 'Network Error',
      };

      const result = handleApiError(networkError);

      expect(result.type).toBe(ApiErrorType.NETWORK_ERROR);
      expect(result.status).toBe(0);
      expect(result.title).toBe('Connection Problem');
      expect(result.message).toBe(
        'Unable to connect to our servers. Please check your internet connection.'
      );
      expect(result.canRetry).toBe(true);
      expect(result.showReportButton).toBe(false);
    });

    it('should show retry toast for network errors with onRetry callback', () => {
      const networkError = {
        request: {},
        message: 'Network Error',
      };
      const onRetry = vi.fn();

      handleApiError(networkError, { onRetry });

      expect(mockToastError).toHaveBeenCalledWith(
        'Unable to connect to our servers. Please check your internet connection.',
        expect.objectContaining({
          description: 'Connection Problem',
          action: expect.objectContaining({
            label: 'Retry',
            onClick: onRetry,
          }),
          duration: 8000,
        })
      );
    });
  });

  describe('Authentication Errors', () => {
    it('should handle 401 errors correctly', () => {
      const authError = {
        response: {
          status: 401,
          data: { detail: 'Invalid credentials' },
        },
      };

      const result = handleApiError(authError);

      expect(result.type).toBe(ApiErrorType.AUTHENTICATION_ERROR);
      expect(result.status).toBe(401);
      expect(result.title).toBe('Authentication Required');
      expect(result.message).toBe(
        'Your session has expired or you need to log in.'
      );
      expect(result.canRetry).toBe(false);
      expect(result.showReportButton).toBe(false);
    });
  });

  describe('Authorization Errors', () => {
    it('should handle 403 errors correctly', () => {
      const forbiddenError = {
        response: {
          status: 403,
          data: { detail: 'Access denied' },
        },
      };

      const result = handleApiError(forbiddenError);

      expect(result.type).toBe(ApiErrorType.AUTHORIZATION_ERROR);
      expect(result.status).toBe(403);
      expect(result.title).toBe('Access Denied');
      expect(result.message).toBe(
        "You don't have permission to perform this action."
      );
      expect(result.canRetry).toBe(false);
      expect(result.showReportButton).toBe(true);
    });
  });

  describe('Validation Errors', () => {
    it('should handle 400 errors correctly', () => {
      const validationError = {
        response: {
          status: 400,
          data: { detail: 'Invalid input' },
        },
      };

      const result = handleApiError(validationError);

      expect(result.type).toBe(ApiErrorType.VALIDATION_ERROR);
      expect(result.status).toBe(400);
      expect(result.title).toBe('Invalid Input');
      expect(result.message).toBe('Please check your input and try again.');
      expect(result.canRetry).toBe(true);
      expect(result.showReportButton).toBe(false);
    });
  });

  describe('Not Found Errors', () => {
    it('should handle 404 errors correctly', () => {
      const notFoundError = {
        response: {
          status: 404,
          data: { detail: 'Resource not found' },
        },
      };

      const result = handleApiError(notFoundError);

      expect(result.type).toBe(ApiErrorType.NOT_FOUND_ERROR);
      expect(result.status).toBe(404);
      expect(result.title).toBe('Not Found');
      expect(result.message).toBe('The requested resource could not be found.');
      expect(result.canRetry).toBe(false);
      expect(result.showReportButton).toBe(true);
    });
  });

  describe('Rate Limit Errors', () => {
    it('should handle 429 errors correctly', () => {
      const rateLimitError = {
        response: {
          status: 429,
          data: { detail: 'Rate limit exceeded' },
        },
      };

      const result = handleApiError(rateLimitError);

      expect(result.type).toBe(ApiErrorType.RATE_LIMIT_ERROR);
      expect(result.status).toBe(429);
      expect(result.title).toBe('Too Many Requests');
      expect(result.message).toBe(
        "You've made too many requests. Please wait before trying again."
      );
      expect(result.canRetry).toBe(true);
      expect(result.showReportButton).toBe(false);
    });
  });

  describe('Server Errors', () => {
    it('should handle 500 errors correctly', () => {
      const serverError = {
        response: {
          status: 500,
          data: { detail: 'Internal server error' },
        },
      };

      const result = handleApiError(serverError);

      expect(result.type).toBe(ApiErrorType.SERVER_ERROR);
      expect(result.status).toBe(500);
      expect(result.title).toBe('Server Error');
      expect(result.message).toBe(
        "Our servers encountered an error. We're working to fix this."
      );
      expect(result.canRetry).toBe(true);
      expect(result.showReportButton).toBe(true);
    });

    it('should handle 502/503/504 errors as service unavailable', () => {
      const serviceUnavailableError = {
        response: {
          status: 503,
          data: { detail: 'Service unavailable' },
        },
      };

      const result = handleApiError(serviceUnavailableError);

      expect(result.type).toBe(ApiErrorType.SERVICE_UNAVAILABLE);
      expect(result.status).toBe(503);
      expect(result.title).toBe('Service Unavailable');
      expect(result.canRetry).toBe(true);
      expect(result.showReportButton).toBe(true);
    });
  });

  describe('Timeout Errors', () => {
    it('should detect timeout errors by message', () => {
      const timeoutError = {
        response: {
          status: 408,
          data: { detail: 'Request timeout' },
        },
        message: 'timeout',
      };

      const result = handleApiError(timeoutError);

      expect(result.type).toBe(ApiErrorType.TIMEOUT_ERROR);
      expect(result.title).toBe('Request Timeout');
    });

    it('should detect timeout errors by ECONNABORTED code', () => {
      const timeoutError = {
        response: {
          status: 408,
          data: { detail: 'Request timeout' },
        },
        code: 'ECONNABORTED',
      };

      const result = handleApiError(timeoutError);

      expect(result.type).toBe(ApiErrorType.TIMEOUT_ERROR);
    });
  });

  describe('Unknown Errors', () => {
    it('should handle unknown errors correctly', () => {
      const unknownError = {
        response: {
          status: 418, // I'm a teapot
          data: { detail: 'Unknown error' },
        },
      };

      const result = handleApiError(unknownError);

      expect(result.type).toBe(ApiErrorType.UNKNOWN_ERROR);
      expect(result.status).toBe(418);
      expect(result.title).toBe('Unexpected Error');
      expect(result.canRetry).toBe(true);
      expect(result.showReportButton).toBe(true);
    });
  });

  describe('Recovery Suggestions', () => {
    it('should include recovery suggestions for each error type', () => {
      const networkError = { request: {} };
      const result = handleApiError(networkError);

      expect(result.suggestions).toEqual([
        'Check your internet connection',
        'Try refreshing the page',
        'Wait a moment and try again',
      ]);
    });
  });

  describe('Error ID Generation', () => {
    it('should generate unique error IDs', () => {
      const error1 = handleApiError({ request: {} });
      const error2 = handleApiError({ request: {} });

      expect(error1.errorId).toMatch(/^api_error_\d+_[a-z0-9]+$/);
      expect(error2.errorId).toMatch(/^api_error_\d+_[a-z0-9]+$/);
      expect(error1.errorId).not.toBe(error2.errorId);
    });
  });

  describe('Toast Options', () => {
    it('should not show toast when showToast is false', () => {
      const error = { response: { status: 500, data: {} } };

      handleApiError(error, { showToast: false });

      expect(mockToastError).not.toHaveBeenCalled();
    });

    it('should show toast by default', () => {
      const error = { response: { status: 500, data: {} } };

      handleApiError(error);

      expect(mockToastError).toHaveBeenCalled();
    });
  });

  describe('Context Logging', () => {
    it('should include context in error logging', () => {
      const consoleGroupSpy = vi
        .spyOn(console, 'group')
        .mockImplementation(() => {});
      const consoleErrorSpy = vi
        .spyOn(console, 'error')
        .mockImplementation(() => {});
      const consoleGroupEndSpy = vi
        .spyOn(console, 'groupEnd')
        .mockImplementation(() => {});

      const error = { response: { status: 500, data: {} } };
      handleApiError(error, { context: 'User Registration' });

      expect(consoleGroupSpy).toHaveBeenCalledWith(
        '🚨 API Error - User Registration'
      );

      consoleGroupSpy.mockRestore();
      consoleErrorSpy.mockRestore();
      consoleGroupEndSpy.mockRestore();
    });
  });

  describe('Structured Logging', () => {
    it('should log structured error information', () => {
      const consoleGroupSpy = vi
        .spyOn(console, 'group')
        .mockImplementation(() => {});
      const consoleErrorSpy = vi
        .spyOn(console, 'error')
        .mockImplementation(() => {});
      const consoleGroupEndSpy = vi
        .spyOn(console, 'groupEnd')
        .mockImplementation(() => {});

      const error = {
        response: {
          status: 404,
          data: { detail: 'User not found' },
        },
      };

      handleApiError(error);

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Error ID:',
        expect.any(String)
      );
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Type:',
        ApiErrorType.NOT_FOUND_ERROR
      );
      expect(consoleErrorSpy).toHaveBeenCalledWith('Status:', 404);
      expect(consoleErrorSpy).toHaveBeenCalledWith('Message:', 'Unknown error');
      expect(consoleErrorSpy).toHaveBeenCalledWith('Data:', {
        detail: 'User not found',
      });
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Timestamp:',
        expect.any(String)
      );

      consoleGroupSpy.mockRestore();
      consoleErrorSpy.mockRestore();
      consoleGroupEndSpy.mockRestore();
    });
  });
});
