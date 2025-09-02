import { Sparkles } from 'lucide-react';
import { Link } from 'react-router';

interface RecommendationLimitMessageProps {
  onClose: () => void;
}

export default function RecommendationLimitMessage({
  onClose,
}: RecommendationLimitMessageProps) {
  return (
    <div className='text-center py-6 px-6'>
      {/* Professional icon */}
      <div className='inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-6'>
        <Sparkles className='w-8 h-8 text-blue-600' />
      </div>

      <h3 className='text-2xl font-bold text-gray-900 mb-3'>
        Recommendation Limit Reached
      </h3>

      <p className='text-lg text-gray-700 mb-4'>
        You&apos;ve used your 3 free recommendations today
      </p>

      <div className='bg-blue-50 rounded-lg p-4 mb-6 border border-blue-200'>
        <p className='text-gray-600 mb-2'>
          Ready for unlimited recommendations?
        </p>
        <p className='text-sm text-gray-500'>
          Join our community and get up to{' '}
          <span className='font-semibold text-blue-600'>
            5 recommendations per day
          </span>
          !
        </p>
      </div>

      <div className='space-y-3'>
        <Link
          to='/register'
          className='inline-flex items-center px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-lg font-semibold shadow-md hover:shadow-lg'
          onClick={onClose}
        >
          Create Free Account
        </Link>

        <p className='text-sm text-gray-500'>
          No credit card required • 2-minute setup
        </p>
      </div>
    </div>
  );
}
