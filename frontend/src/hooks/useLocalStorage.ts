import { useState, useCallback, useEffect } from "react";

interface UseLocalStorageOptions<T> {
  serializer?: (value: T) => string;
  deserializer?: (value: string) => T;
}

type SetValue<T> = T | ((prev: T) => T);

export function useLocalStorage<T>(
  key: string,
  initialValue: T,
  options: UseLocalStorageOptions<T> = {},
): [T, (value: SetValue<T>) => void, () => void] {
  const {
    serializer = JSON.stringify,
    deserializer = JSON.parse,
  } = options;

  // Get stored value or initial value
  const readValue = useCallback((): T => {
    if (typeof window === "undefined") {
      return initialValue;
    }

    try {
      const item = window.localStorage.getItem(key);
      return item ? deserializer(item) : initialValue;
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  }, [key, initialValue, deserializer]);

  const [storedValue, setStoredValue] = useState<T>(readValue);

  // Set value to localStorage
  const setValue = useCallback(
    (value: SetValue<T>) => {
      if (typeof window === "undefined") {
        console.warn(
          `Tried setting localStorage key "${key}" during SSR`,
        );
        return;
      }

      try {
        const newValue =
          value instanceof Function ? value(storedValue) : value;
        window.localStorage.setItem(key, serializer(newValue));
        setStoredValue(newValue);

        // Dispatch storage event for other tabs/windows
        window.dispatchEvent(
          new StorageEvent("storage", {
            key,
            newValue: serializer(newValue),
          }),
        );
      } catch (error) {
        console.warn(`Error setting localStorage key "${key}":`, error);
      }
    },
    [key, serializer, storedValue],
  );

  // Remove value from localStorage
  const removeValue = useCallback(() => {
    if (typeof window === "undefined") {
      return;
    }

    try {
      window.localStorage.removeItem(key);
      setStoredValue(initialValue);
    } catch (error) {
      console.warn(`Error removing localStorage key "${key}":`, error);
    }
  }, [key, initialValue]);

  // Listen for storage changes from other tabs
  useEffect(() => {
    const handleStorageChange = (event: StorageEvent) => {
      if (event.key === key && event.newValue !== null) {
        try {
          setStoredValue(deserializer(event.newValue));
        } catch {
          setStoredValue(initialValue);
        }
      } else if (event.key === key && event.newValue === null) {
        setStoredValue(initialValue);
      }
    };

    window.addEventListener("storage", handleStorageChange);
    return () => window.removeEventListener("storage", handleStorageChange);
  }, [key, initialValue, deserializer]);

  return [storedValue, setValue, removeValue];
}
