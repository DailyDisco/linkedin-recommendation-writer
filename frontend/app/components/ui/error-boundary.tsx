import React from 'react';
import {
  AlertTriangle,
  RefreshCw,
  Home,
  HelpCircle,
  MessageSquare,
} from 'lucide-react';
import { Button } from './button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from './card';
import { Alert, AlertDescription } from './alert';

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorId?: string;
  timestamp?: string;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<{
    error?: Error;
    resetError: () => void;
    errorId?: string;
  }>;
  onError?: (error: Error, errorInfo: React.ErrorInfo, errorId: string) => void;
  showErrorReport?: boolean;
  errorContext?: string; // e.g., "form", "page", "component"
}

export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    const errorId = `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    return {
      hasError: true,
      error,
      errorId,
      timestamp: new Date().toISOString(),
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    const errorId = this.state.errorId || `error_${Date.now()}`;

    // Log structured error information
    console.group(
      `🚨 React Error Boundary - ${this.props.errorContext || 'Unknown Context'}`
    );
    console.error('Error ID:', errorId);
    console.error('Error:', error);
    console.error('Error Info:', errorInfo);
    console.error('Timestamp:', this.state.timestamp);
    console.error('Component Stack:', errorInfo.componentStack);
    console.groupEnd();

    // Call optional error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo, errorId);
    }

    // In a real application, this would send to a logging service
    // For now, we'll just log to console
  }

  resetError = () => {
    this.setState({
      hasError: false,
      error: undefined,
      errorId: undefined,
      timestamp: undefined,
    });
  };

  handleReportError = () => {
    const errorDetails = {
      errorId: this.state.errorId,
      message: this.state.error?.message,
      stack: this.state.error?.stack,
      timestamp: this.state.timestamp,
      context: this.props.errorContext,
      userAgent: navigator.userAgent,
      url: window.location.href,
    };

    // In a real application, this would send to a bug reporting service
    console.log('📋 Error Report:', errorDetails);

    // For now, we'll copy to clipboard and show a message
    navigator.clipboard
      .writeText(JSON.stringify(errorDetails, null, 2))
      .then(() => {
        alert(
          'Error details copied to clipboard. Please include this in your bug report.'
        );
      })
      .catch(() => {
        alert(
          'Error details logged to console. Please check the developer console.'
        );
      });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        const Fallback = this.props.fallback;
        return (
          <Fallback
            error={this.state.error}
            resetError={this.resetError}
            errorId={this.state.errorId}
          />
        );
      }

      return (
        <EnhancedErrorFallback
          error={this.state.error}
          resetError={this.resetError}
          errorId={this.state.errorId}
          showErrorReport={this.props.showErrorReport}
          onReportError={this.handleReportError}
          errorContext={this.props.errorContext}
        />
      );
    }

    return this.props.children;
  }
}

interface EnhancedErrorFallbackProps {
  error?: Error;
  resetError: () => void;
  errorId?: string;
  showErrorReport?: boolean;
  onReportError?: () => void;
  errorContext?: string;
}

const EnhancedErrorFallback: React.FC<EnhancedErrorFallbackProps> = ({
  error,
  resetError,
  errorId,
  showErrorReport = true,
  onReportError,
  errorContext,
}) => {
  // Determine error type and provide contextual help
  const getErrorInfo = () => {
    const message = error?.message?.toLowerCase() || '';

    if (message.includes('network') || message.includes('fetch')) {
      return {
        title: 'Connection Problem',
        message:
          'Unable to connect to our servers. This might be a temporary network issue.',
        suggestions: [
          'Check your internet connection',
          'Try refreshing the page',
          'Wait a moment and try again',
        ],
        icon: 'wifi-off',
      };
    }

    if (message.includes('permission') || message.includes('unauthorized')) {
      return {
        title: 'Access Denied',
        message: "You don't have permission to access this feature.",
        suggestions: [
          'Try logging in again',
          'Contact support if you believe this is an error',
        ],
        icon: 'lock',
      };
    }

    if (message.includes('timeout') || message.includes('slow')) {
      return {
        title: 'Request Timed Out',
        message: 'The operation is taking longer than expected.',
        suggestions: [
          'Try again in a few moments',
          'Check your connection speed',
          'Refresh the page',
        ],
        icon: 'clock',
      };
    }

    // Default error
    return {
      title: 'Something Unexpected Happened',
      message:
        'We encountered an unexpected error. Our team has been notified.',
      suggestions: [
        'Try refreshing the page',
        'Clear your browser cache',
        'Try again in a few minutes',
      ],
      icon: 'alert-triangle',
    };
  };

  const errorInfo = getErrorInfo();

  return (
    <div className='min-h-[500px] flex items-center justify-center p-6 bg-gray-50'>
      <Card className='max-w-lg w-full'>
        <CardHeader className='text-center'>
          <div className='w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4'>
            <AlertTriangle className='w-8 h-8 text-red-600' />
          </div>
          <CardTitle className='text-xl font-semibold text-gray-900'>
            {errorInfo.title}
          </CardTitle>
          <CardDescription className='text-gray-600'>
            {errorInfo.message}
          </CardDescription>
        </CardHeader>

        <CardContent className='space-y-6'>
          {/* Error ID for tracking */}
          {errorId && (
            <Alert>
              <HelpCircle className='h-4 w-4' />
              <AlertDescription className='text-sm'>
                Error ID:{' '}
                <code className='text-xs bg-gray-100 px-1 py-0.5 rounded'>
                  {errorId}
                </code>
                {errorContext && (
                  <span className='ml-2'>Context: {errorContext}</span>
                )}
              </AlertDescription>
            </Alert>
          )}

          {/* Recovery Suggestions */}
          <div className='space-y-2'>
            <h3 className='text-sm font-medium text-gray-900'>
              What you can try:
            </h3>
            <ul className='text-sm text-gray-600 space-y-1'>
              {errorInfo.suggestions.map((suggestion, index) => (
                <li key={index} className='flex items-start'>
                  <span className='text-gray-400 mr-2'>•</span>
                  {suggestion}
                </li>
              ))}
            </ul>
          </div>

          {/* Action Buttons */}
          <div className='flex flex-col sm:flex-row gap-3'>
            <Button onClick={resetError} className='flex-1' variant='default'>
              <RefreshCw className='w-4 h-4 mr-2' />
              Try Again
            </Button>

            <Button
              onClick={() => (window.location.href = '/')}
              variant='outline'
              className='flex-1'
            >
              <Home className='w-4 h-4 mr-2' />
              Go Home
            </Button>

            {showErrorReport && onReportError && (
              <Button onClick={onReportError} variant='outline' size='sm'>
                <MessageSquare className='w-4 h-4 mr-2' />
                Report Issue
              </Button>
            )}
          </div>

          {/* Technical Details (in development) */}
          {process.env.NODE_ENV === 'development' && error?.stack && (
            <details className='mt-4'>
              <summary className='text-sm font-medium text-gray-700 cursor-pointer'>
                Technical Details (Development Only)
              </summary>
              <pre className='mt-2 text-xs bg-gray-100 p-3 rounded overflow-auto max-h-32'>
                {error.stack}
              </pre>
            </details>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default ErrorBoundary;
