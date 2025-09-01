import React, { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card';
import {
  CheckCircle,
  Share2,
  Clipboard,
  ChevronLeft,
  Loader2,
} from 'lucide-react';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import type {
  RecommendationOption,
  ContributorInfo,
  Recommendation as ApiRecommendation,
  KeywordRefinementResult, // Import KeywordRefinementResult
} from '@/types/index';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Plus, X } from 'lucide-react';

interface FormData {
  workingRelationship: string;
  specificSkills: string;
  timeWorkedTogether: string;
  notableAchievements: string;
  recommendation_type:
    | 'professional'
    | 'technical'
    | 'leadership'
    | 'academic'
    | 'personal';
  tone: 'professional' | 'friendly' | 'formal' | 'casual';
  length: 'short' | 'medium' | 'long';
  github_input: string;
  analysis_type: 'profile' | 'repo_only';
  repository_url?: string;
  include_keywords?: string[]; // Added to FormData
  exclude_keywords?: string[]; // Added to FormData
}

interface RecommendationResultDisplayProps {
  generatedRecommendation: ApiRecommendation | null;
  selectedOption: RecommendationOption | null;
  contributor: ContributorInfo;
  formData: FormData;
  activeTab: 'preview' | 'refine';
  resultRef: React.RefObject<HTMLDivElement | null>;
  regenerateInstructions: string;
  setActiveTab: (tab: 'preview' | 'refine') => void;
  setRegenerateInstructions: (instructions: string) => void;

  isRegenerating: boolean;
  onBackToOptions: () => void;
  onGenerateAnother: () => void;
  onRefine: (params: {
    // Modified to accept dynamic parameters
    tone: FormData['tone'];
    length: FormData['length'];
    include_keywords: string[];
    exclude_keywords: string[];
    refinement_instructions: string;
  }) => void;

  initialIncludeKeywords?: string[];
  initialExcludeKeywords?: string[];
}

const TONE_OPTIONS = [
  { value: 'professional', label: 'Professional' },
  { value: 'friendly', label: 'Friendly' },
  { value: 'formal', label: 'Formal' },
  { value: 'casual', label: 'Casual' },
];

const LENGTH_OPTIONS = [
  { value: 'short', label: 'Short' },
  { value: 'medium', label: 'Medium' },
  { value: 'long', label: 'Long' },
];

