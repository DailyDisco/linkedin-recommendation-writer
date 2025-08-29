import {
  isRouteErrorResponse,
  Links,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
  useRouteError,
} from 'react-router';
// import type { Route } from './+types/root';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppLayout } from './layout';
import UIErrorBoundary from './components/ui/error-boundary';
import './styles/index.css';
import { AuthProvider } from './hooks';


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

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang='en'>
      <head>
        <meta charSet='utf-8' />
        <meta name='viewport' content='width=device-width, initial-scale=1' />
        <meta
          name='description'
          content='Generate professional LinkedIn recommendations using GitHub data and AI. Analyze commits, PRs, and contributions to create compelling recommendations.'
        />
        <meta
          name='keywords'
          content='LinkedIn, recommendations, GitHub, AI, professional, networking, career'
        />
        <meta name='author' content='LinkedIn Recommendation Writer' />

        {/* Open Graph / Social Media */}
        <meta property='og:type' content='website' />
        <meta
          property='og:title'
          content='LinkedIn Recommendation Writer - AI-Powered Professional Recommendations'
        />
        <meta
          property='og:description'
          content='Generate personalized LinkedIn recommendations from GitHub data using AI. Transform technical contributions into compelling professional narratives.'
        />
        <meta
          property='og:site_name'
          content='LinkedIn Recommendation Writer'
        />

        {/* Twitter Card */}
        <meta name='twitter:card' content='summary_large_image' />
        <meta name='twitter:title' content='LinkedIn Recommendation Writer' />
        <meta
          name='twitter:description'
          content='Generate professional LinkedIn recommendations using GitHub data and AI'
        />

        {/* Favicon */}
        <link rel='icon' type='image/svg+xml' href='/favicon.svg' />
        <link rel='icon' type='image/png' href='/favicon.png' />

        <Meta />
        <Links />
      </head>
      <body>
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}

export default function Root() {
  return (
    <UIErrorBoundary>
      <AuthProvider>
        <AppLayout>
          <Outlet />
        </AppLayout>
      </AuthProvider>
    </UIErrorBoundary>
  );
}

export function ErrorBoundary() {
  const error = useRouteError();

  return (
    <html lang='en'>
      <head>
        <title>Oh no!</title>
        <Meta />
        <Links />
      </head>
      <body>
        <div className='min-h-screen bg-gray-50 flex items-center justify-center'>
          <div className='text-center'>
            <h1 className='text-4xl font-bold text-gray-900 mb-4'>Oops!</h1>
            {isRouteErrorResponse(error) ? (
              <div>
                <h2 className='text-2xl font-semibold text-gray-700 mb-2'>
                  {error.status} {error.statusText}
                </h2>
                <p className='text-gray-600'>{error.data}</p>
              </div>
            ) : error instanceof Error ? (
              <div>
                <h2 className='text-2xl font-semibold text-gray-700 mb-2'>
                  Error
                </h2>
                <p className='text-gray-600'>{error.message}</p>
              </div>
            ) : (
              <h2 className='text-2xl font-semibold text-gray-700'>
                Unknown Error
              </h2>
            )}
          </div>
        </div>
        <Scripts />
      </body>
    </html>
  );
}
