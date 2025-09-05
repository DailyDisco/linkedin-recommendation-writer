/**
 * Tests for Enhanced Error Boundary Component
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ErrorBoundary } from '../error-boundary';

// Mock lucide-react icons
vi.mock('lucide-react', () => ({
  AlertTriangle: () =>
    React.createElement('div', { 'data-testid': 'alert-triangle' }),
  RefreshCw: () => React.createElement('div', { 'data-testid': 'refresh-cw' }),
  Home: () => React.createElement('div', { 'data-testid': 'home' }),
  HelpCircle: () =>
    React.createElement('div', { 'data-testid': 'help-circle' }),
  MessageSquare: () =>
    React.createElement('div', { 'data-testid': 'message-square' }),
}));

// Mock shadcn components
interface MockProps {
  children?: React.ReactNode;
  onClick?: () => void;
  variant?: string;
  size?: string;
  className?: string;
}

vi.mock('../button', () => ({
  Button: ({ children, onClick, variant, size, className }: MockProps) =>
    React.createElement(
      'button',
      {
        onClick,
        'data-variant': variant,
        'data-size': size,
        className,
        'data-testid': 'button',
      },
      children
    ),
}));

vi.mock('../card', () => ({
  Card: ({ children, className }: MockProps) =>
    React.createElement('div', { className, 'data-testid': 'card' }, children),
  CardContent: ({ children, className }: MockProps) =>
    React.createElement(
      'div',
      { className, 'data-testid': 'card-content' },
      children
    ),
  CardDescription: ({ className }: MockProps) =>
    React.createElement('div', {
      className,
      'data-testid': 'card-description',
    }),
  CardHeader: ({ children, className }: MockProps) =>
    React.createElement(
      'div',
      { className, 'data-testid': 'card-header' },
      children
    ),
  CardTitle: ({ children, className }: MockProps) =>
    React.createElement(
      'div',
      { className, 'data-testid': 'card-title' },
      children
    ),
}));

vi.mock('../alert', () => ({
  Alert: ({ children, className }: MockProps) =>
    React.createElement('div', { className, 'data-testid': 'alert' }, children),
  AlertDescription: ({ children, className }: MockProps) =>
    React.createElement(
      'div',
      { className, 'data-testid': 'alert-description' },
      children
    ),
}));

// Mock navigator.clipboard
Object.defineProperty(navigator, 'clipboard', {
  value: {
    writeText: vi.fn().mockResolvedValue(undefined),
  },
  writable: true,
});

// Test component that throws an error
const ErrorComponent = ({ shouldThrow = true }: { shouldThrow?: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test error message');
  }
  return React.createElement('div', null, 'No error');
};

// Test component with network error
const NetworkErrorComponent = ({
  shouldThrow = true,
}: {
  shouldThrow?: boolean;
}) => {
  if (shouldThrow) {
    throw new Error('Failed to fetch');
  }
  return React.createElement('div', null, 'No error');
};

describe('ErrorBoundary', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render children when no error occurs', () => {
    render(
      React.createElement(
        ErrorBoundary,
        null,
        React.createElement('div', null, 'Test content')
      )
    );

    expect(screen.getByText('Test content')).toBeInTheDocument();
  });

  it('should render error fallback when error occurs', () => {
    // Suppress console.error for this test
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { });
    const consoleGroupSpy = vi
      .spyOn(console, 'group')
      .mockImplementation(() => { });
    const consoleGroupEndSpy = vi
      .spyOn(console, 'groupEnd')
      .mockImplementation(() => { });

    render(
      React.createElement(
        ErrorBoundary,
        null,
        React.createElement(ErrorComponent)
      )
    );

    expect(
      screen.getByText('Something Unexpected Happened')
    ).toBeInTheDocument();
    expect(screen.getByText(/Test error message/)).toBeInTheDocument();

    consoleSpy.mockRestore();
    consoleGroupSpy.mockRestore();
    consoleGroupEndSpy.mockRestore();
  });

  it('should show network-specific error message', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { });
    const consoleGroupSpy = vi
      .spyOn(console, 'group')
      .mockImplementation(() => { });
    const consoleGroupEndSpy = vi
      .spyOn(console, 'groupEnd')
      .mockImplementation(() => { });

    render(
      React.createElement(
        ErrorBoundary,
        null,
        React.createElement(NetworkErrorComponent)
      )
    );

    expect(screen.getByText('Connection Problem')).toBeInTheDocument();
    expect(
      screen.getByText(
        'Unable to connect to our servers. This might be a temporary network issue.'
      )
    ).toBeInTheDocument();

    consoleSpy.mockRestore();
    consoleGroupSpy.mockRestore();
    consoleGroupEndSpy.mockRestore();
  });

  it('should show error ID when error occurs', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { });
    const consoleGroupSpy = vi
      .spyOn(console, 'group')
      .mockImplementation(() => { });
    const consoleGroupEndSpy = vi
      .spyOn(console, 'groupEnd')
      .mockImplementation(() => { });

    render(
      React.createElement(
        ErrorBoundary,
        null,
        React.createElement(ErrorComponent)
      )
    );

    // Error ID should be present in the format error_...
    const errorIdElement = screen.getByText(/Error ID:/);
    expect(errorIdElement).toBeInTheDocument();
    expect(errorIdElement.textContent).toMatch(/Error ID: error_\d+_[a-z0-9]+/);

    consoleSpy.mockRestore();
    consoleGroupSpy.mockRestore();
    consoleGroupEndSpy.mockRestore();
  });

  it('should show recovery suggestions', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { });
    const consoleGroupSpy = vi
      .spyOn(console, 'group')
      .mockImplementation(() => { });
    const consoleGroupEndSpy = vi
      .spyOn(console, 'groupEnd')
      .mockImplementation(() => { });

    render(
      React.createElement(
        ErrorBoundary,
        null,
        React.createElement(ErrorComponent)
      )
    );

    expect(screen.getByText('What you can try:')).toBeInTheDocument();
    expect(screen.getByText('Try refreshing the page')).toBeInTheDocument();
    expect(screen.getByText('Clear your browser cache')).toBeInTheDocument();

    consoleSpy.mockRestore();
    consoleGroupSpy.mockRestore();
    consoleGroupEndSpy.mockRestore();
  });

  it('should reset error when Try Again is clicked', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { });
    const consoleGroupSpy = vi
      .spyOn(console, 'group')
      .mockImplementation(() => { });
    const consoleGroupEndSpy = vi
      .spyOn(console, 'groupEnd')
      .mockImplementation(() => { });

    const { rerender } = render(
      React.createElement(
        ErrorBoundary,
        null,
        React.createElement(ErrorComponent, { shouldThrow: true })
      )
    );

    // Initially shows error
    expect(
      screen.getByText('Something Unexpected Happened')
    ).toBeInTheDocument();

    // Click Try Again
    const tryAgainButton = screen.getByRole('button', { name: /Try Again/i });
    fireEvent.click(tryAgainButton);

    // Rerender with shouldThrow: false
    rerender(
      React.createElement(
        ErrorBoundary,
        null,
        React.createElement(ErrorComponent, { shouldThrow: false })
      )
    );

    // Should now show normal content
    expect(screen.getByText('No error')).toBeInTheDocument();

    consoleSpy.mockRestore();
    consoleGroupSpy.mockRestore();
    consoleGroupEndSpy.mockRestore();
  });

  it('should show Go Home button', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { });
    const consoleGroupSpy = vi
      .spyOn(console, 'group')
      .mockImplementation(() => { });
    const consoleGroupEndSpy = vi
      .spyOn(console, 'groupEnd')
      .mockImplementation(() => { });

    render(
      React.createElement(
        ErrorBoundary,
        null,
        React.createElement(ErrorComponent)
      )
    );

    const goHomeButton = screen.getByRole('button', { name: /Go Home/i });
    expect(goHomeButton).toBeInTheDocument();

    consoleSpy.mockRestore();
    consoleGroupSpy.mockRestore();
    consoleGroupEndSpy.mockRestore();
  });

  it('should show Report Issue button when enabled', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { });
    const consoleGroupSpy = vi
      .spyOn(console, 'group')
      .mockImplementation(() => { });
    const consoleGroupEndSpy = vi
      .spyOn(console, 'groupEnd')
      .mockImplementation(() => { });

    render(
      React.createElement(
        ErrorBoundary,
        { showErrorReport: true },
        null,
        React.createElement(ErrorComponent)
      )
    );

    const reportButton = screen.getByRole('button', { name: /Report Issue/i });
    expect(reportButton).toBeInTheDocument();

    consoleSpy.mockRestore();
    consoleGroupSpy.mockRestore();
    consoleGroupEndSpy.mockRestore();
  });

  it('should copy error details to clipboard when Report Issue is clicked', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { });
    const consoleGroupSpy = vi
      .spyOn(console, 'group')
      .mockImplementation(() => { });
    const consoleGroupEndSpy = vi
      .spyOn(console, 'groupEnd')
      .mockImplementation(() => { });
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => { });

    render(
      React.createElement(
        ErrorBoundary,
        { showErrorReport: true },
        null,
        React.createElement(ErrorComponent)
      )
    );

    const reportButton = screen.getByRole('button', { name: /Report Issue/i });
    fireEvent.click(reportButton);

    expect(navigator.clipboard.writeText).toHaveBeenCalled();
    expect(alertSpy).toHaveBeenCalledWith(
      'Error details copied to clipboard. Please include this in your bug report.'
    );

    consoleSpy.mockRestore();
    consoleGroupSpy.mockRestore();
    consoleGroupEndSpy.mockRestore();
    alertSpy.mockRestore();
  });

  it('should call onError callback when provided', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { });
    const consoleGroupSpy = vi
      .spyOn(console, 'group')
      .mockImplementation(() => { });
    const consoleGroupEndSpy = vi
      .spyOn(console, 'groupEnd')
      .mockImplementation(() => { });

    const onErrorMock = vi.fn();

    render(
      React.createElement(
        ErrorBoundary,
        { onError: onErrorMock },
        null,
        React.createElement(ErrorComponent)
      )
    );

    expect(onErrorMock).toHaveBeenCalledWith(
      expect.any(Error),
      expect.any(Object), // errorInfo
      expect.stringMatching(/^error_\d+_[a-z0-9]+$/) // errorId
    );

    consoleSpy.mockRestore();
    consoleGroupSpy.mockRestore();
    consoleGroupEndSpy.mockRestore();
  });

  it('should show error context when provided', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { });
    const consoleGroupSpy = vi
      .spyOn(console, 'group')
      .mockImplementation(() => { });
    const consoleGroupEndSpy = vi
      .spyOn(console, 'groupEnd')
      .mockImplementation(() => { });

    render(
      React.createElement(
        ErrorBoundary,
        { errorContext: 'Recommendation Form' },
        null,
        React.createElement(ErrorComponent)
      )
    );

    expect(
      screen.getByText('Context: Recommendation Form')
    ).toBeInTheDocument();

    consoleSpy.mockRestore();
    consoleGroupSpy.mockRestore();
    consoleGroupEndSpy.mockRestore();
  });

  it('should use custom fallback when provided', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { });
    const consoleGroupSpy = vi
      .spyOn(console, 'group')
      .mockImplementation(() => { });
    const consoleGroupEndSpy = vi
      .spyOn(console, 'groupEnd')
      .mockImplementation(() => { });

    const CustomFallback = ({ resetError }: { resetError: () => void }) =>
      React.createElement(
        'div',
        { 'data-testid': 'custom-fallback' },
        React.createElement('button', { onClick: resetError }, 'Custom Reset')
      );

    render(
      React.createElement(
        ErrorBoundary,
        { fallback: CustomFallback },
        null,
        React.createElement(ErrorComponent)
      )
    );

    expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();
    expect(screen.getByText('Custom Reset')).toBeInTheDocument();

    consoleSpy.mockRestore();
    consoleGroupSpy.mockRestore();
    consoleGroupEndSpy.mockRestore();
  });
});
