import React from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { AlertCircle } from 'lucide-react';
import { GitHubInputSection } from './form-sections/GitHubInputSection';
import { AnalysisTypeSection } from './form-sections/AnalysisTypeSection';
import { RecommendationSettingsSection } from './form-sections/RecommendationSettingsSection';

import { PromptAssistantChat } from '../PromptAssistantChat';
import type { ContributorInfo, ParsedGitHubInput } from '../../types/index';
import type { RecommendationFormData } from '../../hooks/useRecommendationState';

interface RecommendationFormNewProps {
  contributor: ContributorInfo;
  formData: RecommendationFormData;
  errors: Record<string, string>;
  parsedGitHubInput: ParsedGitHubInput | null;
  isGenerating: boolean;
  firstInputRef: React.RefObject<HTMLTextAreaElement | null>;
  onChange: (field: string, value: string) => void;
  onAnalysisTypeChange: (type: 'profile' | 'repo_only') => void;
  onSubmit: (e: React.FormEvent) => void;
  onCancel: () => void;
  initialInputValue: string;
  mode: 'user' | 'repository';
}

export const RecommendationFormNew: React.FC<RecommendationFormNewProps> = ({
  contributor,
  formData,
  errors,
  parsedGitHubInput,
  isGenerating,
  firstInputRef,
  onChange,
  onAnalysisTypeChange,
  onSubmit,
  onCancel,
  initialInputValue,
  mode,
}) => {
  return (
    <form onSubmit={onSubmit} className='space-y-6'>
      {/* GitHub Input Section */}
      <GitHubInputSection
        githubInput={formData.github_input}
        parsedGitHubInput={parsedGitHubInput}
        errors={errors}
        onChange={onChange}
        initialInputValue={initialInputValue}
        mode={mode}
      />

      {/* Analysis Type Selection */}
      <AnalysisTypeSection
        parsedGitHubInput={parsedGitHubInput}
        analysisType={formData.analysis_type}
        repositoryUrl={formData.repository_url || ''}
        errors={errors}
        onChange={onChange}
        onAnalysisTypeChange={onAnalysisTypeChange}
      />

      {/* Working Relationship */}
      <div>
        <Label
          htmlFor='working-relationship'
          className='block text-sm font-medium text-gray-700 mb-2'
        >
          How did you work together? *
        </Label>
        <Textarea
          id='working-relationship'
          ref={firstInputRef}
          required
          className={`w-full h-20 px-3 py-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 ${
            errors.workingRelationship
              ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
              : 'border-gray-300'
          }`}
          placeholder='e.g., We collaborated on the frontend development team for 8 months...'
          value={formData.workingRelationship}
          onChange={e => onChange('workingRelationship', e.target.value)}
          aria-describedby={
            errors.workingRelationship
              ? 'working-relationship-error'
              : undefined
          }
        />
        {errors.workingRelationship && (
          <div
            id='working-relationship-error'
            className='mt-1 flex items-center space-x-1 text-sm text-red-600'
          >
            <AlertCircle className='w-4 h-4 flex-shrink-0' />
            <p>{errors.workingRelationship}</p>
          </div>
        )}
        <p className='mt-1 text-sm text-gray-600'>
          Describe your professional connection, e.g., &ldquo;We collaborated on
          the frontend team for 8 months&rdquo; or &ldquo;I mentored them during
          their internship.&rdquo;
        </p>
      </div>

      {/* Specific Skills */}
      <div>
        <Label
          htmlFor='specific-skills'
          className='block text-sm font-medium text-gray-700 mb-2'
        >
          What specific skills did you observe?
        </Label>
        <Textarea
          id='specific-skills'
          className='w-full h-20 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500'
          placeholder='e.g., Excellent React skills, great at debugging, strong problem-solving...'
          value={formData.specificSkills}
          onChange={e => onChange('specificSkills', e.target.value)}
          rows={3}
        />
        <p className='mt-1 text-sm text-gray-600'>
          List technical skills you observed, e.g., &ldquo;React, Node.js, API
          design&rdquo; or &ldquo;Strong debugging skills, excellent code
          reviews.&rdquo;
        </p>
      </div>

      {/* Time Worked Together */}
      <div>
        <Label
          htmlFor='time-worked'
          className='block text-sm font-medium text-gray-700 mb-2'
        >
          How long did you work together?
        </Label>
        <Input
          id='time-worked'
          type='text'
          className='w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500'
          placeholder='e.g., 8 months, 2 years...'
          value={formData.timeWorkedTogether}
          onChange={e => onChange('timeWorkedTogether', e.target.value)}
        />
        <p className='mt-1 text-sm text-gray-600'>
          Specify the duration of your collaboration, e.g., &ldquo;6
          months&rdquo;, &ldquo;2 years&rdquo;, or &ldquo;January 2022 - June
          2023&rdquo;.
        </p>
      </div>

      {/* Notable Achievements */}
      <div>
        <Label
          htmlFor='achievements'
          className='block text-sm font-medium text-gray-700 mb-2'
        >
          Notable achievements or impact? (optional)
        </Label>
        <Textarea
          id='achievements'
          className='w-full h-20 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500'
          placeholder='e.g., Reduced load times by 40%, mentored junior developers...'
          value={formData.notableAchievements}
          onChange={e => onChange('notableAchievements', e.target.value)}
          rows={3}
        />
        <p className='mt-1 text-sm text-gray-600'>
          Highlight specific accomplishments or impact, e.g., &ldquo;Reduced app
          load time by 40%&rdquo; or &ldquo;Led the migration to microservices
          architecture.&rdquo;
        </p>
      </div>

      {/* Recommendation Settings */}
      <RecommendationSettingsSection
        recommendationType={formData.recommendation_type}
        tone={formData.tone}
        length={formData.length}
        forceRefresh={formData.force_refresh}
        onChange={onChange}
      />

      {/* Prompt Assistant Chat */}
      <PromptAssistantChat contributor={contributor} formData={formData} />

      {/* Action Buttons */}
      <div className='flex justify-end space-x-3'>
        <Button
          type='button'
          onClick={onCancel}
          className='px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors'
        >
          Cancel
        </Button>
        <Button
          type='submit'
          disabled={isGenerating || !formData.github_input.trim()}
          className='px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2'
        >
          {isGenerating && (
            <div className='w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin' />
          )}
          <span>Generate Recommendation</span>
        </Button>
      </div>
    </form>
  );
};
