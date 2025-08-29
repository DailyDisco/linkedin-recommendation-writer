import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '../hooks/auth-context';
import UIErrorBoundary from '../components/ui/error-boundary';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

interface RootProviderProps {
  children: React.ReactNode;
}

export const RootProvider = ({ children }: RootProviderProps) => {
  return (
    <UIErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>{children}</AuthProvider>
      </QueryClientProvider>
    </UIErrorBoundary>
  );
};
