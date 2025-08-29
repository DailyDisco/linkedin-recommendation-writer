import React, { createContext, useState, useEffect, useCallback } from 'react';
import { recommendationApi } from '../services/api';
import { useLocalStorage } from '../hooks/useLocalStorage';

export interface AuthContextType {
  isLoggedIn: boolean;
  userRecommendationCount: number | null;
  userDailyLimit: number | null;
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

  const fetchUserDetails = useCallback(async () => {
    if (isLoggedIn) {
      try {
        const response = await recommendationApi.getUserDetails();
        setUserRecommendationCount(response.recommendation_count);
        setUserDailyLimit(response.daily_limit);
      } catch (error) {
        console.error('Failed to fetch user details:', error);
        // Optionally log out if fetching details fails (e.g., token expired)
        logout();
      }
    } else {
      setUserRecommendationCount(null);
      setUserDailyLimit(null);
    }
  }, [isLoggedIn, logout]);

  useEffect(() => {
    fetchUserDetails();
  }, [fetchUserDetails]);

  const login = useCallback(
    async (token: string) => {
      setAccessToken(token);
      await fetchUserDetails(); // Fetch user details immediately after login
    },
    [setAccessToken, fetchUserDetails]
  );

  const logout = useCallback(() => {
    setAccessToken(null);
    setUserRecommendationCount(null);
    setUserDailyLimit(null);
  }, [setAccessToken]);

  return (
    <AuthContext.Provider
      value={{
        isLoggedIn,
        userRecommendationCount,
        userDailyLimit,
        login,
        logout,
        fetchUserDetails,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
