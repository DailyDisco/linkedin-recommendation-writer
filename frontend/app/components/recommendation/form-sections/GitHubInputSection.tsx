import React from 'react';
import { AlertCircle } from 'lucide-react';
import { Input } from '@/components/ui/input';
import type { ParsedGitHubInput } from '../../../types/index';

interface GitHubInputSectionProps {
  githubInput: string;
  parsedGitHubInput: ParsedGitHubInput | null;
  errors: Record<string, string>;
  onChange: (field: string, value: string) => void;
  initialInputValue: string;
  mode: 'user' | 'repository';
}

export const GitHubInputSection: React.FC<GitHubInputSectionProps> = ({
  githubInput,
  parsedGitHubInput,
  errors,
  onChange,
  initialInputValue,
  mode,
}) => {
  return (
    <div>
      <label
        htmlFor='github-input'
        className='block text-sm font-medium text-gray-700 mb-2'
      >
        {initialInputValue
          ? `Analyzing ${mode === 'repository' ? 'Repository' : 'User Profile'} *`
          : 'GitHub Username or Repository URL *'}
      </label>
      <Input
        id='github-input'
        type='text'
        required
        readOnly={!!initialInputValue}
        className={`w-full ${
          initialInputValue ? 'bg-gray-50 text-gray-700 cursor-not-allowed' : ''
        } ${
          errors.github_input
            ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
            : 'border-gray-300'
        }`}
        placeholder={
          initialInputValue
            ? 'Auto-populated from your search'
            : 'e.g., johnsmith or https://github.com/johnsmith/myproject'
        }
        value={githubInput}
        onChange={e =>
          !initialInputValue && onChange('github_input', e.target.value)
        }
        aria-describedby={
          errors.github_input ? 'github-input-error' : undefined
        }
      />
      {initialInputValue && (
        <p className='mt-1 text-sm text-gray-600'>
          🔗 This field is auto-populated from your repository/user search.
          {mode === 'repository'
            ? ' The AI will focus only on contributions to this repository.'
            : ' The AI will analyze the full user profile.'}
        </p>
      )}
      {errors.github_input && (
        <div
          id='github-input-error'
          className='mt-1 flex items-center space-x-1 text-sm text-red-600'
        >
          <AlertCircle className='w-4 h-4 flex-shrink-0' />
          <p>{errors.github_input}</p>
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
  );
};
