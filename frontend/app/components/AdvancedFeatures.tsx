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
  Settings,
  FileText,
  Users,
  Target,
  GitBranch,
  Lightbulb,
  TrendingUp,
  Sparkles,
} from 'lucide-react';
import { KeywordRefinement } from './KeywordRefinement';
import { ReadmeGenerator } from './ReadmeGenerator';
import { SkillGapAnalysis } from './SkillGapAnalysis';
import { MultiContributorGenerator } from './MultiContributorGenerator';

interface KeywordRefineData {
  keywords: string[];
  exclude_keywords?: string[];
  tone?: string;
  length?: string;
}

interface ReadmeGenerationData {
  repository_full_name: string;
  style: string;
  include_sections?: string[];
  target_audience: string;
}

interface SkillAnalysisData {
  github_username: string;
  target_role: string;
  industry: string;
  experience_level: string;
}

interface MultiContributorData {
  contributors: Array<{
    github_username: string;
    contribution_type: string;
    project_role?: string;
  }>;
  project_description: string;
  recommendation_tone?: string;
}

interface AdvancedFeaturesProps {
  // API functions that would be passed from parent
  onKeywordRefine: (data: KeywordRefineData) => Promise<unknown>;
  onGenerateReadme: (data: ReadmeGenerationData) => Promise<unknown>;
  onAnalyzeSkills: (data: SkillAnalysisData) => Promise<unknown>;
  onGenerateMultiContributor: (data: MultiContributorData) => Promise<unknown>;
}

const FEATURES = [
  {
    id: 'keyword-refinement',
    title: 'Keyword Refinement',
    description: 'Fine-tune recommendations with specific keywords and phrases',
    icon: Settings,
    component: KeywordRefinement,
  },
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

  {
    id: 'multi-contributor',
    title: 'Team Recommendations',
    description: 'Generate recommendations for collaborative team projects',
    icon: Users,
    component: MultiContributorGenerator,
  },
];

export const AdvancedFeatures: React.FC<AdvancedFeaturesProps> = ({
  onKeywordRefine,
  onGenerateReadme,
  onAnalyzeSkills,
  onGenerateMultiContributor,
}) => {
  const [activeFeature, setActiveFeature] = useState(FEATURES[0].id);

  const renderFeatureComponent = (feature: (typeof FEATURES)[0]) => {
    const Component = feature.component;

    const props: Record<string, unknown> = {};

    switch (feature.id) {
      case 'keyword-refinement':
        props.onRefine = onKeywordRefine;
        break;
      case 'readme-generator':
        props.onGenerate = onGenerateReadme;
        break;
      case 'skill-gap-analysis':
        props.onAnalyze = onAnalyzeSkills;
        break;
      case 'multi-contributor':
        props.onGenerate = onGenerateMultiContributor;
        break;
    }

    return <Component {...props} />;
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
            <TabsList className='grid w-full grid-cols-4'>
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
                <li>• Multi-contributor team recommendations</li>
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
                  to understand your profile, then use Keyword Refinement to
                  fine-tune your recommendations for specific roles.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
