import React, { memo } from 'react';
import { CheckCircle } from 'lucide-react';
import { RecommendationOptionsCard } from './RecommendationOptionsCard';
import type {
  RecommendationOption,
  ContributorInfo,
  ParsedGitHubInput,
  RecommendationFormData,
} from '../../types/index';

interface RecommendationOptionsListProps {
  options: RecommendationOption[];
  contributor: ContributorInfo;
  formData: RecommendationFormData;
  parsedGitHubInput: ParsedGitHubInput | null;
  isCreatingFromOption: boolean;
  viewingFullContent: number | null;
  onViewMore: (optionId: number) => void;
  onOptionSelect: (option: RecommendationOption) => void;
  onEditDetails: () => void;
  onStartOver: () => void;
}

const RecommendationOptionsList: React.FC<RecommendationOptionsListProps> =
  memo(
    ({
      options,
      contributor,
      formData,
      parsedGitHubInput,
      isCreatingFromOption,
      viewingFullContent,
      onViewMore,
      onOptionSelect,
      onEditDetails,
      onStartOver,
    }) => {
      return (
        <div className='space-y-6'>
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
            Here are 2 different recommendation options based on the GitHub
            analysis. Each option has a different focus area. Choose the one
            that best fits your needs.
          </p>

          <div className='space-y-4'>
            {options.map(option => (
              <RecommendationOptionsCard
                key={option.id}
                option={option}
                isViewingFull={viewingFullContent === option.id}
                onViewMore={() => onViewMore(option.id)}
                onSelect={() => onOptionSelect(option)}
                isCreating={isCreatingFromOption}
              />
            ))}
          </div>
        </div>
      );
    }
  );

RecommendationOptionsList.displayName = 'RecommendationOptionsList';

export default RecommendationOptionsList;
