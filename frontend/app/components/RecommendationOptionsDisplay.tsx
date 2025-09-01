import React from 'react';
import { CheckCircle, Eye, EyeOff, Loader2 } from 'lucide-react';
import type {
  ContributorInfo,
  ParsedGitHubInput,
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

interface ApiRecommendationOption {
  id: number;
  name: string;
  content: string;
  title: string;
  word_count: number;
  focus: string;
  explanation: string;
  generation_parameters?: Record<string, unknown>;
}

interface RecommendationOptionsDisplayProps {
  recommendationOptions: ApiRecommendationOption[];
  contributor: ContributorInfo;
  formData: FormData;
  parsedGitHubInput: ParsedGitHubInput | null;
  isCreatingFromOption: boolean;
  viewingFullContent: number | null;
  optionsRef: React.RefObject<HTMLDivElement | null>;
  onViewMore: (optionId: number) => void;
  onOptionSelect: (option: ApiRecommendationOption) => void;
  onEditDetails: () => void;
  onStartOver: () => void;
}

export default function RecommendationOptionsDisplay({
  recommendationOptions,
  contributor,
  formData,
  parsedGitHubInput,
  isCreatingFromOption,
  viewingFullContent,
  optionsRef,
  onViewMore,
  onOptionSelect,
  onEditDetails,
  onStartOver,
}: RecommendationOptionsDisplayProps) {
  return (
    <div ref={optionsRef} className='space-y-6'>
      {/* Header with navigation */}
      <div className='flex items-center justify-between'>
        <div className='flex items-center space-x-3'>
          <CheckCircle className='w-6 h-6 text-green-600' />
          <div>
            <h3 className='text-xl font-semibold text-gray-900'>
              Choose Your Recommendation
            </h3>
            <p className='text-sm text-gray-600'>
              for {contributor.full_name || contributor.username}
            </p>
          </div>
        </div>
        <div className='flex space-x-2'>
          <button
            onClick={onEditDetails}
            className='px-3 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors text-sm'
          >
            ← Edit Details
          </button>
          <button
            onClick={onStartOver}
            className='px-3 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors text-sm'
          >
            Start Over
          </button>
        </div>
      </div>

      {/* Generation summary */}
      <div className='bg-blue-50 border border-blue-200 rounded-lg p-4'>
        <div className='flex items-center space-x-2 mb-2'>
          <div className='w-2 h-2 bg-blue-600 rounded-full'></div>
          <span className='text-sm font-medium text-blue-900'>
            Generated based on your inputs
          </span>
        </div>
        <p className='text-sm text-blue-800'>
          {parsedGitHubInput?.type === 'repo_url'
            ? `Repository: ${parsedGitHubInput.username}/${parsedGitHubInput.repository}`
            : `GitHub Profile: ${parsedGitHubInput?.username || contributor.username}`}{' '}
          • {formData.recommendation_type} • {formData.tone} tone •{' '}
          {formData.length}
        </p>
      </div>

      <p className='text-gray-600'>
        Here are 3 different recommendation options based on the GitHub
        analysis. Each option has a different focus area. Choose the one that
        best fits your needs.
      </p>

      <div className='space-y-4'>
        {recommendationOptions.map(option => (
          <div
            key={option.id}
            className='border-2 border-gray-200 rounded-lg p-6 hover:border-blue-300 hover:shadow-md transition-all duration-200'
          >
            <div className='flex items-start justify-between mb-4'>
              <div className='flex-1'>
                <h4 className='text-lg font-semibold text-gray-900 mb-1'>
                  {option.name}
                </h4>
                <div className='flex items-center space-x-4 text-sm text-gray-600'>
                  <span className='flex items-center space-x-1'>
                    <span className='font-medium'>Focus:</span>
                    <span className='capitalize'>
                      {option.focus.replace('_', ' ')}
                    </span>
                  </span>
                  <span className='flex items-center space-x-1'>
                    <span className='font-medium'>Words:</span>
                    <span>{option.word_count}</span>
                  </span>
                </div>
              </div>
            </div>

            <div className='bg-gray-50 p-4 rounded-md mb-4 border-l-4 border-blue-200'>
              <p className='text-gray-900 leading-relaxed'>
                {viewingFullContent === option.id
                  ? option.content
                  : option.content.length > 400
                    ? option.content.substring(0, 400) + '...'
                    : option.content}
              </p>
            </div>

            <div className='flex space-x-3'>
              <button
                onClick={() => onViewMore(option.id)}
                className='flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors text-sm flex items-center justify-center space-x-2'
              >
                {viewingFullContent === option.id ? (
                  <>
                    <EyeOff className='w-4 h-4' />
                    <span>Show Less</span>
                  </>
                ) : (
                  <>
                    <Eye className='w-4 h-4' />
                    <span>Read Full</span>
                  </>
                )}
              </button>
              <button
                onClick={() => onOptionSelect(option)}
                disabled={isCreatingFromOption}
                className='flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm flex items-center justify-center space-x-2 font-medium'
              >
                {isCreatingFromOption ? (
                  <>
                    <Loader2 className='w-4 h-4 animate-spin' />
                    <span>Creating...</span>
                  </>
                ) : (
                  <>
                    <CheckCircle className='w-4 h-4' />
                    <span>Select This</span>
                  </>
                )}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
