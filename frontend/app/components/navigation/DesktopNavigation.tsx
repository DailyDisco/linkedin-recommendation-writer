import React from 'react';
import { Link, useLocation } from 'react-router';
import type { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

export interface NavigationItem {
  name: string;
  href: string;
  icon: LucideIcon;
}

interface DesktopNavigationProps {
  navigation: NavigationItem[];
  isLoggedIn: boolean;
  onLogout: () => void;
}

export const DesktopNavigation = ({
  navigation,
  isLoggedIn,
  onLogout,
}: DesktopNavigationProps) => {
  const location = useLocation();

  return (
    <div className='hidden md:flex md:items-center md:space-x-1'>
      {navigation.map(item => {
        const Icon = item.icon;
        const isActive = location.pathname === item.href;

        return (
          <Link
            key={item.name}
            to={item.href}
            className={cn(
              'inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 border-b-2 border-transparent',
              'hover:bg-gray-50 hover:text-gray-900',
              isActive
                ? 'text-blue-600 bg-blue-50 border-b-blue-500'
                : 'text-gray-600'
            )}
          >
            <Icon className='w-4 h-4 mr-2' />
            <span className='hidden lg:block'>{item.name}</span>
          </Link>
        );
      })}
      <div className='flex items-center space-x-2 ml-4'>
        {!isLoggedIn ? (
          <>
            <Link to='/login'>
              <Button variant='ghost' size='sm'>
                Login
              </Button>
            </Link>
            <Link to='/register'>
              <Button size='sm'>Sign Up</Button>
            </Link>
          </>
        ) : (
          <Button variant='ghost' size='sm' onClick={onLogout}>
            Logout
          </Button>
        )}
      </div>
    </div>
  );
};
