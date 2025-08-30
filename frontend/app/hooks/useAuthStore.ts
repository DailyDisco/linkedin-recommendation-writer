import { create } from 'zustand';
import { persist, devtools } from 'zustand/middleware';
import { recommendationApi } from '../services/api';
import type { HttpError } from '../types/index';

export interface AuthState {
  accessToken: string | null;
  userRecommendationCount: number | null;
  userDailyLimit: number | null;
  isLoadingUserDetails: boolean;
  userDetailsError: string | null;
  isAuthenticating: boolean;
  lastFetchTime: number;
}

export interface AuthActions {
  login: (token: string) => Promise<void>;
  logout: () => void;
  fetchUserDetails: () => Promise<void>;
  setUserDetails: (count: number | null, limit: number | null) => void;
  setLoadingUserDetails: (loading: boolean) => void;
  setUserDetailsError: (error: string | null) => void;
  setAuthenticating: (authenticating: boolean) => void;
}

export interface AuthStore extends AuthState, AuthActions {
  // No computed properties - isLoggedIn will be computed in useAuth hook
}

const THROTTLE_MS = 5000; // 5 seconds minimum between fetches

export const useAuthStore = create<AuthStore>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        accessToken: null,
        userRecommendationCount: null,
        userDailyLimit: null,
        isLoadingUserDetails: false,
        userDetailsError: null,
        isAuthenticating: false,
        lastFetchTime: 0,

        // Remove computed property - will use selector in useAuth hook instead

        // Actions
        setUserDetails: (count: number | null, limit: number | null) => {
          set({
            userRecommendationCount: count,
            userDailyLimit: limit,
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
          set({
            isAuthenticating: true,
            accessToken: null,
            userRecommendationCount: null,
            userDailyLimit: null,
            userDetailsError: null,
            lastFetchTime: 0,
          });
          set({ isAuthenticating: false });
        },

        fetchUserDetails: async () => {
          const state = get();

          // Throttle API calls to prevent rate limiting
          const now = Date.now();
          if (now - state.lastFetchTime < THROTTLE_MS) {
            return;
          }

          if (state.isLoggedIn) {
            set({
              isLoadingUserDetails: true,
              userDetailsError: null,
              lastFetchTime: now,
            });

            try {
              const response = await recommendationApi.getUserDetails();
              set({
                userRecommendationCount: response.recommendation_count,
                userDailyLimit: response.daily_limit,
                isLoadingUserDetails: false,
              });
            } catch (error: unknown) {
              console.error('Failed to fetch user details:', error);
              set({
                userDetailsError:
                  (error instanceof Error && error.message) ||
                  'Failed to fetch user details',
                isLoadingUserDetails: false,
              });

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
            }
          } else {
            // Only clear user details if we're actually not logged in
            set({
              userRecommendationCount: null,
              userDailyLimit: null,
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
      }
    ),
    { name: 'auth-store' }
  )
);

// Note: User details fetching is handled in the login function
// No additional subscription needed for now
