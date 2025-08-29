import React, { createContext, useState, useEffect, useCallback } from 'react';
import { recommendationApi } from '../services/api';

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
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('accessToken') ? true : false;
    }
    return false;
  });
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
        // logout();
      }
    } else {
      setUserRecommendationCount(null);
      setUserDailyLimit(null);
    }
  }, [isLoggedIn]);

  useEffect(() => {
    fetchUserDetails();
  }, [fetchUserDetails]);

  const login = useCallback(
    async (token: string) => {
      localStorage.setItem('accessToken', token);
      setIsLoggedIn(true);
      await fetchUserDetails(); // Fetch user details immediately after login
    },
    [fetchUserDetails]
  );

  const logout = useCallback(() => {
    localStorage.removeItem('accessToken');
    setIsLoggedIn(false);
    setUserRecommendationCount(null);
    setUserDailyLimit(null);
  }, []);

  useEffect(() => {
    const handleStorageChange = () => {
      const newLoggedInStatus = localStorage.getItem('accessToken')
        ? true
        : false;
      if (newLoggedInStatus !== isLoggedIn) {
        setIsLoggedIn(newLoggedInStatus);
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }, [isLoggedIn]);

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
