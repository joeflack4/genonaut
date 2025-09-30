/**
 * Hook for managing state that persists in localStorage
 */

import { useState, useEffect, useCallback } from 'react';

export function usePersistedState<T>(
  key: string,
  defaultValue: T,
  serializer: {
    serialize: (value: T) => string;
    deserialize: (value: string) => T;
  } = {
    serialize: JSON.stringify,
    deserialize: JSON.parse,
  }
): [T, (value: T) => void] {
  // State to store our value
  const [state, setState] = useState<T>(() => {
    try {
      // Get from local storage by key
      const item = window.localStorage.getItem(key);
      // Parse stored json or if none return defaultValue
      return item ? serializer.deserialize(item) : defaultValue;
    } catch (error) {
      // If error also return defaultValue
      console.warn(`Error reading localStorage key "${key}":`, error);
      return defaultValue;
    }
  });

  // Return a wrapped version of useState's setter function that ...
  // ... persists the new value to localStorage.
  const setValue = useCallback(
    (value: T) => {
      try {
        // Allow value to be a function so we have same API as useState
        const valueToStore = value instanceof Function ? value(state) : value;
        // Save state
        setState(valueToStore);
        // Save to local storage
        window.localStorage.setItem(key, serializer.serialize(valueToStore));
      } catch (error) {
        // A more advanced implementation would handle the error case
        console.warn(`Error setting localStorage key "${key}":`, error);
      }
    },
    [key, serializer, state]
  );

  return [state, setValue];
}

// Specialized hook for persisting Set<string> objects
export function usePersistedSetState(
  key: string,
  defaultValue: Set<string> = new Set()
): [Set<string>, (value: Set<string>) => void] {
  return usePersistedState(
    key,
    defaultValue,
    {
      serialize: (set: Set<string>) => JSON.stringify(Array.from(set)),
      deserialize: (str: string) => new Set(JSON.parse(str)),
    }
  );
}