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
  const store = useAuthStore();

  return {
    isLoggedIn: store.isLoggedIn,
    userRecommendationCount: store.userRecommendationCount,
    userDailyLimit: store.userDailyLimit,
    isLoadingUserDetails: store.isLoadingUserDetails,
    userDetailsError: store.userDetailsError,
    isAuthenticating: store.isAuthenticating,
    login: store.login,
    logout: store.logout,
    fetchUserDetails: store.fetchUserDetails,
  };
};
