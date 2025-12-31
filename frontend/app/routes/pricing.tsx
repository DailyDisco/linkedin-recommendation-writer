import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router';
import { Check, Sparkles, Zap, Crown, Loader2, CreditCard } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '~/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '~/components/ui/card';
import { Badge } from '~/components/ui/badge';
import { Separator } from '~/components/ui/separator';
import { useAuthStore } from '~/hooks/useAuthStore';
import { billingApi } from '~/services/api';
import type { CreditPack, Plan, CreditBalance } from '~/types';

function CreditPackCard({
  pack,
  onPurchase,
  isLoading,
  isAuthenticated,
}: {
  pack: CreditPack;
  onPurchase: (packId: 'starter' | 'pro') => void;
  isLoading: boolean;
  isAuthenticated: boolean;
}) {
  const isPro = pack.id === 'pro';

  return (
    <Card
      className={`relative flex flex-col ${
        isPro ? 'border-primary shadow-lg scale-105' : ''
      }`}
    >
      {isPro && (
        <Badge className='absolute -top-3 left-1/2 -translate-x-1/2 bg-primary'>
          Best Value
        </Badge>
      )}

      <CardHeader className='text-center pb-2'>
        <div
          className={`mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full ${
            isPro ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'
          }`}
        >
          {isPro ? <Zap className='h-6 w-6' /> : <Sparkles className='h-6 w-6' />}
        </div>
        <CardTitle className='text-2xl'>{pack.name}</CardTitle>
        <CardDescription className='text-sm mt-1'>
          {pack.description}
        </CardDescription>
        <div className='mt-4'>
          <span className='text-4xl font-bold'>
            ${(pack.price_cents / 100).toFixed(0)}
          </span>
          <span className='text-muted-foreground ml-2'>
            for {pack.credits} credits
          </span>
        </div>
        <p className='text-sm text-muted-foreground mt-1'>
          ${((pack.price_cents / 100) / pack.credits).toFixed(2)} per recommendation
        </p>
      </CardHeader>

      <CardContent className='flex-1'>
        <ul className='space-y-3'>
          <li className='flex items-start gap-2'>
            <Check className='h-5 w-5 text-green-500 shrink-0 mt-0.5' />
            <span className='text-sm'>{pack.credits} recommendations</span>
          </li>
          <li className='flex items-start gap-2'>
            <Check className='h-5 w-5 text-green-500 shrink-0 mt-0.5' />
            <span className='text-sm'>
              {pack.options_per_generation} option{pack.options_per_generation > 1 ? 's' : ''} per generation
            </span>
          </li>
          <li className='flex items-start gap-2'>
            <Check className='h-5 w-5 text-green-500 shrink-0 mt-0.5' />
            <span className='text-sm'>Credits never expire</span>
          </li>
          {isPro && (
            <>
              <li className='flex items-start gap-2'>
                <Check className='h-5 w-5 text-green-500 shrink-0 mt-0.5' />
                <span className='text-sm'>All tones unlocked</span>
              </li>
              <li className='flex items-start gap-2'>
                <Check className='h-5 w-5 text-green-500 shrink-0 mt-0.5' />
                <span className='text-sm'>Keyword refinement</span>
              </li>
            </>
          )}
        </ul>
      </CardContent>

      <CardFooter>
        <Button
          className='w-full'
          variant={isPro ? 'default' : 'outline'}
          disabled={isLoading}
          onClick={() => onPurchase(pack.id)}
        >
          {isLoading ? (
            <>
              <Loader2 className='mr-2 h-4 w-4 animate-spin' />
              Processing...
            </>
          ) : (
            <>
              <CreditCard className='mr-2 h-4 w-4' />
              {isAuthenticated ? 'Buy Credits' : 'Sign Up to Buy'}
            </>
          )}
        </Button>
      </CardFooter>
    </Card>
  );
}

