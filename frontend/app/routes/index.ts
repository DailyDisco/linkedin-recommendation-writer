import type { RouteConfig } from '@react-router/dev/routes';
import Index from './_index';
import Generate from './generate';
import Advanced from './advanced';
import History from './history';
import About from './about';
import Login from './login';
import Register from './register';

export default [
  {
    path: '/',
    component: Index,
  },
  {
    path: '/generate',
    component: Generate,
  },
  {
    path: '/advanced',
    component: Advanced,
  },
  {
    path: '/history',
    component: History,
  },
  {
    path: '/about',
    component: About,
  },
  // Login
  {
    path: '/login',
    component: Login,
  },
  // Register
  {
    path: '/register',
    component: Register,
  },
] satisfies RouteConfig;
