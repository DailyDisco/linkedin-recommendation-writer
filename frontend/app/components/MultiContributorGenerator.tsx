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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Users, GitFork, Lightbulb, Zap } from 'lucide-react';

interface Contributor {
  username: string;
  full_name?: string;
  contributions: number;
  contribution_focus: string;
  primary_languages: string[];
}

interface MultiContributorGeneratorProps {
  onGenerate: (data: {
    repository_full_name: string;
    max_contributors: number;
    min_contributions: number;
    focus_areas?: string[];
    recommendation_type: string;
    tone: string;
    length: string;
  }) => Promise<{
    repository_name: string;
    repository_full_name: string;
    total_contributors: number;
    contributors_analyzed: number;
    contributors: Array<{
      username: string;
      full_name?: string;
      contributions: number;
      primary_languages: string[];
      top_skills: string[];
      contribution_focus: string;
      key_contributions: string[];
    }>;
    recommendation: string;
    team_highlights: string[];
    collaboration_insights: string[];
    technical_diversity: Record<string, number>;
    word_count: number;
    confidence_score: number;
  }>;
}

const FOCUS_AREAS = [
  'Frontend Development',
  'Backend Development',
  'DevOps',
  'Testing',
  'Documentation',
  'Architecture',
  'Performance',
  'Security',
  'Mobile Development',
  'Data Science',
];

const RECOMMENDATION_TYPES = [
  {
    value: 'professional',
    label: 'Professional',
    description: 'Formal, business-focused',
  },
  {
    value: 'technical',
    label: 'Technical',
    description: 'Emphasize technical expertise',
  },
  {
    value: 'leadership',
    label: 'Leadership',
    description: 'Highlight team leadership',
  },
];

const TONES = [
  {
    value: 'professional',
    label: 'Professional',
    description: 'Formal and polished',
  },
  {
    value: 'friendly',
    label: 'Friendly',
    description: 'Warm and approachable',
  },
  {
    value: 'enthusiastic',
    label: 'Enthusiastic',
    description: 'Energetic and passionate',
  },
];

const LENGTHS = [
  { value: 'short', label: 'Short', description: '100-150 words' },
  { value: 'medium', label: 'Medium', description: '150-200 words' },
  { value: 'long', label: 'Long', description: '200-300 words' },
];

export const MultiContributorGenerator: React.FC<
  MultiContributorGeneratorProps
