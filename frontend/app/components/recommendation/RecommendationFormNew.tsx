import React, { useEffect, useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandItem,
} from '@/components/ui/command';
import {
  Popover,
  PopoverContent,
} from '@/components/ui/popover';
import { AlertCircle, Loader2, Lightbulb } from 'lucide-react';
import { GitHubInputSection } from './form-sections/GitHubInputSection';
import { AnalysisTypeSection } from './form-sections/AnalysisTypeSection';
import { RecommendationSettingsSection } from './form-sections/RecommendationSettingsSection';
import { PromptAssistantChat } from '../PromptAssistantChat';
import { apiClient } from '@/services/api';
import type {
  ContributorInfo,
  ParsedGitHubInput,
  PromptSuggestionsResponse,
} from '../../types/index';
import type { RecommendationFormData } from '../../hooks/useRecommendationState';

// Custom debounce hook
function useDebounce(value: string, delay: number): string {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

interface RecommendationFormNewProps {
  contributor: ContributorInfo;
  formData: RecommendationFormData;
  errors: Record<string, string>;
  parsedGitHubInput: ParsedGitHubInput | null;
  isGenerating: boolean;
  firstInputRef: React.RefObject<HTMLTextAreaElement | null>;
  initialSuggestions: PromptSuggestionsResponse | null;
  isLoadingSuggestions: boolean;
  onChange: (field: string, value: string) => void;
  onAnalysisTypeChange: (type: 'profile' | 'repo_only') => void;
  onFetchSuggestions: (
    githubUsername: string,
    recommendationType: string,
    tone: string,
    length: string
  ) => void;
  onSubmit: (e: React.FormEvent) => void;
  onCancel: () => void;
}

export const RecommendationFormNew: React.FC<RecommendationFormNewProps> = ({
  contributor,
  formData,
  errors,
  parsedGitHubInput,
  isGenerating,
  firstInputRef,
  initialSuggestions,
  isLoadingSuggestions,
  onChange,
  onAnalysisTypeChange,
  onFetchSuggestions,
  onSubmit,
  onCancel,
}) => {
  // Local state for autocomplete
  const [autocompleteOpen, setAutocompleteOpen] = useState<
    Record<string, boolean>
  >({});
  const [autocompleteLoading, setAutocompleteLoading] = useState<
    Record<string, boolean>
  >({});
  const [autocompleteSuggestions, setAutocompleteSuggestions] = useState<
    Record<string, string[]>
  >({});

  // Debounced values for autocomplete
  const debouncedSkills = useDebounce(formData.specificSkills, 500);
  const debouncedAchievements = useDebounce(formData.notableAchievements, 500);

  // Fetch suggestions when key form fields change
  useEffect(() => {
    if (
      contributor.username &&
      formData.recommendation_type &&
      formData.tone &&
      formData.length
    ) {
      onFetchSuggestions(
        contributor.username,
        formData.recommendation_type,
        formData.tone,
        formData.length
      );
    }
  }, [
    contributor.username,
    formData.recommendation_type,
    formData.tone,
    formData.length,
    onFetchSuggestions,
  ]);

  // Fetch autocomplete suggestions
  const fetchAutocompleteSuggestions = useCallback(
    async (
      fieldName: 'specific_skills' | 'notable_achievements',
      currentInput: string
    ) => {
      if (!currentInput.trim() || !contributor.username) return;

      setAutocompleteLoading(prev => ({ ...prev, [fieldName]: true }));

      try {
        const suggestions = await apiClient.getAutocompleteSuggestions({
          github_username: contributor.username,
          field_name: fieldName,
          current_input: currentInput,
        });
        setAutocompleteSuggestions(prev => ({
          ...prev,
          [fieldName]: suggestions,
        }));
      } catch (error) {
        console.error('Error fetching autocomplete suggestions:', error);
        setAutocompleteSuggestions(prev => ({ ...prev, [fieldName]: [] }));
      } finally {
        setAutocompleteLoading(prev => ({ ...prev, [fieldName]: false }));
      }
    },
    [contributor.username]
  );

  // Effect for skills autocomplete
  useEffect(() => {
    if (debouncedSkills) {
      fetchAutocompleteSuggestions('specific_skills', debouncedSkills);
    }
  }, [debouncedSkills, fetchAutocompleteSuggestions]);

  // Effect for achievements autocomplete
  useEffect(() => {
    if (debouncedAchievements) {
      fetchAutocompleteSuggestions(
        'notable_achievements',
        debouncedAchievements
      );
    }
  }, [debouncedAchievements, fetchAutocompleteSuggestions]);

  // Helper function to apply a suggestion to a form field
  const applySuggestion = (fieldName: string, suggestion: string) => {
    const currentValue = formData[
      fieldName as keyof RecommendationFormData
    ] as string;
    const newValue = currentValue
      ? `${currentValue}\n\n${suggestion}`
      : suggestion;
    onChange(fieldName, newValue);
    setAutocompleteOpen(prev => ({ ...prev, [fieldName]: false }));
  };

  // Helper function to apply autocomplete suggestion
  const applyAutocompleteSuggestion = (
    fieldName: string,
    suggestion: string
  ) => {
    const currentValue = formData[
      fieldName as keyof RecommendationFormData
    ] as string;
    const newValue = currentValue
      ? `${currentValue}, ${suggestion}`
      : suggestion;
    onChange(fieldName, newValue);
    setAutocompleteOpen(prev => ({ ...prev, [fieldName]: false }));
  };
  return (
    <form onSubmit={onSubmit} className='space-y-6'>
      {/* GitHub Input Section */}
      <GitHubInputSection
        githubInput={formData.github_input}
        parsedGitHubInput={parsedGitHubInput}
        errors={errors}
        onChange={onChange}
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
          Describe your professional connection, e.g., &ldquo;We collaborated on the
          frontend team for 8 months&rdquo; or &ldquo;I mentored them during their
          internship.&rdquo;
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
        <div className='relative'>
          <Textarea
            id='specific-skills'
            className='w-full h-20 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500'
            placeholder='e.g., Excellent React skills, great at debugging, strong problem-solving...'
            value={formData.specificSkills}
            onChange={e => onChange('specificSkills', e.target.value)}
            onFocus={() => {
              if (autocompleteSuggestions.specific_skills?.length > 0) {
                setAutocompleteOpen(prev => ({
                  ...prev,
                  specific_skills: true,
                }));
              }
            }}
          />
          {autocompleteLoading.specific_skills && (
            <div className='absolute right-2 top-2'>
              <Loader2 className='w-4 h-4 animate-spin text-gray-400' />
            </div>
          )}
          <Popover
            open={autocompleteOpen.specific_skills}
            onOpenChange={open =>
              setAutocompleteOpen(prev => ({ ...prev, specific_skills: open }))
            }
          >
            <PopoverContent className='w-full p-0' align='start'>
              <Command>
                <CommandEmpty>No suggestions found.</CommandEmpty>
                <CommandGroup>
                  {autocompleteSuggestions.specific_skills?.map(
                    (suggestion, index) => (
                      <CommandItem
                        key={index}
                        onSelect={() =>
                          applyAutocompleteSuggestion(
                            'specificSkills',
                            suggestion
                          )
                        }
                        className='cursor-pointer'
                      >
                        {suggestion}
                      </CommandItem>
                    )
                  )}
                </CommandGroup>
              </Command>
            </PopoverContent>
          </Popover>
        </div>
        <p className='mt-1 text-sm text-gray-600'>
          List technical skills you observed, e.g., &ldquo;React, Node.js, API design&rdquo;
          or &ldquo;Strong debugging skills, excellent code reviews.&rdquo;
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
          Specify the duration of your collaboration, e.g., &ldquo;6 months&rdquo;, &ldquo;2
          years&rdquo;, or &ldquo;January 2022 - June 2023&rdquo;.
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
        <div className='relative'>
          <Textarea
            id='achievements'
            className='w-full h-20 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500'
            placeholder='e.g., Reduced load times by 40%, mentored junior developers...'
            value={formData.notableAchievements}
            onChange={e => onChange('notableAchievements', e.target.value)}
            onFocus={() => {
              if (autocompleteSuggestions.notable_achievements?.length > 0) {
                setAutocompleteOpen(prev => ({
                  ...prev,
                  notable_achievements: true,
                }));
              }
            }}
          />
          {autocompleteLoading.notable_achievements && (
            <div className='absolute right-2 top-2'>
              <Loader2 className='w-4 h-4 animate-spin text-gray-400' />
            </div>
          )}
          <Popover
            open={autocompleteOpen.notable_achievements}
            onOpenChange={open =>
              setAutocompleteOpen(prev => ({
                ...prev,
                notable_achievements: open,
              }))
            }
          >
            <PopoverContent className='w-full p-0' align='start'>
              <Command>
                <CommandEmpty>No suggestions found.</CommandEmpty>
                <CommandGroup>
                  {autocompleteSuggestions.notable_achievements?.map(
                    (suggestion, index) => (
                      <CommandItem
                        key={index}
                        onSelect={() =>
                          applyAutocompleteSuggestion(
                            'notableAchievements',
                            suggestion
                          )
                        }
                        className='cursor-pointer'
                      >
                        {suggestion}
                      </CommandItem>
                    )
                  )}
                </CommandGroup>
              </Command>
            </PopoverContent>
          </Popover>
        </div>
        <p className='mt-1 text-sm text-gray-600'>
          Highlight specific accomplishments or impact, e.g., &ldquo;Reduced app load
          time by 40%&rdquo; or &ldquo;Led the migration to microservices architecture.&rdquo;
        </p>
      </div>

      {/* Recommendation Settings */}
      <RecommendationSettingsSection
        recommendationType={formData.recommendation_type}
        tone={formData.tone}
        length={formData.length}
        onChange={onChange}
      />

      {/* AI-Powered Suggestions */}
      {(isLoadingSuggestions || initialSuggestions) && (
        <div className='bg-blue-50 border border-blue-200 rounded-lg p-4'>
          <div className='flex items-center space-x-2 mb-3'>
            <Lightbulb className='w-5 h-5 text-blue-600' />
            <h3 className='text-lg font-medium text-blue-900'>
              AI Writing Assistant
            </h3>
            {isLoadingSuggestions && (
              <Loader2 className='w-4 h-4 animate-spin text-blue-600' />
            )}
          </div>

          {isLoadingSuggestions ? (
            <p className='text-blue-700 text-sm'>
              Generating personalized suggestions based on{' '}
              {contributor.username}&rsquo;s GitHub profile...
            </p>
          ) : initialSuggestions ? (
            <div className='space-y-4'>
              <p className='text-blue-700 text-sm mb-3'>
                Click on any suggestion below to add it to the corresponding
                field:
              </p>

              {/* Working Relationship Suggestions */}
              {initialSuggestions.suggested_working_relationship.length > 0 && (
                <div>
                  <Label className='text-sm font-medium text-blue-800 mb-2 block'>
                    Working Relationship Examples:
                  </Label>
                  <div className='flex flex-wrap gap-2'>
                    {initialSuggestions.suggested_working_relationship.map(
                      (suggestion, index) => (
                        <Badge
                          key={index}
                          variant='outline'
                          className='cursor-pointer hover:bg-blue-100 text-xs px-2 py-1'
                          onClick={() =>
                            applySuggestion('workingRelationship', suggestion)
                          }
                        >
                          {suggestion.length > 30
                            ? `${suggestion.substring(0, 30)}...`
                            : suggestion}
                        </Badge>
                      )
                    )}
                  </div>
                </div>
              )}

              {/* Skills Suggestions */}
              {initialSuggestions.suggested_specific_skills.length > 0 && (
                <div>
                  <Label className='text-sm font-medium text-blue-800 mb-2 block'>
                    Skills Examples:
                  </Label>
                  <div className='flex flex-wrap gap-2'>
                    {initialSuggestions.suggested_specific_skills.map(
                      (suggestion, index) => (
                        <Badge
                          key={index}
                          variant='outline'
                          className='cursor-pointer hover:bg-blue-100 text-xs px-2 py-1'
                          onClick={() =>
                            applySuggestion('specificSkills', suggestion)
                          }
                        >
                          {suggestion.length > 25
                            ? `${suggestion.substring(0, 25)}...`
                            : suggestion}
                        </Badge>
                      )
                    )}
                  </div>
                </div>
              )}

              {/* Achievements Suggestions */}
              {initialSuggestions.suggested_notable_achievements.length > 0 && (
                <div>
                  <Label className='text-sm font-medium text-blue-800 mb-2 block'>
                    Achievements Examples:
                  </Label>
                  <div className='flex flex-wrap gap-2'>
                    {initialSuggestions.suggested_notable_achievements.map(
                      (suggestion, index) => (
                        <Badge
                          key={index}
                          variant='outline'
                          className='cursor-pointer hover:bg-blue-100 text-xs px-2 py-1'
                          onClick={() =>
                            applySuggestion('notableAchievements', suggestion)
                          }
                        >
                          {suggestion.length > 30
                            ? `${suggestion.substring(0, 30)}...`
                            : suggestion}
                        </Badge>
                      )
                    )}
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </div>
      )}

      {/* Prompt Assistant Chat */}
      <PromptAssistantChat
        contributor={contributor}
        formData={formData}
        onApplyFormUpdates={updates => {
          Object.entries(updates).forEach(([field, value]) => {
            if (value && typeof value === 'string') {
              onChange(field, value);
            }
          });
        }}
      />

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
