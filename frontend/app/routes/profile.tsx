import React from 'react';
import { AdvancedFeatures } from '@/components/AdvancedFeatures';
import { useAuth } from '../hooks/useAuth';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Sparkles,
  User,
  Database,
  TrendingUp,
  Calendar,
  Mail,
  Edit,
  Plus,
  BarChart3,
  Settings,
  RefreshCw,
} from 'lucide-react';
import { apiClient } from '@/services/api';
import type { ReadmeGenerationData, SkillAnalysisData } from '../types/index';
import { PleaseSignInOrRegister } from '../components/PleaseSignInOrRegister';
import { Link } from 'react-router';
import { trackEngagement } from '../utils/analytics';

export default function UserProfilePage() {
  const {
    isLoggedIn,
    userDetails,
    userRecommendationCount,
    userDailyLimit,
    isLoadingUserDetails,
    fetchUserDetails,
  } = useAuth();

  // Track profile page view
  React.useEffect(() => {
    trackEngagement.viewProfile();
  }, []);

  // Fetch user details on mount if not already loaded
  React.useEffect(() => {
    if (isLoggedIn && !userDetails && !isLoadingUserDetails) {
      fetchUserDetails();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLoggedIn, userDetails, isLoadingUserDetails]); // Remove fetchUserDetails from dependencies to prevent infinite loop

  const handleRefresh = () => {
    fetchUserDetails(true); // Force refresh
  };

  // Generate avatar initials from username or email
  const getAvatarInitials = (username: string, email: string) => {
    if (username) return username.slice(0, 2).toUpperCase();
    if (email) return email.slice(0, 2).toUpperCase();
    return 'U';
  };

  // Format date for display
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  if (!isLoggedIn) {
    return <PleaseSignInOrRegister />;
  }

  const handleReadmeGeneration = async (data: ReadmeGenerationData) => {
    try {
      const response = await apiClient.generateReadme(data);
      console.log('README generation successful:', response);
      return response;
    } catch (error) {
      console.error('README generation failed:', error);
      throw error;
    }
  };

  const handleSkillAnalysis = async (data: SkillAnalysisData) => {
    try {
      const response = await apiClient.analyzeSkillGaps(data);
      console.log('Skill gap analysis successful:', response);
      return response;
    } catch (error) {
      console.error('Skill gap analysis failed:', error);
      throw error;
    }
  };

  const recommendationProgress =
    userDailyLimit && userRecommendationCount
      ? (userRecommendationCount / userDailyLimit) * 100
      : 0;

  return (
    <div className='container mx-auto p-6 space-y-8'>
      <div className='text-center'>
        <div className='flex items-center justify-center gap-4 mb-2'>
          <h1 className='text-4xl font-bold tracking-tight lg:text-5xl bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent'>
            Profile Dashboard
          </h1>
          {isLoadingUserDetails && (
            <RefreshCw className='w-6 h-6 animate-spin text-blue-600' />
          )}
        </div>
        <div className='flex items-center justify-center gap-2'>
          <p className='text-lg text-muted-foreground'>
            Manage your account and access powerful AI features ✨
          </p>
          <Button
            variant='ghost'
            size='sm'
            onClick={handleRefresh}
            disabled={isLoadingUserDetails}
            className='hover:bg-blue-50'
          >
            <RefreshCw
              className={`w-4 h-4 ${isLoadingUserDetails ? 'animate-spin' : ''}`}
            />
          </Button>
        </div>
      </div>

      {/* Profile Information */}
      <Card className='shadow-sm hover:shadow-md transition-shadow duration-300'>
        <CardHeader>
          <CardTitle className='flex items-center gap-2'>
            <User className='w-5 h-5' />
            Profile Information
          </CardTitle>
          <CardDescription>
            Your account details and current status
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className='flex items-start gap-6'>
            <div className='relative'>
              {isLoadingUserDetails ? (
                <Skeleton className='w-20 h-20 rounded-full' />
              ) : (
                <Avatar className='w-20 h-20 ring-2 ring-blue-200'>
                  <AvatarFallback className='bg-gray-600 text-white font-medium'>
                    {userDetails
                      ? getAvatarInitials(
                          userDetails.username,
                          userDetails.email
                        )
                      : 'U'}
                  </AvatarFallback>
                </Avatar>
              )}
            </div>
            <div className='flex-1 space-y-4'>
              <div>
                {isLoadingUserDetails ? (
                  <div className='space-y-2'>
                    <Skeleton className='h-8 w-48' />
                    <Skeleton className='h-4 w-32' />
                  </div>
                ) : (
                  <>
                    <h3 className='text-2xl font-semibold text-gray-900'>
                      {userDetails?.full_name ||
                        userDetails?.username ||
                        'User'}
                    </h3>
                    <p className='text-muted-foreground'>
                      @{userDetails?.username}
                    </p>
                  </>
                )}
              </div>
              <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
                {isLoadingUserDetails ? (
                  <>
                    <Skeleton className='h-4 w-32' />
                    <Skeleton className='h-4 w-40' />
                    <Skeleton className='h-4 w-36' />
                    <Skeleton className='h-6 w-16' />
                  </>
                ) : (
                  <>
                    <div className='flex items-center gap-2'>
                      <Mail className='w-4 h-4 text-muted-foreground' />
                      <span className='text-sm'>{userDetails?.email}</span>
                    </div>
                    <div className='flex items-center gap-2'>
                      <Calendar className='w-4 h-4 text-muted-foreground' />
                      <span className='text-sm'>
                        Last active:{' '}
                        {formatDate(
                          userDetails?.last_recommendation_date ?? null
                        )}
                      </span>
                    </div>
                    <div className='flex items-center gap-2'>
                      <Database className='w-4 h-4 text-muted-foreground' />
                      <span className='text-sm'>
                        {userRecommendationCount} recommendations created
                      </span>
                    </div>
                    <div className='flex items-center gap-2'>
                      <Badge
                        variant={
                          userDetails?.is_active ? 'default' : 'secondary'
                        }
                      >
                        {userDetails?.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </div>
                  </>
                )}
              </div>
            </div>
            <Button variant='outline' size='sm'>
              <Edit className='w-4 h-4 mr-2' />
              Edit Profile
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className='grid grid-cols-1 md:grid-cols-2 gap-6'>
        {/* Usage Analytics */}
        <Card className='shadow-sm hover:shadow-md transition-shadow duration-300'>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>
              📊 Today&apos;s Usage
            </CardTitle>
            <BarChart3 className='h-4 w-4 text-blue-600' />
          </CardHeader>
          <CardContent>
            {isLoadingUserDetails ? (
              <div className='space-y-3'>
                <Skeleton className='h-8 w-24' />
                <Skeleton className='h-4 w-48' />
                <Skeleton className='h-2 w-full' />
                <Skeleton className='h-4 w-32' />
              </div>
            ) : (
              <>
                <div className='text-3xl font-bold text-gray-900'>
                  {userRecommendationCount !== null
                    ? userRecommendationCount
                    : 'N/A'}{' '}
                  <span className='text-lg text-muted-foreground'>/</span>{' '}
                  {userDailyLimit !== null ? userDailyLimit : 'N/A'}
                </div>
                <p className='text-xs text-muted-foreground mb-3'>
                  Recommendations generated today
                </p>
                <Progress value={recommendationProgress} className='h-2' />
                <div className='mt-3 text-xs text-muted-foreground'>
                  {userDailyLimit && userRecommendationCount !== null
                    ? `${userDailyLimit - userRecommendationCount} recommendations remaining`
                    : 'Loading usage data...'}
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Quick Actions Panel */}
        <Card className='shadow-sm hover:shadow-md transition-shadow duration-300'>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>
              ⚡ Quick Actions
            </CardTitle>
            <Sparkles className='h-4 w-4 text-purple-600' />
          </CardHeader>
          <CardContent className='space-y-3'>
            <Link to='/generate'>
              <Button
                className='w-full justify-start hover:bg-gray-50 transition-colors duration-200'
                variant='outline'
              >
                <Plus className='w-4 h-4 mr-2' />
                Generate New Recommendation
              </Button>
            </Link>
            <Link to='/history'>
              <Button
                className='w-full justify-start hover:bg-gray-50 transition-colors duration-200'
                variant='outline'
              >
                <Database className='w-4 h-4 mr-2' />
                View History
              </Button>
            </Link>
            <Button
              className='w-full justify-start hover:bg-gray-50 transition-colors duration-200'
              variant='outline'
            >
              <Settings className='w-4 h-4 mr-2' />
              Account Settings
            </Button>
          </CardContent>
        </Card>
      </div>

      <div className='grid grid-cols-1 lg:grid-cols-3 gap-6'>
        {/* Recent Activity Feed */}
        <Card className='lg:col-span-2 shadow-sm hover:shadow-md transition-shadow duration-300'>
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
              {/* Placeholder for recent activity - will be enhanced later */}
              <div className='flex items-center gap-4 p-3 border rounded-lg hover:bg-gray-50 transition-colors duration-200'>
                <div className='w-2 h-2 bg-blue-500 rounded-full'></div>
                <div className='flex-1'>
                  <p className='text-sm font-medium'>
                    Welcome to your profile!
                  </p>
                  <p className='text-xs text-muted-foreground'>
                    Your account is ready to use
                  </p>
                </div>
                <span className='text-xs text-muted-foreground'>Just now</span>
              </div>
              <div className='flex items-center gap-4 p-3 border rounded-lg hover:bg-gray-50 transition-colors duration-200'>
                <div className='w-2 h-2 bg-green-500 rounded-full'></div>
                <div className='flex-1'>
                  <p className='text-sm font-medium'>
                    Advanced features unlocked
                  </p>
                  <p className='text-xs text-muted-foreground'>
                    Access to AI-powered tools
                  </p>
                </div>
                <span className='text-xs text-muted-foreground'>Today</span>
              </div>
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

        {/* Settings Panel */}
        <Card className='shadow-sm hover:shadow-md transition-shadow duration-300'>
          <CardHeader>
            <CardTitle className='flex items-center gap-2'>
              <Settings className='w-5 h-5' />
              Settings
            </CardTitle>
            <CardDescription>Manage your preferences</CardDescription>
          </CardHeader>
          <CardContent className='space-y-4'>
            <div className='space-y-3'>
              <div className='flex items-center justify-between'>
                <span className='text-sm font-medium'>Email Notifications</span>
                <Button variant='outline' size='sm'>
                  Configure
                </Button>
              </div>
              <div className='flex items-center justify-between'>
                <span className='text-sm font-medium'>Default Tone</span>
                <span className='text-sm text-muted-foreground'>
                  Professional
                </span>
              </div>
              <div className='flex items-center justify-between'>
                <span className='text-sm font-medium'>Language</span>
                <span className='text-sm text-muted-foreground'>English</span>
              </div>
            </div>
            <div className='pt-4 border-t'>
              <Button variant='outline' size='sm' className='w-full'>
                <Edit className='w-4 h-4 mr-2' />
                Change Password
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Advanced Features Section */}
      <Card className='shadow-sm hover:shadow-md transition-shadow duration-300'>
        <CardHeader>
          <CardTitle className='flex items-center gap-2'>
            <Sparkles className='w-5 h-5 text-indigo-600' />
            🤖 Advanced AI Tools
          </CardTitle>
          <CardDescription>
            Unlock powerful capabilities to supercharge your professional
            presence with cutting-edge AI technology
          </CardDescription>
        </CardHeader>
        <CardContent>
          <AdvancedFeatures
            onGenerateReadme={handleReadmeGeneration}
            onAnalyzeSkills={handleSkillAnalysis}
          />
        </CardContent>
      </Card>
    </div>
  );
}
