import type { ParsedGitHubInput } from '../types';

/**
 * Parse GitHub input to determine if it's a username or repository URL
 */
export function parseGitHubInput(input: string): ParsedGitHubInput {
  const trimmed = input.trim();

  // Check if it's a full URL
  const urlRegex = /^https?:\/\/(?:www\.)?github\.com\/([^/]+)(?:\/([^/]+))?/i;
  const match = trimmed.match(urlRegex);

  if (match) {
    const username = match[1];
    const repository = match[2];

    if (repository) {
      // It's a repository URL
      return {
        type: 'repo_url',
        username,
        repository,
        fullUrl: trimmed,
      };
    } else {
      // It's a user profile URL
      return {
        type: 'username',
        username,
        fullUrl: trimmed,
      };
    }
  }

  // Check if it contains a slash (likely owner/repo format)
  if (trimmed.includes('/')) {
    const parts = trimmed.split('/');
    if (parts.length === 2) {
      const [username, repository] = parts;
      if (username && repository) {
        return {
          type: 'repo_url',
          username,
          repository,
        };
      }
    }
  }

  // Default to username
  return {
    type: 'username',
    username: trimmed,
  };
}

/**
 * Validate GitHub input
 */
export function validateGitHubInput(input: string): {
  isValid: boolean;
  error?: string;
} {
  const trimmed = input.trim();

  if (!trimmed) {
    return {
      isValid: false,
      error: 'GitHub username or repository URL is required',
    };
  }

  const parsed = parseGitHubInput(trimmed);

  // Basic username/repo validation
  const usernameRegex = /^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$/;
  const repoRegex = /^[a-zA-Z0-9._-]+$/;

  if (!usernameRegex.test(parsed.username)) {
    return { isValid: false, error: 'Invalid GitHub username format' };
  }

  if (parsed.repository && !repoRegex.test(parsed.repository)) {
    return { isValid: false, error: 'Invalid repository name format' };
  }

  return { isValid: true };
}
