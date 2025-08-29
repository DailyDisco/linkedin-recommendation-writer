import React from 'react';

interface AuthLayoutProps {
  children: React.ReactNode;
}

export const AuthLayout = ({ children }: AuthLayoutProps) => {
  return (
    <div className='min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex flex-col'>
      {/* Header with logo/branding */}
      <header className='py-6'>
        <div className='max-w-md mx-auto px-4 text-center'>
          <h1 className='text-2xl font-bold text-gray-900'>
            LinkedIn Recommendation Writer
          </h1>
          <p className='text-sm text-gray-600 mt-1'>
            AI-powered professional recommendations
          </p>
        </div>
      </header>

      {/* Main content - centered auth forms */}
      <main className='flex-1 flex items-center justify-center px-4'>
        <div className='w-full max-w-md'>{children}</div>
      </main>

      {/* Minimal footer */}
      <footer className='py-4'>
        <div className='text-center text-xs text-gray-500'>
          <p>Secure authentication powered by modern web technologies</p>
        </div>
      </footer>
    </div>
  );
};
