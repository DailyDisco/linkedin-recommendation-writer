import { Loader2 } from 'lucide-react';
import type { ContributorInfo } from '../types/index';

interface RecommendationGeneratingStateProps {
  contributor: ContributorInfo;
}

export default function RecommendationGeneratingState({
  contributor,
}: RecommendationGeneratingStateProps) {
  return (
    <div className='text-center py-12'>
      <Loader2 className='w-12 h-12 animate-spin text-blue-600 mx-auto mb-4' />
      <h3 className='text-lg font-medium text-gray-900 mb-2'>
        Generating Recommendation Options
      </h3>
      <p className='text-gray-600 mb-4'>
        Analyzing {contributor.username}&apos;s GitHub profile and creating
        multiple options...
      </p>
      <div className='bg-gray-200 rounded-full h-2 w-64 mx-auto mb-4'>
        <div
          className='bg-blue-600 h-2 rounded-full animate-pulse'
          style={{ width: '60%' }}
        ></div>
      </div>
      <p className='text-sm text-gray-500'>This may take up to 60 seconds...</p>
    </div>
  );
}
