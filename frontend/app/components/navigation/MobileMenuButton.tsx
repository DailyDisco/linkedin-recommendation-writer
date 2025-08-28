import React from 'react';
import { Menu, X } from 'lucide-react';
import { Button } from '../ui/button';

interface MobileMenuButtonProps {
  isOpen: boolean;
  onClick: () => void;
}

export const MobileMenuButton = ({
  isOpen,
  onClick,
}: MobileMenuButtonProps) => {
  return (
    <Button
      variant='ghost'
      size='sm'
      className='md:hidden p-2 h-auto'
      onClick={onClick}
      aria-label={isOpen ? 'Close menu' : 'Open menu'}
      aria-expanded={isOpen}
    >
      {isOpen ? (
        <X className='h-6 w-6 text-gray-600' />
      ) : (
        <Menu className='h-6 w-6 text-gray-600' />
      )}
    </Button>
  );
};
