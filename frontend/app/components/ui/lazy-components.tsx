import { lazy } from 'react';

// Lazy load heavy components for better performance
export const LazyRecommendationModal = lazy(
  () => import('../RecommendationModal')
);
export const LazyHistoryPage = lazy(() => import('../../routes/history'));
export const LazyAboutPage = lazy(() => import('../../routes/about'));

// Preload components for better UX
export const preloadRecommendationModal = () => {
  const componentImport = import('../RecommendationModal');
  return componentImport;
};

export const preloadHistoryPage = () => {
  const componentImport = import('../../routes/history');
  return componentImport;
};

export const preloadAboutPage = () => {
  const componentImport = import('../../routes/about');
  return componentImport;
};
