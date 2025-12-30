import { useNavigate } from 'react-router';
import { XCircle, ArrowLeft } from 'lucide-react';

import { Button } from '~/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '~/components/ui/card';

export default function CheckoutCancelPage() {
  const navigate = useNavigate();

  return (
    <div className='container mx-auto px-4 py-16 flex items-center justify-center min-h-[60vh]'>
      <Card className='max-w-md text-center'>
        <CardHeader>
          <div className='mx-auto mb-4'>
            <XCircle className='h-16 w-16 text-muted-foreground' />
          </div>
          <CardTitle className='text-2xl'>Checkout Cancelled</CardTitle>
          <CardDescription>
            No worries! Your checkout was cancelled and you weren&apos;t
            charged.
          </CardDescription>
        </CardHeader>
        <CardContent className='space-y-6'>
          <p className='text-sm text-muted-foreground'>
            If you have any questions about our plans or need help deciding,
            feel free to reach out to us.
          </p>

          <div className='flex flex-col gap-3'>
            <Button onClick={() => navigate('/pricing')} className='w-full'>
              View Plans Again
            </Button>
            <Button
              variant='outline'
              onClick={() => navigate('/generate')}
              className='w-full'
            >
              <ArrowLeft className='mr-2 h-4 w-4' />
              Continue with Free
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
