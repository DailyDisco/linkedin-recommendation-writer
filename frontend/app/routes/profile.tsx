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
} from 'lucide-react';
import { apiClient } from '@/services/api';
import type { ReadmeGenerationData, SkillAnalysisData } from '../types';
import { PleaseSignInOrRegister } from '../components/PleaseSignInOrRegister';
import { Link } from 'react-router';

export default function UserProfilePage() {
  const { isLoggedIn, userDetails, userRecommendationCount, userDailyLimit } =
    useAuth();

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
      const response = await apiClient.analyzeSkillGap(data);
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
        <h1 className='text-4xl font-extrabold tracking-tight lg:text-5xl'>
          User Profile
        </h1>
        <p className='mt-3 text-xl text-muted-foreground'>
          Manage your account and access powerful AI features
        </p>
      </div>

      {/* Enhanced User Info Display */}
      <Card>
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
            <Avatar className='w-20 h-20'>
              <AvatarFallback className='text-2xl'>
                {userDetails
                  ? getAvatarInitials(userDetails.username, userDetails.email)
                  : 'U'}
              </AvatarFallback>
            </Avatar>
            <div className='flex-1 space-y-4'>
              <div>
                <h3 className='text-2xl font-semibold'>
                  {userDetails?.full_name || userDetails?.username || 'User'}
                </h3>
                <p className='text-muted-foreground'>
                  @{userDetails?.username}
                </p>
              </div>
              <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
                <div className='flex items-center gap-2'>
                  <Mail className='w-4 h-4 text-muted-foreground' />
                  <span className='text-sm'>{userDetails?.email}</span>
                </div>
                <div className='flex items-center gap-2'>
                  <Calendar className='w-4 h-4 text-muted-foreground' />
                  <span className='text-sm'>
                    Last active:{' '}
                    {formatDate(userDetails?.last_recommendation_date)}
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
                    variant={userDetails?.is_active ? 'default' : 'secondary'}
                  >
                    {userDetails?.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                </div>
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
        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>Today&apos;s Usage</CardTitle>
            <BarChart3 className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>
              {userRecommendationCount !== null
                ? userRecommendationCount
                : 'N/A'}{' '}
              / {userDailyLimit !== null ? userDailyLimit : 'N/A'}
            </div>
            <p className='text-xs text-muted-foreground'>
              Recommendations generated today
            </p>
            <Progress value={recommendationProgress} className='mt-2' />
            <div className='mt-4 text-xs text-muted-foreground'>
              {userDailyLimit && userRecommendationCount !== null
                ? `${userDailyLimit - userRecommendationCount} recommendations remaining`
                : 'Loading usage data...'}
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions Panel */}
        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>Quick Actions</CardTitle>
            <Sparkles className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent className='space-y-3'>
            <Link to='/generate'>
              <Button className='w-full justify-start' variant='outline'>
                <Plus className='w-4 h-4 mr-2' />
                Generate New Recommendation
              </Button>
            </Link>
            <Link to='/history'>
              <Button className='w-full justify-start' variant='outline'>
                <Database className='w-4 h-4 mr-2' />
                View History
              </Button>
            </Link>
            <Button className='w-full justify-start' variant='outline'>
              <Settings className='w-4 h-4 mr-2' />
              Account Settings
            </Button>
          </CardContent>
        </Card>
      </div>

      <div className='grid grid-cols-1 lg:grid-cols-3 gap-6'>
        {/* Recent Activity Feed */}
        <Card className='lg:col-span-2'>
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
              <div className='flex items-center gap-4 p-3 border rounded-lg'>
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
              <div className='flex items-center gap-4 p-3 border rounded-lg'>
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
        <Card>
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
      <Card>
        <CardHeader>
          <CardTitle className='flex items-center gap-2'>
            <Sparkles className='w-5 h-5' />
            Advanced AI Tools
          </CardTitle>
          <CardDescription>
            Unlock powerful capabilities to supercharge your professional
            presence.
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
