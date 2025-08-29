import { Button } from '@/components/ui/button';

export default function NotFound() {
  return (
    <div className='min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-purple-50 px-4'>
      <div className='max-w-md w-full text-center space-y-8'>
        {/* Animated 404 Number */}
        <div className='relative'>
          <h1 className='text-9xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-blue-600 animate-pulse'>
            404
          </h1>
          <div className='absolute -top-2 -right-2 text-4xl animate-bounce'>
            🤖
          </div>
        </div>

        {/* Fun Message */}
        <div className='space-y-4'>
          <h2 className='text-2xl font-semibold text-gray-800'>
            Oops! This page went on vacation
          </h2>
          <p className='text-gray-600 text-lg'>
            Looks like you&apos;ve stumbled into the digital wilderness! 🌲
            <br />
            Don&apos;t worry, even the best explorers get lost sometimes.
          </p>
        </div>

        {/* Decorative Elements */}
        <div className='flex justify-center space-x-4 text-3xl'>
          <span className='animate-bounce delay-100'>🚀</span>
          <span className='animate-bounce delay-200'>⭐</span>
          <span className='animate-bounce delay-300'>🎯</span>
        </div>

        {/* Action Buttons */}
        <div className='space-y-4'>
          <Button
            onClick={() => window.history.back()}
            className='w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-medium py-3 px-6 rounded-lg transition-all duration-300 transform hover:scale-105'
          >
            Take Me Back 🏠
          </Button>

          <Button
            variant='outline'
            onClick={() => (window.location.href = '/')}
            className='w-full border-purple-300 text-purple-700 hover:bg-purple-50 font-medium py-3 px-6 rounded-lg transition-all duration-300'
          >
            Go to Homepage 🎯
          </Button>
        </div>

        {/* Fun Footer */}
        <div className='pt-8 text-sm text-gray-500'>
          <p>Lost? Try checking your URL or use the navigation above!</p>
          <div className='mt-2 text-xs opacity-75'>
            Error Code: 404 • Page Not Found
          </div>
        </div>
      </div>
    </div>
  );
}
