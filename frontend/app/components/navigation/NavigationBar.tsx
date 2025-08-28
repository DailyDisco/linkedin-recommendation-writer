import React, { useState } from 'react';
import { Github, FileText, History, Info } from 'lucide-react';
import { Logo } from './Logo';
import { DesktopNavigation, type NavigationItem } from './DesktopNavigation';
import { MobileNavigation } from './MobileNavigation';
import { MobileMenuButton } from './MobileMenuButton';

const navigation: NavigationItem[] = [
  { name: 'Home', href: '/', icon: Github },
  { name: 'Get Contributors', href: '/generate', icon: FileText },
  { name: 'History', href: '/history', icon: History },
  { name: 'About', href: '/about', icon: Info },
];

export const NavigationBar = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false);
  };

  return (
    <nav className='bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50'>
      <div className='max-w-7xl mx-auto px-4 sm:px-6 lg:px-8'>
        <div className='flex justify-between items-center h-16'>
          {/* Logo section */}
          <div className='flex-shrink-0'>
            <Logo />
          </div>

          {/* Desktop navigation */}
          <DesktopNavigation navigation={navigation} />

          {/* Mobile menu button */}
          <MobileMenuButton
            isOpen={isMobileMenuOpen}
            onClick={toggleMobileMenu}
          />
        </div>
      </div>

      {/* Mobile navigation */}
      <MobileNavigation
        navigation={navigation}
        isOpen={isMobileMenuOpen}
        onClose={closeMobileMenu}
      />
    </nav>
  );
};
