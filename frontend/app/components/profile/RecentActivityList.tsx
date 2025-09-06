import React from 'react';
import { Link } from 'react-router';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { TrendingUp, FileText, Info } from 'lucide-react';
import { useUserRecommendations } from '../../hooks/useRecommendationQueries';
import { formatDate } from '../../utils/formatDate';
import { RecommendationSkeleton } from '../ui/loading-skeleton';
import { ErrorAlert } from '../ui/error-alert';
import type { Recommendation } from '../../types';

interface RecentActivityListProps {
  githubUsername?: string;
}

export const RecentActivityList: React.FC<RecentActivityListProps> = ({
  githubUsername,
}) => {
  const {
    data: recommendations,
    isLoading,
    isError,
    error,
  } = useUserRecommendations(githubUsername, true);

  const displayRecommendations =
    recommendations?.recommendations.slice(0, 5) || []; // Show up to 5 recent activities

  if (isLoading) {
    return <RecommendationSkeleton count={3} />; // Show skeleton for loading state
  }

  if (isError) {
    const errorMessage =
      error instanceof Error ? error.message : 'An unknown error occurred.';
    return (
      <div className='p-4'>
        <ErrorAlert
          title='Failed to load activity'
          message={errorMessage}
          suggestions={[
            'Check your internet connection.',
            'Try refreshing the page.',
          ]}
          showRetryButton
          onRetry={() => {
            /* Implement retry logic or refetch */
          }}
        />
      </div>
    );
  }

  if (!displayRecommendations || displayRecommendations.length === 0) {
    return (
      <div className='p-4 text-center text-muted-foreground'>
        <Info className='mx-auto h-8 w-8 text-gray-400 mb-3' />
        <p className='text-lg font-medium'>No Recent Activity</p>
        <p className='text-sm'>
          Generate your first recommendation to see it here!
        </p>
        <Link to='/generate' className='mt-4 inline-block'>
          <Button variant='secondary'>
            <FileText className='w-4 h-4 mr-2' />
            Generate Recommendation
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <Card className='shadow-sm hover:shadow-md transition-shadow duration-300'>
      <CardHeader>
        <CardTitle className='flex items-center gap-2'>
          <TrendingUp className='w-5 h-5' />
          Recent Activity
        </CardTitle>
        <CardDescription>
          Your latest recommendations and activities
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className='space-y-4'>
          {displayRecommendations.map((rec: Recommendation) => (
            <div
              key={rec.id}
              className='flex items-center gap-4 p-3 border rounded-lg hover:bg-gray-50 transition-colors duration-200'
            >
              <div className='w-2 h-2 bg-blue-500 rounded-full'></div>
              <div className='flex-1'>
                <p className='text-sm font-medium'>
                  {rec.title || `Recommendation for ${rec.github_username}`}
                </p>
                <p className='text-xs text-muted-foreground'>
                  Generated on {formatDate(rec.created_at)}
                </p>
              </div>
              <Link to={`/history/${rec.id}`}>
                <Button variant='outline' size='sm'>
                  View
                </Button>
              </Link>
            </div>
          ))}
        </div>
        <div className='mt-4'>
          <Link to='/history'>
            <Button variant='outline' size='sm' className='w-full'>
              View All Activity
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
};
