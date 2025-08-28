import React from "react";
import { Link, useLocation } from "react-router";
import type { LucideIcon } from "lucide-react";
import { cn } from "../../lib/utils";

export interface NavigationItem {
  name: string;
  href: string;
  icon: LucideIcon;
}

interface DesktopNavigationProps {
  navigation: NavigationItem[];
}

export const DesktopNavigation = ({ navigation }: DesktopNavigationProps) => {
  const location = useLocation();

  return (
    <div className="hidden md:flex md:items-center md:space-x-1">
      {navigation.map((item) => {
        const Icon = item.icon;
        const isActive = location.pathname === item.href;

        return (
          <Link
            key={item.name}
            to={item.href}
            className={cn(
              "inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 border-b-2 border-transparent",
              "hover:bg-gray-50 hover:text-gray-900",
              isActive
                ? "text-blue-600 bg-blue-50 border-b-blue-500"
                : "text-gray-600",
            )}
          >
            <Icon className="w-4 h-4 mr-2" />
            <span className="hidden lg:block">{item.name}</span>
          </Link>
        );
      })}
    </div>
  );
};
