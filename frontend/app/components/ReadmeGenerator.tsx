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
import { Textarea } from '@/components/ui/textarea';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { FileText, Download, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { apiClient, handleApiError } from '@/services/api';

interface ReadmeGeneratorProps {
  onGenerate?: (data: {
    repository_full_name: string;
    style: string;
    include_sections?: string[];
    target_audience: string;
  }) => Promise<{
    repository_name: string;
    generated_content: string;
    sections: Record<string, string>;
  }>;
  onGenerationComplete?: (result: unknown) => void;
}

const STYLE_OPTIONS = [
  {
    value: 'comprehensive',
    label: 'Comprehensive',
    description: 'Complete README with all sections',
  },
  {
    value: 'minimal',
    label: 'Minimal',
    description: 'Essential information only',
  },
  {
    value: 'technical',
    label: 'Technical',
    description: 'Focus on technical details',
  },
];

const AUDIENCE_OPTIONS = [
  {
    value: 'developers',
    label: 'Developers',
    description: 'Technical audience',
  },
  { value: 'users', label: 'End Users', description: 'Non-technical users' },
  { value: 'both', label: 'Both', description: 'Mixed audience' },
];

const SECTION_OPTIONS = [
  'Installation',
  'Usage',
  'Features',
  'Requirements',
  'API Documentation',
  'Contributing',
  'Testing',
  'Deployment',
];

export const ReadmeGenerator: React.FC<ReadmeGeneratorProps> = ({
  onGenerate,
  onGenerationComplete,
}) => {
  const [repositoryName, setRepositoryName] = useState('');
  const [style, setStyle] = useState('comprehensive');
  const [targetAudience, setTargetAudience] = useState('developers');
  const [includeSections, setIncludeSections] = useState<string[]>([]);
  const [generatedReadme, setGeneratedReadme] = useState<{
    repository_name: string;
    generated_content: string;
    sections: Record<string, string>;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const toggleSection = (section: string) => {
    setIncludeSections(prev =>
      prev.includes(section)
        ? prev.filter(s => s !== section)
        : [...prev, section]
    );
  };

  const handleGenerate = async () => {
    if (!repositoryName.trim()) {
      toast.error('Please enter a repository name.');
      return;
    }

    setIsLoading(true);

    try {
      const generationData = {
        repository_full_name: repositoryName,
        style,
        include_sections:
          includeSections.length > 0 ? includeSections : undefined,
        target_audience: targetAudience,
      };

      // Call the API
      const apiResult = await apiClient.generateReadme(generationData);
      setGeneratedReadme(apiResult);

      toast.success(`README generated successfully for ${repositoryName}!`);

      // Call the callback if provided
      if (onGenerate) {
        await onGenerate(generationData);
      }

      if (onGenerationComplete) {
        onGenerationComplete(apiResult);
      }
    } catch (err: unknown) {
      const errorInfo = handleApiError(err);
      toast.error(
        errorInfo.message || 'Failed to generate README. Please try again.'
      );
      console.error('README generation failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const downloadReadme = () => {
    if (!generatedReadme) return;

    const blob = new Blob([generatedReadme.generated_content], {
      type: 'text/markdown',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'README.md';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    toast.success('README.md downloaded successfully!');
  };

  return (
    <div className='space-y-6'>
      <Card>
        <CardHeader>
          <CardTitle className='flex items-center gap-2'>
            <FileText className='w-5 h-5' />
            README Generator
          </CardTitle>
          <CardDescription>
            Generate professional README files for your GitHub repositories
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
              placeholder='e.g., octocat/Hello-World'
            />
          </div>

          {/* Style Selection */}
          <div className='space-y-2'>
            <Label>README Style</Label>
            <Select value={style} onValueChange={setStyle}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {STYLE_OPTIONS.map(option => (
                  <SelectItem key={option.value} value={option.value}>
                    <div>
                      <div className='font-medium'>{option.label}</div>
                      <div className='text-sm text-muted-foreground'>
                        {option.description}
                      </div>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Target Audience */}
          <div className='space-y-2'>
            <Label>Target Audience</Label>
            <Select value={targetAudience} onValueChange={setTargetAudience}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {AUDIENCE_OPTIONS.map(option => (
                  <SelectItem key={option.value} value={option.value}>
                    <div>
                      <div className='font-medium'>{option.label}</div>
                      <div className='text-sm text-muted-foreground'>
                        {option.description}
                      </div>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Custom Sections */}
          <div className='space-y-3'>
            <Label>Additional Sections (Optional)</Label>
            <div className='grid grid-cols-2 gap-2'>
              {SECTION_OPTIONS.map(section => (
                <Button
                  key={section}
                  type='button'
                  variant={
                    includeSections.includes(section) ? 'default' : 'outline'
                  }
                  size='sm'
                  onClick={() => toggleSection(section)}
                >
                  {section}
                </Button>
              ))}
            </div>
            {includeSections.length > 0 && (
              <div className='flex flex-wrap gap-2'>
                {includeSections.map(section => (
                  <Badge key={section} variant='secondary'>
                    {section}
                  </Badge>
                ))}
              </div>
            )}
          </div>

          <Button
            onClick={handleGenerate}
            disabled={isLoading || !repositoryName.trim()}
            className='w-full'
          >
            {isLoading && <Loader2 className='w-4 h-4 mr-2 animate-spin' />}
            {isLoading ? 'Generating...' : 'Generate README'}
          </Button>
        </CardContent>
      </Card>

      {/* Generated README Display */}
      {generatedReadme && (
        <Card>
          <CardHeader>
            <div className='flex items-center justify-between'>
              <div>
                <CardTitle>Generated README</CardTitle>
                <CardDescription>
                  Repository: {generatedReadme.repository_name}
                </CardDescription>
              </div>
              <div className='flex gap-2'>
                <Button variant='outline' size='sm' onClick={downloadReadme}>
                  <Download className='w-4 h-4 mr-2' />
                  Download
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue='preview' className='w-full'>
              <TabsList>
                <TabsTrigger value='preview'>Preview</TabsTrigger>
                <TabsTrigger value='sections'>Sections</TabsTrigger>
                <TabsTrigger value='raw'>Raw Markdown</TabsTrigger>
              </TabsList>

              <TabsContent value='preview' className='mt-4'>
                <div className='prose prose-sm max-w-none'>
                  <pre className='whitespace-pre-wrap font-sans text-sm'>
                    {generatedReadme.generated_content}
                  </pre>
                </div>
              </TabsContent>

              <TabsContent value='sections' className='mt-4'>
                <div className='space-y-4'>
                  {Object.entries(generatedReadme.sections).map(
                    ([section, content]) => (
                      <div key={section} className='border rounded-lg p-4'>
                        <h3 className='font-semibold text-lg mb-2'>
                          {section}
                        </h3>
                        <div className='prose prose-sm max-w-none'>
                          <pre className='whitespace-pre-wrap font-sans text-sm'>
                            {String(content)}
                          </pre>
                        </div>
                      </div>
                    )
                  )}
                </div>
              </TabsContent>

              <TabsContent value='raw' className='mt-4'>
                <Textarea
                  value={generatedReadme.generated_content}
                  readOnly
                  rows={20}
                  className='font-mono text-sm'
                />
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
