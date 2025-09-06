import { useAuthStore } from './useAuthStore';

export interface AuthContextType {
  isLoggedIn: boolean;
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
  login: (token: string) => Promise<void>;
  logout: () => void;
  fetchUserDetails: (forceRefresh?: boolean) => Promise<void>;
}

export const useAuth = (): AuthContextType => {
  // Use selectors for reactive properties
  const isLoggedIn = useAuthStore(state => !!state.accessToken);
  const userDetails = useAuthStore(state => state.userDetails);
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

  return {
    isLoggedIn,
    userDetails,
    userRecommendationCount, // Keep for backward compatibility
    userDailyLimit, // Keep for backward compatibility
    isLoadingUserDetails,
    userDetailsError,
    isAuthenticating,
    login: store.login,
    logout: store.logout,
    fetchUserDetails: (forceRefresh?: boolean) =>
      store.fetchUserDetails(forceRefresh ?? false),
  };
};
