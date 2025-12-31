import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router';
import {
  CreditCard,
  Sparkles,
  Crown,
  Settings,
  Loader2,
  ExternalLink,
  Clock,
  Package,
} from 'lucide-react';
import { toast } from 'sonner';
import { format } from 'date-fns';

import { Button } from '~/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '~/components/ui/card';
import { Badge } from '~/components/ui/badge';
import { useAuthStore } from '~/hooks/useAuthStore';
import { billingApi } from '~/services/api';
import type { CreditBalance, CreditPurchase, Subscription } from '~/types';

export default function BillingSettingsPage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();

  const [creditBalance, setCreditBalance] = useState<CreditBalance | null>(
    null
  );
  const [purchaseHistory, setPurchaseHistory] = useState<CreditPurchase[]>([]);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isPortalLoading, setIsPortalLoading] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login?redirect=/settings/billing');
      return;
    }

    const fetchData = async () => {
      setIsLoading(true);
      try {
        const [balance, history, sub] = await Promise.all([
          billingApi.getCreditBalance(),
          billingApi.getCreditHistory(),
          billingApi.getSubscription().catch(() => null),
        ]);
        setCreditBalance(balance);
        setPurchaseHistory(history);
        setSubscription(sub);
      } catch (error) {
        console.error('Failed to fetch billing data:', error);
        toast.error('Failed to load billing information');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [isAuthenticated, navigate]);

  const handleManageSubscription = async () => {
    setIsPortalLoading(true);
    try {
      const result = await billingApi.createPortalSession();
      if (result.portal_url) {
        window.location.href = result.portal_url;
      }
    } catch {
      toast.error('Failed to open billing portal');
    } finally {
      setIsPortalLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className='container mx-auto px-4 py-16 flex items-center justify-center'>
        <Loader2 className='h-8 w-8 animate-spin text-muted-foreground' />
      </div>
    );
  }

  const hasUnlimited = creditBalance?.has_unlimited || false;

  return (
    <div className='container mx-auto px-4 py-8 max-w-4xl'>
      <div className='mb-8'>
        <h1 className='text-3xl font-bold'>Billing & Credits</h1>
        <p className='text-muted-foreground mt-2'>
          Manage your credits and subscription.
        </p>
      </div>

      <div className='grid gap-6 md:grid-cols-2'>
        {/* Credit Balance Card */}
        <Card>
          <CardHeader>
            <CardTitle className='flex items-center gap-2'>
              <Sparkles className='h-5 w-5' />
              Credit Balance
            </CardTitle>
          </CardHeader>
          <CardContent className='space-y-4'>
            <div className='text-center py-6'>
              {hasUnlimited ? (
                <div className='space-y-2'>
                  <Crown className='h-12 w-12 mx-auto text-purple-500' />
                  <p className='text-3xl font-bold text-purple-600'>
                    Unlimited
                  </p>
                  <p className='text-sm text-muted-foreground'>
                    Active subscription - no credit limits
                  </p>
                </div>
              ) : (
                <div className='space-y-2'>
                  <p className='text-5xl font-bold text-primary'>
                    {creditBalance?.credits || 0}
                  </p>
                  <p className='text-muted-foreground'>credits remaining</p>
                </div>
              )}
            </div>

            {!hasUnlimited && (
              <div className='text-center text-sm text-muted-foreground'>
                <p>
                  Lifetime credits purchased:{' '}
                  <strong>
                    {creditBalance?.lifetime_credits_purchased || 0}
                  </strong>
                </p>
                {creditBalance?.last_pack_purchased && (
                  <p className='mt-1'>
                    Last pack:{' '}
                    <Badge variant='outline' className='ml-1'>
                      {creditBalance.last_pack_purchased === 'pro'
                        ? 'Pro Pack'
                        : 'Starter Pack'}
                    </Badge>
                  </p>
                )}
              </div>
            )}

            <div className='pt-4'>
              <Button className='w-full' onClick={() => navigate('/pricing')}>
                <Package className='mr-2 h-4 w-4' />
                {hasUnlimited ? 'View Plans' : 'Buy More Credits'}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Subscription Status Card */}
        <Card>
          <CardHeader>
            <CardTitle className='flex items-center gap-2'>
              <CreditCard className='h-5 w-5' />
              Subscription
            </CardTitle>
          </CardHeader>
          <CardContent className='space-y-4'>
            {hasUnlimited ? (
              <>
                <div className='flex items-center justify-between'>
                  <div>
                    <Badge variant='default' className='text-lg px-3 py-1'>
                      Unlimited Monthly
                    </Badge>
                    <div className='mt-2 text-sm text-muted-foreground'>
                      Status:{' '}
                      <span className='text-green-600'>
                        {subscription?.status === 'active'
                          ? 'Active'
                          : subscription?.status || 'Active'}
                      </span>
                    </div>
                  </div>
                </div>

                {subscription?.current_period_end && (
                  <div className='flex items-center gap-2 text-sm text-muted-foreground'>
                    <Clock className='h-4 w-4' />
                    <span>
                      {subscription.cancel_at_period_end ? 'Ends' : 'Renews'}:{' '}
                      {format(
                        new Date(subscription.current_period_end),
                        'MMM d, yyyy'
                      )}
                    </span>
                  </div>
                )}

                <Button
                  variant='outline'
                  className='w-full'
                  onClick={handleManageSubscription}
                  disabled={isPortalLoading}
                >
                  {isPortalLoading ? (
                    <Loader2 className='mr-2 h-4 w-4 animate-spin' />
                  ) : (
                    <Settings className='mr-2 h-4 w-4' />
                  )}
                  Manage Subscription
                </Button>
              </>
            ) : (
              <div className='text-center py-6'>
                <Crown className='h-12 w-12 mx-auto text-muted-foreground/30 mb-4' />
                <p className='text-muted-foreground mb-4'>
                  No active subscription
                </p>
                <p className='text-sm text-muted-foreground mb-4'>
                  Get unlimited recommendations for $29/month
                </p>
                <Button variant='outline' onClick={() => navigate('/pricing')}>
                  View Unlimited Plan
                  <ExternalLink className='ml-2 h-4 w-4' />
                </Button>
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
            Features available based on your credits and subscription
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className='grid gap-4 sm:grid-cols-2 lg:grid-cols-3'>
            <FeatureItem
              name='Recommendations'
              value={
                hasUnlimited
                  ? 'Unlimited'
                  : `${creditBalance?.credits || 0} credits`
              }
            />
            <FeatureItem
              name='Options per Generation'
              value={
                hasUnlimited || creditBalance?.last_pack_purchased === 'pro'
                  ? '3'
                  : '1'
              }
            />
            <FeatureItem
              name='All Tones'
              value={
                hasUnlimited || creditBalance?.last_pack_purchased === 'pro'
                  ? 'Yes'
                  : 'No'
              }
              isEnabled={
                hasUnlimited || creditBalance?.last_pack_purchased === 'pro'
              }
            />
            <FeatureItem
              name='Keyword Refinement'
              value={
                hasUnlimited || creditBalance?.last_pack_purchased === 'pro'
                  ? 'Yes'
                  : 'No'
              }
              isEnabled={
                hasUnlimited || creditBalance?.last_pack_purchased === 'pro'
              }
            />
            <FeatureItem
              name='API Access'
              value={
                hasUnlimited ||
                (creditBalance?.lifetime_credits_purchased || 0) >= 50
                  ? 'Yes'
                  : 'No'
              }
              isEnabled={
                hasUnlimited ||
                (creditBalance?.lifetime_credits_purchased || 0) >= 50
              }
            />
            <FeatureItem
              name='Priority Support'
              value={hasUnlimited ? 'Yes' : 'No'}
              isEnabled={hasUnlimited}
            />
          </div>
        </CardContent>
      </Card>

      {/* Purchase History */}
      {purchaseHistory.length > 0 && (
        <Card className='mt-6'>
          <CardHeader>
            <CardTitle>Purchase History</CardTitle>
            <CardDescription>Your credit pack purchases</CardDescription>
          </CardHeader>
          <CardContent>
            <div className='space-y-3'>
              {purchaseHistory.map(purchase => (
                <div
                  key={purchase.id}
                  className='flex items-center justify-between p-3 rounded-lg bg-muted/50'
                >
                  <div className='flex items-center gap-3'>
                    <Package className='h-5 w-5 text-muted-foreground' />
                    <div>
                      <p className='font-medium'>
                        {purchase.pack_type === 'pro'
                          ? 'Pro Pack'
                          : 'Starter Pack'}
                      </p>
                      <p className='text-sm text-muted-foreground'>
                        {purchase.credits_amount} credits
                      </p>
                    </div>
                  </div>
                  <div className='text-right'>
                    <p className='font-medium'>
                      ${(purchase.price_cents / 100).toFixed(2)}
                    </p>
                    <p className='text-sm text-muted-foreground'>
                      {purchase.completed_at
                        ? format(new Date(purchase.completed_at), 'MMM d, yyyy')
                        : format(new Date(purchase.created_at), 'MMM d, yyyy')}
                    </p>
                  </div>
                  <Badge
                    variant={
                      purchase.status === 'completed' ? 'default' : 'secondary'
                    }
                  >
                    {purchase.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
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
