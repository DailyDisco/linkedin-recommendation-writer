import { AlertCircle } from 'lucide-react';

interface RecommendationLimitMessageProps {
  onClose: () => void;
}

export default function RecommendationLimitMessage({
  onClose,
}: RecommendationLimitMessageProps) {
  return (
    <div className='text-center py-12'>
      <AlertCircle className='w-16 h-16 text-red-500 mx-auto mb-4' />
      <h3 className='text-2xl font-bold text-gray-900 mb-2'>
        Recommendation Limit Reached
      </h3>
      <p className='text-lg text-gray-700 mb-6'>
        You have used your one free recommendation for today.
      </p>
      <p className='text-gray-600 mb-6'>
        Please create an account to generate up to 3 recommendations per day.
      </p>
      <button
        onClick={onClose}
        className='px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-lg font-semibold'
      >
        Create Account
      </button>
    </div>
  );
}
