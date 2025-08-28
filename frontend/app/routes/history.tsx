import { useState, useEffect } from 'react';
import {
  FileText,
  Calendar,
  User,
  Copy,
  Eye,
  EyeOff,
} from 'lucide-react';
import { recommendationApi } from '../services/api';
import type { HttpError, Recommendation } from '../types';
import { RecommendationSkeleton } from '../components/ui/loading-skeleton';
import ErrorBoundary from '../components/ui/error-boundary';

export default function HistoryPage() {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [expandedRecs, setExpandedRecs] = useState<Set<number>>(new Set());
  const [copiedIds, setCopiedIds] = useState<Set<number>>(new Set());

  useEffect(() => {
    loadRecommendations();
  }, []);

  const loadRecommendations = async () => {
    try {
      setIsLoading(true);
      setError('');
      const data = await recommendationApi.getAll();
      setRecommendations(data);
    } catch (err: unknown) {
      const error = err as HttpError;
      setError(error.response?.data?.detail || 'Failed to load recommendations');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleExpanded = (id: number) => {
    const newExpanded = new Set(expandedRecs);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedRecs(newExpanded);
  };

  const handleCopy = async (rec: Recommendation) => {
    try {
      await navigator.clipboard.writeText(rec.content);
      const newCopied = new Set(copiedIds);
      newCopied.add(rec.id);
      setCopiedIds(newCopied);
      setTimeout(() => {
        setCopiedIds(prev => {
          const updated = new Set(prev);
          updated.delete(rec.id);
          return updated;
        });
      }, 2000);
    } catch (err) {
      // Fallback for browsers that don't support clipboard API
      console.error('Failed to copy to clipboard', err);
    }
  };

  return (
    <ErrorBoundary>
      <div className='max-w-6xl mx-auto space-y-8'>
        <div className='text-center space-y-4'>
          <h1 className='text-3xl font-bold text-gray-900'>
            Recommendation History
          </h1>
          <p className='text-lg text-gray-600'>
            View and manage all your generated recommendations
          </p>
        </div>

        {isLoading ? (
          <RecommendationSkeleton />
        ) : error ? (
          <div className='rounded-lg border border-red-200 bg-red-50 shadow-sm'>
            <div className='p-6 text-center'>
              <p className='text-red-600 mb-4'>{error}</p>
              <button
                onClick={loadRecommendations}
                className='inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-blue-600 text-white shadow hover:bg-blue-700 active:bg-blue-800 h-9 px-4 py-2'
              >
                Retry
              </button>
            </div>
          </div>
        ) : recommendations.length === 0 ? (
          <div className='rounded-lg border border-gray-200 bg-white shadow-sm'>
            <div className='p-6 pt-0 text-center py-12'>
              <FileText className='w-12 h-12 text-gray-400 mx-auto mb-4' />
              <h3 className='text-lg font-medium text-gray-900 mb-2'>
                No recommendations yet
              </h3>
              <p className='text-gray-600 mb-6'>
                Generate your first recommendation to see it here
              </p>
              <a
                href='/generate'
                className='inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-blue-600 text-white shadow hover:bg-blue-700 active:bg-blue-800 h-9 px-4 py-2'
              >
                Generate Recommendation
              </a>
            </div>
          </div>
        ) : (
          <div className='space-y-6'>
            {recommendations.map(rec => {
              const isExpanded = expandedRecs.has(rec.id);
              const isCopied = copiedIds.has(rec.id);
              return (
                <div
                  key={rec.id}
                  className='rounded-lg border border-gray-200 bg-white shadow-sm'
                >
                  <div className='flex flex-col space-y-1.5 p-6 pb-4'>
                    <div className='flex items-start justify-between'>
                      <div className='space-y-1 flex-1'>
                        <h3 className='text-lg font-semibold leading-none tracking-tight'>
                          {rec.title ||
                            `${rec.recommendation_type} recommendation for ${rec.github_username}`}
                        </h3>
                        <div className='flex items-center space-x-4 text-sm text-gray-600 flex-wrap'>
                          <div className='flex items-center space-x-1'>
                            <User className='w-4 h-4' />
                            <span>{rec.github_username}</span>
                          </div>
                          <div className='flex items-center space-x-1'>
                            <Calendar className='w-4 h-4' />
                            <span>
                              {new Date(rec.created_at).toLocaleDateString()}
                            </span>
                          </div>
                          <span className='inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-800'>
                            {rec.recommendation_type}
                          </span>
                          <span className='inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-800'>
                            {rec.word_count} words
                          </span>
                          <span className='inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-purple-100 text-purple-800'>
                            {rec.tone}
                          </span>
                          <span className='inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-800'>
                            {rec.length}
                          </span>
                        </div>
                      </div>
                      <div className='flex space-x-2 ml-4'>
                        <button
                          onClick={() => toggleExpanded(rec.id)}
                          className='inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 border border-gray-300 bg-white text-gray-700 shadow-sm hover:bg-gray-50 active:bg-gray-100 h-8 px-3 text-xs space-x-1'
                          aria-label={
                            isExpanded
                              ? 'Hide recommendation content'
                              : 'View full recommendation content'
                          }
                          aria-expanded={isExpanded}
                        >
                          {isExpanded ? (
                            <EyeOff className='w-3 h-3' />
                          ) : (
                            <Eye className='w-3 h-3' />
                          )}
                          <span className='hidden sm:inline'>
                            {isExpanded ? 'Hide' : 'View'}
                          </span>
                        </button>
                        <button
                          onClick={() => handleCopy(rec)}
                          className='inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 border border-gray-300 bg-white text-gray-700 shadow-sm hover:bg-gray-50 active:bg-gray-100 h-8 px-3 text-xs space-x-1'
                          aria-label={`Copy recommendation content to clipboard`}
                        >
                          <Copy className='w-3 h-3' />
                          <span className='hidden sm:inline'>
                            {isCopied ? 'Copied!' : 'Copy'}
                          </span>
                        </button>
                      </div>
                    </div>
                  </div>
                  <div className='p-6 pt-0'>
                    <div
                      className={`text-gray-700 leading-relaxed ${isExpanded ? '' : 'line-clamp-3'}`}
                    >
                      <p className='whitespace-pre-wrap'>{rec.content}</p>
                    </div>
                    {!isExpanded && rec.content.length > 200 && (
                      <button
                        onClick={() => toggleExpanded(rec.id)}
                        className='mt-2 text-blue-600 hover:text-blue-700 text-sm font-medium'
                      >
                        Read more...
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
}
