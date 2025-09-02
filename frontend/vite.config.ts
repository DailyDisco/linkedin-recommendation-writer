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
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
          rewrite: path => path.replace(/^\/api/, '/api/v1'),
          configure: (proxy, _options) => {
            // Handle SSE connections
            proxy.on('error', (err, _req, _res) => {
              console.log('proxy error', err);
            });
            proxy.on('proxyReq', (proxyReq, req, _res) => {
              if (req.headers.accept?.includes('text/event-stream')) {
                proxyReq.setHeader('Cache-Control', 'no-cache');
                proxyReq.setHeader('Accept', 'text/event-stream');
              }
            });
          },
        },
      },
    },
    test: {
      globals: true,
      environment: 'happy-dom',
      setupFiles: './app/test/setup.ts',
      // Ensure path aliases work in test environment
      server: {
        deps: {
          inline: ['@react-router-node'],
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
