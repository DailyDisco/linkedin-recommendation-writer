import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';

import {
  FileText,
  Target,
  GitBranch,
  Lightbulb,
  TrendingUp,
  Sparkles,
} from 'lucide-react';
import { ReadmeGenerator } from './ReadmeGenerator';
import { SkillGapAnalysis } from './SkillGapAnalysis';
import type { ReadmeGenerationData, SkillAnalysisData } from '../types/index';

interface AdvancedFeaturesProps {
  // API functions that would be passed from parent
  onGenerateReadme: (data: ReadmeGenerationData) => Promise<{
    repository_name: string;
    generated_content: string;
    sections: Record<string, string>;
    confidence_score: number;
  }>;
  onAnalyzeSkills: (data: SkillAnalysisData) => Promise<{
    overall_match_score: number;
    skill_analysis: Array<{
      skill: string;
      match_level: string;
      evidence: string[];
      confidence_score: number;
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
      <Card>
        <CardHeader>
          <CardTitle className='flex items-center gap-2'>
            <Sparkles className='w-5 h-5' />
            Advanced Features
          </CardTitle>
          <CardDescription>
            Powerful new capabilities to enhance your LinkedIn recommendation
            workflow
          </CardDescription>
        </CardHeader>
        <CardContent>
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
                <Card>
                  <CardHeader>
                    <CardTitle className='flex items-center gap-2'>
                      <feature.icon className='w-5 h-5' />
                      {feature.title}
                    </CardTitle>
                    <CardDescription>{feature.description}</CardDescription>
                  </CardHeader>
                  <CardContent>{renderFeatureComponent(feature)}</CardContent>
                </Card>
              </TabsContent>
            ))}
          </Tabs>
        </CardContent>
      </Card>

      {/* Feature Overview */}
      <Card>
        <CardHeader>
          <CardTitle className='flex items-center gap-2'>
            <TrendingUp className='w-5 h-5' />
            What&apos;s New
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className='grid gap-4 md:grid-cols-2'>
            <div className='space-y-3'>
              <h3 className='font-semibold flex items-center gap-2'>
                <Lightbulb className='w-4 h-4' />
                Enhanced Data Quality
              </h3>
              <ul className='text-sm text-muted-foreground space-y-1'>
                <li>• Analyzes dependency files and starred repositories</li>
                <li>• Parses conventional commits for better insights</li>
                <li>• Extracts API endpoints from source code</li>
                <li>• Improved confidence scoring system</li>
              </ul>
            </div>

            <div className='space-y-3'>
              <h3 className='font-semibold flex items-center gap-2'>
                <GitBranch className='w-4 h-4' />
                New Features
              </h3>
              <ul className='text-sm text-muted-foreground space-y-1'>
                <li>• Keyword refinement with include/exclude lists</li>
                <li>• Automated README generation</li>
                <li>• Skill gap analysis for target roles</li>
                <li>• Recommendation version history</li>
              </ul>
            </div>
          </div>

          <div className='mt-6 p-4 bg-muted rounded-lg'>
            <div className='flex items-start gap-3'>
              <TrendingUp className='w-5 h-5 text-primary mt-0.5' />
              <div>
                <h4 className='font-medium mb-1'>Pro Tip</h4>
                <p className='text-sm text-muted-foreground'>
                  Try the new features in order - start with Skill Gap Analysis
                  to understand your profile, then use README Generator to
                  create professional documentation for your projects.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
