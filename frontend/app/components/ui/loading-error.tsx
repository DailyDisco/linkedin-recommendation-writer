import React from 'react';
import { AlertTriangle, RefreshCw, Wifi, Clock } from 'lucide-react';
import { Button } from './button';
import { Card, CardContent } from './card';
import { Skeleton } from './skeleton';

export interface LoadingErrorProps {
  error?: string;
  onRetry?: () => void;
  isRetrying?: boolean;
  showSkeleton?: boolean;
  context?: string;
  className?: string;
}

/**
 * Loading error state component with retry functionality
 */
export const LoadingError: React.FC<LoadingErrorProps> = ({
  error = 'Failed to load content',
  onRetry,
  isRetrying = false,
  showSkeleton = false,
  context = '',
  className = '',
}) => {
  const getErrorIcon = () => {
    if (
      error.toLowerCase().includes('network') ||
      error.toLowerCase().includes('connection')
    ) {
      return <Wifi className='h-8 w-8 text-gray-400' />;
    }
    if (error.toLowerCase().includes('timeout')) {
      return <Clock className='h-8 w-8 text-gray-400' />;
    }
    return <AlertTriangle className='h-8 w-8 text-gray-400' />;
  };

  const getErrorMessage = () => {
    if (error.toLowerCase().includes('network')) {
      return 'Unable to connect. Please check your internet connection.';
    }
    if (error.toLowerCase().includes('timeout')) {
      return 'Request timed out. The server is taking too long to respond.';
    }
    return error;
  };

  if (showSkeleton) {
    return (
      <div className={`space-y-4 ${className}`}>
        <Skeleton className='h-8 w-3/4' />
        <Skeleton className='h-4 w-full' />
        <Skeleton className='h-4 w-2/3' />
        <Skeleton className='h-32 w-full' />
      </div>
    );
  }

  return (
    <Card className={`border-gray-200 ${className}`}>
      <CardContent className='flex flex-col items-center justify-center py-12 px-6'>
        <div className='text-center space-y-4'>
          {getErrorIcon()}

          <div className='space-y-2'>
            <h3 className='text-lg font-medium text-gray-900'>
              {context ? `${context} Error` : 'Loading Error'}
            </h3>
            <p className='text-gray-600 max-w-sm'>{getErrorMessage()}</p>
          </div>

          {onRetry && (
            <Button
              onClick={onRetry}
              disabled={isRetrying}
              variant='outline'
              className='mt-4'
            >
              {isRetrying ? (
                <>
                  <RefreshCw className='h-4 w-4 mr-2 animate-spin' />
                  Retrying...
                </>
              ) : (
                <>
                  <RefreshCw className='h-4 w-4 mr-2' />
                  Try Again
                </>
              )}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export interface InlineLoadingErrorProps {
  error?: string;
  onRetry?: () => void;
  className?: string;
}

/**
 * Inline loading error for smaller UI elements
 */
export const InlineLoadingError: React.FC<InlineLoadingErrorProps> = ({
  error = 'Failed to load',
  onRetry,
  className = '',
}) => {
  return (
    <div className={`flex items-center justify-center py-4 px-2 ${className}`}>
      <div className='text-center space-y-2'>
        <AlertTriangle className='h-5 w-5 text-gray-400 mx-auto' />
        <p className='text-sm text-gray-600'>{error}</p>
        {onRetry && (
          <Button
            onClick={onRetry}
            variant='ghost'
            size='sm'
            className='h-7 text-xs'
          >
            <RefreshCw className='h-3 w-3 mr-1' />
            Retry
          </Button>
        )}
      </div>
    </div>
  );
};

export default LoadingError;
