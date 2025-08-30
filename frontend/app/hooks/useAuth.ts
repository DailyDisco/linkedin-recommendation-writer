import { useAuthStore } from './useAuthStore';

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

export const useAuth = (): AuthContextType => {
  // Use selectors for reactive properties
  const isLoggedIn = useAuthStore(state => !!state.accessToken);
  const userRecommendationCount = useAuthStore(
    state => state.userRecommendationCount
  );
  const userDailyLimit = useAuthStore(state => state.userDailyLimit);
  const isLoadingUserDetails = useAuthStore(
    state => state.isLoadingUserDetails
  );
  const userDetailsError = useAuthStore(state => state.userDetailsError);
  const isAuthenticating = useAuthStore(state => state.isAuthenticating);

  // Get actions (these don't need to be reactive)
  const store = useAuthStore();

  // Debug: Authentication state working correctly
  // console.log('🔐 useAuth hook - isLoggedIn:', isLoggedIn);

  return {
    isLoggedIn,
    userRecommendationCount,
    userDailyLimit,
    isLoadingUserDetails,
    userDetailsError,
    isAuthenticating,
    login: store.login,
    logout: store.logout,
    fetchUserDetails: store.fetchUserDetails,
  };
};
