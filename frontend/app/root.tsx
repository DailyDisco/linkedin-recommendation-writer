import {
  isRouteErrorResponse,
  Links,
  Meta,
  Outlet,
  Scripts,
  useRouteError,
} from 'react-router';
// import type { Route } from './+types/root';
import './styles/index.css';
import { AppLayout } from './layouts/AppLayout';
import { RootProvider } from './providers/RootProvider';
import { RootHtmlDocument } from './layouts/RootHtmlDocument';
import { initializeGlobalErrorHandling } from './utils/globalErrorHandler';

// Initialize global error handling
if (typeof window !== 'undefined') {
  initializeGlobalErrorHandling();
}

export default function Root() {
  return (
    <RootHtmlDocument>
      <RootProvider>
        <AppLayout>
          <Outlet />
        </AppLayout>
      </RootProvider>
    </RootHtmlDocument>
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
