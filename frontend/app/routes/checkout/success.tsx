import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router';
import { CheckCircle, Sparkles } from 'lucide-react';
import { motion } from 'motion/react';

import { Button } from '~/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '~/components/ui/card';
import { useSubscriptionStore } from '~/hooks/useSubscriptionStore';

export default function CheckoutSuccessPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get('session_id');
  const { refreshAll } = useSubscriptionStore();

  useEffect(() => {
    // Refresh subscription data after successful checkout
    refreshAll();
  }, [refreshAll]);

  return (
    <div className='container mx-auto px-4 py-16 flex items-center justify-center min-h-[60vh]'>
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
      >
        <Card className='max-w-md text-center'>
          <CardHeader>
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
              className='mx-auto mb-4'
            >
              <div className='relative'>
                <CheckCircle className='h-16 w-16 text-green-500' />
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.5 }}
                  className='absolute -top-2 -right-2'
                >
                  <Sparkles className='h-6 w-6 text-yellow-500' />
                </motion.div>
              </div>
            </motion.div>
            <CardTitle className='text-2xl'>Welcome to Pro!</CardTitle>
            <CardDescription>
              Your subscription is now active. You have access to all Pro
              features.
            </CardDescription>
          </CardHeader>
          <CardContent className='space-y-6'>
            <div className='bg-muted rounded-lg p-4 text-left'>
              <h3 className='font-semibold mb-2'>What&apos;s new for you:</h3>
              <ul className='space-y-2 text-sm text-muted-foreground'>
                <li className='flex items-center gap-2'>
                  <CheckCircle className='h-4 w-4 text-green-500' />
                  50 recommendations per day
                </li>
                <li className='flex items-center gap-2'>
                  <CheckCircle className='h-4 w-4 text-green-500' />3 options
                  per generation
                </li>
                <li className='flex items-center gap-2'>
                  <CheckCircle className='h-4 w-4 text-green-500' />
                  Keyword refinement
                </li>
                <li className='flex items-center gap-2'>
                  <CheckCircle className='h-4 w-4 text-green-500' />
                  Full version history
                </li>
              </ul>
            </div>

            <div className='flex flex-col gap-3'>
              <Button onClick={() => navigate('/generate')} className='w-full'>
                Start Generating
              </Button>
              <Button
                variant='outline'
                onClick={() => navigate('/settings/billing')}
                className='w-full'
              >
                View Billing Details
              </Button>
            </div>

            {sessionId && (
              <p className='text-xs text-muted-foreground'>
                Session: {sessionId.slice(0, 20)}...
              </p>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
