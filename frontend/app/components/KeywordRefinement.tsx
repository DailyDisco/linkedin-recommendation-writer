import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { X, Plus, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { apiClient, handleApiError } from '@/services/api';
import type { HttpError } from '../types';
import type { KeywordRefinementResult } from '../types';

interface KeywordRefinementProps {
  recommendationId: number;
  onRefine?: (data: {
    include_keywords: string[];
    exclude_keywords: string[];
    refinement_instructions?: string;
  }) => Promise<void>;
  onRefinementComplete?: (result: KeywordRefinementResult) => void;
}

export const KeywordRefinement: React.FC<KeywordRefinementProps> = ({
  recommendationId,
  onRefine,
  onRefinementComplete,
}) => {
  const [includeKeywords, setIncludeKeywords] = useState<string[]>([]);
  const [excludeKeywords, setExcludeKeywords] = useState<string[]>([]);
  const [refinementInstructions, setRefinementInstructions] = useState('');
  const [newIncludeKeyword, setNewIncludeKeyword] = useState('');
  const [newExcludeKeyword, setNewExcludeKeyword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<KeywordRefinementResult | null>(null);

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

  const handleRefine = async () => {
    if (
      includeKeywords.length === 0 &&
      excludeKeywords.length === 0 &&
      !refinementInstructions.trim()
    ) {
      toast.error(
        'Please add at least one keyword to include, exclude, or provide refinement instructions.'
      );
      return;
    }

    setIsLoading(true);

    try {
      const refinementData = {
        recommendation_id: recommendationId,
        include_keywords:
          includeKeywords.length > 0 ? includeKeywords : undefined,
        exclude_keywords:
          excludeKeywords.length > 0 ? excludeKeywords : undefined,
        refinement_instructions: refinementInstructions || undefined,
      };

      // Call the API
      const apiResult = await apiClient.refineKeywords(refinementData);
      setResult(apiResult);

      toast.success('Recommendation refined successfully!');

      // Call the callback if provided
      if (onRefine) {
        await onRefine({
          include_keywords: includeKeywords,
          exclude_keywords: excludeKeywords,
          refinement_instructions: refinementInstructions || undefined,
        });
      }

      if (onRefinementComplete) {
        onRefinementComplete(apiResult);
      }
    } catch (err: unknown) {
      const error = err as HttpError;
      const errorInfo = handleApiError(error);
      toast.error(
        errorInfo.message ||
          'Failed to refine recommendation. Please try again.'
      );
      console.error('Keyword refinement failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>Keyword Refinement</CardTitle>
          <CardDescription>
            Fine-tune your recommendation by specifying keywords to include or
            exclude
          </CardDescription>
        </CardHeader>
        <CardContent className='space-y-6'>
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

          {/* Additional Instructions */}
          <div className='space-y-3'>
            <Label htmlFor='refinement-instructions'>
              Additional Refinement Instructions
            </Label>
            <Textarea
              id='refinement-instructions'
              value={refinementInstructions}
              onChange={e => setRefinementInstructions(e.target.value)}
              placeholder='Enter any specific instructions for refining the recommendation...'
              rows={3}
            />
          </div>

          {/* Action Button */}
          <Button
            onClick={handleRefine}
            disabled={
              isLoading ||
              (includeKeywords.length === 0 && excludeKeywords.length === 0)
            }
            className='w-full'
          >
            {isLoading && <Loader2 className='w-4 h-4 mr-2 animate-spin' />}
            {isLoading ? 'Refining...' : 'Refine Recommendation'}
          </Button>
        </CardContent>
      </Card>

      {/* Result Display */}
      {result && (
        <Card>
          <CardHeader>
            <CardTitle>Refined Recommendation</CardTitle>
            <CardDescription>
              Original recommendation refined with your keyword preferences
            </CardDescription>
          </CardHeader>
          <CardContent className='space-y-4'>
            <div className='grid grid-cols-2 gap-4 text-sm'>
              <div>
                <strong>Confidence Score:</strong> {result.confidence_score}%
              </div>
              <div>
                <strong>Word Count:</strong> {result.word_count}
              </div>
            </div>

            {result.refinement_summary && (
              <div>
                <h4 className='font-medium mb-2'>Refinement Summary</h4>
                <p className='text-sm text-muted-foreground'>
                  {result.refinement_summary}
                </p>
              </div>
            )}

            {result.include_keywords_used &&
              result.include_keywords_used.length > 0 && (
                <div>
                  <h4 className='font-medium mb-2'>
                    Keywords Successfully Included
                  </h4>
                  <div className='flex flex-wrap gap-1'>
                    {result.include_keywords_used.map(
                      (keyword: string, index: number) => (
                        <Badge key={index} variant='secondary'>
                          {keyword}
                        </Badge>
                      )
                    )}
                  </div>
                </div>
              )}

            {result.exclude_keywords_avoided &&
              result.exclude_keywords_avoided.length > 0 && (
                <div>
                  <h4 className='font-medium mb-2'>
                    Keywords Successfully Avoided
                  </h4>
                  <div className='flex flex-wrap gap-1'>
                    {result.exclude_keywords_avoided.map(
                      (keyword: string, index: number) => (
                        <Badge key={index} variant='outline'>
                          {keyword}
                        </Badge>
                      )
                    )}
                  </div>
                </div>
              )}

            <div>
              <h4 className='font-medium mb-2'>Refined Content</h4>
              <div className='prose prose-sm max-w-none'>
                <pre className='whitespace-pre-wrap font-sans text-sm bg-muted p-4 rounded-md'>
                  {result.refined_content}
                </pre>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </>
  );
};
