import { X } from 'lucide-react';
import type { ContributorInfo } from '../types/index';

interface RecommendationModalHeaderProps {
  contributor: ContributorInfo;
  onClose: () => void;
}

export default function RecommendationModalHeader({
  contributor,
  onClose,
}: RecommendationModalHeaderProps) {
  return (
    <div className='flex items-center justify-between p-6 border-b'>
      <div className='flex items-center space-x-3'>
        <img
          src={contributor.avatar_url}
          alt={contributor.username}
          className='w-10 h-10 rounded-full'
        />
        <div>
          <h2 id='modal-title' className='text-xl font-semibold text-gray-900'>
            Write LinkedIn Recommendation
          </h2>
          <p className='text-gray-600'>
            for {contributor.full_name || contributor.username} (@
            {contributor.username})
          </p>
        </div>
      </div>
      <button
        onClick={onClose}
        className='text-gray-400 hover:text-gray-600'
        aria-label='Close modal'
      >
        <X className='w-6 h-6' />
      </button>
    </div>
  );
}
