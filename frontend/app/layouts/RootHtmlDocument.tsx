import { Links, Meta, Scripts, ScrollRestoration } from 'react-router';
import React from 'react';

export function RootHtmlDocument({ children }: { children: React.ReactNode }) {
  return (
    <html lang='en'>
      <head>
        <meta charSet='utf-8' />
        <meta name='viewport' content='width=device-width, initial-scale=1' />
        <meta
          name='description'
          content='Generate professional LinkedIn recommendations using GitHub data and AI. Analyze commits, PRs, and contributions to create compelling recommendations.'
        />
        <meta
          name='keywords'
          content='LinkedIn, recommendations, GitHub, AI, professional, networking, career'
        />
        <meta name='author' content='LinkedIn Recommendation Writer' />

        {/* Open Graph / Social Media */}
        <meta property='og:type' content='website' />
        <meta
          property='og:title'
          content='LinkedIn Recommendation Writer - AI-Powered Professional Recommendations'
        />
        <meta
          property='og:description'
          content='Generate personalized LinkedIn recommendations from GitHub data using AI. Transform technical contributions into compelling professional narratives.'
        />
        <meta
          property='og:site_name'
          content='LinkedIn Recommendation Writer'
        />

        {/* Twitter Card */}
        <meta name='twitter:card' content='summary_large_image' />
        <meta name='twitter:title' content='LinkedIn Recommendation Writer' />
        <meta
          name='twitter:description'
          content='Generate professional LinkedIn recommendations using GitHub data and AI'
        />

        {/* Favicon */}
        <link rel='icon' type='image/svg+xml' href='/favicon.svg' />
        <link rel='icon' type='image/png' href='/favicon.png' />

        <Meta />
        <Links />
      </head>
      <body>
        {children}
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}
