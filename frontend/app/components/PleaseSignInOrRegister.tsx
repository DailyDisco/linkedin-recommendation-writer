import { Button } from '@/components/ui/button';
import { Link } from 'react-router';
import { Sparkles, FileText, History, Zap, Users } from 'lucide-react';

export const PleaseSignInOrRegister = () => {
  return (
    <div className='flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 p-4'>
      <div className='bg-white p-8 rounded-xl shadow-xl text-center max-w-2xl w-full border border-gray-100'>
        <div className='relative mb-6'>
          <Sparkles className='w-6 h-6 text-yellow-400 absolute -top-2 -right-8 animate-pulse' />
          <Sparkles className='w-4 h-4 text-pink-400 absolute -bottom-2 -left-8 animate-bounce' />
        </div>

        <h1 className='text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4'>
          🚀 Supercharge Your LinkedIn Game!
        </h1>

        {/* Features Grid */}
        <div className='grid grid-cols-1 md:grid-cols-2 gap-4 mb-8'>
          <div className='flex items-center space-x-3 bg-blue-50 p-4 rounded-lg border border-blue-100'>
            <FileText className='w-8 h-8 text-blue-600' />
            <div className='text-left'>
              <h3 className='font-semibold text-blue-900'>
                AI-Powered Recommendations
              </h3>
              <p className='text-sm text-blue-700'>
                Get personalized, professional recommendations tailored to your
                industry
              </p>
            </div>
          </div>

          <div className='flex items-center space-x-3 bg-purple-50 p-4 rounded-lg border border-purple-100'>
            <History className='w-8 h-8 text-purple-600' />
            <div className='text-left'>
              <h3 className='font-semibold text-purple-900'>
                Recommendation History
              </h3>
              <p className='text-sm text-purple-700'>
                Save and manage all your generated recommendations in one place
              </p>
            </div>
          </div>

          <div className='flex items-center space-x-3 bg-green-50 p-4 rounded-lg border border-green-100'>
            <Zap className='w-8 h-8 text-green-600' />
            <div className='text-left'>
              <h3 className='font-semibold text-green-900'>
                Advanced Customization
              </h3>
              <p className='text-sm text-green-700'>
                Fine-tune tone, length, and style to match your unique voice
              </p>
            </div>
          </div>

          <div className='flex items-center space-x-3 bg-orange-50 p-4 rounded-lg border border-orange-100'>
            <Users className='w-8 h-8 text-orange-600' />
            <div className='text-left'>
              <h3 className='font-semibold text-orange-900'>
                Professional Templates
              </h3>
              <p className='text-sm text-orange-700'>
                Access curated templates for different industries and roles
              </p>
            </div>
          </div>
        </div>

        <div className='bg-gradient-to-r from-yellow-50 to-orange-50 p-6 rounded-lg mb-8 border border-yellow-200'>
          <p className='text-yellow-800 font-medium'>
            🎯 <strong>Pro Tip:</strong> You get 3 free recommendations a day!
            Upgrade anytime to unlock unlimited access.
          </p>
        </div>

        <div className='flex flex-col space-y-4'>
          <Link to='/login' className='w-full'>
            <Button className='w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white py-3 px-6 rounded-lg text-lg font-semibold shadow-lg hover:shadow-xl transition-all duration-200 transform hover:-translate-y-1'>
              🎉 Sign In & Get Started
            </Button>
          </Link>
          <Link to='/register' className='w-full'>
            <Button
              variant='outline'
              className='w-full border-2 border-purple-600 text-purple-600 hover:bg-purple-50 py-3 px-6 rounded-lg text-lg font-semibold hover:shadow-md transition-all duration-200 transform hover:-translate-y-0.5'
            >
              🌟 Create Free Account
            </Button>
          </Link>
        </div>

        <p className='text-sm text-gray-500 mt-6'>
          Join dozens of professionals who&apos;ve boosted their LinkedIn
          profiles! ⭐
        </p>
      </div>
    </div>
  );
};
