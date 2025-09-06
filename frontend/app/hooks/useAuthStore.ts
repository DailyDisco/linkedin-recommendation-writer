import { create } from 'zustand';
import { persist, devtools } from 'zustand/middleware';
import { recommendationApi } from '../services/api';
import type { HttpError } from '../types/index';

export interface AuthState {
  accessToken: string | null;
  userDetails: {
    id: number;
    email: string;
    username: string;
    full_name: string;
    is_active: boolean;
    recommendation_count: number;
    last_recommendation_date: string | null;
    daily_limit: number;
    bio?: string; // Add bio field
    email_notifications_enabled?: boolean; // New field
    default_tone?: string; // New field
    language?: string; // New field
  } | null;
  userRecommendationCount: number | null; // Keep for backward compatibility
  userDailyLimit: number | null; // Keep for backward compatibility
  isLoadingUserDetails: boolean;
  userDetailsError: string | null;
  isAuthenticating: boolean;
  lastFetchTime: number;
}

export interface AuthActions {
  login: (token: string) => Promise<void>;
  logout: () => void;
  fetchUserDetails: (forceRefresh?: boolean) => Promise<void>;
  setUserDetails: (userDetails: AuthState['userDetails']) => void;
  setLoadingUserDetails: (loading: boolean) => void;
  setUserDetailsError: (error: string | null) => void;
  setAuthenticating: (authenticating: boolean) => void;
}

export interface AuthStore extends AuthState, AuthActions {
  // No computed properties - isLoggedIn will be computed in useAuth hook
}

const THROTTLE_MS = 30000; // 30 seconds minimum between fetches for better caching
const CACHE_DURATION_MS = 5 * 60 * 1000; // 5 minutes cache duration

export const useAuthStore = create<AuthStore>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        accessToken: null,
        userDetails: null,
        userRecommendationCount: null, // Keep for backward compatibility
        userDailyLimit: null, // Keep for backward compatibility
        isLoadingUserDetails: false,
        userDetailsError: null,
        isAuthenticating: false,
        lastFetchTime: 0,

        // Remove computed property - will use selector in useAuth hook instead

        // Actions
        setUserDetails: (userDetails: AuthState['userDetails']) => {
          set({
            userDetails,
            userRecommendationCount: userDetails?.recommendation_count || null, // Keep for backward compatibility
            userDailyLimit: userDetails?.daily_limit || null, // Keep for backward compatibility
            userDetailsError: null,
          });
        },

        setLoadingUserDetails: (loading: boolean) => {
          set({ isLoadingUserDetails: loading });
        },

        setUserDetailsError: (error: string | null) => {
          set({ userDetailsError: error });
        },

        setAuthenticating: (authenticating: boolean) => {
          set({ isAuthenticating: authenticating });
        },

        logout: () => {
          console.log(
            '🔐 Auth Store: Logout called, clearing authentication state'
          );
          set({
            isAuthenticating: true,
            accessToken: null,
            userDetails: null,
            userRecommendationCount: null, // Keep for backward compatibility
            userDailyLimit: null, // Keep for backward compatibility
            userDetailsError: null,
            lastFetchTime: 0,
          });
          console.log(
            '🔐 Auth Store: State cleared, authentication set to false'
          );
          set({ isAuthenticating: false });
        },

        fetchUserDetails: async (forceRefresh: boolean = false) => {
          const state = get();

          // If we have cached data and it's still fresh, don't fetch unless forced
          if (
            !forceRefresh &&
            state.userDetails &&
            state.lastFetchTime &&
            Date.now() - state.lastFetchTime < CACHE_DURATION_MS
          ) {
            return;
          }

          // If we don't have userDetails but have a recent lastFetchTime, this might indicate
          // a page refresh where data was lost but timestamp was preserved. Force a refresh.
          if (
            !forceRefresh &&
            !state.userDetails &&
            state.lastFetchTime &&
            Date.now() - state.lastFetchTime < CACHE_DURATION_MS
          ) {
            forceRefresh = true;
          }

          // Throttle API calls to prevent rate limiting
          const now = Date.now();
          if (!forceRefresh && now - state.lastFetchTime < THROTTLE_MS) {
            return;
          }

          if (state.accessToken) {
            set({
              isLoadingUserDetails: true,
              userDetailsError: null,
              lastFetchTime: now,
            });

            try {
              const response = await recommendationApi.getUserDetails();
              set({
                userDetails: response,
                userRecommendationCount: response.recommendation_count, // Keep for backward compatibility
                userDailyLimit: response.daily_limit, // Keep for backward compatibility
                isLoadingUserDetails: false,
              });
            } catch (error: unknown) {
              console.error(
                '🔐 Auth Store: Failed to fetch user details:',
                error
              );
              const httpError = error as HttpError;
              console.log(
                '🔐 Auth Store: Error status:',
                httpError?.response?.status
              );
              console.log('🔐 Auth Store: Error code:', httpError?.code);

              set({
                userDetailsError:
                  (error instanceof Error && error.message) ||
                  'Failed to fetch user details',
                isLoadingUserDetails: false,
              });

              // Only logout if it's an authentication error (401/403), not network issues
              // The global API interceptor will handle token removal and redirect for 401s
              if (
                httpError?.response?.status === 401 ||
                httpError?.response?.status === 403
              ) {
                console.log(
                  '🔐 Auth Store: Auth error detected, letting global interceptor handle logout'
                );
              } else if (
                httpError?.code === 'NETWORK_ERROR' ||
                !httpError?.response
              ) {
                // For network errors, don't logout - just show error
                console.log(
                  '🔐 Auth Store: Network error fetching user details, keeping user logged in'
                );
              } else {
                console.log(
                  '🔐 Auth Store: Other error fetching user details, keeping user logged in'
                );
              }
            }
          } else {
            // Only clear user details if we're actually not logged in
            set({
              userDetails: null,
              userRecommendationCount: null, // Keep for backward compatibility
              userDailyLimit: null, // Keep for backward compatibility
              userDetailsError: null,
              isLoadingUserDetails: false,
            });
          }
        },

        login: async (token: string) => {
          const { fetchUserDetails } = get();

          set({ isAuthenticating: true, accessToken: token });

          try {
            await fetchUserDetails(); // Fetch user details immediately after login
          } catch (error: unknown) {
            console.error('Failed to fetch user details after login:', error);

            // If user details fetch fails with auth error, the global interceptor will handle logout
            // For other errors, we keep the user logged in but show an error
            if (
              (error as HttpError)?.response?.status === 401 ||
              (error as HttpError)?.response?.status === 403
            ) {
              console.log(
                '🔐 Auth Store: Auth error during user details fetch, global interceptor will handle'
              );
            } else {
              console.log(
                '⚠️ Auth Store: Non-auth error during user details fetch, keeping user logged in'
              );
              set({
                userDetailsError:
                  'Failed to load user details, but you are logged in',
              });
            }
          } finally {
            set({ isAuthenticating: false });
          }
        },
      }),
      {
        name: 'auth-storage',
        // Only persist accessToken and lastFetchTime, not derived state
        partialize: state => ({
          accessToken: state.accessToken,
          lastFetchTime: state.lastFetchTime,
        }),
        onRehydrateStorage: () => _state => {
          // Store rehydration complete
        },
      }
    ),
    { name: 'auth-store' }
  )
);

// Note: User details fetching is handled in the login function
// No additional subscription needed for now
