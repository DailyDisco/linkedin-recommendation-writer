import React, {
  createContext,
  useState,
  useEffect,
  useCallback,
  useMemo,
  useRef,
} from 'react';
import { recommendationApi } from '../services/api';
import { useLocalStorage } from '../hooks/useLocalStorage';
import type { HttpError } from '../types';

export interface AuthContextType {
  isLoggedIn: boolean;
  userRecommendationCount: number | null;
  userDailyLimit: number | null;
  isLoadingUserDetails: boolean;
  userDetailsError: string | null;
  isAuthenticating: boolean;
  login: (token: string) => Promise<void>;
  logout: () => void;
  fetchUserDetails: () => Promise<void>;
}

// eslint-disable-next-line react-refresh/only-export-components
export const AuthContext = createContext<AuthContextType | undefined>(
  undefined
);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [accessToken, setAccessToken] = useLocalStorage<string | null>(
    'accessToken',
    null
  );
  const isLoggedIn = !!accessToken;
  const [userRecommendationCount, setUserRecommendationCount] = useState<
    number | null
  >(null);
  const [userDailyLimit, setUserDailyLimit] = useState<number | null>(null);
  const [isLoadingUserDetails, setIsLoadingUserDetails] =
    useState<boolean>(false);
  const [userDetailsError, setUserDetailsError] = useState<string | null>(null);
  const [isAuthenticating, setIsAuthenticating] = useState<boolean>(false);

  // Throttle user details fetching to prevent rate limiting
  const lastFetchRef = useRef<number>(0);
  const THROTTLE_MS = 5000; // 5 seconds minimum between fetches

  const logout = useCallback(() => {
    setIsAuthenticating(true);
    setAccessToken(null);
    setUserRecommendationCount(null);
    setUserDailyLimit(null);
    setIsAuthenticating(false);
  }, [setAccessToken]);

  const fetchUserDetails = useCallback(async () => {
    // Throttle API calls to prevent rate limiting
    const now = Date.now();
    if (now - lastFetchRef.current < THROTTLE_MS) {
      return;
    }
    lastFetchRef.current = now;

    if (isLoggedIn) {
      setIsLoadingUserDetails(true);
      setUserDetailsError(null);
      try {
        const response = await recommendationApi.getUserDetails();
        setUserRecommendationCount(response.recommendation_count);
        setUserDailyLimit(response.daily_limit);
      } catch (error: unknown) {
        console.error('Failed to fetch user details:', error);
        setUserDetailsError(
          (error instanceof Error && error.message) ||
            'Failed to fetch user details'
        );
        // Only logout if it's an authentication error (401/403), not network issues
        // The global API interceptor will handle token removal and redirect for 401s
        if (
          (error as HttpError)?.response?.status === 401 ||
          (error as HttpError)?.response?.status === 403
        ) {
          // Let the global interceptor handle this to avoid conflicts
          console.log(
            'Auth error detected, letting global interceptor handle logout'
          );
        } else if (
          (error as HttpError)?.code === 'NETWORK_ERROR' ||
          !(error as HttpError)?.response
        ) {
          // For network errors, don't logout - just show error
          console.log(
            'Network error fetching user details, keeping user logged in'
          );
        }
      } finally {
        setIsLoadingUserDetails(false);
      }
    } else {
      // Only clear user details if we're actually not logged in
      setUserRecommendationCount(null);
      setUserDailyLimit(null);
      setUserDetailsError(null);
    }
  }, [isLoggedIn, THROTTLE_MS]);

  useEffect(() => {
    // Only fetch user details if we're logged in
    if (isLoggedIn) {
      fetchUserDetails();
    } else {
      // Clear loading state when not logged in
      setIsLoadingUserDetails(false);
    }
  }, [isLoggedIn, fetchUserDetails]);

  const login = useCallback(
    async (token: string) => {
      setIsAuthenticating(true);
      setAccessToken(token);
      try {
        await fetchUserDetails(); // Fetch user details immediately after login
      } catch (error: unknown) {
        console.error(
          'Login: Failed to fetch user details after token set:',
          error
        );
        // If user details fetch fails with auth error, the global interceptor will handle logout
        // For other errors, we keep the user logged in but show an error
        if (
          (error as HttpError)?.response?.status === 401 ||
          (error as HttpError)?.response?.status === 403
        ) {
          console.log(
            'Login: Auth error during user details fetch, global interceptor will handle'
          );
        } else {
          setUserDetailsError(
            'Failed to load user details, but you are logged in'
          );
        }
      } finally {
        setIsAuthenticating(false);
      }
    },
    [setAccessToken, fetchUserDetails]
  );

  const memoizedValue = useMemo(
    () => ({
      isLoggedIn,
      userRecommendationCount,
      userDailyLimit,
      isLoadingUserDetails,
      userDetailsError,
      isAuthenticating,
      login,
      logout,
      fetchUserDetails,
    }),
    [
      isLoggedIn,
      userRecommendationCount,
      userDailyLimit,
      isLoadingUserDetails,
      userDetailsError,
      isAuthenticating,
      login,
      logout,
      fetchUserDetails,
    ]
  );

  return (
    <AuthContext.Provider value={memoizedValue}>
      {children}
    </AuthContext.Provider>
  );
};
