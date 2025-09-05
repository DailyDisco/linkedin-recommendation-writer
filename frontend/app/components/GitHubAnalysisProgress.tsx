import React from 'react';
import { Loader2, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import type { GitHubAnalysisProgress } from '../hooks/useGitHubAnalysisStream';

interface GitHubAnalysisProgressProps {
  progress: GitHubAnalysisProgress | null;
  isStreaming: boolean;
  error: string | null;
}

export const GitHubAnalysisProgress: React.FC<GitHubAnalysisProgressProps> = ({
  progress,
  isStreaming,
  error,
}) => {
  if (!progress && !isStreaming && !error) {
    return null;
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className='w-5 h-5 text-green-600' />;
      case 'failed':
      case 'error':
      case 'not_found':
        return <XCircle className='w-5 h-5 text-red-600' />;
      case 'processing':
        return <Loader2 className='w-5 h-5 text-blue-600 animate-spin' />;
      default:
        return <AlertCircle className='w-5 h-5 text-yellow-600' />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-700 bg-green-50 border-green-200';
      case 'failed':
      case 'error':
      case 'not_found':
        return 'text-red-700 bg-red-50 border-red-200';
      case 'processing':
        return 'text-blue-700 bg-blue-50 border-blue-200';
      default:
        return 'text-gray-700 bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50'>
      <div className='bg-white rounded-lg shadow-xl max-w-md w-full p-6'>
        <div className='flex items-center space-x-3 mb-4'>
          {progress && getStatusIcon(progress.status)}
          <h3 className='text-lg font-semibold text-gray-900'>
            GitHub Analysis Progress
          </h3>
        </div>

        {error && (
          <div className='mb-4 p-3 bg-red-50 border border-red-200 rounded-lg'>
            <div className='flex items-center space-x-2'>
              <XCircle className='w-4 h-4 text-red-600' />
              <span className='text-red-700 text-sm'>{error}</span>
            </div>
          </div>
        )}

        {progress && (
          <div className='space-y-4'>
            <div
              className={`p-4 rounded-lg border ${getStatusColor(progress.status)}`}
            >
              <div className='flex items-center justify-between mb-2'>
                <span className='font-medium'>Status</span>
                <span className='text-sm capitalize'>{progress.status}</span>
              </div>

              {progress.stage && (
                <div className='mb-2'>
                  <p className='text-sm'>{progress.stage}</p>
                </div>
              )}

              <div className='mb-2'>
                <div className='flex items-center justify-between text-sm mb-1'>
                  <span>Progress</span>
                  <span>{progress.progress}%</span>
                </div>
                <div className='w-full bg-gray-200 rounded-full h-2'>
                  <div
                    className='bg-blue-600 h-2 rounded-full transition-all duration-300'
                    style={{ width: `${progress.progress}%` }}
                  />
                </div>
              </div>

              {progress.username && (
                <div className='text-sm text-gray-600'>
                  Analyzing: @{progress.username}
                </div>
              )}
            </div>

            {progress.timestamp && (
              <div className='text-xs text-gray-500 text-center'>
                Last updated:{' '}
                {new Date(progress.timestamp).toLocaleTimeString()}
              </div>
            )}
          </div>
        )}

        {isStreaming && !progress && (
          <div className='text-center py-8'>
            <Loader2 className='w-8 h-8 animate-spin text-blue-600 mx-auto mb-4' />
            <p className='text-gray-600'>Connecting to analysis stream...</p>
          </div>
        )}
      </div>
    </div>
  );
};