function UnlimitedPlanCard({
  plan,
  hasSubscription,
  onSubscribe,
  isLoading,
  isAuthenticated,
}: {
  plan: Plan | null;
  hasSubscription: boolean;
  onSubscribe: () => void;
  isLoading: boolean;
  isAuthenticated: boolean;
}) {
  if (!plan) return null;

  return (
    <Card className='border-2 border-dashed'>
      <CardHeader className='text-center pb-2'>
        <div className='mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-purple-100 text-purple-800'>
          <Crown className='h-6 w-6' />
        </div>
        <CardTitle className='text-2xl'>{plan.name}</CardTitle>
        <CardDescription className='text-sm mt-1'>
          For power users who need unlimited access
        </CardDescription>
        <div className='mt-4'>
          <span className='text-4xl font-bold'>
            ${(plan.price_cents / 100).toFixed(0)}
          </span>
          <span className='text-muted-foreground'>/month</span>
        </div>
      </CardHeader>

      <CardContent className='flex-1'>
        <ul className='space-y-3'>
          {plan.features.map((feature, index) => (
            <li key={index} className='flex items-start gap-2'>
              <Check className='h-5 w-5 text-green-500 shrink-0 mt-0.5' />
              <span className='text-sm'>{feature}</span>
            </li>
          ))}
        </ul>
      </CardContent>

      <CardFooter>
        <Button
          className='w-full'
          variant='outline'
          disabled={hasSubscription || isLoading}
          onClick={onSubscribe}
        >
          {isLoading ? (
            <>
              <Loader2 className='mr-2 h-4 w-4 animate-spin' />
              Processing...
            </>
          ) : hasSubscription ? (
            'Current Plan'
          ) : isAuthenticated ? (
            'Subscribe Monthly'
          ) : (
            'Sign Up to Subscribe'
          )}
        </Button>
      </CardFooter>
    </Card>
  );
}

