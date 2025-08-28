import { useState, useEffect, useCallback } from 'react';

const LOCAL_STORAGE_KEY = 'anonRecommendationCount';
const LOCAL_STORAGE_DATE_KEY = 'anonRecommendationDate';

export const useRecommendationCount = () => {
  const [count, setCount] = useState<number>(0);

  useEffect(() => {
    const storedCount = localStorage.getItem(LOCAL_STORAGE_KEY);
    const storedDate = localStorage.getItem(LOCAL_STORAGE_DATE_KEY);
    const today = new Date().toDateString();

    if (storedDate === today && storedCount) {
      setCount(parseInt(storedCount, 10));
    } else {
      // Reset count if it's a new day
      localStorage.setItem(LOCAL_STORAGE_KEY, '0');
      localStorage.setItem(LOCAL_STORAGE_DATE_KEY, today);
      setCount(0);
    }
  }, []);

  const incrementCount = useCallback(() => {
    setCount(prevCount => {
      const newCount = prevCount + 1;
      localStorage.setItem(LOCAL_STORAGE_KEY, newCount.toString());
      localStorage.setItem(LOCAL_STORAGE_DATE_KEY, new Date().toDateString());
      return newCount;
    });
  }, []);

  const resetCount = useCallback(() => {
    localStorage.setItem(LOCAL_STORAGE_KEY, '0');
    localStorage.setItem(LOCAL_STORAGE_DATE_KEY, new Date().toDateString());
    setCount(0);
  }, []);

  return { count, incrementCount, resetCount };
};
