import { AlertCircle, Sparkles, Rocket, X } from 'lucide-react';
import { Link } from 'react-router';
import { useEffect } from 'react';

interface RegistrationModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function RegistrationModal({
  isOpen,
  onClose,
}: RegistrationModalProps) {
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50'
      onClick={handleBackdropClick}
      role='dialog'
      aria-modal='true'
      aria-labelledby='modal-title'
    >
      <div
        className='bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto'
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className='flex items-center justify-between p-6 border-b border-gray-200'>
          <div className='flex items-center space-x-3'>
            <div className='inline-flex items-center justify-center w-10 h-10 bg-blue-100 rounded-full'>
              <Sparkles className='w-5 h-5 text-blue-600' />
            </div>
            <h2
              id='modal-title'
              className='text-xl font-semibold text-gray-900'
            >
              You&apos;ve reached your limit!
            </h2>
          </div>
          <button
            onClick={onClose}
            className='text-gray-400 hover:text-gray-600 transition-colors'
            aria-label='Close modal'
          >
            <X className='w-5 h-5' />
          </button>
        </div>

        {/* Content */}
        <div className='p-6'>
          <div className='text-center'>
            <div className='inline-flex items-center justify-center w-16 h-16 bg-orange-100 rounded-full mb-6'>
              <AlertCircle className='w-8 h-8 text-orange-600' />
            </div>

            <h3 className='text-xl font-bold text-gray-900 mb-3'>
              0 of 3 Free Recommendations Used
            </h3>

            <p className='text-gray-600 mb-6'>
              You&apos;ve used all your free recommendations for today. Sign up
              now to get 5 recommendations per day and unlock premium features!
            </p>

            <div className='bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-4 mb-6 border border-blue-200'>
              <div className='flex items-center justify-center space-x-2 mb-2'>
                <Rocket className='w-5 h-5 text-blue-600' />
                <p className='font-semibold text-blue-600'>Upgrade Benefits</p>
              </div>
              <ul className='text-sm text-gray-600 space-y-1'>
                <li>• 5 recommendations per day (vs 3 free)</li>
                <li>• Save and manage your recommendations</li>
                <li>• Export recommendations to PDF/Word</li>
                <li>• Priority support</li>
              </ul>
            </div>

            <div className='space-y-3'>
              <Link
                to='/register'
                className='inline-flex items-center justify-center w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-base font-semibold shadow-md hover:shadow-lg'
                onClick={onClose}
              >
                <Sparkles className='w-4 h-4 mr-2' />
                Sign up for 5 Daily Recommendations
              </Link>

              <button
                onClick={onClose}
                className='w-full px-6 py-2 text-gray-600 hover:text-gray-800 transition-colors text-sm'
              >
                Maybe Later
              </button>
            </div>

            <p className='text-xs text-gray-500 mt-4'>
              No credit card required • Free account setup in 2 minutes
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
