import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

import { Target, Lightbulb, TrendingUp } from 'lucide-react';

export const AdvancedFeatures: React.FC = () => {
  return (
    <div className='space-y-6'>
      <Card>
        <CardHeader>
          <CardTitle className='flex items-center gap-2'>
            <Target className='w-5 h-5' />
            Advanced Features
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className='text-muted-foreground'>
            Advanced features are currently being updated. Stay tuned for new
            capabilities!
          </p>
        </CardContent>
      </Card>

      {/* Quick Start Guide */}
      <Card>
        <CardHeader>
          <CardTitle className='flex items-center gap-2'>
            <TrendingUp className='w-5 h-5' />
            Quick Start Guide
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className='p-4 bg-muted rounded-lg'>
            <div className='flex items-start gap-3'>
              <Lightbulb className='w-5 h-5 text-primary mt-0.5' />
              <div>
                <h4 className='font-medium mb-2'>Recommended Workflow</h4>
                <p className='text-sm text-muted-foreground mb-3'>
                  Get the most out of these AI tools by following this simple
                  process:
                </p>
                <div className='text-sm text-muted-foreground'>
                  <p>
                    <strong>Generate recommendations</strong> to showcase your
                    GitHub profile and professional achievements effectively.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
