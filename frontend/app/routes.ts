import {
  type RouteConfig,
  route,
  index,
  layout,
} from '@react-router/dev/routes';

export default [
  // Basic route configuration examples:
  // index("./home.tsx") - renders at "/"
  // route("about", "./about.tsx") - renders at "/about"
  // route("users/:userId", "./user.tsx") - dynamic segment at "/users/123"
  // route("docs/*", "./docs.tsx") - catchall at "/docs/anything/here"

  // Root route - renders at "/"
  index('routes/_index.tsx'),

  // Public routes - accessible to all users
  route('generate', 'routes/generate.tsx'),
  route('about', 'routes/about.tsx'),

  // Authentication layout with nested routes
  // Example: layout creates shared UI without affecting URL structure
  layout('layouts/AuthLayout.tsx', [
    route('login', 'routes/auth/login.tsx'), // renders at "/login"
    route('register', 'routes/auth/register.tsx'), // renders at "/register"
  ]),

  route('advanced', 'routes/advanced.tsx'), // renders at "/advanced"
  route('history', 'routes/history.tsx'), // renders at "/history"

  // Protected routes - require authentication
  // Using prefix to group related functionality under "/app"
  //   ...prefix('app', [
  //     route('advanced', 'routes/protected/advanced.tsx'), // renders at "/app/advanced"
  //     route('history', 'routes/protected/history.tsx'), // renders at "/app/history"

  // Example of nested routes with dynamic segments:
  // route("recommendations/:id", "./recommendation.tsx"),          // "/app/recommendations/123"
  // route("recommendations/:id/edit", "./edit-recommendation.tsx"), // "/app/recommendations/123/edit"
  //   ]),

  // Admin routes - require admin privileges
  // Example admin section:
  // ...prefix("admin", [
  //   index("./admin/dashboard.tsx"),                    // "/admin"
  //   route("users", "./admin/users.tsx"),               // "/admin/users"
  //   route("users/:userId", "./admin/user-detail.tsx"), // "/admin/users/123"
  //   route("settings", "./admin/settings.tsx"),         // "/admin/settings"
  // ]),

  // API routes (if handling client-side API calls)
  // ...prefix("api", [
  //   route("recommendations", "./api/recommendations.tsx"),
  //   route("github/:username", "./api/github.tsx"),     // "/api/github/johndoe"
  // ]),

  // Catchall route - handles 404s
  route('*', 'routes/404.tsx'),
] satisfies RouteConfig;
