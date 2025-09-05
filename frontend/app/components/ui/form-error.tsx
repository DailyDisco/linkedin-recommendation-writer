import React from 'react';
import { AlertTriangle, Info } from 'lucide-react';
import { cn } from '../../lib/utils';

export interface FormErrorProps {
  error?: string;
  errors?: string[];
  touched?: boolean;
  className?: string;
  showIcon?: boolean;
  variant?: 'inline' | 'block';
}

/**
 * Form error component for displaying validation errors
 */
export const FormError: React.FC<FormErrorProps> = ({
  error,
  errors = [],
  touched = true,
  className = '',
  showIcon = true,
  variant = 'inline',
}) => {
  // Don't show errors if field hasn't been touched
  if (!touched) return null;

  const allErrors = error ? [error] : errors;
  if (allErrors.length === 0) return null;

  const baseClasses = 'text-sm text-red-600';
  const variantClasses = {
    inline: 'flex items-center gap-1',
    block: 'block',
  };

  return (
    <div className={cn(baseClasses, variantClasses[variant], className)}>
      {showIcon && variant === 'inline' && (
        <AlertTriangle className='h-3 w-3 flex-shrink-0' />
      )}

      {showIcon && variant === 'block' && (
        <div className='flex items-start gap-1'>
          <AlertTriangle className='h-3 w-3 flex-shrink-0 mt-0.5' />
          <div>
            {allErrors.map((errorMsg, index) => (
              <p key={index} className={index > 0 ? 'mt-1' : ''}>
                {errorMsg}
              </p>
            ))}
          </div>
        </div>
      )}

      {!showIcon && (
        <div>
          {allErrors.map((errorMsg, index) => (
            <p key={index} className={index > 0 ? 'mt-1' : ''}>
              {errorMsg}
            </p>
          ))}
        </div>
      )}
    </div>
  );
};

export interface FieldErrorProps {
  error?: string;
  touched?: boolean;
  className?: string;
}

/**
 * Simple field-level error component
 */
export const FieldError: React.FC<FieldErrorProps> = ({
  error,
  touched = true,
  className = '',
}) => {
  if (!touched || !error) return null;

  return (
    <p
      className={cn('text-sm text-red-600 flex items-center gap-1', className)}
    >
      <AlertTriangle className='h-3 w-3 flex-shrink-0' />
      {error}
    </p>
  );
};

export interface FormSuccessProps {
  message: string;
  className?: string;
  showIcon?: boolean;
}

/**
 * Form success message component
 */
export const FormSuccess: React.FC<FormSuccessProps> = ({
  message,
  className = '',
  showIcon = true,
}) => {
  return (
    <p
      className={cn(
        'text-sm text-green-600 flex items-center gap-1',
        className
      )}
    >
      {showIcon && <Info className='h-3 w-3 flex-shrink-0' />}
      {message}
    </p>
  );
};

export default FormError;
