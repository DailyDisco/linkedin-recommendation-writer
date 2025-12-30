import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router';
import { Check, Sparkles, Zap, Building2, Loader2 } from 'lucide-react';
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
import { useSubscriptionStore } from '~/hooks/useSubscriptionStore';
import { useAuthStore } from '~/hooks/useAuthStore';
import type { Plan, TierType } from '~/types';

const tierIcons: Record<TierType, React.ReactNode> = {
  free: <Sparkles className='h-6 w-6' />,
  pro: <Zap className='h-6 w-6' />,
  team: <Building2 className='h-6 w-6' />,
};

const tierColors: Record<TierType, string> = {
  free: 'bg-gray-100 text-gray-800',
  pro: 'bg-blue-100 text-blue-800',
  team: 'bg-purple-100 text-purple-800',
};

function PricingCard({
  plan,
  currentTier,
  onSelectPlan,
  isLoading,
}: {
  plan: Plan;
  currentTier: TierType;
  onSelectPlan: (plan: Plan) => void;
  isLoading: boolean;
}) {
  const isCurrentPlan = plan.id === currentTier;
  const isUpgrade = !isCurrentPlan && plan.price_cents > 0;
  const isPopular = plan.is_popular;

  const priceDisplay =
    plan.price_cents === 0 ? (
      <span className='text-4xl font-bold'>Free</span>
    ) : (
      <>
        <span className='text-4xl font-bold'>
          ${(plan.price_cents / 100).toFixed(0)}
        </span>
        <span className='text-muted-foreground'>/month</span>
      </>
    );

  return (
    <Card
      className={`relative flex flex-col ${
        isPopular ? 'border-primary shadow-lg scale-105' : ''
      } ${isCurrentPlan ? 'ring-2 ring-primary' : ''}`}
    >
      {isPopular && (
        <Badge className='absolute -top-3 left-1/2 -translate-x-1/2 bg-primary'>
          Most Popular
        </Badge>
      )}
      {isCurrentPlan && (
        <Badge className='absolute -top-3 right-4 bg-green-600'>
          Current Plan
        </Badge>
      )}

      <CardHeader className='text-center pb-2'>
        <div
          className={`mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full ${tierColors[plan.id]}`}
        >
          {tierIcons[plan.id]}
        </div>
        <CardTitle className='text-2xl'>{plan.name}</CardTitle>
        <CardDescription className='text-3xl font-bold mt-2'>
          {priceDisplay}
        </CardDescription>
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
          variant={isPopular ? 'default' : 'outline'}
          disabled={isCurrentPlan || isLoading}
          onClick={() => onSelectPlan(plan)}
        >
          {isLoading ? (
            <>
              <Loader2 className='mr-2 h-4 w-4 animate-spin' />
              Processing...
            </>
          ) : isCurrentPlan ? (
            'Current Plan'
          ) : isUpgrade ? (
            plan.id === 'pro' ? (
              'Start 7-Day Free Trial'
            ) : (
              'Upgrade to Team'
            )
          ) : (
            'Get Started'
          )}
        </Button>
      </CardFooter>
    </Card>
  );
}

export default function PricingPage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();
  const { plans, subscription, fetchPlans, createCheckout, isLoading } =
    useSubscriptionStore();

  const [loadingPlan, setLoadingPlan] = useState<string | null>(null);

  useEffect(() => {
    fetchPlans();
  }, [fetchPlans]);

  const currentTier = subscription?.tier || 'free';

  const handleSelectPlan = async (plan: Plan) => {
    if (plan.id === 'free') {
      navigate('/generate');
      return;
    }

    if (!isAuthenticated) {
      toast.info('Please log in to upgrade your plan');
      navigate('/login?redirect=/pricing');
      return;
    }

    if (!plan.stripe_price_id) {
      toast.error('This plan is not available for purchase yet');
      return;
    }

    setLoadingPlan(plan.id);
    try {
      const checkoutUrl = await createCheckout(plan.stripe_price_id);
      window.location.href = checkoutUrl;
    } catch {
      toast.error('Failed to start checkout. Please try again.');
    } finally {
      setLoadingPlan(null);
    }
  };

  return (
    <div className='container mx-auto px-4 py-16'>
      {/* Header */}
      <div className='text-center mb-12'>
        <h1 className='text-4xl font-bold mb-4'>Simple, Transparent Pricing</h1>
        <p className='text-xl text-muted-foreground max-w-2xl mx-auto'>
          Start free, upgrade when you need more. All plans include our
          AI-powered recommendation engine.
        </p>
      </div>

      {/* Pricing Cards */}
      <div className='grid md:grid-cols-3 gap-8 max-w-5xl mx-auto'>
        {plans.map(plan => (
          <PricingCard
            key={plan.id}
            plan={plan}
            currentTier={currentTier}
            onSelectPlan={handleSelectPlan}
            isLoading={loadingPlan === plan.id || isLoading}
          />
        ))}
      </div>

      {/* FAQ Section */}
      <div className='mt-20 max-w-3xl mx-auto'>
        <h2 className='text-2xl font-bold text-center mb-8'>
          Frequently Asked Questions
        </h2>

        <div className='space-y-6'>
          <div>
            <h3 className='font-semibold mb-2'>
              What happens when I reach my daily limit?
            </h3>
            <p className='text-muted-foreground'>
              You&apos;ll see a friendly prompt to upgrade or wait until the
              next day. Your limit resets at midnight UTC.
            </p>
          </div>

          <div>
            <h3 className='font-semibold mb-2'>Can I cancel anytime?</h3>
            <p className='text-muted-foreground'>
              Yes! You can cancel your subscription at any time. You&apos;ll
              continue to have access until the end of your billing period.
            </p>
          </div>

          <div>
            <h3 className='font-semibold mb-2'>
              What&apos;s included in the free trial?
            </h3>
            <p className='text-muted-foreground'>
              The 7-day free trial gives you full access to Pro features. No
              charge until the trial ends, and you can cancel anytime.
            </p>
          </div>

          <div>
            <h3 className='font-semibold mb-2'>Do you offer refunds?</h3>
            <p className='text-muted-foreground'>
              We offer a 14-day money-back guarantee. If you&apos;re not
              satisfied, contact us for a full refund.
            </p>
          </div>

          <div>
            <h3 className='font-semibold mb-2'>
              What payment methods do you accept?
            </h3>
            <p className='text-muted-foreground'>
              We accept all major credit cards, debit cards, and some regional
              payment methods through Stripe.
            </p>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className='mt-16 text-center'>
        <p className='text-muted-foreground mb-4'>
          Have questions? Need a custom plan for your team?
        </p>
        <Button variant='outline' onClick={() => navigate('/about')}>
          Contact Us
        </Button>
      </div>
    </div>
  );
}
