import React from "react";
import { Link, useLocation } from "react-router";
import { cn } from "../../lib/utils";
import type { NavigationItem } from "./DesktopNavigation";

interface MobileNavigationProps {
  navigation: NavigationItem[];
  isOpen: boolean;
  onClose: () => void;
}

export const MobileNavigation = ({
  navigation,
  isOpen,
  onClose,
}: MobileNavigationProps) => {
  const location = useLocation();

  if (!isOpen) return null;

  return (
    <div className="md:hidden">
      <div className="px-2 pt-2 pb-3 space-y-1 bg-white border-t border-gray-200 shadow-lg">
        {navigation.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.href;

          return (
            <Link
              key={item.name}
              to={item.href}
              onClick={onClose}
              className={cn(
                "group flex items-center px-3 py-3 rounded-lg text-base font-medium transition-all duration-200",
                "hover:bg-gray-50 active:bg-gray-100",
                isActive
                  ? "bg-blue-50 text-blue-700 border-l-4 border-blue-500"
                  : "text-gray-700 border-l-4 border-transparent",
              )}
            >
              <Icon
                className={cn(
                  "w-5 h-5 mr-3 transition-colors",
                  isActive
                    ? "text-blue-600"
                    : "text-gray-500 group-hover:text-gray-700",
                )}
              />
              {item.name}
            </Link>
          );
        })}
      </div>
    </div>
  );
};
