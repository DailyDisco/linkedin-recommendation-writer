import { useEffect, useState } from 'react';
import { FileText, Loader2, AlertCircle } from 'lucide-react';
import { recommendationApi } from '../services/api';
import type { Recommendation } from '../types';
import { formatDate } from '../utils/formatDate';
import ErrorBoundary from '../components/ui/error-boundary';
import { useAuth } from '../hooks/useAuth';
import { Link } from 'react-router';
import { PleaseSignInOrRegister } from '../components/PleaseSignInOrRegister';

const RecommendationsHistory = () => {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isLoggedIn } = useAuth(); // Get authentication status from context

  useEffect(() => {
    const fetchRecommendations = async () => {
      if (!isLoggedIn) {
        setIsLoading(false);
        setRecommendations([]);
        return;
      }
      try {
        setIsLoading(true);
        setError(null);
        const data = await recommendationApi.getAll();
        setRecommendations(data);
      } catch (err) {
        console.error('Failed to fetch recommendations:', err);
        setError('Failed to load recommendations. Please try again later.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchRecommendations();
  }, [isLoggedIn]);

  if (!isLoggedIn) {
    return <PleaseSignInOrRegister />;
  }

  return (
    <ErrorBoundary>
      <div className='max-w-4xl mx-auto space-y-8'>
        <div className='text-center space-y-4'>
          <h1 className='text-3xl font-bold text-gray-900'>
            Your Recommendation History
          </h1>
          <p className='text-lg text-gray-600'>
            View and manage all the LinkedIn recommendations you&apos;ve
            generated.
          </p>
        </div>

        {isLoading ? (
          <div className='text-center py-12'>
            <Loader2 className='w-12 h-12 animate-spin text-blue-600 mx-auto mb-4' />
            <p className='text-gray-600'>Loading your recommendations...</p>
          </div>
        ) : error ? (
          <div className='bg-red-50 border border-red-200 rounded-md p-6 text-center text-red-700 flex items-center justify-center space-x-3'>
            <AlertCircle className='w-5 h-5' />
            <p>{error}</p>
          </div>
        ) : recommendations.length === 0 ? (
          <div className='bg-gray-50 rounded-lg p-6 text-center text-gray-500'>
            <FileText className='w-12 h-12 mx-auto mb-4 text-gray-400' />
            <p className='text-lg font-medium'>No recommendations yet!</p>
            <p className='mt-2'>
              Start generating personalized LinkedIn recommendations from the
              <Link to='/generate' className='text-blue-600 hover:underline'>
                {' '}
                Generate page
              </Link>
              .
            </p>
          </div>
        ) : (
          <div className='space-y-4'>
            {recommendations.map(rec => (
              <div
                key={rec.id}
                className='bg-white border border-gray-200 rounded-lg shadow-sm p-6 space-y-3'
              >
                <div className='flex justify-between items-center'>
                  <h2 className='text-xl font-semibold text-gray-900'>
                    Recommendation for {rec.github_username}
                  </h2>
                  <span className='text-sm text-gray-500'>
                    {formatDate(rec.created_at)}
                  </span>
                </div>
                <p className='text-gray-700 whitespace-pre-wrap'>
                  {rec.content}
                </p>
                <div className='flex flex-wrap gap-2 text-sm text-gray-600'>
                  <span className='px-2 py-1 bg-gray-100 rounded-full'>
                    Type: {rec.recommendation_type}
                  </span>
                  <span className='px-2 py-1 bg-gray-100 rounded-full'>
                    Tone: {rec.tone}
                  </span>
                  <span className='px-2 py-1 bg-gray-100 rounded-full'>
                    Length: {rec.length}
                  </span>
                  <span className='px-2 py-1 bg-gray-100 rounded-full'>
                    Words: {rec.word_count}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
};

export default RecommendationsHistory;
