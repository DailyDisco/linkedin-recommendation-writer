import { useEffect } from 'react';
import { useNavigate } from 'react-router';
import {
  CreditCard,
  Calendar,
  BarChart3,
  Settings,
  Loader2,
  ExternalLink,
} from 'lucide-react';
import { toast } from 'sonner';
import { format, formatDistanceToNow } from 'date-fns';

import { Button } from '~/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '~/components/ui/card';
import { Badge } from '~/components/ui/badge';
import { Progress } from '~/components/ui/progress';
import { useSubscriptionStore } from '~/hooks/useSubscriptionStore';
import { useAuthStore } from '~/hooks/useAuthStore';

export default function BillingSettingsPage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();
  const { subscription, usage, refreshAll, openPortal, isLoading } =
    useSubscriptionStore();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login?redirect=/settings/billing');
      return;
    }
    refreshAll();
  }, [isAuthenticated, navigate, refreshAll]);

  const handleManageSubscription = async () => {
    try {
      const portalUrl = await openPortal();
      window.location.href = portalUrl;
    } catch {
      toast.error('Failed to open billing portal');
    }
  };

  if (isLoading && !subscription) {
    return (
      <div className='container mx-auto px-4 py-16 flex items-center justify-center'>
        <Loader2 className='h-8 w-8 animate-spin text-muted-foreground' />
      </div>
    );
  }

  const tier = subscription?.tier || 'free';
  const status = subscription?.status || 'active';
  const usagePercent =
    usage && usage.generations_limit > 0
      ? Math.min(100, (usage.generations_used / usage.generations_limit) * 100)
      : 0;

  return (
    <div className='container mx-auto px-4 py-8 max-w-4xl'>
      <div className='mb-8'>
        <h1 className='text-3xl font-bold'>Billing & Usage</h1>
        <p className='text-muted-foreground mt-2'>
          Manage your subscription and view usage statistics.
        </p>
      </div>

      <div className='grid gap-6 md:grid-cols-2'>
        {/* Current Plan Card */}
        <Card>
          <CardHeader>
            <CardTitle className='flex items-center gap-2'>
              <CreditCard className='h-5 w-5' />
              Current Plan
            </CardTitle>
          </CardHeader>
          <CardContent className='space-y-4'>
            <div className='flex items-center justify-between'>
              <div>
                <Badge
                  variant={tier === 'free' ? 'secondary' : 'default'}
                  className='text-lg px-3 py-1'
                >
                  {tier.charAt(0).toUpperCase() + tier.slice(1)}
                </Badge>
                <div className='mt-2 text-sm text-muted-foreground'>
                  Status:{' '}
                  <span
                    className={
                      status === 'active'
                        ? 'text-green-600'
                        : status === 'trialing'
                          ? 'text-blue-600'
                          : 'text-yellow-600'
                    }
                  >
                    {status.charAt(0).toUpperCase() + status.slice(1)}
                  </span>
                </div>
              </div>
            </div>

            {subscription?.current_period_end && (
              <div className='flex items-center gap-2 text-sm text-muted-foreground'>
                <Calendar className='h-4 w-4' />
                <span>
                  {subscription.cancel_at_period_end ? 'Ends' : 'Next billing'}:{' '}
                  {format(
                    new Date(subscription.current_period_end),
                    'MMM d, yyyy'
                  )}
                </span>
              </div>
            )}

            {subscription?.trial_end && status === 'trialing' && (
              <div className='bg-blue-50 text-blue-800 rounded-lg p-3 text-sm'>
                Trial ends{' '}
                {formatDistanceToNow(new Date(subscription.trial_end), {
                  addSuffix: true,
                })}
              </div>
            )}

            <div className='pt-4 space-y-2'>
              {tier !== 'free' ? (
                <Button
                  variant='outline'
                  className='w-full'
                  onClick={handleManageSubscription}
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <Loader2 className='mr-2 h-4 w-4 animate-spin' />
                  ) : (
                    <Settings className='mr-2 h-4 w-4' />
                  )}
                  Manage Subscription
                </Button>
              ) : (
                <Button className='w-full' onClick={() => navigate('/pricing')}>
                  Upgrade Plan
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Usage Card */}
        <Card>
          <CardHeader>
            <CardTitle className='flex items-center gap-2'>
              <BarChart3 className='h-5 w-5' />
              Usage This Period
            </CardTitle>
            <CardDescription>
              {usage?.generations_limit === -1
                ? 'Unlimited generations'
                : `${usage?.generations_used || 0} of ${usage?.generations_limit || 0} generations used`}
            </CardDescription>
          </CardHeader>
          <CardContent className='space-y-4'>
            {usage?.generations_limit !== -1 && (
              <div className='space-y-2'>
                <Progress value={usagePercent} className='h-3' />
                <div className='flex justify-between text-sm text-muted-foreground'>
                  <span>{usage?.generations_remaining || 0} remaining</span>
                  <span>
                    Resets{' '}
                    {usage?.resets_at
                      ? formatDistanceToNow(new Date(usage.resets_at), {
                          addSuffix: true,
                        })
                      : 'at midnight'}
                  </span>
                </div>
              </div>
            )}

            {usage?.generations_limit === -1 && (
              <div className='bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-4 text-center'>
                <p className='text-lg font-semibold text-purple-700'>
                  Unlimited
                </p>
                <p className='text-sm text-muted-foreground'>
                  Generate as many recommendations as you need
                </p>
              </div>
            )}

            {/* Usage History Chart Placeholder */}
            {usage?.history && usage.history.length > 0 && (
              <div className='pt-4'>
                <h4 className='text-sm font-medium mb-2'>Recent Activity</h4>
                <div className='flex items-end gap-1 h-16'>
                  {usage.history.slice(0, 14).map((day, i) => (
                    <div
                      key={i}
                      className='flex-1 bg-primary/20 rounded-t'
                      style={{
                        height: `${Math.max(10, (day.count / Math.max(...usage.history.map(d => d.count))) * 100)}%`,
                      }}
                      title={`${day.date}: ${day.count} generations`}
                    />
                  ))}
                </div>
                <p className='text-xs text-muted-foreground mt-1'>
                  Last 14 days
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Feature Access */}
      <Card className='mt-6'>
        <CardHeader>
          <CardTitle>Your Features</CardTitle>
          <CardDescription>
            Features available on your current plan
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className='grid gap-4 sm:grid-cols-2 lg:grid-cols-3'>
            <FeatureItem
              name='Daily Generations'
              value={
                usage?.generations_limit === -1
                  ? 'Unlimited'
                  : `${usage?.generations_limit || 3}/day`
              }
            />
            <FeatureItem
              name='Options per Generation'
              value={tier === 'free' ? '1' : tier === 'pro' ? '3' : '5'}
            />
            <FeatureItem
              name='Keyword Refinement'
              value={tier !== 'free' ? 'Yes' : 'No'}
              isEnabled={tier !== 'free'}
            />
            <FeatureItem
              name='Version History'
              value={tier !== 'free' ? 'Full' : 'Limited'}
              isEnabled={tier !== 'free'}
            />
            <FeatureItem
              name='API Access'
              value={tier === 'team' ? 'Yes' : 'No'}
              isEnabled={tier === 'team'}
            />
            <FeatureItem
              name='Priority Support'
              value={tier === 'team' ? 'Yes' : 'No'}
              isEnabled={tier === 'team'}
            />
          </div>

          {tier !== 'team' && (
            <div className='mt-6 pt-6 border-t'>
              <p className='text-sm text-muted-foreground mb-3'>
                Want more features?
              </p>
              <Button variant='outline' onClick={() => navigate('/pricing')}>
                View All Plans
                <ExternalLink className='ml-2 h-4 w-4' />
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function FeatureItem({
  name,
  value,
  isEnabled = true,
}: {
  name: string;
  value: string;
  isEnabled?: boolean;
}) {
  return (
    <div className='flex items-center justify-between p-3 rounded-lg bg-muted/50'>
      <span className='text-sm'>{name}</span>
      <Badge variant={isEnabled ? 'default' : 'secondary'}>{value}</Badge>
    </div>
  );
}
