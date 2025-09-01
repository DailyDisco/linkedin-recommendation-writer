import React from 'react';
import { CheckCircle, Loader2, FileText } from 'lucide-react';
import { toast } from 'sonner';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { KeywordRefinement } from './KeywordRefinement';
import type {
  ContributorInfo,
  RecommendationOption,
  KeywordRefinementResult,
} from '../types/index';

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
}

interface ApiRecommendation {
  id: number;
  title: string;
  content: string;
  recommendation_type: string;
  tone: string;
  length: string;
  word_count: number;
  created_at: string;
  github_username: string;
  ai_model?: string;
  updated_at?: string;
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
  setGeneratedRecommendation: (rec: ApiRecommendation | null) => void;
  isRegenerating: boolean;
  onBackToOptions: () => void;
  onGenerateAnother: () => void;
  onRefine: (instructions: string) => void;
  onClose: () => void;
}

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
  setGeneratedRecommendation,
  isRegenerating,
  onBackToOptions,
  onGenerateAnother,
  onRefine,
  onClose,
}: RecommendationResultDisplayProps) {
  return (
    <div ref={resultRef} className='space-y-6'>
      <Tabs
        value={activeTab}
        onValueChange={value => setActiveTab(value as 'preview' | 'refine')}
      >
        <TabsList className='grid w-full grid-cols-2 h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground'>
          <TabsTrigger
            value='preview'
            className='inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm'
          >
            Preview
          </TabsTrigger>
          <TabsTrigger
            value='refine'
            className='inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm'
          >
            Refine
          </TabsTrigger>
        </TabsList>

        <TabsContent value='preview' className='mt-4'>
          <div className='flex items-center justify-between'>
            <div className='flex items-center space-x-3'>
              <CheckCircle className='w-6 h-6 text-green-600' />
              <div>
                <h3 className='text-xl font-semibold text-gray-900'>
                  Recommendation Ready
                </h3>
                <p className='text-sm text-gray-600'>
                  for {contributor.full_name || contributor.username}
                </p>
              </div>
            </div>
            <div className='flex space-x-2'>
              <button
                onClick={onBackToOptions}
                className='px-3 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors text-sm'
              >
                ← Back to Options
              </button>
              <button
                onClick={onGenerateAnother}
                className='px-3 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors text-sm'
              >
                Generate Another
              </button>
            </div>
          </div>

          <div className='bg-gray-50 p-6 rounded-lg mt-4'>
            <div className='mb-4 flex items-center justify-between text-sm text-gray-600'>
              <div className='flex items-center space-x-4'>
                <span>
                  Type:{' '}
                  {generatedRecommendation?.recommendation_type ||
                    formData.recommendation_type}
                </span>
                <span>
                  Tone: {generatedRecommendation?.tone || formData.tone}
                </span>
                <span>
                  Length: {generatedRecommendation?.length || formData.length}
                </span>
              </div>
              <span>
                {generatedRecommendation?.word_count ||
                  selectedOption?.word_count}{' '}
                words
              </span>
            </div>
            <div className='prose max-w-none'>
              <p className='text-gray-900 leading-relaxed whitespace-pre-wrap'>
                {generatedRecommendation?.content || selectedOption?.content}
              </p>
            </div>
          </div>

          {/* Regeneration Section */}
          <div className='bg-blue-50 p-4 rounded-lg mt-4'>
            <h4 className='font-medium text-gray-900 mb-2'>
              Want to refine this recommendation?
            </h4>
            <p className='text-sm text-gray-600 mb-3'>
              Provide specific instructions for how you&apos;d like the
              recommendation modified.
            </p>
            <textarea
              className='w-full h-20 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 mb-3'
              placeholder='e.g., Make it more specific about their React skills, focus less on teamwork, emphasize their problem-solving abilities...'
              value={regenerateInstructions}
              onChange={e => setRegenerateInstructions(e.target.value)}
            />
            <button
              onClick={() => onRefine(regenerateInstructions)}
              disabled={!regenerateInstructions.trim() || isRegenerating}
              className='px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2'
            >
              {isRegenerating ? (
                <Loader2 className='w-4 h-4 animate-spin' />
              ) : (
                <FileText className='w-4 h-4' />
              )}
              <span>
                {isRegenerating ? 'Refining...' : 'Refine Recommendation'}
              </span>
            </button>
          </div>

          <div className='flex justify-end space-x-3 mt-4'>
            <button
              onClick={onClose}
              className='px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors'
            >
              Done
            </button>
          </div>
        </TabsContent>

        <TabsContent value='refine' className='mt-4'>
          <KeywordRefinement
            recommendationId={generatedRecommendation?.id || 0}
            onRefinementComplete={(refinedContent: KeywordRefinementResult) => {
              setGeneratedRecommendation(prev =>
                prev
                  ? {
                      ...prev,
                      content: refinedContent.refined_content,
                    }
                  : null
              );
              toast.success('Recommendation refined successfully');
            }}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
