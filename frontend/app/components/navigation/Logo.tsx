import React from 'react';
import { Link } from 'react-router';
import { Github } from 'lucide-react';

export const Logo = () => {
  return (
    <Link
      to='/'
      className='flex items-center space-x-3 transition-opacity hover:opacity-80'
    >
      <Github className='h-8 w-8 text-blue-600' />
      <span className='text-xl font-bold text-gray-900 hidden sm:block'>
        LinkedIn Recommender
      </span>
      <span className='text-lg font-bold text-gray-900 sm:hidden'>LR</span>
    </Link>
  );
};