> = ({ onGenerate }) => {
  const [repositoryName, setRepositoryName] = useState('');
  const [maxContributors, setMaxContributors] = useState(5);
  const [minContributions, setMinContributions] = useState(1);
  const [focusAreas, setFocusAreas] = useState<string[]>([]);
  const [recommendationType, setRecommendationType] = useState('professional');
  const [tone, setTone] = useState('professional');
  const [length, setLength] = useState('medium');
  const [result, setResult] = useState<Awaited<
    ReturnType<MultiContributorGeneratorProps['onGenerate']>
  > | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const toggleFocusArea = (area: string) => {
    setFocusAreas(prev =>
      prev.includes(area) ? prev.filter(a => a !== area) : [...prev, area]
    );
  };

  const handleGenerate = async () => {
    if (!repositoryName.trim()) return;

    setIsLoading(true);
    try {
      const data = await onGenerate({
        repository_full_name: repositoryName,
        max_contributors: maxContributors,
        min_contributions: minContributions,
        focus_areas: focusAreas.length > 0 ? focusAreas : undefined,
        recommendation_type: recommendationType,
        tone: tone,
        length: length,
      });
      setResult(data);
    } catch (error) {
      console.error(
        'Failed to generate multi-contributor recommendation:',
        error
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className='space-y-6'>
      <Card>
        <CardHeader>
          <CardTitle className='flex items-center gap-2'>
            <Users className='w-5 h-5' />
            Multi-Contributor Recommendation
          </CardTitle>
          <CardDescription>
            Generate recommendations highlighting collaborative team work on
            GitHub repositories
          </CardDescription>
        </CardHeader>
        <CardContent className='space-y-6'>
          {/* Repository Input */}
          <div className='space-y-2'>
            <Label htmlFor='repository'>Repository (owner/repo)</Label>
            <Input
              id='repository'
              value={repositoryName}
              onChange={e => setRepositoryName(e.target.value)}
              placeholder='e.g., facebook/react'
            />
          </div>

          {/* Contributor Settings */}
          <div className='grid grid-cols-2 gap-4'>
            <div className='space-y-2'>
              <Label htmlFor='max-contributors'>Max Contributors</Label>
              <Select
                value={maxContributors.toString()}
                onValueChange={v => setMaxContributors(parseInt(v))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {[3, 5, 7, 10].map(num => (
                    <SelectItem key={num} value={num.toString()}>
                      {num}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className='space-y-2'>
              <Label htmlFor='min-contributions'>Min Contributions</Label>
              <Select
                value={minContributions.toString()}
                onValueChange={v => setMinContributions(parseInt(v))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {[1, 5, 10, 20, 50].map(num => (
                    <SelectItem key={num} value={num.toString()}>
                      {num}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Focus Areas */}
          <div className='space-y-3'>
            <Label>Focus Areas (Optional)</Label>
            <div className='grid grid-cols-2 gap-2'>
              {FOCUS_AREAS.map(area => (
                <Button
                  key={area}
                  type='button'
                  variant={focusAreas.includes(area) ? 'default' : 'outline'}
                  size='sm'
                  onClick={() => toggleFocusArea(area)}
                >
                  {area}
                </Button>
              ))}
            </div>
            {focusAreas.length > 0 && (
              <div className='flex flex-wrap gap-2'>
                {focusAreas.map(area => (
                  <Badge key={area} variant='secondary'>
                    {area}
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* Recommendation Settings */}
          <div className='grid grid-cols-3 gap-4'>
            <div className='space-y-2'>
              <Label>Style</Label>
              <Select
                value={recommendationType}
                onValueChange={setRecommendationType}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {RECOMMENDATION_TYPES.map(type => (
                    <SelectItem key={type.value} value={type.value}>
                      <div>
                        <div className='font-medium'>{type.label}</div>
                        <div className='text-sm text-muted-foreground'>
                          {type.description}
                        </div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className='space-y-2'>
              <Label>Tone</Label>
              <Select value={tone} onValueChange={setTone}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TONES.map(t => (
                    <SelectItem key={t.value} value={t.value}>
                      <div>
                        <div className='font-medium'>{t.label}</div>
                        <div className='text-sm text-muted-foreground'>
                          {t.description}
                        </div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className='space-y-2'>
              <Label>Length</Label>
              <Select value={length} onValueChange={setLength}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {LENGTHS.map(l => (
                    <SelectItem key={l.value} value={l.value}>
                      <div>
                        <div className='font-medium'>{l.label}</div>
                        <div className='text-sm text-muted-foreground'>
                          {l.description}
                        </div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <Button
            onClick={handleGenerate}
            disabled={isLoading || !repositoryName.trim()}
            className='w-full'
          >
            {isLoading ? 'Generating...' : 'Generate Team Recommendation'}
          </Button>
        </CardContent>
      </Card>

      {/* Results */}
      {result && (
        <Card>
          <CardHeader>
            <CardTitle>Team Recommendation</CardTitle>
            <CardDescription>
              Repository: {result.repository_full_name} |
              {result.contributors_analyzed} contributors analyzed | Confidence:{' '}
              {result.confidence_score}%
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue='recommendation' className='w-full'>
              <TabsList className='grid w-full grid-cols-4'>
                <TabsTrigger value='recommendation'>Recommendation</TabsTrigger>
                <TabsTrigger value='contributors'>Contributors</TabsTrigger>
                <TabsTrigger value='insights'>Team Insights</TabsTrigger>
                <TabsTrigger value='diversity'>Tech Diversity</TabsTrigger>
              </TabsList>

              <TabsContent value='recommendation' className='space-y-4'>
                <div className='prose prose-sm max-w-none'>
                  <pre className='whitespace-pre-wrap font-sans text-sm'>
                    {result.recommendation}
                  </pre>
                </div>
                <div className='text-sm text-muted-foreground'>
                  {result.word_count} words
                </div>
              </TabsContent>

              <TabsContent value='contributors' className='space-y-4'>
                <div className='grid gap-4'>
                  {result.contributors.map(
                    (contributor: Contributor, index: number) => (
                      <Card key={index}>
                        <CardContent className='p-4'>
                          <div className='flex items-center justify-between mb-2'>
                            <div>
                              <h3 className='font-semibold'>
                                {contributor.full_name || contributor.username}
                              </h3>
                              <p className='text-sm text-muted-foreground'>
                                @{contributor.username}
                              </p>
                            </div>
                            <Badge variant='outline'>
                              {contributor.contributions} contributions
                            </Badge>
                          </div>

                          <div className='space-y-2 text-sm'>
                            <div>
                              <strong>Focus:</strong>{' '}
                              {contributor.contribution_focus}
                            </div>
                            {contributor.primary_languages.length > 0 && (
                              <div>
                                <strong>Languages:</strong>{' '}
                                {contributor.primary_languages.join(', ')}
                              </div>
                            )}
                            {contributor.top_skills.length > 0 && (
                              <div>
                                <strong>Skills:</strong>{' '}
                                {contributor.top_skills.join(', ')}
                              </div>
                            )}
                            {contributor.key_contributions.length > 0 && (
                              <div>
                                <strong>Key Contributions:</strong>
                                <ul className='mt-1 ml-4'>
                                  {contributor.key_contributions.map(
                                    (contrib: string, i: number) => (
                                      <li key={i}>• {contrib}</li>
                                    )
                                  )}
                                </ul>
                              </div>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    )
                  )}
                </div>
              </TabsContent>

              <TabsContent value='insights' className='space-y-4'>
                <div className='grid gap-4'>
                  <div>
                    <h3 className='font-semibold mb-3 flex items-center gap-2'>
                      <Lightbulb className='w-4 h-4' />
                      Team Highlights
                    </h3>
                    <div className='space-y-2'>
                      {result.team_highlights.map(
                        (highlight: string, index: number) => (
                          <div
                            key={index}
                            className='flex items-start gap-3 p-3 border rounded-lg'
                          >
                            <Zap className='w-4 h-4 text-primary mt-0.5' />
                            <p className='text-sm'>{highlight}</p>
                          </div>
                        )
                      )}
                    </div>
                  </div>

                  <div>
                    <h3 className='font-semibold mb-3 flex items-center gap-2'>
                      <GitFork className='w-4 h-4' />
                      Collaboration Insights
                    </h3>
                    <div className='space-y-2'>
                      {result.collaboration_insights.map(
                        (insight: string, index: number) => (
                          <div
                            key={index}
                            className='flex items-start gap-3 p-3 border rounded-lg'
                          >
                            <Users className='w-4 h-4 text-primary mt-0.5' />
                            <p className='text-sm'>{insight}</p>
                          </div>
                        )
                      )}
                    </div>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value='diversity' className='space-y-4'>
                <div>
                  <h3 className='font-semibold mb-3'>Technical Diversity</h3>
                  <div className='space-y-3'>
                    {Object.entries(result.technical_diversity).map(
                      ([tech, count]) => (
                        <div
                          key={tech}
                          className='flex items-center justify-between'
                        >
                          <span className='text-sm'>{tech}</span>
                          <div className='flex items-center gap-2'>
                            <Progress
                              value={(count as number) * 20}
                              className='w-24'
                            />
                            <span className='text-sm text-muted-foreground'>
                              {count}
                            </span>
                          </div>
                        </div>
                      )
                    )}
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
