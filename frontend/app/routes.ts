import type { RouteConfig } from '@react-router/dev/routes';

export default [
  {
    path: '/',
    file: 'routes/_index.tsx',
  },
  {
    path: '/generate',
    file: 'routes/generate.tsx',
  },
  {
    path: '/advanced',
    file: 'routes/advanced.tsx',
  },
  {
    path: '/history',
    file: 'routes/history.tsx',
  },
  {
    path: '/about',
    file: 'routes/about.tsx',
  },
  // Login
  {
    path: '/login',
    file: 'routes/login.tsx',
  },
  // Register
  {
    path: '/register',
    file: 'routes/register.tsx',
  },
] satisfies RouteConfig;
