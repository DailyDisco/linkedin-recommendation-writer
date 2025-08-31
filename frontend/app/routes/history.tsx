import { useEffect, useState, useRef, useCallback } from 'react';
import { FileText, Loader2, History } from 'lucide-react';
import { toast } from 'sonner';
import { recommendationApi, apiClient } from '../services/api';
import type { Recommendation } from '../types';
import { formatDate } from '../utils/formatDate';
import ErrorBoundary from '../components/ui/error-boundary';
import { useAuth } from '../hooks/useAuth';
import { Link } from 'react-router';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { VersionHistory } from '@/components/VersionHistory';
import { PleaseSignInOrRegister } from '../components/PleaseSignInOrRegister';
import { KeywordRefinement } from '../components/KeywordRefinement';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import type { KeywordRefinementResult } from '../types';
import { trackEngagement } from '../utils/analytics';

const RecommendationsHistory = () => {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedRecId, setSelectedRecId] = useState<number | null>(null);
  const { isLoggedIn } = useAuth(); // Get authentication status from context
  const hasShownToastRef = useRef<boolean>(false); // Track if toast has been shown

  // Reset toast flag when user logs out
  useEffect(() => {
    if (!isLoggedIn) {
      hasShownToastRef.current = false;
    }
  }, [isLoggedIn]);

  const fetchRecommendations = useCallback(async () => {
    if (!isLoggedIn) {
      setIsLoading(false);
      setRecommendations([]);
      return;
    }
    try {
      setIsLoading(true);
      const data = await recommendationApi.getAll();
      setRecommendations(data);

      // Track history page view with recommendation count
      trackEngagement.viewHistory();

      if (data.length > 0 && !hasShownToastRef.current) {
        toast.success(
          `Loaded ${data.length} recommendation${data.length === 1 ? '' : 's'} from your history!`
        );
        hasShownToastRef.current = true;
      }
    } catch (err) {
      console.error('Failed to fetch recommendations:', err);
      toast.error('Failed to load recommendations. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  }, [isLoggedIn]);

  useEffect(() => {
    fetchRecommendations();
  }, [fetchRecommendations]);

  // Version History API handlers
  const handleGetVersionHistory = async (recommendationId: number) => {
    try {
      const history = await apiClient.getVersionHistory(recommendationId);
      return history;
    } catch (error) {
      console.error('Failed to get version history:', error);
      toast.error('Failed to load version history');
      throw error;
    }
  };

  const handleCompareVersions = async (
    recommendationId: number,
    versionA: number,
    versionB: number
  ) => {
    try {
      const comparison = await apiClient.compareVersions(
        recommendationId,
        versionA,
        versionB
      );
      return comparison;
    } catch (error) {
      console.error('Failed to compare versions:', error);
      toast.error('Failed to compare versions');
      throw error;
    }
  };

  const handleRevertVersion = async (
    recommendationId: number,
    versionId: number,
    reason: string
  ): Promise<void> => {
    try {
      const data = { version_id: versionId, revert_reason: reason };
      await apiClient.revertVersion(recommendationId, data);
      toast.success('Successfully reverted to previous version');
      // Refresh the recommendations list
      fetchRecommendations();
    } catch (error) {
      console.error('Failed to revert version:', error);
      toast.error('Failed to revert version');
      throw error;
    }
  };

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
                  <div className='flex items-center gap-2'>
                    <Button
                      variant='outline'
                      size='sm'
                      onClick={() => setSelectedRecId(rec.id)}
                      className='flex items-center gap-1'
                    >
                      <History className='w-4 h-4' />
                      View History
                    </Button>
                    <span className='text-sm text-gray-500'>
                      {formatDate(rec.created_at)}
                    </span>
                  </div>
                </div>
                {/* Add Tabs for content and refinement */}
                <Tabs defaultValue='content' className='w-full'>
                  <TabsList className='grid w-full grid-cols-2 h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground'>
                    <TabsTrigger
                      value='content'
                      className='inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm'
                    >
                      Content
                    </TabsTrigger>
                    <TabsTrigger
                      value='refine'
                      className='inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm'
                    >
                      Refine
                    </TabsTrigger>
                  </TabsList>
                  <TabsContent value='content'>
                    <p className='text-gray-700 whitespace-pre-wrap'>
                      {rec.content}
                    </p>
                  </TabsContent>
                  <TabsContent value='refine'>
                    <KeywordRefinement
                      recommendationId={rec.id}
                      onRefinementComplete={(
                        refinedContent: KeywordRefinementResult
                      ) => {
                        // Update recommendation content
                        setRecommendations(prev =>
                          prev.map(r =>
                            r.id === rec.id
                              ? {
                                  ...r,
                                  content: refinedContent.refined_content,
                                }
                              : r
                          )
                        );
                        toast.success('Recommendation refined successfully');
                      }}
                    />
                  </TabsContent>
                </Tabs>
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

        {/* Version History Modal */}
        <Dialog
          open={!!selectedRecId}
          onOpenChange={() => setSelectedRecId(null)}
        >
          <DialogContent className='max-w-4xl max-h-[80vh] overflow-y-auto'>
            <DialogHeader>
              <DialogTitle>Version History</DialogTitle>
              <DialogDescription>
                Track changes and manage versions of this recommendation
              </DialogDescription>
            </DialogHeader>
            {selectedRecId && (
              <VersionHistory
                recommendationId={selectedRecId}
                onGetHistory={handleGetVersionHistory}
                onCompareVersions={handleCompareVersions}
                onRevertToVersion={handleRevertVersion}
              />
            )}
          </DialogContent>
        </Dialog>
      </div>
    </ErrorBoundary>
  );
};

export default RecommendationsHistory;
