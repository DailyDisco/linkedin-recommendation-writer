import React from 'react';
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
  Calendar,
  Mail,
  Edit,
  Plus,
  BarChart3,
  Settings,
  RefreshCw,
} from 'lucide-react';
import { PleaseSignInOrRegister } from '../components/PleaseSignInOrRegister';
import { Link } from 'react-router';
import { trackEngagement } from '../utils/analytics';
import { formatDate } from '../utils/formatDate'; // Import formatDate
import { getAvatarInitials } from '../utils/string'; // Import getAvatarInitials
import { RecentActivityList } from '../components/profile/RecentActivityList'; // Import new component
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'; // Import Dialog components
import { EditProfileForm } from '../components/profile/EditProfileForm'; // Import EditProfileForm
import { Switch } from '@/components/ui/switch'; // Import Switch component
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'; // Import Select components
import { toast } from 'sonner'; // Import toast for notifications
import { apiClient } from '../services/api'; // Import apiClient
import { ChangePasswordForm } from '../components/profile/ChangePasswordForm'; // Import ChangePasswordForm

export default function UserProfilePage() {
  const {
    isLoggedIn,
    userDetails,
    userRecommendationCount,
    userDailyLimit,
    isLoadingUserDetails,
    fetchUserDetails,
  } = useAuth();

  const [isUpdatingSettings, setIsUpdatingSettings] = React.useState(false);
  const [isChangePasswordDialogOpen, setIsChangePasswordDialogOpen] =
    React.useState(false);
  const [isEditProfileDialogOpen, setIsEditProfileDialogOpen] =
    React.useState(false);

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

  const handleUpdateSetting = async (
    field: string,
    value: string | boolean
  ) => {
    if (!userDetails?.id) {
      toast.error('User ID not found. Please log in again.');
      return;
    }
    setIsUpdatingSettings(true);
    try {
      await apiClient.updateUserProfile(userDetails.id, { [field]: value });
      await fetchUserDetails(true); // Refresh user details
      toast.success(
        `${field.replace(/([A-Z])/g, ' $1').toLowerCase()} updated successfully.`
      );
    } catch (error) {
      console.error(`Failed to update ${field}:`, error);
      toast.error(
        `Failed to update ${field.replace(/([A-Z])/g, ' $1').toLowerCase()}.`
      );
    } finally {
      setIsUpdatingSettings(false);
    }
  };

  const handleEmailNotificationsToggle = (checked: boolean) => {
    handleUpdateSetting('email_notifications_enabled', checked);
  };

  const handleDefaultToneChange = (value: string) => {
    handleUpdateSetting('default_tone', value);
  };

  const handleLanguageChange = (value: string) => {
    handleUpdateSetting('language', value);
  };

  if (!isLoggedIn) {
    return <PleaseSignInOrRegister />;
  }

  const recommendationProgress =
    userDailyLimit && userRecommendationCount
      ? (userRecommendationCount / userDailyLimit) * 100
      : 0;

  return (
    <div className='min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50/30'>
      <div className='container mx-auto p-4 sm:p-6 space-y-6 sm:space-y-8'>
        <div className='text-center'>
          <div className='flex items-center justify-center gap-3 sm:gap-4 mb-2'>
            <h1 className='text-3xl sm:text-4xl font-bold tracking-tight lg:text-5xl bg-gradient-to-r from-gray-900 via-gray-800 to-gray-700 bg-clip-text text-transparent'>
              Profile Dashboard
            </h1>
            {isLoadingUserDetails && (
              <RefreshCw className='w-5 h-5 sm:w-6 sm:h-6 animate-spin text-blue-600' />
            )}
          </div>
          <div className='flex items-center justify-center gap-2'>
            <p className='text-base sm:text-lg text-muted-foreground'>
              Manage your account and access powerful AI features ✨
            </p>
            <Button
              variant='ghost'
              size='sm'
              onClick={handleRefresh}
              disabled={isLoadingUserDetails}
              className='hover:bg-blue-50 hover:scale-105 transition-all duration-200'
            >
              <RefreshCw
                className={`w-4 h-4 ${isLoadingUserDetails ? 'animate-spin' : ''}`}
              />
            </Button>
          </div>
        </div>

        {/* Profile Information */}
        <Card className='shadow-sm hover:shadow-lg hover:scale-[1.02] transition-all duration-300 bg-white/80 backdrop-blur-sm border-0'>
          <CardHeader>
            <CardTitle className='flex items-center gap-2'>
              <User className='w-5 h-5 text-blue-600' />
              Profile Information
            </CardTitle>
            <CardDescription>
              Your account details and current status
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className='flex flex-col sm:flex-row items-start gap-4 sm:gap-6'>
              <div className='relative'>
                {isLoadingUserDetails ? (
                  <Skeleton className='w-20 h-20 rounded-full' />
                ) : (
                  <Avatar className='w-20 h-20 ring-3 ring-blue-200 ring-offset-2 shadow-lg hover:shadow-xl transition-shadow duration-300'>
                    <AvatarFallback className='bg-gradient-to-br from-blue-600 to-purple-600 text-white font-semibold text-lg'>
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
                      <h3 className='text-xl sm:text-2xl font-bold text-gray-900 tracking-tight'>
                        {userDetails?.full_name ||
                          userDetails?.username ||
                          'User'}
                      </h3>
                      <p className='text-muted-foreground font-medium'>
                        @{userDetails?.username}
                      </p>
                    </>
                  )}
                </div>
                <div className='grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4'>
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
                        <Mail className='w-4 h-4 text-blue-500' />
                        <span className='text-sm font-medium'>
                          {userDetails?.email}
                        </span>
                      </div>
                      <div className='flex items-center gap-2'>
                        <Calendar className='w-4 h-4 text-green-500' />
                        <span className='text-sm font-medium'>
                          Last active:{' '}
                          {formatDate(
                            userDetails?.last_recommendation_date ?? null
                          )}
                        </span>
                      </div>
                      <div className='flex items-center gap-2'>
                        <Database className='w-4 h-4 text-purple-500' />
                        <span className='text-sm font-medium'>
                          {userRecommendationCount} recommendations created
                        </span>
                      </div>
                      <div className='flex items-center gap-2'>
                        <Badge
                          variant={
                            userDetails?.is_active ? 'default' : 'secondary'
                          }
                          className={
                            userDetails?.is_active
                              ? 'bg-green-100 text-green-800 hover:bg-green-200'
                              : ''
                          }
                        >
                          {userDetails?.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </div>
                    </>
                  )}
                </div>
              </div>
              <Dialog
                open={isEditProfileDialogOpen}
                onOpenChange={setIsEditProfileDialogOpen}
              >
                <DialogTrigger asChild>
                  <Button
                    variant='outline'
                    size='sm'
                    className='hover:bg-blue-50 hover:scale-105 transition-all duration-200 border-blue-200 hover:border-blue-300'
                    onClick={() => {
                      // Check authentication before opening dialog
                      const authStorage = localStorage.getItem('auth-storage');
                      if (!authStorage) {
                        toast.error(
                          'Authentication session expired. Please log in again.'
                        );
                        return;
                      }
                      try {
                        const parsed = JSON.parse(authStorage);
                        const accessToken = parsed?.state?.accessToken;
                        if (!accessToken) {
                          toast.error(
                            'Authentication token not found. Please log in again.'
                          );
                          return;
                        }
                        setIsEditProfileDialogOpen(true);
                      } catch (error) {
                        console.error('Failed to parse auth storage:', error);
                        toast.error(
                          'Authentication session corrupted. Please log in again.'
                        );
                      }
                    }}
                  >
                    <Edit className='w-4 h-4 mr-2 text-blue-600' />
                    Edit Profile
                  </Button>
                </DialogTrigger>
                <DialogContent className='sm:max-w-[425px] mx-4 sm:mx-auto'>
                  <DialogHeader>
                    <DialogTitle>Edit Profile</DialogTitle>
                    <DialogDescription>
                      Update your profile information including name, username,
                      and bio.
                    </DialogDescription>
                  </DialogHeader>
                  <EditProfileForm
                    onSave={() => setIsEditProfileDialogOpen(false)}
                    onCancel={() => setIsEditProfileDialogOpen(false)}
                  />
                </DialogContent>
              </Dialog>
            </div>
          </CardContent>
        </Card>

        <div className='grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6'>
          {/* Usage Analytics */}
          <Card className='shadow-sm hover:shadow-lg hover:scale-[1.02] transition-all duration-300 bg-white/80 backdrop-blur-sm border-0'>
            <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
              <CardTitle className='text-sm font-semibold text-gray-800'>
                📊 Today&apos;s Usage
              </CardTitle>
              <BarChart3 className='h-5 w-5 text-blue-600' />
            </CardHeader>
            <CardContent>
              {isLoadingUserDetails ? (
                <div className='space-y-3'>
                  <Skeleton className='h-8 w-24' />
                  <Skeleton className='h-4 w-48' />
                  <Skeleton className='h-3 w-full' />
                  <Skeleton className='h-4 w-32' />
                </div>
              ) : (
                <>
                  <div className='text-2xl sm:text-3xl font-bold text-gray-900 mb-1'>
                    {userRecommendationCount !== null
                      ? userRecommendationCount
                      : 'N/A'}{' '}
                    <span className='text-lg text-muted-foreground'>/</span>{' '}
                    {userDailyLimit !== null ? userDailyLimit : 'N/A'}
                  </div>
                  <p className='text-xs text-muted-foreground mb-3 font-medium'>
                    Recommendations generated today
                  </p>
                  <Progress
                    value={recommendationProgress}
                    className='h-3 mb-3 bg-blue-100'
                  />
                  <div className='text-xs text-muted-foreground font-medium'>
                    {userDailyLimit && userRecommendationCount !== null
                      ? `${userDailyLimit - userRecommendationCount} recommendations remaining`
                      : 'Loading usage data...'}
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* Quick Actions Panel */}
          <Card className='shadow-sm hover:shadow-lg hover:scale-[1.02] transition-all duration-300 bg-white/80 backdrop-blur-sm border-0'>
            <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
              <CardTitle className='text-sm font-semibold text-gray-800'>
                ⚡ Quick Actions
              </CardTitle>
              <Sparkles className='h-5 w-5 text-purple-600' />
            </CardHeader>
            <CardContent className='space-y-3'>
              <Link to='/generate'>
                <Button
                  className='w-full justify-start hover:bg-blue-50 hover:scale-105 transition-all duration-200 border-blue-200 hover:border-blue-300'
                  variant='outline'
                >
                  <Plus className='w-4 h-4 mr-3 text-blue-600' />
                  Generate New Recommendation
                </Button>
              </Link>
              <Link to='/history'>
                <Button
                  className='w-full justify-start hover:bg-purple-50 hover:scale-105 transition-all duration-200 border-purple-200 hover:border-purple-300'
                  variant='outline'
                >
                  <Database className='w-4 h-4 mr-3 text-purple-600' />
                  View History
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>

        <div className='grid grid-cols-1 xl:grid-cols-3 gap-4 sm:gap-6'>
          {/* Recent Activity Feed */}
          <div className='xl:col-span-2'>
            <RecentActivityList githubUsername={userDetails?.username} />
          </div>

          {/* Settings Panel */}
          <Card className='shadow-sm hover:shadow-lg hover:scale-[1.02] transition-all duration-300 bg-white/80 backdrop-blur-sm border-0'>
            <CardHeader>
              <CardTitle className='flex items-center gap-2'>
                <Settings className='w-5 h-5 text-indigo-600' />
                Settings
              </CardTitle>
              <CardDescription>Manage your preferences</CardDescription>
            </CardHeader>
            <CardContent className='space-y-5'>
              <div className='space-y-4'>
                <div className='flex items-center justify-between p-3 rounded-lg bg-blue-50/50 hover:bg-blue-50 transition-colors duration-200'>
                  <span className='text-sm font-semibold text-gray-700'>
                    Email Notifications
                  </span>
                  <Switch
                    checked={userDetails?.email_notifications_enabled ?? true}
                    onCheckedChange={handleEmailNotificationsToggle}
                    disabled={isUpdatingSettings}
                    className='data-[state=checked]:bg-blue-600'
                  />
                </div>
                <div className='flex items-center justify-between p-3 rounded-lg bg-purple-50/50 hover:bg-purple-50 transition-colors duration-200'>
                  <span className='text-sm font-semibold text-gray-700'>
                    Default Tone
                  </span>
                  <Select
                    value={userDetails?.default_tone || 'professional'}
                    onValueChange={handleDefaultToneChange}
                    disabled={isUpdatingSettings}
                  >
                    <SelectTrigger className='w-[160px] sm:w-[180px] border-purple-200 focus:border-purple-300'>
                      <SelectValue placeholder='Select a tone' />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value='professional'>Professional</SelectItem>
                      <SelectItem value='friendly'>Friendly</SelectItem>
                      <SelectItem value='formal'>Formal</SelectItem>
                      <SelectItem value='casual'>Casual</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className='flex items-center justify-between p-3 rounded-lg bg-green-50/50 hover:bg-green-50 transition-colors duration-200'>
                  <span className='text-sm font-semibold text-gray-700'>
                    Language
                  </span>
                  <Select
                    value={userDetails?.language || 'en'}
                    onValueChange={handleLanguageChange}
                    disabled={isUpdatingSettings}
                  >
                    <SelectTrigger className='w-[160px] sm:w-[180px] border-green-200 focus:border-green-300'>
                      <SelectValue placeholder='Select a language' />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value='en'>English</SelectItem>
                      <SelectItem value='es'>Español</SelectItem>
                      {/* Add more languages as needed */}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className='pt-4 border-t border-gray-200'>
                <Dialog
                  open={isChangePasswordDialogOpen}
                  onOpenChange={setIsChangePasswordDialogOpen}
                >
                  <DialogTrigger asChild>
                    <Button
                      variant='outline'
                      size='sm'
                      className='w-full hover:bg-orange-50 hover:scale-105 transition-all duration-200 border-orange-200 hover:border-orange-300'
                    >
                      <Edit className='w-4 h-4 mr-2 text-orange-600' />
                      Change Password
                    </Button>
                  </DialogTrigger>
                  <DialogContent className='sm:max-w-[425px] mx-4 sm:mx-auto'>
                    <DialogHeader>
                      <DialogTitle>Change Password</DialogTitle>
                      <DialogDescription>
                        Enter your current password and choose a new secure
                        password.
                      </DialogDescription>
                    </DialogHeader>
                    <ChangePasswordForm
                      onSave={() => setIsChangePasswordDialogOpen(false)}
                      onCancel={() => setIsChangePasswordDialogOpen(false)}
                    />
                  </DialogContent>
                </Dialog>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
