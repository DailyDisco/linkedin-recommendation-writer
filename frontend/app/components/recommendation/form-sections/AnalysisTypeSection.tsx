import React from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { AlertCircle } from 'lucide-react';
import type { ParsedGitHubInput } from '../../../types/index';

interface AnalysisTypeSectionProps {
  parsedGitHubInput: ParsedGitHubInput | null;
  analysisType: 'profile' | 'repo_only';
  repositoryUrl: string;
  errors: Record<string, string>;
  onChange: (field: string, value: string) => void;
  onAnalysisTypeChange: (type: 'profile' | 'repo_only') => void;
}

export const AnalysisTypeSection: React.FC<AnalysisTypeSectionProps> = ({
  parsedGitHubInput,
  analysisType,
  repositoryUrl,
  errors,
  onChange,
  onAnalysisTypeChange,
}) => {
  if (!parsedGitHubInput || parsedGitHubInput.type !== 'username') {
    return null;
  }

  return (
    <>
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
              checked={analysisType === 'profile'}
              onChange={e =>
                onAnalysisTypeChange(e.target.value as 'profile' | 'repo_only')
              }
              className='mr-2'
            />
            <span className='text-sm'>
              <strong>Full Profile Analysis</strong> - Use all repositories and
              profile information
            </span>
          </label>
          <label className='flex items-center'>
            <input
              type='radio'
              name='analysis_type'
              value='repo_only'
              checked={analysisType === 'repo_only'}
              onChange={e =>
                onAnalysisTypeChange(e.target.value as 'profile' | 'repo_only')
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

      {analysisType === 'repo_only' && (
        <div>
          <Label
            htmlFor='repository-url'
            className='block text-sm font-medium text-gray-700 mb-2'
          >
            Repository URL *
          </Label>
          <Input
            id='repository-url'
            type='text'
            required
            className={`w-full ${
              errors.repository_url
                ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
                : 'border-gray-300'
            }`}
            placeholder='e.g., https://github.com/username/repository or username/repository'
            value={repositoryUrl}
            onChange={e => onChange('repository_url', e.target.value)}
          />
          <p className='text-xs text-gray-500 mt-1'>
            Enter the specific repository URL you want to focus on for the
            recommendation.
          </p>
          {errors.repository_url && (
            <div className='mt-1 flex items-center space-x-1 text-sm text-red-600'>
              <AlertCircle className='w-4 h-4 flex-shrink-0' />
              <p>{errors.repository_url}</p>
            </div>
          )}
        </div>
      )}
    </>
  );
};
