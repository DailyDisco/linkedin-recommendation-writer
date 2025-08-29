import { Button } from '@/components/ui/button';
import { Link } from 'react-router';
import { LogIn } from 'lucide-react'; // Import an icon

export const PleaseSignInOrRegister = () => {
  return (
    <div className='flex flex-col items-center justify-center min-h-screen bg-gray-50 p-4'>
      <div className='bg-white p-8 rounded-lg shadow-md text-center max-w-md w-full'>
        <LogIn className='w-16 h-16 text-blue-500 mx-auto mb-6' />{' '}
        {/* Add an icon */}
        <h1 className='text-3xl font-bold text-gray-800 mb-4'>
          Unlock Your Full Potential!
        </h1>
        <p className='text-gray-600 mb-6'>
          Sign in or register to access personalized recommendations, advanced
          features, and more.
        </p>
        <div className='flex flex-col space-y-4'>
          <Link to='/login' className='w-full'>
            <Button className='w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-md text-lg'>
              Sign In
            </Button>
          </Link>
          <Link to='/register' className='w-full'>
            <Button
              variant='outline'
              className='w-full border-blue-600 text-blue-600 hover:bg-blue-50 py-2 px-4 rounded-md text-lg'
            >
              Register Now
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
};
