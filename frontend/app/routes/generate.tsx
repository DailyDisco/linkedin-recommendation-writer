import { useState, useCallback, useMemo, useEffect } from 'react';
import { Github, Loader2, Users, User } from 'lucide-react';
import { toast } from 'sonner';
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
  throw new Error(
    'Invalid repository input. Please use owner/repo format or a valid GitHub URL.'
  );
};

export default function GeneratorPage() {
  const [mode, setMode] = useState<'user' | 'repository'>('repository');
  const [isLoading, setIsLoading] = useState(false);
  const [contributors, setContributors] = useState<ContributorInfo[]>([]);
  const [repositoryInfo, setRepositoryInfo] = useState<RepositoryInfo | null>(
    null
  );
  const [selectedContributor, setSelectedContributor] =
    useState<ContributorInfo | null>(null);
  const [showRecommendationModal, setShowRecommendationModal] = useState(false);

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

  const handleGetUsers = async () => {
    if (!formData.input_value.trim()) {
      toast.error(
        mode === 'repository'
          ? 'Please enter a repository name (e.g., facebook/react) or GitHub URL'
          : 'Please enter a GitHub username'
      );
      return;
    }

    setIsLoading(true);
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
          toast.error(error);
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
          toast.error(error);
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
          description: result.repository.description ?? null,
          html_url: result.repository.url,
          language: result.repository.language ?? null,
          stargazers_count: result.repository.stars,
          forks_count: result.repository.forks,
          open_issues_count: 0, // Default to 0 if not available
          created_at: result.repository.created_at ?? '',
          updated_at: result.repository.updated_at ?? '',
          topics: result.repository.topics ?? [],
          owner: result.repository.owner
            ? {
              login: result.repository.owner.login,
              avatar_url: result.repository.owner.avatar_url ?? '',
              html_url: result.repository.owner.html_url ?? '',
            }
            : {
              login: result.repository.full_name.split('/')[0],
              avatar_url: '',
              html_url: '',
            }, // Default owner if not present
        };
        setRepositoryInfo(repoInfo);
        toast.success(
          `Found ${result.contributors.length} contributors for ${result.repository.full_name}!`
        );
      } else {
        // Handle user mode
        const username = formData.input_value.trim();
        const result = await githubApi.analyzeProfile(username);
        // Extract user data from the nested response structure
        const userData = result.user_data;
        // Convert single user to contributor format for consistency
        setContributors([
          {
            username: userData.github_username || userData.login || '',
            full_name:
              userData.full_name ||
              userData.name ||
              userData.github_username ||
              userData.login ||
              '',
            first_name:
              (userData.full_name || userData.name)?.split(' ')[0] || '',
            last_name:
              (userData.full_name || userData.name)
                ?.split(' ')
                .slice(1)
                .join(' ') || '',
            email: userData.email,
            bio: userData.bio,
            company: userData.company,
            location: userData.location,
            avatar_url: userData.avatar_url || '',
            contributions: userData.public_repos || 0,
            profile_url: `https://github.com/${userData.github_username || userData.login}`,
            followers: userData.followers || 0,
            public_repos: userData.public_repos || 0,
          },
        ]);
        toast.success(
          `Found GitHub profile for ${userData.github_username || userData.login || 'user'}!`
        );
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

        if (
          err instanceof Error &&
          err.message.includes('Invalid repository input')
        ) {
          errorMessage = err.message;
        } else if (error.response?.status === 404) {
          errorMessage = `Repository "${parseRepositoryInput(formData.input_value)}" not found. Please check the repository name or URL.`;
        } else if (error.response?.status === 403) {
          errorMessage =
            'GitHub API rate limit exceeded or access denied. Please try again later.';
        } else if (error.response?.status === 401) {
          errorMessage =
            'GitHub authentication failed. Please contact support.';
        } else if (error.response?.data?.detail) {
          const detail = error.response.data.detail;
          errorMessage =
            typeof detail === 'string' ? detail : JSON.stringify(detail);
        }

        console.log('🚨 FRONTEND: Setting error message:', errorMessage);
        toast.error(errorMessage);
      } else {
        const rawErrorMessage =
          error.response?.data?.detail ||
          'GitHub user not found. Please check the username.';
        const errorMessage =
          typeof rawErrorMessage === 'string'
            ? rawErrorMessage
            : JSON.stringify(rawErrorMessage);
        let enhancedMessage = errorMessage;

        if (errorMessage.includes('not found')) {
          enhancedMessage = `${errorMessage}\n\n💡 Tips:\n• Check for typos in the username\n• GitHub usernames are case-sensitive\n• Make sure the user exists and has a public profile\n• Try the username in lowercase`;
        } else if (errorMessage.includes('rate limit')) {
          enhancedMessage = `${errorMessage}\n\n💡 The GitHub API rate limit has been exceeded. Please wait a few minutes and try again.`;
        } else if (
          errorMessage.includes('403') ||
          errorMessage.includes('forbidden')
        ) {
          enhancedMessage = `${errorMessage}\n\n💡 Access denied. This could mean:\n• The user's profile is private\n• GitHub API rate limit exceeded\n• Authentication issues`;
        } else if (
          errorMessage.includes('401') ||
          errorMessage.includes('authentication')
        ) {
          enhancedMessage = `${errorMessage}\n\n💡 Authentication failed. Please contact support.`;
        }

        toast.error(enhancedMessage);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await handleGetUsers();
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
                    />
                  </div>
                  {mode === 'repository' && (
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

          {/* Contributors List */}
          <div className='rounded-lg border border-gray-200 bg-white shadow-sm'>
            <div className='flex flex-col space-y-1.5 p-6 pb-4'>
              <h2 className='text-lg font-semibold leading-none tracking-tight'>
                {mode === 'repository' ? 'Repository Results' : 'User Details'}
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
                <div>
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

                  <div className='space-y-4 max-h-96 overflow-y-auto'>
                    {parsedContributors.map(contributor => (
                      <ContributorCard
                        key={contributor.username}
                        contributor={contributor}
                        onWriteRecommendation={handleWriteRecommendation}
                        mode={mode}
                      />
                    ))}
                  </div>
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
