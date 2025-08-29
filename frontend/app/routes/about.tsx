import { Github, Sparkles, Database, Shield, Globe, Workflow } from 'lucide-react';

export default function AboutPage() {
  return (
    <div className='max-w-4xl mx-auto space-y-12'>
      <div className='text-center space-y-4'>
        <h1 className='text-3xl font-bold text-gray-900'>
          About LinkedIn Recommendation Writer
        </h1>
        <p className='text-lg text-gray-600'>
          AI-powered tool for generating professional LinkedIn recommendations
          from GitHub data
        </p>
      </div>

      <div className='prose prose-lg max-w-none'>
        <div className='rounded-lg border border-gray-200 bg-white shadow-sm'>
          <div className='p-6 space-y-6'>
            <h2 className='text-2xl font-bold text-gray-900'>
              What is this tool?
            </h2>
            <p className='text-gray-700'>
              The LinkedIn Recommendation Writer is an innovative tool that
              analyzes GitHub profiles and generates professional, personalized
              LinkedIn recommendations using advanced AI. It transforms
              technical contributions and coding patterns into compelling
              professional narratives.
            </p>

            <h2 className='text-2xl font-bold text-gray-900'>
              How does it work?
            </h2>
            <div className='space-y-4'>
              <div className='flex items-start space-x-3'>
                <Github className='w-6 h-6 text-blue-600 mt-1' />
                <div>
                  <h3 className='font-semibold'>GitHub Analysis</h3>
                  <p className='text-gray-600'>
                    We analyze public repositories, programming languages,
                    contribution patterns, and project descriptions to
                    understand technical expertise.
                  </p>
                </div>
              </div>
              <div className='flex items-start space-x-3'>
                <Sparkles className='w-6 h-6 text-blue-600 mt-1' />
                <div>
                  <h3 className='font-semibold'>AI Processing</h3>
                  <p className='text-gray-600'>
                    Google Gemini AI processes the technical data and generates
                    natural, professional recommendations that highlight
                    strengths and achievements.
                  </p>
                </div>
              </div>
              <div className='flex items-start space-x-3'>
                <Database className='w-6 h-6 text-blue-600 mt-1' />
                <div>
                  <h3 className='font-semibold'>Intelligent Caching</h3>
                  <p className='text-gray-600'>
                    We cache GitHub data and AI responses to provide fast
                    results and minimize API usage while keeping data fresh.
                  </p>
                </div>
              </div>
            </div>

            <h2 className='text-2xl font-bold text-gray-900'>Features</h2>
            <ul className='list-disc list-inside space-y-2 text-gray-700'>
              <li>
                Analyzes GitHub repositories, languages, and contribution
                patterns
              </li>
              <li>
                Generates recommendations in multiple styles (professional,
                technical, leadership)
              </li>
              <li>Customizable tone and length options</li>
              <li>Fast results with intelligent caching</li>
              <li>History tracking for all generated recommendations</li>
              <li>No registration required - completely free to use</li>
            </ul>

            <h2 className='text-2xl font-bold text-gray-900'>
              Privacy & Security
            </h2>
            <div className='bg-green-50 border border-green-200 rounded-lg p-4'>
              <div className='flex items-start space-x-3'>
                <Shield className='w-6 h-6 text-green-600 mt-1' />
                <div>
                  <h3 className='font-semibold text-green-800'>
                    Your Privacy Matters
                  </h3>
                  <ul className='text-green-700 mt-2 space-y-1'>
                    <li>• We only access public GitHub data</li>
                    <li>• No personal information is stored</li>
                    <li>• All data is processed securely</li>
                    <li>
                      • Recommendations are temporarily cached for performance
                    </li>
                  </ul>
                </div>
              </div>
            </div>

            <h2 className='text-2xl font-bold text-gray-900'>
              Technology Stack
            </h2>
            <div className='grid sm:grid-cols-2 gap-4'>
              <div className='space-y-2'>
                <h3 className='font-semibold'>Backend</h3>
                <ul className='text-gray-600 space-y-1'>
                  <li>• FastAPI (Python)</li>
                  <li>• PostgreSQL Database</li>
                  <li>• Redis Caching</li>
                  <li>• Google Gemini AI</li>
                </ul>
              </div>
              <div className='space-y-2'>
                <h3 className='font-semibold'>Frontend</h3>
                <ul className='text-gray-600 space-y-1'>
                  <li>• React + TypeScript</li>
                  <li>• Tailwind CSS</li>
                  <li>• React Query</li>
                  <li>• Vite Build System</li>
                </ul>
              </div>
            </div>

            <h2 className='text-2xl font-bold text-gray-900'>
              Deployment & Infrastructure
            </h2>
            <div className='grid sm:grid-cols-2 gap-4'>
              <div className='flex items-start space-x-3'>
                <Globe className='w-6 h-6 text-purple-600 mt-1' />
                <div>
                  <h3 className='font-semibold'>Containerization</h3>
                  <p className='text-gray-600'>
                    The application is containerized using Docker, ensuring consistent
                    environments across development and production.
                  </p>
                </div>
              </div>
              <div className='flex items-start space-x-3'>
                <Workflow className='w-6 h-6 text-purple-600 mt-1' />
                <div>
                  <h3 className='font-semibold'>Cloud Deployment</h3>
                  <p className='text-gray-600'>
                    Deployed on Railway, leveraging its robust infrastructure for
                    scalability and reliability.
                  </p>
                </div>
              </div>
            </div>

            <h2 className='text-2xl font-bold text-gray-900'>Roadmap</h2>
            <ul className='list-disc list-inside space-y-2 text-gray-700'>
              <li>Implement user authentication and personalized dashboards</li>
              <li>Expand AI models for more nuanced recommendation styles</li>
              <li>Integrate with other professional networking platforms</li>
              <li>Offer advanced customization options for generated recommendations</li>
              <li>Improve GitHub analysis with deeper insights into project contributions</li>
            </ul>

            <h2 className='text-2xl font-bold text-gray-900'>Open Source</h2>
            <p className='text-gray-700'>
              This project is open source and available on GitHub.
              Contributions, bug reports, and feature requests are welcome! We
              believe in transparency and community-driven development.
            </p>

            <div className='bg-blue-50 border border-blue-200 rounded-lg p-4'>
              <p className='text-blue-800'>
                <strong>Note:</strong> This tool is designed to help create
                authentic recommendations based on real GitHub activity. Please
                ensure any recommendations generated reflect genuine
                professional relationships and experiences.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
