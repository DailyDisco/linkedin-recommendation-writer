/**
 * Debug utility for testing repository URL parsing
 * Run this in browser console to test various URL formats
 */

export const testRepositoryUrlParsing = () => {
  const parseRepositoryInput = (input: string): string => {
    const trimmed = input.trim().toLowerCase();

    console.log('🔍 Testing repository input:', input);
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

  const testCases = [
    // Standard repository names
    'facebook/react',
    'Microsoft/VSCode',
    'octocat/Hello-World',

    // Standard GitHub URLs
    'https://github.com/facebook/react',
    'https://github.com/Microsoft/VSCode',
    'http://github.com/octocat/Hello-World',

    // GitHub URLs with paths
    'https://github.com/facebook/react/tree/main',
    'https://github.com/microsoft/vscode/blob/main/README.md',
    'https://github.com/facebook/react/issues/123',
    'https://github.com/facebook/react/pull/456',

    // GitHub URLs with anchors and query params
    'https://github.com/facebook/react?tab=readme-ov-file',
    'https://github.com/facebook/react#installation',
    'https://github.com/facebook/react/tree/main?tab=readme-ov-file#quick-start',

    // SSH URLs
    'git@github.com:facebook/react.git',
    'git@github.com:Microsoft/VSCode',

    // URLs with www
    'https://www.github.com/facebook/react',

    // Edge cases
    'FACEBOOK/REACT',
    'facebook/react/',
    'facebook/react.git',

    // Invalid cases
    'facebook',
    'just-a-string',
    'https://gitlab.com/some/repo',
    '',
  ];

  console.log('🧪 Running URL parsing tests...');
  console.log('='.repeat(50));

  testCases.forEach((testCase, index) => {
    console.log(`\nTest ${index + 1}: "${testCase}"`);
    try {
      const result = parseRepositoryInput(testCase);
      console.log(`   Result: "${result}"`);

      // Validate result
      if (result.includes('/') && result.split('/').length === 2) {
        const [owner, repo] = result.split('/');
        if (owner.trim() && repo.trim()) {
          console.log(`   ✅ Valid: owner="${owner}", repo="${repo}"`);
        } else {
          console.log(`   ❌ Invalid: empty owner or repo`);
        }
      } else {
        console.log(`   ❌ Invalid: not in owner/repo format`);
      }
    } catch (error) {
      console.log(`   💥 Error:`, error);
    }
  });

  console.log('\n' + '='.repeat(50));
  console.log('🏁 URL parsing tests complete!');
};

// Run tests if in browser environment
if (typeof window !== 'undefined') {
  (window as any).testRepositoryUrlParsing = testRepositoryUrlParsing;
  console.log(
    '🔧 Debug utility loaded! Run testRepositoryUrlParsing() in console to test URL parsing.'
  );
}
