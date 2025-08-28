/// <reference types="vitest" />
import { reactRouter } from '@react-router/dev/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';
import tsconfigPaths from 'vite-tsconfig-paths';
import path from 'path';

export default defineConfig(({ mode }) => {
  // Include React Router plugin in development/production, skip in test mode
  const plugins = [tailwindcss(), tsconfigPaths()];

  // Only add React Router plugin when NOT in test mode
  if (mode !== 'test') {
    plugins.unshift(reactRouter());
  }

  return {
    plugins,
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './app'),
      },
    },
    server: {
      host: '0.0.0.0',
      port: 5173,
    },
    test: {
      globals: true,
      environment: 'happy-dom',
      setupFiles: './app/test/setup.ts',
      // Ensure path aliases work in test environment
      server: {
        deps: {
          inline: ['react-router-node'],
        },
      },
      // Explicitly configure path aliases for Vitest
      resolve: {
        alias: {
          '@': path.resolve(__dirname, './app'),
        },
      },
    },
  };
});
