import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

import { Target, Lightbulb, TrendingUp } from 'lucide-react';
import { SkillGapAnalysis } from './SkillGapAnalysis';
import type { SkillAnalysisData } from '../types/index';

interface AdvancedFeaturesProps {
  // API functions that would be passed from parent
  onAnalyzeSkills: (data: SkillAnalysisData) => Promise<{
    overall_match_score: number;
    skill_analysis: Array<{
      skill: string;
      match_level: string;
      evidence: string[];
    }>;
    strengths: string[];
    gaps: string[];
    recommendations: string[];
    learning_resources: string[];
    analysis_summary: string;
  }>;
}

const FEATURES = [
  {
    id: 'skill-gap-analysis',
    title: 'Skill Gap Analysis',
    description:
      'Analyze skill gaps for target roles and get learning recommendations',
    icon: Target,
    component: SkillGapAnalysis,
  },
];

export const AdvancedFeatures: React.FC<AdvancedFeaturesProps> = ({
  onAnalyzeSkills,
}) => {
  const [activeFeature, setActiveFeature] = useState(FEATURES[0].id);

  const renderFeatureComponent = (feature: (typeof FEATURES)[0]) => {
    switch (feature.id) {
      case 'skill-gap-analysis':
        return <SkillGapAnalysis onAnalyze={onAnalyzeSkills} />;
    }
    return null;
  };

  return (
    <div className='space-y-6'>
      <Tabs
        value={activeFeature}
        onValueChange={setActiveFeature}
        className='w-full'
      >
        <TabsList className='grid w-full grid-cols-1'>
          {FEATURES.map(feature => {
            const Icon = feature.icon;
            return (
              <TabsTrigger
                key={feature.id}
                value={feature.id}
                className='flex items-center gap-2 text-xs'
              >
                <Icon className='w-4 h-4' />
                <span className='hidden sm:inline'>{feature.title}</span>
              </TabsTrigger>
            );
          })}
        </TabsList>

        {FEATURES.map(feature => (
          <TabsContent key={feature.id} value={feature.id} className='mt-6'>
            {renderFeatureComponent(feature)}
          </TabsContent>
        ))}
      </Tabs>

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
                    <strong>Use Skill Gap Analysis</strong> to understand your
                    current skill profile and identify areas for growth based on
                    your target role.
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
