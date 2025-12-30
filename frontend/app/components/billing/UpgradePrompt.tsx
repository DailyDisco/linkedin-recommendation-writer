import { useState } from 'react';
import { useNavigate } from 'react-router';
import { Zap, Check, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '~/components/ui/button';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from '~/components/ui/sheet';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '~/components/ui/dialog';
import { useSubscriptionStore } from '~/hooks/useSubscriptionStore';
import { useAuthStore } from '~/hooks/useAuthStore';

interface UpgradePromptProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  variant?: 'sheet' | 'dialog';
  trigger?: 'limit' | 'feature';
  featureName?: string;
}

const proFeatures = [
  '50 recommendations per day',
  '3 options per generation',
  'Keyword refinement',
  'Full version history',
  'All tone options',
];

export function UpgradePrompt({
  open,
  onOpenChange,
  variant = 'sheet',
  trigger = 'limit',
  featureName,
}: UpgradePromptProps) {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();
  const { plans, createCheckout, isLoading } = useSubscriptionStore();
  const [isUpgrading, setIsUpgrading] = useState(false);

  const proPlan = plans.find(p => p.id === 'pro');
  const priceId = proPlan?.stripe_price_id;

  const handleUpgrade = async () => {
    if (!isAuthenticated) {
      toast.info('Please log in to upgrade');
      navigate('/login?redirect=/pricing');
      onOpenChange(false);
      return;
    }

    if (!priceId) {
      navigate('/pricing');
      onOpenChange(false);
      return;
    }

    setIsUpgrading(true);
    try {
      const checkoutUrl = await createCheckout(priceId);
      window.location.href = checkoutUrl;
    } catch {
      toast.error('Failed to start checkout. Please try again.');
    } finally {
      setIsUpgrading(false);
    }
  };

  const handleViewPlans = () => {
    onOpenChange(false);
    navigate('/pricing');
  };

  const title =
    trigger === 'limit'
      ? "You've reached your daily limit"
      : `${featureName} requires Pro`;

  const description =
    trigger === 'limit'
      ? 'Upgrade to Pro for 50 recommendations per day and more features.'
      : `Unlock ${featureName} and other premium features with Pro.`;

  const content = (
    <>
      <div className='space-y-4 py-4'>
        <div className='flex items-center gap-3 p-3 rounded-lg bg-primary/10'>
          <Zap className='h-6 w-6 text-primary' />
          <div>
            <p className='font-semibold'>Pro Plan</p>
            <p className='text-sm text-muted-foreground'>
              $9/month • 7-day free trial
            </p>
          </div>
        </div>

        <div className='space-y-2'>
          {proFeatures.map((feature, index) => (
            <div key={index} className='flex items-center gap-2'>
              <Check className='h-4 w-4 text-green-500' />
              <span className='text-sm'>{feature}</span>
            </div>
          ))}
        </div>
      </div>

      <div className='flex flex-col gap-2'>
        <Button
          onClick={handleUpgrade}
          disabled={isUpgrading || isLoading}
          className='w-full'
        >
          {isUpgrading ? (
            <>
              <Loader2 className='mr-2 h-4 w-4 animate-spin' />
              Processing...
            </>
          ) : (
            'Start Free Trial'
          )}
        </Button>
        <Button variant='ghost' onClick={handleViewPlans} className='w-full'>
          View All Plans
        </Button>
        <Button
          variant='ghost'
          onClick={() => onOpenChange(false)}
          className='w-full text-muted-foreground'
        >
          Maybe Later
        </Button>
      </div>
    </>
  );

  if (variant === 'dialog') {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className='sm:max-w-md'>
          <DialogHeader>
            <DialogTitle>{title}</DialogTitle>
            <DialogDescription>{description}</DialogDescription>
          </DialogHeader>
          {content}
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side='right' className='w-full sm:max-w-md'>
        <SheetHeader>
          <SheetTitle>{title}</SheetTitle>
          <SheetDescription>{description}</SheetDescription>
        </SheetHeader>
        {content}
      </SheetContent>
    </Sheet>
  );
}

// Hook to easily show upgrade prompt
export function useUpgradePrompt() {
  const [isOpen, setIsOpen] = useState(false);
  const [trigger, setTrigger] = useState<'limit' | 'feature'>('limit');
  const [featureName, setFeatureName] = useState<string>('');

  const showLimitPrompt = () => {
    setTrigger('limit');
    setIsOpen(true);
  };

  const showFeaturePrompt = (feature: string) => {
    setTrigger('feature');
    setFeatureName(feature);
    setIsOpen(true);
  };

  return {
    isOpen,
    setIsOpen,
    trigger,
    featureName,
    showLimitPrompt,
    showFeaturePrompt,
  };
}

// Usage badge component for showing remaining generations
export function UsageBadge() {
  const { usage, subscription } = useSubscriptionStore();

  if (!usage) return null;
  if (usage.generations_limit === -1) return null; // Don't show for unlimited

  const remaining = usage.generations_remaining;
  const limit = usage.generations_limit;
  const percent = ((limit - remaining) / limit) * 100;

  let variant: 'default' | 'secondary' | 'destructive' = 'secondary';
  if (percent >= 100) variant = 'destructive';
  else if (percent >= 80) variant = 'default';

  return (
    <div className='flex items-center gap-2 text-sm'>
      <span className='text-muted-foreground'>
        {remaining}/{limit} left
      </span>
      {percent >= 80 && subscription?.tier === 'free' && (
        <Button variant='link' size='sm' className='h-auto p-0 text-primary'>
          Upgrade
        </Button>
      )}
    </div>
  );
}
