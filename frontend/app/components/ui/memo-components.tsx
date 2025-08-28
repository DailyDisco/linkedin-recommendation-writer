import { memo } from 'react';
import type { ContributorInfo } from '../../types';

interface ContributorCardProps {
  contributor: ContributorInfo;
  onWriteRecommendation: (contributor: ContributorInfo) => void;
  mode: 'user' | 'repository';
}

export const ContributorCard = memo(
  ({ contributor, onWriteRecommendation, mode }: ContributorCardProps) => {
    return (
      <div className='flex items-center space-x-3 p-3 bg-gray-50 rounded-lg'>
        <img
          src={contributor.avatar_url}
          alt={contributor.username}
          className='w-10 h-10 rounded-full'
          loading='lazy'
        />
        <div className='flex-1'>
          <div className='flex items-center space-x-2'>
            <span className='font-semibold text-gray-900'>
              {contributor.full_name || contributor.username}
            </span>
            {contributor.first_name && contributor.last_name && (
              <span className='text-sm text-blue-600 bg-blue-100 px-2 py-1 rounded'>
                {contributor.first_name} {contributor.last_name}
              </span>
            )}
          </div>
          <div className='text-sm text-gray-600'>
            @{contributor.username}
            {mode === 'repository' && (
              <span className='ml-2'>
                • {contributor.contributions} contributions
              </span>
            )}
          </div>
          {contributor.company && (
            <div className='text-xs text-gray-500'>{contributor.company}</div>
          )}
        </div>
        <div className='flex items-center space-x-2'>
          <button
            onClick={() => onWriteRecommendation(contributor)}
            className='inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-green-600 text-white shadow hover:bg-green-700 active:bg-green-800 h-8 px-3 space-x-1'
            aria-label={`Write recommendation for ${contributor.full_name || contributor.username}`}
          >
            <svg
              className='w-3 h-3'
              fill='none'
              stroke='currentColor'
              viewBox='0 0 24 24'
            >
              <path
                strokeLinecap='round'
                strokeLinejoin='round'
                strokeWidth={2}
                d='M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z'
              />
            </svg>
            <span className='hidden sm:inline'>Write Rec</span>
          </button>
          <a
            href={contributor.profile_url}
            target='_blank'
            rel='noopener noreferrer'
            className='text-blue-600 hover:text-blue-700'
            title='View GitHub Profile'
          >
            <svg className='w-4 h-4' fill='currentColor' viewBox='0 0 24 24'>
              <path d='M12 0C5.374 0 0 5.373 0 12 0 17.302 3.438 21.8 8.207 23.387c.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z' />
            </svg>
          </a>
        </div>
      </div>
    );
  },
  (prevProps, nextProps) => {
    // Custom comparison for optimization
    return (
      prevProps.contributor.username === nextProps.contributor.username &&
      prevProps.mode === nextProps.mode
    );
  }
);

ContributorCard.displayName = 'ContributorCard';