export default function PricingPage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();

  const [creditPacks, setCreditPacks] = useState<CreditPack[]>([]);
  const [unlimitedPlan, setUnlimitedPlan] = useState<Plan | null>(null);
  const [creditBalance, setCreditBalance] = useState<CreditBalance | null>(null);
  const [loadingPack, setLoadingPack] = useState<string | null>(null);
  const [isLoadingSubscription, setIsLoadingSubscription] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [packsRes, plansRes] = await Promise.all([
          billingApi.getCreditPacks(),
          billingApi.getPlans(),
        ]);
        setCreditPacks(packsRes.packs || []);
        setUnlimitedPlan(plansRes.plans?.[0] || null);

        if (isAuthenticated) {
          const balance = await billingApi.getCreditBalance();
          setCreditBalance(balance);
        }
      } catch (error) {
        console.error('Failed to fetch pricing data:', error);
      }
    };
    fetchData();
  }, [isAuthenticated]);

  const handlePurchasePack = async (packId: 'starter' | 'pro') => {
    if (!isAuthenticated) {
      toast.info('Please log in to purchase credits');
      navigate('/login?redirect=/pricing');
      return;
    }

    setLoadingPack(packId);
    try {
      const result = await billingApi.purchaseCreditPack({ pack_id: packId });
      if (result.checkout_url) {
        window.location.href = result.checkout_url;
      }
    } catch {
      toast.error('Failed to start checkout. Please try again.');
    } finally {
      setLoadingPack(null);
    }
  };

  const handleSubscribe = async () => {
    if (!isAuthenticated) {
      toast.info('Please log in to subscribe');
      navigate('/login?redirect=/pricing');
      return;
    }

    if (!unlimitedPlan?.stripe_price_id) {
      toast.error('Subscription not available yet');
      return;
    }

    setIsLoadingSubscription(true);
    try {
      const result = await billingApi.createCheckoutSession({
        price_id: unlimitedPlan.stripe_price_id,
      });
      if (result.checkout_url) {
        window.location.href = result.checkout_url;
      }
    } catch {
      toast.error('Failed to start checkout. Please try again.');
    } finally {
      setIsLoadingSubscription(false);
    }
  };

  return (
    <div className='container mx-auto px-4 py-16'>
      {/* Header */}
      <div className='text-center mb-12'>
        <h1 className='text-4xl font-bold mb-4'>Pay As You Go</h1>
        <p className='text-xl text-muted-foreground max-w-2xl mx-auto'>
          Buy credits when you need them. No subscription required.
          Credits never expire.
        </p>
        {isAuthenticated && creditBalance && (
          <div className='mt-4 inline-flex items-center gap-2 bg-primary/10 px-4 py-2 rounded-full'>
            <Sparkles className='h-5 w-5 text-primary' />
            <span className='font-medium'>
              {creditBalance.has_unlimited
                ? 'Unlimited'
                : `${creditBalance.credits} credits remaining`}
            </span>
          </div>
        )}
      </div>

      {/* Free Tier Info */}
      <div className='max-w-2xl mx-auto mb-12 text-center'>
        <Card className='bg-gradient-to-r from-green-50 to-emerald-50 border-green-200'>
          <CardContent className='pt-6'>
            <div className='flex items-center justify-center gap-2 mb-2'>
              <Sparkles className='h-5 w-5 text-green-600' />
              <span className='font-semibold text-green-800'>Free to Start</span>
            </div>
            <p className='text-green-700'>
              New users get <strong>3 free credits</strong> to try out the app.
              No credit card required.
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Credit Pack Cards */}
      <div className='grid md:grid-cols-2 gap-8 max-w-3xl mx-auto mb-16'>
        {creditPacks.map(pack => (
          <CreditPackCard
            key={pack.id}
            pack={pack}
            onPurchase={handlePurchasePack}
            isLoading={loadingPack === pack.id}
            isAuthenticated={isAuthenticated}
          />
        ))}
      </div>

      {/* Divider */}
      <div className='max-w-3xl mx-auto mb-16'>
        <div className='flex items-center gap-4'>
          <Separator className='flex-1' />
          <span className='text-muted-foreground text-sm'>OR</span>
          <Separator className='flex-1' />
        </div>
      </div>

      {/* Unlimited Subscription */}
      <div className='max-w-md mx-auto mb-16'>
        <h2 className='text-2xl font-bold text-center mb-6'>Need Unlimited?</h2>
        <UnlimitedPlanCard
          plan={unlimitedPlan}
          hasSubscription={creditBalance?.has_unlimited || false}
          onSubscribe={handleSubscribe}
          isLoading={isLoadingSubscription}
          isAuthenticated={isAuthenticated}
        />
      </div>

      {/* FAQ Section */}
      <div className='mt-20 max-w-3xl mx-auto'>
        <h2 className='text-2xl font-bold text-center mb-8'>
          Frequently Asked Questions
        </h2>

        <div className='space-y-6'>
          <div>
            <h3 className='font-semibold mb-2'>Do credits expire?</h3>
            <p className='text-muted-foreground'>
              No! Your credits never expire. Use them whenever you need a
              recommendation.
            </p>
          </div>

          <div>
            <h3 className='font-semibold mb-2'>
              What&apos;s the difference between Starter and Pro packs?
            </h3>
            <p className='text-muted-foreground'>
              Pro packs give you 3 options per generation instead of 1, plus
              access to all tones and keyword refinement. The cost per credit
              is also lower.
            </p>
          </div>

          <div>
            <h3 className='font-semibold mb-2'>
              When should I get the unlimited subscription?
            </h3>
            <p className='text-muted-foreground'>
              If you write more than ~20 recommendations per month regularly
              (recruiters, HR professionals), the unlimited plan saves money.
            </p>
          </div>

          <div>
            <h3 className='font-semibold mb-2'>Can I cancel the subscription?</h3>
            <p className='text-muted-foreground'>
              Yes! You can cancel anytime. You&apos;ll keep access until the end
              of your billing period.
            </p>
          </div>

          <div>
            <h3 className='font-semibold mb-2'>Do you offer refunds?</h3>
            <p className='text-muted-foreground'>
              We offer refunds within 14 days if you haven&apos;t used your
              credits. Contact us for help.
            </p>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className='mt-16 text-center'>
        <p className='text-muted-foreground mb-4'>
          Have questions? Need help choosing?
        </p>
        <Button variant='outline' onClick={() => navigate('/about')}>
          Contact Us
        </Button>
      </div>
    </div>
  );
}
