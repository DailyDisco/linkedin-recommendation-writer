import React from 'react';
import { AlertTriangle, X, RefreshCw, Home } from 'lucide-react';
import { Button } from './button';
import { Alert, AlertDescription } from './alert';

export interface ErrorAlertProps {
  title?: string;
  message: string;
  suggestions?: string[];
  onRetry?: () => void;
  onDismiss?: () => void;
  onGoHome?: () => void;
  showRetryButton?: boolean;
  showHomeButton?: boolean;
  showDismissButton?: boolean;
  variant?: 'default' | 'destructive' | 'warning';
  className?: string;
}

/**
 * A reusable error alert component with consistent styling and actions
 */
export const ErrorAlert: React.FC<ErrorAlertProps> = ({
  title = 'Error',
  message,
  suggestions = [],
  onRetry,
  onDismiss,
  onGoHome,
  showRetryButton = false,
  showHomeButton = false,
  showDismissButton = false,
  variant = 'destructive',
  className = '',
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'warning':
        return 'border-yellow-200 bg-yellow-50 text-yellow-800';
      case 'destructive':
        return 'border-red-200 bg-red-50 text-red-800';
      default:
        return 'border-gray-200 bg-gray-50 text-gray-800';
    }
  };

  return (
    <Alert className={`${getVariantStyles()} ${className}`}>
      <AlertTriangle className='h-4 w-4' />
      <div className='flex-1'>
        <div className='flex items-center justify-between'>
          <h4 className='font-medium'>{title}</h4>
          {showDismissButton && onDismiss && (
            <Button
              variant='ghost'
              size='sm'
              onClick={onDismiss}
              className='h-6 w-6 p-0 hover:bg-transparent'
            >
              <X className='h-4 w-4' />
            </Button>
          )}
        </div>

        <AlertDescription className='mt-2'>
          <p>{message}</p>

          {suggestions.length > 0 && (
            <div className='mt-3'>
              <p className='text-sm font-medium'>Try these solutions:</p>
              <ul className='mt-1 list-disc list-inside text-sm space-y-1'>
                {suggestions.map((suggestion, index) => (
                  <li key={index}>{suggestion}</li>
                ))}
              </ul>
            </div>
          )}

          {(showRetryButton || showHomeButton) && (
            <div className='mt-4 flex gap-2'>
              {showRetryButton && onRetry && (
                <Button
                  variant='outline'
                  size='sm'
                  onClick={onRetry}
                  className='h-8'
                >
                  <RefreshCw className='h-3 w-3 mr-1' />
                  Try Again
                </Button>
              )}

              {showHomeButton && onGoHome && (
                <Button
                  variant='outline'
                  size='sm'
                  onClick={onGoHome}
                  className='h-8'
                >
                  <Home className='h-3 w-3 mr-1' />
                  Go Home
                </Button>
              )}
            </div>
          )}
        </AlertDescription>
      </div>
    </Alert>
  );
};

export default ErrorAlert;