export default function RecommendationResultDisplay({
  generatedRecommendation,
  selectedOption,
  contributor,
  formData,
  activeTab,
  resultRef,
  regenerateInstructions,
  setActiveTab,
  setRegenerateInstructions,
  isRegenerating,
  onBackToOptions,
  onGenerateAnother,
  onRefine,
  initialIncludeKeywords = [],
  initialExcludeKeywords = [],
}: RecommendationResultDisplayProps) {
  const [isCopied, setIsCopied] = useState(false);

  // State for dynamic refinement
  const [dynamicTone, setDynamicTone] = useState<FormData['tone']>(
    formData.tone
  );
  const [dynamicLength, setDynamicLength] = useState<FormData['length']>(
    formData.length
  );
  const [includeKeywords, setIncludeKeywords] = useState<string[]>(
    initialIncludeKeywords
  );
  const [excludeKeywords, setExcludeKeywords] = useState<string[]>(
    initialExcludeKeywords
  );
  const [newIncludeKeyword, setNewIncludeKeyword] = useState('');
  const [newExcludeKeyword, setNewExcludeKeyword] = useState('');

  useEffect(() => {
    if (generatedRecommendation) {
      setIsCopied(false);
    }
  }, [generatedRecommendation]);

  // Initialize and update dynamic parameters when formData changes or component mounts
  useEffect(() => {
    setDynamicTone(formData.tone);
    setDynamicLength(formData.length);
    setIncludeKeywords(formData.include_keywords || []);
    setExcludeKeywords(formData.exclude_keywords || []);
    // Note: regenerateInstructions is managed by its own state in RecommendationModal/useRecommendationState
  }, [
    formData.tone,
    formData.length,
    formData.include_keywords,
    formData.exclude_keywords,
  ]);

  // Update dynamic keywords if initial props change (e.g., when a regenerated result comes back)
  useEffect(() => {
    setIncludeKeywords(initialIncludeKeywords);
  }, [initialIncludeKeywords]);

  useEffect(() => {
    setExcludeKeywords(initialExcludeKeywords);
  }, [initialExcludeKeywords]);

  const currentContent =
    generatedRecommendation?.content || selectedOption?.content || '';
  const currentTitle =
    generatedRecommendation?.title || selectedOption?.title || '';
  const currentWordCount =
    generatedRecommendation?.word_count || selectedOption?.word_count || 0;

  const copyToClipboard = () => {
    navigator.clipboard.writeText(currentContent);
    setIsCopied(true);
    toast.success('Recommendation copied to clipboard!');
  };

  const addKeyword = (keyword: string, type: 'include' | 'exclude') => {
    if (!keyword.trim()) return;

    if (type === 'include') {
      if (!includeKeywords.includes(keyword.trim())) {
        setIncludeKeywords([...includeKeywords, keyword.trim()]);
      }
      setNewIncludeKeyword('');
    } else {
      if (!excludeKeywords.includes(keyword.trim())) {
        setExcludeKeywords([...excludeKeywords, keyword.trim()]);
      }
      setNewExcludeKeyword('');
    }
  };

  const removeKeyword = (keyword: string, type: 'include' | 'exclude') => {
    if (type === 'include') {
      setIncludeKeywords(includeKeywords.filter(k => k !== keyword));
    } else {
      setExcludeKeywords(excludeKeywords.filter(k => k !== keyword));
    }
  };

  const handleRefineClick = () => {
    onRefine({
      tone: dynamicTone,
      length: dynamicLength,
      include_keywords: includeKeywords,
      exclude_keywords: excludeKeywords,
      refinement_instructions: regenerateInstructions,
    });
  };

  return (
    <div ref={resultRef} className='space-y-6'>
      <Card>
        <CardHeader>
          <div className='flex items-center justify-between'>
            <div>
              <CardTitle className='text-2xl font-bold'>
                {currentTitle}
              </CardTitle>
              <CardDescription className='text-gray-600'>
                Recommendation for{' '}
                {contributor.full_name || contributor.username}
              </CardDescription>
            </div>
            <div className='flex items-center gap-2'>
              <Button
                onClick={copyToClipboard}
                variant='secondary'
                size='sm'
                className='flex items-center gap-1'
                disabled={isCopied}
              >
                {isCopied ? (
                  <CheckCircle className='w-4 h-4 text-green-500' />
                ) : (
                  <Clipboard className='w-4 h-4' />
                )}
                {isCopied ? 'Copied!' : 'Copy'}
              </Button>
              <Button
                variant='outline'
                size='sm'
                className='flex items-center gap-1'
              >
                <Share2 className='w-4 h-4' /> Share
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Tabs
            value={activeTab}
            onValueChange={value => setActiveTab(value as 'preview' | 'refine')}
            className='w-full'
          >
            <TabsList className='grid w-full grid-cols-2'>
              <TabsTrigger value='preview'>Preview</TabsTrigger>
              <TabsTrigger value='refine'>Refine</TabsTrigger>
            </TabsList>

            {/* Preview Tab */}
            <TabsContent value='preview' className='mt-4'>
              <div className='prose prose-sm max-w-none mb-4'>
                <pre className='whitespace-pre-wrap font-sans text-sm bg-muted p-4 rounded-md'>
                  {currentContent}
                </pre>
              </div>
              <div className='flex justify-between items-center text-sm text-gray-500'>
                <span>Word Count: {currentWordCount}</span>
                <span>
                  Type: {formData.recommendation_type} | Tone: {dynamicTone} |
                  Length: {dynamicLength}
                </span>
              </div>
            </TabsContent>

            {/* Refine Tab */}
            <TabsContent value='refine' className='mt-4 space-y-6'>
              <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
                {/* Tone Selection */}
                <div className='space-y-2'>
                  <Label htmlFor='tone-select'>Tone</Label>
                  <Select
                    value={dynamicTone}
                    onValueChange={value =>
                      setDynamicTone(value as FormData['tone'])
                    }
                  >
                    <SelectTrigger id='tone-select'>
                      <SelectValue placeholder='Select tone' />
                    </SelectTrigger>
                    <SelectContent>
                      {TONE_OPTIONS.map(option => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Length Selection */}
                <div className='space-y-2'>
                  <Label htmlFor='length-select'>Length</Label>
                  <Select
                    value={dynamicLength}
                    onValueChange={value =>
                      setDynamicLength(value as FormData['length'])
                    }
                  >
                    <SelectTrigger id='length-select'>
                      <SelectValue placeholder='Select length' />
                    </SelectTrigger>
                    <SelectContent>
                      {LENGTH_OPTIONS.map(option => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Include Keywords */}
              <div className='space-y-3'>
                <Label htmlFor='include-keywords'>Keywords to Include</Label>
                <div className='flex gap-2'>
                  <Input
                    id='include-keywords'
                    value={newIncludeKeyword}
                    onChange={e => setNewIncludeKeyword(e.target.value)}
                    placeholder='Enter keyword to include...'
                    onKeyPress={e => {
                      if (e.key === 'Enter') {
                        addKeyword(newIncludeKeyword, 'include');
                      }
                    }}
                  />
                  <Button
                    type='button'
                    variant='outline'
                    size='sm'
                    onClick={() => addKeyword(newIncludeKeyword, 'include')}
                  >
                    <Plus className='w-4 h-4' />
                  </Button>
                </div>
                <div className='flex flex-wrap gap-2'>
                  {includeKeywords.map(keyword => (
                    <Badge
                      key={keyword}
                      variant='default'
                      className='flex items-center gap-1'
                    >
                      {keyword}
                      <X
                        className='w-3 h-3 cursor-pointer'
                        onClick={() => removeKeyword(keyword, 'include')}
                      />
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Exclude Keywords */}
              <div className='space-y-3'>
                <Label htmlFor='exclude-keywords'>Keywords to Exclude</Label>
                <div className='flex gap-2'>
                  <Input
                    id='exclude-keywords'
                    value={newExcludeKeyword}
                    onChange={e => setNewExcludeKeyword(e.target.value)}
                    placeholder='Enter keyword to exclude...'
                    onKeyPress={e => {
                      if (e.key === 'Enter') {
                        addKeyword(newExcludeKeyword, 'exclude');
                      }
                    }}
                  />
                  <Button
                    type='button'
                    variant='outline'
                    size='sm'
                    onClick={() => addKeyword(newExcludeKeyword, 'exclude')}
                  >
                    <Plus className='w-4 h-4' />
                  </Button>
                </div>
                <div className='flex flex-wrap gap-2'>
                  {excludeKeywords.map(keyword => (
                    <Badge
                      key={keyword}
                      variant='destructive'
                      className='flex items-center gap-1'
                    >
                      {keyword}
                      <X
                        className='w-3 h-3 cursor-pointer'
                        onClick={() => removeKeyword(keyword, 'exclude')}
                      />
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Additional Refinement Instructions */}
              <div className='space-y-3'>
                <Label htmlFor='refinement-instructions'>
                  Additional Refinement Instructions
                </Label>
                <Textarea
                  id='refinement-instructions'
                  value={regenerateInstructions}
                  onChange={e => setRegenerateInstructions(e.target.value)}
                  placeholder='Enter any specific instructions for refining the recommendation (e.g., "Make it more concise", "Emphasize leadership skills")...'
                  rows={3}
                />
              </div>

              <Button
                onClick={handleRefineClick}
                disabled={isRegenerating}
                className='w-full'
              >
                {isRegenerating && (
                  <Loader2 className='w-4 h-4 mr-2 animate-spin' />
                )}
                {isRegenerating ? 'Refining...' : 'Refine Recommendation'}
              </Button>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className='flex justify-between mt-6'>
        <Button
          variant='outline'
          onClick={onBackToOptions}
          className='flex items-center gap-2'
        >
          <ChevronLeft className='w-4 h-4' /> Back to Options
        </Button>
        <Button onClick={onGenerateAnother}>Generate Another</Button>
      </div>
    </div>
  );
}
