/**
 * Tests for Global Error Handler
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  initializeGlobalErrorHandling,
  cleanupGlobalErrorHandling,
  GlobalErrorType,
  createErrorContext,
  logError,
  showErrorToast,
  handleUncaughtException,
  handleUnhandledRejection,
  handleResourceError,
} from '../globalErrorHandler';

// Mock toast
vi.mock('sonner', () => ({
  toast: {
    error: vi.fn(),
  },
}));

// Import the mocked toast for testing
import { toast } from 'sonner';
const mockToast = vi.mocked(toast).error;

// Mock navigator.clipboard
Object.defineProperty(navigator, 'clipboard', {
  value: {
    writeText: vi.fn().mockResolvedValue(undefined),
  },
  writable: true,
});

// Mock window.location.reload
Object.defineProperty(window, 'location', {
  value: {
    reload: vi.fn(),
  },
  writable: true,
});

describe('Global Error Handler', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanupGlobalErrorHandling();
  });

  describe('createErrorContext', () => {
    it('should create error context for Error objects', () => {
      const error = new Error('Test error');
      const context = createErrorContext(
        GlobalErrorType.UNCAUGHT_EXCEPTION,
        error
      );

      expect(context.type).toBe(GlobalErrorType.UNCAUGHT_EXCEPTION);
      expect(context.message).toBe('Test error');
      expect(context.stack).toBe(error.stack);
      expect(context.timestamp).toBeDefined();
      expect(context.userAgent).toBe(navigator.userAgent);
      expect(context.url).toBe(window.location.href);
    });

    it('should create error context for string errors', () => {
      const error = 'String error';
      const context = createErrorContext(
        GlobalErrorType.UNCAUGHT_EXCEPTION,
        error
      );

      expect(context.type).toBe(GlobalErrorType.UNCAUGHT_EXCEPTION);
      expect(context.message).toBe('String error');
      expect(context.stack).toBeUndefined();
    });

    it('should create error context for Event objects', () => {
      const event = new Event('error');
      const context = createErrorContext(GlobalErrorType.RESOURCE_ERROR, event);

      expect(context.type).toBe(GlobalErrorType.RESOURCE_ERROR);
      expect(context.message).toBe('error');
    });

    it('should handle resource error with additional data', () => {
      const error = 'Resource failed';
      const additionalData = { filename: 'test.js', lineno: 42, colno: 10 };
      const context = createErrorContext(
        GlobalErrorType.RESOURCE_ERROR,
        error,
        additionalData
      );

      expect(context.filename).toBe('test.js');
      expect(context.lineno).toBe(42);
      expect(context.colno).toBe(10);
    });
  });

  describe('logError', () => {
    it('should log error context to console', () => {
      const consoleSpy = vi
        .spyOn(console, 'group')
        .mockImplementation(() => {});
      const consoleErrorSpy = vi
        .spyOn(console, 'error')
        .mockImplementation(() => {});
      const consoleGroupEndSpy = vi
        .spyOn(console, 'groupEnd')
        .mockImplementation(() => {});

      const context = createErrorContext(
        GlobalErrorType.UNCAUGHT_EXCEPTION,
        new Error('Test error')
      );

      logError(context);

      expect(consoleSpy).toHaveBeenCalledWith(
        '🚨 Global Error - uncaught_exception'
      );
      expect(consoleErrorSpy).toHaveBeenCalledWith('Message:', context.message);
      expect(consoleErrorSpy).toHaveBeenCalledWith('Stack:', context.stack);
      expect(consoleErrorSpy).toHaveBeenCalledWith('URL:', context.url);
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Timestamp:',
        context.timestamp
      );
      expect(consoleGroupEndSpy).toHaveBeenCalled();

      consoleSpy.mockRestore();
      consoleErrorSpy.mockRestore();
      consoleGroupEndSpy.mockRestore();
    });
  });

  describe('showErrorToast', () => {
    beforeEach(() => {
      mockToast.mockClear();
    });

    it('should show toast with refresh action for critical errors', () => {
      showErrorToast(GlobalErrorType.UNCAUGHT_EXCEPTION);

      expect(mockToast).toHaveBeenCalledWith(
        'Something unexpected happened. The page has been refreshed to restore functionality.',
        expect.objectContaining({
          description: 'Unexpected Error',
          action: expect.objectContaining({
            label: 'Refresh Page',
            onClick: expect.any(Function),
          }),
          duration: 10000,
        })
      );
    });

    it('should show toast without refresh action for non-critical errors', () => {
      showErrorToast(GlobalErrorType.UNHANDLED_REJECTION);

      expect(mockToast).toHaveBeenCalledWith(
        'A background request failed. You can continue using the application.',
        expect.objectContaining({
          description: 'Request Failed',
          duration: 5000,
        })
      );
    });
  });

  describe('initializeGlobalErrorHandling', () => {
    it('should add event listeners', () => {
      const addEventListenerSpy = vi.spyOn(window, 'addEventListener');

      initializeGlobalErrorHandling();

      expect(addEventListenerSpy).toHaveBeenCalledTimes(3);
      expect(addEventListenerSpy).toHaveBeenCalledWith(
        'error',
        handleUncaughtException
      );
      expect(addEventListenerSpy).toHaveBeenCalledWith(
        'unhandledrejection',
        handleUnhandledRejection
      );
      expect(addEventListenerSpy).toHaveBeenCalledWith(
        'error',
        handleResourceError,
        true
      );

      addEventListenerSpy.mockRestore();
    });
  });

  describe('cleanupGlobalErrorHandling', () => {
    it('should remove event listeners', () => {
      const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener');

      cleanupGlobalErrorHandling();

      expect(removeEventListenerSpy).toHaveBeenCalledTimes(3);
      expect(removeEventListenerSpy).toHaveBeenCalledWith(
        'error',
        handleUncaughtException
      );
      expect(removeEventListenerSpy).toHaveBeenCalledWith(
        'unhandledrejection',
        handleUnhandledRejection
      );
      expect(removeEventListenerSpy).toHaveBeenCalledWith(
        'error',
        handleResourceError,
        true
      );

      removeEventListenerSpy.mockRestore();
    });
  });

  describe('Error handling functions', () => {
    beforeEach(() => {
      mockToast.mockClear();
    });

    it('should handle uncaught exception events', () => {
      const mockEvent = {
        error: new Error('Test uncaught error'),
        filename: 'test.js',
        lineno: 42,
        colno: 10,
        preventDefault: vi.fn(),
      };

      handleUncaughtException(mockEvent as ErrorEvent);

      expect(mockToast).toHaveBeenCalled();
      expect(mockEvent.preventDefault).toHaveBeenCalled();
    });

    it('should handle unhandled rejection events', () => {
      const mockEvent = {
        reason: 'Test rejection reason',
        preventDefault: vi.fn(),
      };

      handleUnhandledRejection(mockEvent as PromiseRejectionEvent);

      expect(mockToast).toHaveBeenCalled();
      expect(mockEvent.preventDefault).toHaveBeenCalled();
    });

    it('should handle resource error events', () => {
      const mockTarget = {
        src: 'test.js',
        tagName: 'SCRIPT',
      };
      const mockEvent = {
        target: mockTarget,
      };

      handleResourceError(mockEvent as ErrorEvent);

      expect(mockToast).toHaveBeenCalled();
    });
  });
});
