import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Target, TrendingUp, BookOpen, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { apiClient, handleApiError } from '@/services/api';
import type { SkillGapAnalysisResponse } from '../types';

interface Skill {
  skill: string;
  match_level: string;
  evidence: string[];
  confidence_score: number;
}

interface SkillGapAnalysisProps {
  onAnalyze?: (data: {
    github_username: string;
    target_role: string;
    industry: string;
    experience_level: string;
  }) => Promise<{
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
  onAnalysisComplete?: (result: unknown) => void;
}

const ROLE_OPTIONS = [
  'Frontend Developer',
  'Backend Developer',
  'Full Stack Developer',
  'Data Scientist',
  'DevOps Engineer',
  'Mobile Developer',
  'Product Manager',
  'UX Designer',
  'System Architect',
];

const INDUSTRY_OPTIONS = [
  'Technology',
  'Finance',
  'Healthcare',
  'E-commerce',
  'Education',
  'Entertainment',
  'Government',
  'Consulting',
];

const EXPERIENCE_LEVELS = [
  { value: 'junior', label: 'Junior (0-2 years)' },
  { value: 'mid', label: 'Mid-level (2-5 years)' },
  { value: 'senior', label: 'Senior (5+ years)' },
];

const getMatchLevelColor = (level: string) => {
  switch (level) {
    case 'strong':
      return 'bg-green-500';
    case 'moderate':
      return 'bg-yellow-500';
    case 'weak':
      return 'bg-orange-500';
    case 'missing':
      return 'bg-red-500';
    default:
      return 'bg-gray-500';
  }
};

const getMatchLevelLabel = (level: string) => {
  switch (level) {
    case 'strong':
      return 'Strong Match';
    case 'moderate':
      return 'Moderate Match';
    case 'weak':
      return 'Weak Match';
    case 'missing':
      return 'Missing';
    default:
      return level;
  }
};

export const SkillGapAnalysis: React.FC<SkillGapAnalysisProps> = ({
  onAnalyze,
  onAnalysisComplete,
}) => {
  const [githubUsername, setGithubUsername] = useState('');
  const [targetRole, setTargetRole] = useState('');
  const [industry, setIndustry] = useState('technology');
  const [experienceLevel, setExperienceLevel] = useState('mid');
  const [analysisResult, setAnalysisResult] =
    useState<SkillGapAnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleAnalyze = async () => {
    if (!githubUsername.trim()) {
      toast.error('Please enter a GitHub username.');
      return;
    }
    if (!targetRole.trim()) {
      toast.error('Please select a target role.');
      return;
    }

    setIsLoading(true);

    try {
      const analysisData = {
        github_username: githubUsername,
        target_role: targetRole,
        industry,
        experience_level: experienceLevel,
      };

      // Call the API
      const apiResult = await apiClient.analyzeSkillGaps(analysisData);
      setAnalysisResult(apiResult);

      toast.success(`Skill gap analysis completed for ${githubUsername}!`);

      // Call the callback if provided
      if (onAnalyze) {
        await onAnalyze(analysisData);
      }

      if (onAnalysisComplete) {
        onAnalysisComplete(apiResult);
      }
    } catch (err: unknown) {
      const errorInfo = handleApiError(err);
      toast.error(
        errorInfo.message ||
          'Failed to perform skill gap analysis. Please try again.'
      );
      console.error('Skill gap analysis failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className='space-y-6'>
      <Card>
        <CardHeader>
          <CardTitle className='flex items-center gap-2'>
            <Target className='w-5 h-5' />
            Skill Gap Analysis
          </CardTitle>
          <CardDescription>
            Analyze your GitHub profile against job requirements and get
            personalized recommendations
          </CardDescription>
        </CardHeader>
        <CardContent className='space-y-6'>
          {/* GitHub Username */}
          <div className='space-y-2'>
            <Label htmlFor='github-username'>GitHub Username</Label>
            <Input
              id='github-username'
              value={githubUsername}
              onChange={e => setGithubUsername(e.target.value)}
              placeholder='e.g., octocat'
            />
          </div>

          {/* Target Role */}
          <div className='space-y-2'>
            <Label htmlFor='target-role'>Target Role</Label>
            <Select value={targetRole} onValueChange={setTargetRole}>
              <SelectTrigger>
                <SelectValue placeholder='Select target role' />
              </SelectTrigger>
              <SelectContent>
                {ROLE_OPTIONS.map(role => (
                  <SelectItem key={role} value={role}>
                    {role}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Industry */}
          <div className='space-y-2'>
            <Label htmlFor='industry'>Industry</Label>
            <Select value={industry} onValueChange={setIndustry}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {INDUSTRY_OPTIONS.map(ind => (
                  <SelectItem key={ind} value={ind.toLowerCase()}>
                    {ind}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Experience Level */}
          <div className='space-y-2'>
            <Label htmlFor='experience'>Experience Level</Label>
            <Select value={experienceLevel} onValueChange={setExperienceLevel}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {EXPERIENCE_LEVELS.map(level => (
                  <SelectItem key={level.value} value={level.value}>
                    {level.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Button
            onClick={handleAnalyze}
            disabled={isLoading || !githubUsername.trim() || !targetRole.trim()}
            className='w-full'
          >
            {isLoading && <Loader2 className='w-4 h-4 mr-2 animate-spin' />}
            {isLoading ? 'Analyzing...' : 'Analyze Skills'}
          </Button>
        </CardContent>
      </Card>

      {/* Analysis Results */}
      {analysisResult && (
        <Card>
          <CardHeader>
            <CardTitle>Analysis Results</CardTitle>
            <CardDescription>
              GitHub: {githubUsername} | Target: {targetRole} | Match Score:{' '}
              {analysisResult.overall_match_score}%
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue='overview' className='w-full'>
              <TabsList className='grid w-full grid-cols-4'>
                <TabsTrigger value='overview'>Overview</TabsTrigger>
                <TabsTrigger value='skills'>Skills</TabsTrigger>
                <TabsTrigger value='recommendations'>
                  Recommendations
                </TabsTrigger>
                <TabsTrigger value='resources'>Resources</TabsTrigger>
              </TabsList>

              <TabsContent value='overview' className='space-y-6'>
                {/* Overall Match Score */}
                <div className='text-center'>
                  <div className='text-4xl font-bold text-primary mb-2'>
                    {analysisResult.overall_match_score}%
                  </div>
                  <Progress
                    value={analysisResult.overall_match_score}
                    className='w-full'
                  />
                  <p className='text-sm text-muted-foreground mt-2'>
                    Overall match for {targetRole} role
                  </p>
                </div>

                {/* Summary */}
                <div className='bg-muted p-4 rounded-lg'>
                  <p className='text-sm'>{analysisResult.analysis_summary}</p>
                </div>

                {/* Quick Stats */}
                <div className='grid grid-cols-2 gap-4'>
                  <div className='text-center p-4 border rounded-lg'>
                    <div className='text-2xl font-bold text-green-600'>
                      {analysisResult.strengths.length}
                    </div>
                    <div className='text-sm text-muted-foreground'>
                      Strengths
                    </div>
                  </div>
                  <div className='text-center p-4 border rounded-lg'>
                    <div className='text-2xl font-bold text-red-600'>
                      {analysisResult.gaps.length}
                    </div>
                    <div className='text-sm text-muted-foreground'>
                      Skill Gaps
                    </div>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value='skills' className='space-y-4'>
                {analysisResult.skill_analysis.map(
                  (skill: Skill, index: number) => (
                    <div key={index} className='border rounded-lg p-4'>
                      <div className='flex items-center justify-between mb-2'>
                        <h3 className='font-semibold'>{skill.skill}</h3>
                        <Badge
                          className={getMatchLevelColor(skill.match_level)}
                        >
                          {getMatchLevelLabel(skill.match_level)}
                        </Badge>
                      </div>
                      {skill.evidence.length > 0 && (
                        <div className='space-y-1'>
                          <div className='text-sm font-medium'>Evidence:</div>
                          <ul className='text-sm text-muted-foreground'>
                            {skill.evidence.map(
                              (evidence: string, i: number) => (
                                <li key={i}>• {evidence}</li>
                              )
                            )}
                          </ul>
                        </div>
                      )}
                    </div>
                  )
                )}
              </TabsContent>

              <TabsContent value='recommendations' className='space-y-4'>
                <div className='grid gap-4'>
                  {analysisResult.recommendations.map(
                    (rec: string, index: number) => (
                      <div
                        key={index}
                        className='flex items-start gap-3 p-4 border rounded-lg'
                      >
                        <TrendingUp className='w-5 h-5 text-primary mt-0.5' />
                        <p className='text-sm'>{rec}</p>
                      </div>
                    )
                  )}
                </div>
              </TabsContent>

              <TabsContent value='resources' className='space-y-4'>
                <div className='grid gap-4'>
                  {analysisResult.learning_resources.map(
                    (resource: string, index: number) => (
                      <div
                        key={index}
                        className='flex items-start gap-3 p-4 border rounded-lg'
                      >
                        <BookOpen className='w-5 h-5 text-primary mt-0.5' />
                        <p className='text-sm'>{resource}</p>
                      </div>
                    )
                  )}
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
