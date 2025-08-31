import React, { useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'sonner';
import UIErrorBoundary from '../components/ui/error-boundary';
import { initializeGA4 } from '../utils/analytics';

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
  // Initialize Google Analytics 4
  useEffect(() => {
    initializeGA4();
  }, []);

  return (
    <UIErrorBoundary>
      <QueryClientProvider client={queryClient}>
        {children}
        <Toaster position='top-right' richColors />
      </QueryClientProvider>
    </UIErrorBoundary>
  );
};
