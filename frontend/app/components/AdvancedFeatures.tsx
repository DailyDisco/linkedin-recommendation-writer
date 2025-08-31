import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

import { FileText, Target, Lightbulb, TrendingUp } from 'lucide-react';
import { ReadmeGenerator } from './ReadmeGenerator';
import { SkillGapAnalysis } from './SkillGapAnalysis';
import type { ReadmeGenerationData, SkillAnalysisData } from '../types/index';

interface AdvancedFeaturesProps {
  // API functions that would be passed from parent
  onGenerateReadme: (data: ReadmeGenerationData) => Promise<{
    repository_name: string;
    generated_content: string;
    sections: Record<string, string>;
  }>;
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
    id: 'readme-generator',
    title: 'README Generator',
    description: 'Create professional READMEs from repository analysis',
    icon: FileText,
    component: ReadmeGenerator,
  },
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
  onGenerateReadme,
  onAnalyzeSkills,
}) => {
  const [activeFeature, setActiveFeature] = useState(FEATURES[0].id);

  const renderFeatureComponent = (feature: (typeof FEATURES)[0]) => {
    switch (feature.id) {
      case 'readme-generator':
        return <ReadmeGenerator onGenerate={onGenerateReadme} />;
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
        <TabsList className='grid w-full grid-cols-2'>
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
                <ol className='text-sm text-muted-foreground space-y-2 list-decimal list-inside'>
                  <li>
                    <strong>Start with Skill Gap Analysis</strong> - Understand
                    your current skill profile
                  </li>
                  <li>
                    <strong>Generate READMEs</strong> - Create professional
                    documentation for your projects
                  </li>
                </ol>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
