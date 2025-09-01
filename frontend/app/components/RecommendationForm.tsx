import React from 'react';
import { FileText, AlertCircle } from 'lucide-react';
import type { ContributorInfo, ParsedGitHubInput } from '../types/index';

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

interface RecommendationFormProps {
  contributor: ContributorInfo;
  formData: FormData;
  setFormData: (data: FormData) => void;
  validationErrors: Record<string, string>;
  setValidationErrors: (errors: Record<string, string>) => void;
  parsedGitHubInput: ParsedGitHubInput | null;
  isGenerating: boolean;
  firstInputRef: React.RefObject<HTMLTextAreaElement | null>;
  onSubmit: (e: React.FormEvent) => void;
  onCancel: () => void;
}

export default function RecommendationForm({
  contributor: _contributor,
  formData,
  setFormData,
  validationErrors,
  setValidationErrors,
  parsedGitHubInput,
  isGenerating,
  firstInputRef,
  onSubmit,
  onCancel,
}: RecommendationFormProps) {
  return (
    <form onSubmit={onSubmit} className='space-y-6'>
      {/* GitHub Input Section */}
      <div>
        <label
          htmlFor='github-input'
          className='block text-sm font-medium text-gray-700 mb-2'
        >
          GitHub Username or Repository URL *
        </label>
        <input
          id='github-input'
          type='text'
          required
          className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 ${
            validationErrors.github_input
              ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
              : 'border-gray-300'
          }`}
          placeholder='e.g., johnsmith or https://github.com/johnsmith/myproject'
          value={formData.github_input}
          onChange={e => {
            setFormData({
              ...formData,
              github_input: e.target.value,
            });
            if (validationErrors.github_input) {
              setValidationErrors({
                ...validationErrors,
                github_input: '',
              });
            }
          }}
          aria-describedby={
            validationErrors.github_input ? 'github-input-error' : undefined
          }
        />
        {validationErrors.github_input && (
          <div
            id='github-input-error'
            className='mt-1 flex items-center space-x-1 text-sm text-red-600'
          >
            <AlertCircle className='w-4 h-4 flex-shrink-0' />
            <p>{validationErrors.github_input}</p>
          </div>
        )}
        {parsedGitHubInput && (
          <div className='mt-2 p-2 bg-gray-50 rounded-md'>
            <p className='text-sm text-gray-600'>
              {parsedGitHubInput.type === 'repo_url' ? (
                <>
                  📁 Repository:{' '}
                  <strong>
                    {parsedGitHubInput.username}/{parsedGitHubInput.repository}
                  </strong>
                </>
              ) : (
                <>
                  👤 User: <strong>{parsedGitHubInput.username}</strong>
                </>
              )}
            </p>
          </div>
        )}
      </div>

      {/* Analysis Type Selection */}
      {parsedGitHubInput && parsedGitHubInput.type === 'username' && (
        <div>
          <label className='block text-sm font-medium text-gray-700 mb-2'>
            Analysis Type
          </label>
          <div className='space-y-2'>
            <label className='flex items-center'>
              <input
                type='radio'
                name='analysis_type'
                value='profile'
                checked={formData.analysis_type === 'profile'}
                onChange={e =>
                  setFormData({
                    ...formData,
                    analysis_type: e.target.value as 'profile' | 'repo_only',
                  })
                }
                className='mr-2'
              />
              <span className='text-sm'>
                <strong>Full Profile Analysis</strong> - Use all repositories
                and profile information
              </span>
            </label>
            <label className='flex items-center'>
              <input
                type='radio'
                name='analysis_type'
                value='repo_only'
                checked={formData.analysis_type === 'repo_only'}
                onChange={e =>
                  setFormData({
                    ...formData,
                    analysis_type: e.target.value as 'profile' | 'repo_only',
                  })
                }
                className='mr-2'
              />
              <span className='text-sm text-gray-600'>
                <strong>Repository Only</strong> - Focus on specific repository
                (you&apos;ll be asked to provide one)
              </span>
            </label>
          </div>
        </div>
      )}

      {/* Repository Selection for repo_only mode */}
      {formData.analysis_type === 'repo_only' &&
        parsedGitHubInput &&
        parsedGitHubInput.type === 'username' && (
          <div>
            <label
              htmlFor='repository-url'
              className='block text-sm font-medium text-gray-700 mb-2'
            >
              Repository URL *
            </label>
            <input
              id='repository-url'
              type='text'
              required
              className='w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500'
              placeholder='e.g., https://github.com/username/repository or username/repository'
              value={formData.repository_url || ''}
              onChange={e =>
                setFormData({
                  ...formData,
                  repository_url: e.target.value,
                })
              }
            />
            <p className='text-xs text-gray-500 mt-1'>
              Enter the specific repository URL you want to focus on for the
              recommendation.
            </p>
            {validationErrors.repository_url && (
              <div className='mt-1 flex items-center space-x-1 text-sm text-red-600'>
                <AlertCircle className='w-4 h-4 flex-shrink-0' />
                <p>{validationErrors.repository_url}</p>
              </div>
            )}
          </div>
        )}

      <div>
        <label
          htmlFor='working-relationship'
          className='block text-sm font-medium text-gray-700 mb-2'
        >
          How did you work together? *
        </label>
        <textarea
          id='working-relationship'
          ref={firstInputRef}
          required
          className={`w-full h-20 px-3 py-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 ${
            validationErrors.workingRelationship
              ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
              : 'border-gray-300'
          }`}
          placeholder='e.g., We collaborated on the frontend development team for 8 months...'
          value={formData.workingRelationship}
          onChange={e => {
            setFormData({
              ...formData,
              workingRelationship: e.target.value,
            });
            if (validationErrors.workingRelationship) {
              setValidationErrors({
                ...validationErrors,
                workingRelationship: '',
              });
            }
          }}
          aria-describedby={
            validationErrors.workingRelationship
              ? 'working-relationship-error'
              : undefined
          }
        />
        {validationErrors.workingRelationship && (
          <div
            id='working-relationship-error'
            className='mt-1 flex items-center space-x-1 text-sm text-red-600'
          >
            <AlertCircle className='w-4 h-4 flex-shrink-0' />
            <p>{validationErrors.workingRelationship}</p>
          </div>
        )}
      </div>

      <div>
        <label
          htmlFor='specific-skills'
          className='block text-sm font-medium text-gray-700 mb-2'
        >
          What specific skills did you observe?
        </label>
        <textarea
          id='specific-skills'
          className='w-full h-20 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500'
          placeholder='e.g., Excellent React skills, great at debugging, strong problem-solving...'
          value={formData.specificSkills}
          onChange={e =>
            setFormData({
              ...formData,
              specificSkills: e.target.value,
            })
          }
        />
      </div>

      <div>
        <label
          htmlFor='time-worked'
          className='block text-sm font-medium text-gray-700 mb-2'
        >
          How long did you work together?
        </label>
        <input
          id='time-worked'
          type='text'
          className='w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500'
          placeholder='e.g., 8 months, 2 years...'
          value={formData.timeWorkedTogether}
          onChange={e =>
            setFormData({
              ...formData,
              timeWorkedTogether: e.target.value,
            })
          }
        />
      </div>

      <div>
        <label
          htmlFor='achievements'
          className='block text-sm font-medium text-gray-700 mb-2'
        >
          Notable achievements or impact? (optional)
        </label>
        <textarea
          id='achievements'
          className='w-full h-20 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500'
          placeholder='e.g., Reduced load times by 40%, mentored junior developers...'
          value={formData.notableAchievements}
          onChange={e =>
            setFormData({
              ...formData,
              notableAchievements: e.target.value,
            })
          }
        />
      </div>

      {/* Recommendation Settings */}
      <div className='bg-gray-50 p-4 rounded-lg space-y-4'>
        <h3 className='font-medium text-gray-900'>Recommendation Settings</h3>

        <div className='grid grid-cols-1 md:grid-cols-3 gap-4'>
          <div>
            <label
              htmlFor='rec-type'
              className='block text-sm font-medium text-gray-700 mb-1'
            >
              Type
            </label>
            <p className='text-xs text-gray-500 mb-2'>
              Focus area of the recommendation
            </p>
            <select
              id='rec-type'
              className='w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500'
              value={formData.recommendation_type}
              onChange={e =>
                setFormData({
                  ...formData,
                  recommendation_type: e.target.value as
                    | 'professional'
                    | 'technical'
                    | 'leadership'
                    | 'academic'
                    | 'personal',
                })
              }
            >
              <option value='professional'>Professional</option>
              <option value='technical'>Technical</option>
              <option value='leadership'>Leadership</option>
              <option value='academic'>Academic</option>
              <option value='personal'>Personal</option>
            </select>
          </div>

          <div>
            <label
              htmlFor='rec-tone'
              className='block text-sm font-medium text-gray-700 mb-1'
            >
              Tone
            </label>
            <p className='text-xs text-gray-500 mb-2'>
              Writing style and voice
            </p>
            <select
              id='rec-tone'
              className='w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500'
              value={formData.tone}
              onChange={e =>
                setFormData({
                  ...formData,
                  tone: e.target.value as
                    | 'professional'
                    | 'friendly'
                    | 'formal'
                    | 'casual',
                })
              }
            >
              <option value='professional'>Professional</option>
              <option value='friendly'>Friendly</option>
              <option value='formal'>Formal</option>
              <option value='casual'>Casual</option>
            </select>
          </div>

          <div>
            <label
              htmlFor='rec-length'
              className='block text-sm font-medium text-gray-700 mb-1'
            >
              Length
            </label>
            <p className='text-xs text-gray-500 mb-2'>
              Word count of the recommendation
            </p>
            <select
              id='rec-length'
              className='w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500'
              value={formData.length}
              onChange={e =>
                setFormData({
                  ...formData,
                  length: e.target.value as 'short' | 'medium' | 'long',
                })
              }
            >
              <option value='short'>Short</option>
              <option value='medium'>Medium</option>
              <option value='long'>Long</option>
            </select>
          </div>
        </div>
      </div>

      <div className='flex justify-end space-x-3'>
        <button
          type='button'
          onClick={onCancel}
          className='px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors'
        >
          Cancel
        </button>
        <button
          type='submit'
          disabled={isGenerating}
          className='px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2'
        >
          <FileText className='w-4 h-4' />
          <span>Generate Recommendation</span>
        </button>
      </div>
    </form>
  );
}
