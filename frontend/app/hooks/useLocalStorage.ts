import { useState } from 'react';

type SetValue<T> = (value: T | ((val: T) => T)) => void;

export function useLocalStorage<T>(
  key: string,
  initialValue: T
): [T, SetValue<T>] {
  // State to store our value
  // Pass initial state function to useState so logic is only executed once
  const [storedValue, setStoredValue] = useState<T>(() => {
    if (typeof window === 'undefined') {
      return initialValue;
    }
    try {
      // Get from local storage by key
      const item = window.localStorage.getItem(key);
      // Directly return string items or parse others. Trim and remove quotes if found.
      if (typeof item === 'string' && key === 'accessToken') {
        return item.trim().replace(/^"|"$/g, '') as T;
      }
      const parsedItem = item ? JSON.parse(item) : initialValue;
      return parsedItem;
    } catch (error) {
      // If error also return initialValue
      console.error(error);
      return initialValue;
    }
  });

  // Return a wrapped version of useState's setter function that ...
  // ... persists the new value to localStorage.
  const setValue: SetValue<T> = value => {
    try {
      // Allow value to be a function so we have same API as useState
      const valueToStore =
        value instanceof Function ? value(storedValue) : value;

      let finalValueToStore = valueToStore;
      // If it's the accessToken, store it directly as a cleaned string without JSON.stringify
      if (typeof finalValueToStore === 'string' && key === 'accessToken') {
        finalValueToStore = finalValueToStore.trim().replace(/^"|"$/g, '') as T;
        setStoredValue(finalValueToStore);
        window.localStorage.setItem(key, finalValueToStore as string); // Store raw string
        return;
      }
      // Save state
      setStoredValue(finalValueToStore);
      // Save to local storage
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(key, JSON.stringify(finalValueToStore));
      }
    } catch (error) {
      // A more advanced implementation would handle the error case
      console.error(error);
    }
  };

  return [storedValue, setValue];
}

export * from './useRecommendationCount';
