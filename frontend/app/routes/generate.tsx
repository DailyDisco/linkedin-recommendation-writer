import { useState, useCallback, useMemo, useEffect } from 'react';
import {
  Github,
  Loader2,
  Users,
  User,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  CheckCircle,
  XCircle,
  AlertTriangle,
} from 'lucide-react';
import { githubApi } from '../services/api';
import type { ContributorInfo, HttpError, RepositoryInfo } from '../types';

// Extend window interface for debug utilities
declare global {
  interface Window {
    testRepositoryUrlParsing?: typeof testRepositoryUrlParsing;
  }
}
import RecommendationModal from '../components/RecommendationModal';
import { ContributorSkeleton } from '../components/ui/loading-skeleton';
import ErrorBoundary from '../components/ui/error-boundary';
import { ContributorCard } from '../components/ui/memo-components';
import { testRepositoryUrlParsing } from '../utils/debug-url-parser';
import { useAuth } from '../hooks/useAuth'; // Import useAuth hook

export default function GeneratorPage() {
  const [mode, setMode] = useState<'user' | 'repository'>('repository');
  const [isLoading, setIsLoading] = useState(false);
  const [contributors, setContributors] = useState<ContributorInfo[]>([]);
  const [repositoryInfo, setRepositoryInfo] = useState<RepositoryInfo | null>(
    null
  );
  const [error, setError] = useState<string>('');
  const [selectedContributor, setSelectedContributor] =
    useState<ContributorInfo | null>(null);
  const [showRecommendationModal, setShowRecommendationModal] = useState(false);
  const [showDiagnostics, setShowDiagnostics] = useState(false);
  const [diagnostics, setDiagnostics] = useState<{
    status: string;
    message: string;
    github_token_configured: boolean;
    rate_limit_remaining?: number;
  } | null>(null);
  const {
    isLoggedIn,
    userRecommendationCount,
    userDailyLimit,
    fetchUserDetails,
  } = useAuth(); // Get auth status and user details

  const [formData, setFormData] = useState({
    input_value: '', // This will be either username or repository
    recommendation_type: 'professional',
    tone: 'professional',
    length: 'medium',
    custom_prompt: '',
    target_role: '',
  });

  // Load debug utility in development
  useEffect(() => {
    if (import.meta.env.DEV && typeof window !== 'undefined') {
      window.testRepositoryUrlParsing = testRepositoryUrlParsing;
      console.log(
        '🔧 Debug utility loaded! Run testRepositoryUrlParsing() in console to test URL parsing.'
      );
    }
  }, []);

  // Fetch user details when the component mounts or isLoggedIn changes
  useEffect(() => {
    fetchUserDetails();
  }, [fetchUserDetails]);

  // Helper function to parse GitHub URL or repository name
  const parseRepositoryInput = (input: string): string => {
    const trimmed = input.trim().toLowerCase();

    console.log('🔍 FRONTEND: Parsing repository input:', input);
    console.log('   • Trimmed input:', trimmed);

    // Handle various GitHub URL formats
    const githubUrlPatterns = [
      // Standard GitHub URLs with optional paths/anchors
      /^https?:\/\/(?:www\.)?github\.com\/([^/\s]+)\/([^/\s]+)(?:\/.*)?(?:\?.*)?(?:#.*)?$/i,
      // SSH URLs
      /^git@github\.com:([^/\s]+)\/([^/\s]+)(?:\.git)?$/i,
      // GitHub CLI format
      /^gh:([^/\s]+)\/([^/\s]+)$/i,
    ];

    for (const pattern of githubUrlPatterns) {
      const match = input.trim().match(pattern);
      if (match) {
        const [, owner, repo] = match;
        // Remove .git suffix if present
        const cleanRepo = repo.replace(/\.git$/, '');
        const result = `${owner}/${cleanRepo}`;
        console.log('   ✅ Matched URL pattern, extracted:', result);
        return result;
      }
    }

    // If it's already in owner/repo format, return as-is
    if (
      trimmed.includes('/') &&
      !trimmed.includes('http') &&
      !trimmed.includes('git@')
    ) {
      console.log('   ✅ Already in owner/repo format:', trimmed);
      return trimmed;
    }

    // Otherwise, return original input (will likely cause an error)
    console.log('   ⚠️ No pattern matched, returning original:', trimmed);
    return trimmed;
  };

  const handleGetUsers = async () => {
    if (!formData.input_value.trim()) {
      setError(
        mode === 'repository'
          ? 'Please enter a repository name (e.g., facebook/react) or GitHub URL'
          : 'Please enter a GitHub username'
      );
      return;
    }

    setIsLoading(true);
    setError('');
    setContributors([]);
    setRepositoryInfo(null);

    try {
      if (mode === 'repository') {
        const repositoryName = parseRepositoryInput(formData.input_value);

        console.log(
          '🚀 FRONTEND: Attempting to fetch contributors for:',
          repositoryName
        );

        // Validate the parsed repository name
        if (
          !repositoryName.includes('/') ||
          repositoryName.split('/').length !== 2
        ) {
          const error =
            'Please enter a valid repository name (e.g., facebook/react) or GitHub URL (e.g., https://github.com/facebook/react)';
          console.log('❌ FRONTEND: Validation failed:', error);
          setError(error);
          return;
        }

        // Additional validation for empty owner/repo parts
        const [owner, repo] = repositoryName.split('/');
        if (!owner.trim() || !repo.trim()) {
          const error = 'Repository owner and name cannot be empty';
          console.log('❌ FRONTEND: Empty owner/repo validation failed:', {
            owner,
            repo,
          });
          setError(error);
          return;
        }

        console.log('📡 FRONTEND: Making API request to get contributors...');
        const result = await githubApi.getRepositoryContributors(
          repositoryName,
          50
        );

        console.log('✅ FRONTEND: API response received:', {
          contributorsCount: result.contributors.length,
          repositoryName: result.repository.full_name,
        });

        setContributors(result.contributors);
        // Convert SimpleRepositoryInfo to RepositoryInfo format
        const repoInfo: RepositoryInfo = {
          name: result.repository.name,
          full_name: result.repository.full_name,
          description: result.repository.description || null,
          html_url: result.repository.url,
          language: result.repository.language || null,
          stargazers_count: result.repository.stars,
          forks_count: result.repository.forks,
          open_issues_count: 0, // Not available in SimpleRepositoryInfo
          created_at: result.repository.created_at || '',
          updated_at: result.repository.updated_at || '',
          topics: result.repository.topics,
          owner: {
            login: result.repository.full_name.split('/')[0],
            avatar_url: '', // Not available in SimpleRepositoryInfo
            html_url: result.repository.url.replace('/' + result.repository.name, ''),
          },
        };
        setRepositoryInfo(repoInfo);
      } else {
        // Handle user mode
        const username = formData.input_value.trim();
        const result = await githubApi.analyzeProfile(username);
        // Convert single user to contributor format for consistency
        setContributors([
          {
            username: result.github_username,
            full_name: result.full_name || result.github_username,
            first_name: result.full_name ? result.full_name.split(' ')[0] : '',
            last_name: result.full_name
              ? result.full_name.split(' ').slice(1).join(' ')
              : '',
            email: result.email,
            bio: result.bio,
            company: result.company,
            location: result.location,
            avatar_url: result.avatar_url || '',
            contributions: result.public_repos,
            profile_url: `https://github.com/${result.github_username}`,
            followers: result.followers,
            public_repos: result.public_repos,
          },
        ]);
      }
    } catch (err: unknown) {
      const error = err as HttpError;
      console.error('💥 FRONTEND: API request failed:', {
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        message: error.message,
        mode: mode,
        input: formData.input_value,
      });

      if (mode === 'repository') {
        let errorMessage =
          "Repository not found. Please check the repository name or URL and ensure it's a public repository.";

        if (error.response?.status === 404) {
          errorMessage = `Repository "${parseRepositoryInput(formData.input_value)}" not found. Please check the repository name or URL.`;
        } else if (error.response?.status === 403) {
          errorMessage =
            'GitHub API rate limit exceeded or access denied. Please try again later.';
        } else if (error.response?.status === 401) {
          errorMessage =
            'GitHub authentication failed. Please contact support.';
        } else if (error.response?.data?.detail) {
          // Ensure error message is always a string
          const detail = error.response.data.detail;
          errorMessage = typeof detail === 'string' ? detail : JSON.stringify(detail);
        }

        console.log('🚨 FRONTEND: Setting error message:', errorMessage);
        setError(errorMessage);
      } else {
        // Ensure error message is always a string
        const rawErrorMessage = error.response?.data?.detail || 'GitHub user not found. Please check the username.';
        const errorMessage = typeof rawErrorMessage === 'string' ? rawErrorMessage : JSON.stringify(rawErrorMessage);

        // Add diagnostic suggestion if it looks like a configuration issue
        const enhancedMessage =
          errorMessage.includes('GitHub token') ||
            errorMessage.includes('not configured')
            ? `${errorMessage} Please check the Service Diagnostics section below for configuration issues.`
            : errorMessage;

        setError(enhancedMessage);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await handleGetUsers();
  };

  const handleRunDiagnostics = async () => {
    try {
      const result = await githubApi.checkHealth();
      setDiagnostics(result);
      setShowDiagnostics(true);
    } catch (err: unknown) {
      const error = err as HttpError;
      setDiagnostics({
        status: 'error',
        message: `Failed to check GitHub service: ${error.response?.data?.detail || error.message}`,
        github_token_configured: false,
      });
      setShowDiagnostics(true);
    }
  };

  const handleWriteRecommendation = useCallback(
    (contributor: ContributorInfo) => {
      setSelectedContributor(contributor);
      setShowRecommendationModal(true);
    },
    []
  );

  // Memoize expensive computations
  const parsedContributors = useMemo(() => {
    return contributors.map(contributor => ({
      ...contributor,
      displayName: contributor.full_name || contributor.username,
      hasFullName: !!(contributor.first_name && contributor.last_name),
    }));
  }, [contributors]);

  return (
    <ErrorBoundary>
      <div className='max-w-6xl mx-auto space-y-8'>
        <div className='text-center space-y-4'>
          <h1 className='text-3xl font-bold text-gray-900'>
            Generate LinkedIn Recommendations
          </h1>
          <p className='text-lg text-gray-600'>
            Find GitHub contributors and create personalized LinkedIn
            recommendations using AI
          </p>
          {isLoggedIn &&
            userRecommendationCount !== null &&
            userDailyLimit !== null && (
              <p className='text-sm text-gray-500'>
                You have {userDailyLimit - userRecommendationCount} of{' '}
                {userDailyLimit} recommendations remaining today.
              </p>
            )}
        </div>

        <div className='grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8'>
          {/* Form */}
          <div className='rounded-lg border border-gray-200 bg-white shadow-sm'>
            <div className='flex flex-col space-y-1.5 p-6 pb-4'>
              <h2 className='text-lg font-semibold leading-none tracking-tight'>
                Repository Search
              </h2>
              <p className='text-sm text-gray-600'>
                Enter a repository to find all contributors
              </p>
            </div>
            <div className='p-6 pt-0'>
              <form onSubmit={handleSubmit} className='space-y-6'>
                {/* Mode Toggle */}
                <div className='flex items-center space-x-4 p-3 bg-gray-50 rounded-lg'>
                  <button
                    type='button'
                    onClick={() => setMode('repository')}
                    className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${mode === 'repository'
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-600 hover:text-gray-900'
                      }`}
                  >
                    <Users className='w-4 h-4' />
                    <span>Repository Mode</span>
                  </button>
                  <button
                    type='button'
                    onClick={() => setMode('user')}
                    className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${mode === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-600 hover:text-gray-900'
                      }`}
                  >
                    <User className='w-4 h-4' />
                    <span>Single User</span>
                  </button>
                </div>

                <div>
                  <label className='block text-sm font-medium text-gray-700 mb-2'>
                    {mode === 'repository'
                      ? 'Repository Name or URL *'
                      : 'GitHub Username *'}
                  </label>
                  <div className='relative'>
                    {mode === 'repository' ? (
                      <Users className='absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400' />
                    ) : (
                      <Github className='absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400' />
                    )}
                    <input
                      type='text'
                      required
                      className='flex h-9 w-full rounded-md border border-gray-300 bg-white px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-gray-500 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-blue-500 disabled:cursor-not-allowed disabled:opacity-50 pl-10'
                      placeholder={
                        mode === 'repository'
                          ? 'e.g. facebook/react or https://github.com/facebook/react'
                          : 'e.g. octocat'
                      }
                      value={formData.input_value}
                      onChange={e =>
                        setFormData(prev => ({
                          ...prev,
                          input_value: e.target.value,
                        }))
                      }
                      aria-label={
                        mode === 'repository'
                          ? 'Repository Name or URL'
                          : 'GitHub Username'
                      }
                      aria-describedby={error ? 'input-error' : undefined}
                    />
                  </div>
                  {mode === 'repository' && !error && (
                    <div>
                      <p className='mt-1 text-sm text-gray-500'>
                        Enter either a repository name (owner/repo) or a full
                        GitHub URL
                      </p>
                      <div className='mt-1 text-xs text-gray-400'>
                        <p>
                          <strong>Examples:</strong>
                        </p>
                        <p>• facebook/react</p>
                        <p>• https://github.com/facebook/react</p>
                        <p>• https://github.com/microsoft/vscode/tree/main</p>
                      </div>
                    </div>
                  )}
                  {error && (
                    <div
                      id='input-error'
                      className='mt-2 flex items-center space-x-2 text-sm text-red-600'
                    >
                      <AlertCircle className='w-4 h-4 flex-shrink-0' />
                      <p>{error}</p>
                    </div>
                  )}
                </div>

                <button
                  type='submit'
                  disabled={isLoading || !formData.input_value}
                  className='inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-blue-600 text-white shadow hover:bg-blue-700 active:bg-blue-800 h-9 px-4 py-2 w-full'
                >
                  {isLoading ? (
                    <>
                      <Loader2 className='w-4 h-4 mr-2 animate-spin' />
                      {mode === 'repository'
                        ? 'Getting Contributors...'
                        : 'Getting User...'}
                    </>
                  ) : (
                    <>
                      <Users className='w-4 h-4 mr-2' />
                      {mode === 'repository' ? 'Get Contributors' : 'Get User'}
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>

          {/* Diagnostics Section */}
          <div className='rounded-lg border border-gray-200 bg-white shadow-sm'>
            <div className='flex items-center justify-between p-6 pb-4'>
              <h2 className='text-lg font-semibold leading-none tracking-tight'>
                Service Diagnostics
              </h2>
              <button
                onClick={() => setShowDiagnostics(!showDiagnostics)}
                className='flex items-center space-x-2 px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-md transition-colors'
              >
                <span>GitHub API Status</span>
                {showDiagnostics ? (
                  <ChevronUp className='w-4 h-4' />
                ) : (
                  <ChevronDown className='w-4 h-4' />
                )}
              </button>
            </div>

            {showDiagnostics && (
              <div className='p-6 pt-0'>
                {diagnostics ? (
                  <div className='space-y-4'>
                    <div className='flex items-center space-x-2'>
                      {diagnostics.status === 'healthy' && (
                        <CheckCircle className='w-5 h-5 text-green-600' />
                      )}
                      {diagnostics.status === 'degraded' && (
                        <AlertTriangle className='w-5 h-5 text-yellow-600' />
                      )}
                      {(diagnostics.status === 'unhealthy' ||
                        diagnostics.status === 'error') && (
                          <XCircle className='w-5 h-5 text-red-600' />
                        )}
                      <span
                        className={`font-medium ${diagnostics.status === 'healthy'
                            ? 'text-green-600'
                            : diagnostics.status === 'degraded'
                              ? 'text-yellow-600'
                              : 'text-red-600'
                          }`}
                      >
                        {diagnostics.status.toUpperCase()}
                      </span>
                    </div>

                    <p className='text-gray-700'>{diagnostics.message}</p>

                    <div className='grid grid-cols-1 md:grid-cols-2 gap-4 text-sm'>
                      <div>
                        <span className='font-medium text-gray-600'>
                          GitHub Token:
                        </span>
                        <span
                          className={`ml-2 ${diagnostics.github_token_configured
                              ? 'text-green-600'
                              : 'text-red-600'
                            }`}
                        >
                          {diagnostics.github_token_configured
                            ? '✓ Configured'
                            : '✗ Not Configured'}
                        </span>
                      </div>

                      {diagnostics.rate_limit_remaining !== undefined && (
                        <div>
                          <span className='font-medium text-gray-600'>
                            API Quota Remaining:
                          </span>
                          <span
                            className={`ml-2 ${diagnostics.rate_limit_remaining > 100
                                ? 'text-green-600'
                                : diagnostics.rate_limit_remaining > 0
                                  ? 'text-yellow-600'
                                  : 'text-red-600'
                              }`}
                          >
                            {diagnostics.rate_limit_remaining.toLocaleString()}{' '}
                            requests
                          </span>
                        </div>
                      )}
                    </div>

                    {!diagnostics.github_token_configured && (
                      <div className='bg-red-50 border border-red-200 rounded-md p-4'>
                        <h4 className='font-medium text-red-800 mb-2'>
                          How to Fix:
                        </h4>
                        <ul className='text-sm text-red-700 space-y-1'>
                          <li>
                            • Set the{' '}
                            <code className='bg-red-100 px-1 rounded'>
                              GITHUB_TOKEN
                            </code>{' '}
                            environment variable
                          </li>
                          <li>
                            • Token should start with{' '}
                            <code className='bg-red-100 px-1 rounded'>
                              ghp_
                            </code>{' '}
                            or{' '}
                            <code className='bg-red-100 px-1 rounded'>
                              github_pat_
                            </code>
                          </li>
                          <li>
                            • Check your{' '}
                            <code className='bg-red-100 px-1 rounded'>
                              .env
                            </code>{' '}
                            file or server configuration
                          </li>
                        </ul>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className='text-center py-8'>
                    <button
                      onClick={handleRunDiagnostics}
                      className='px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors'
                    >
                      Check GitHub Service Status
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Contributors List */}
          <div className='rounded-lg border border-gray-200 bg-white shadow-sm'>
            <div className='flex flex-col space-y-1.5 p-6 pb-4'>
              <h2 className='text-lg font-semibold leading-none tracking-tight'>
                {mode === 'repository' ? 'Contributors' : 'User Details'}
              </h2>
              <p className='text-sm text-gray-600'>
                {contributors.length > 0
                  ? `Found ${contributors.length} ${mode === 'repository' ? 'contributors' : 'user'}`
                  : 'Contributors will appear here'}
              </p>
            </div>
            <div className='p-6 pt-0'>
              {isLoading ? (
                <ContributorSkeleton />
              ) : contributors.length > 0 ? (
                <div className='space-y-4 max-h-96 overflow-y-auto'>
                  {repositoryInfo && mode === 'repository' && (
                    <div className='border-b pb-4 mb-4'>
                      <h3 className='font-semibold text-lg'>
                        {repositoryInfo.full_name}
                      </h3>
                      <p className='text-gray-600 text-sm'>
                        {repositoryInfo.description}
                      </p>
                      <div className='flex items-center space-x-4 mt-2 text-sm text-gray-500'>
                        <span>⭐ {repositoryInfo.stargazers_count}</span>
                        <span>🍴 {repositoryInfo.forks_count}</span>
                        <span>💻 {repositoryInfo.language}</span>
                      </div>
                    </div>
                  )}
                  {parsedContributors.map(contributor => (
                    <ContributorCard
                      key={contributor.username}
                      contributor={contributor}
                      onWriteRecommendation={handleWriteRecommendation}
                      mode={mode}
                    />
                  ))}
                </div>
              ) : (
                <div className='bg-gray-50 rounded-lg p-6 min-h-[300px] flex items-center justify-center text-gray-500'>
                  <div className='text-center'>
                    <Users className='w-12 h-12 mx-auto mb-4 text-gray-400' />
                    <p>
                      Enter a repository name or URL and click &quot;Get
                      Contributors&quot;
                    </p>
                    <div className='text-sm mt-2 space-y-1'>
                      <p>
                        <strong>Repository format:</strong> facebook/react,
                        microsoft/vscode
                      </p>
                      <p>
                        <strong>GitHub URL:</strong>{' '}
                        https://github.com/facebook/react
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Recommendation Modal */}
        {selectedContributor && (
          <RecommendationModal
            contributor={selectedContributor}
            isOpen={showRecommendationModal}
            onClose={() => {
              setShowRecommendationModal(false);
              setSelectedContributor(null);
            }}
            isLoggedIn={isLoggedIn} // Pass isLoggedIn prop
          />
        )}
      </div>
    </ErrorBoundary>
  );
}
