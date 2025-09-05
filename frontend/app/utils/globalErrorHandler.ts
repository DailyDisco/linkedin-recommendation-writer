/**
 * Global Error Handler
 *
 * Handles uncaught exceptions and unhandled promise rejections
 * that occur outside of React's error boundaries.
 */

import { toast } from 'sonner';

// Error types for better categorization
export enum GlobalErrorType {
  UNCAUGHT_EXCEPTION = 'uncaught_exception',
  UNHANDLED_REJECTION = 'unhandled_rejection',
  RESOURCE_ERROR = 'resource_error',
}

// Error context for logging
interface ErrorContext {
  type: GlobalErrorType;
  message: string;
  stack?: string;
  filename?: string;
  lineno?: number;
  colno?: number;
  timestamp: string;
  userAgent: string;
  url: string;
}

// User-friendly error messages based on error types
const ERROR_MESSAGES = {
  [GlobalErrorType.UNCAUGHT_EXCEPTION]: {
    title: 'Unexpected Error',
    message:
      'Something unexpected happened. The page has been refreshed to restore functionality.',
    action: 'refresh',
  },
  [GlobalErrorType.UNHANDLED_REJECTION]: {
    title: 'Request Failed',
    message:
      'A background request failed. You can continue using the application.',
    action: 'continue',
  },
  [GlobalErrorType.RESOURCE_ERROR]: {
    title: 'Resource Loading Error',
    message:
      'Some resources failed to load. Please refresh the page to try again.',
    action: 'refresh',
  },
};

/**
 * Logs error to console with structured format
 */
function logError(context: ErrorContext): void {
  console.group(`🚨 Global Error - ${context.type}`);
  console.error('Message:', context.message);
  if (context.stack) console.error('Stack:', context.stack);
  if (context.filename) console.error('File:', context.filename);
  if (context.lineno) console.error('Line:', context.lineno);
  console.error('URL:', context.url);
  console.error('Timestamp:', context.timestamp);
  console.groupEnd();

  // In a real application, this would send to a logging service
  // For now, we'll just log to console
}

/**
 * Shows user-friendly error notification
 */
function showErrorToast(type: GlobalErrorType): void {
  const errorInfo = ERROR_MESSAGES[type];

  // Show toast with appropriate styling and action
  if (errorInfo.action === 'refresh') {
    toast.error(errorInfo.message, {
      description: errorInfo.title,
      action: {
        label: 'Refresh Page',
        onClick: () => window.location.reload(),
      },
      duration: 10000, // Longer duration for critical errors
    });
  } else {
    toast.error(errorInfo.message, {
      description: errorInfo.title,
      duration: 5000,
    });
  }
}

/**
 * Creates error context from various error sources
 */
function createErrorContext(
  type: GlobalErrorType,
  error: Error | Event | string,
  additionalData?: any
): ErrorContext {
  const now = new Date().toISOString();

  let message: string;
  let stack: string | undefined;

  if (error instanceof Error) {
    message = error.message;
    stack = error.stack;
  } else if (error instanceof Event) {
    message = error.type;
  } else {
    message = String(error);
  }

  const context: ErrorContext = {
    type,
    message,
    stack,
    timestamp: now,
    userAgent: navigator.userAgent,
    url: window.location.href,
  };

  // Add additional context based on error type
  if (type === GlobalErrorType.RESOURCE_ERROR && additionalData) {
    context.filename = additionalData.filename;
    context.lineno = additionalData.lineno;
    context.colno = additionalData.colno;
  }

  return context;
}

/**
 * Handles uncaught exceptions
 */
function handleUncaughtException(event: ErrorEvent): void {
  const context = createErrorContext(
    GlobalErrorType.UNCAUGHT_EXCEPTION,
    event.error || event.message,
    {
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
    }
  );

  logError(context);
  showErrorToast(GlobalErrorType.UNCAUGHT_EXCEPTION);

  // Prevent default error handling
  event.preventDefault();
}

/**
 * Handles unhandled promise rejections
 */
function handleUnhandledRejection(event: PromiseRejectionEvent): void {
  const context = createErrorContext(
    GlobalErrorType.UNHANDLED_REJECTION,
    event.reason
  );

  logError(context);
  showErrorToast(GlobalErrorType.UNHANDLED_REJECTION);

  // Prevent default error handling
  event.preventDefault();
}

/**
 * Handles resource loading errors
 */
function handleResourceError(event: ErrorEvent): void {
  // Only handle resource errors (not script errors which are handled by uncaught exception)
  if (event.target && (event.target as HTMLElement).tagName) {
    const target = event.target as
      | HTMLImageElement
      | HTMLScriptElement
      | HTMLLinkElement;

    const context = createErrorContext(
      GlobalErrorType.RESOURCE_ERROR,
      `Failed to load resource: ${target.src || target.href || 'unknown'}`,
      {
        filename: target.src || target.href,
      }
    );

    logError(context);
    showErrorToast(GlobalErrorType.RESOURCE_ERROR);
  }
}

/**
 * Initializes global error handlers
 * Should be called early in the application lifecycle
 */
export function initializeGlobalErrorHandling(): void {
  // Handle uncaught exceptions
  window.addEventListener('error', handleUncaughtException);

  // Handle unhandled promise rejections
  window.addEventListener('unhandledrejection', handleUnhandledRejection);

  // Handle resource loading errors
  window.addEventListener('error', handleResourceError, true); // Use capture phase

  console.log('🔧 Global error handling initialized');
}

/**
 * Cleanup function to remove error handlers
 * Useful for testing or when reinitializing
 */
export function cleanupGlobalErrorHandling(): void {
  window.removeEventListener('error', handleUncaughtException);
  window.removeEventListener('unhandledrejection', handleUnhandledRejection);
  window.removeEventListener('error', handleResourceError, true);

  console.log('🧹 Global error handling cleaned up');
}

// Export for testing
export {
  handleUncaughtException,
  handleUnhandledRejection,
  handleResourceError,
  createErrorContext,
  logError,
  showErrorToast,
};
