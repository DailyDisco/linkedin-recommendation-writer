import React from "react";
import { NavigationBar } from "./components/navigation";

interface LayoutProps {
  children: React.ReactNode;
}

export const AppLayout = ({ children }: LayoutProps) => {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <NavigationBar />

      {/* Main content */}
      <main className="flex-1">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8">
          {children}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8">
          <div className="text-center text-xs sm:text-sm text-gray-600 space-y-2">
            <p className="leading-relaxed">
              LinkedIn Recommendation Writer - Generate professional
              recommendations using GitHub data and AI
            </p>
            <p className="text-gray-500 leading-relaxed">
              Built with ❤️ using Vite + React, FastAPI, React Router v7, Shadcn
              UI, Tailwind CSS, GoLang, and Google Gemini AI
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};
