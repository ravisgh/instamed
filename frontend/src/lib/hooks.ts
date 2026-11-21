"use client";

import { useEffect, useState, useSyncExternalStore } from "react";

/** The value, but only after it stopped changing for `delay` ms (for search-as-you-type). */
export function useDebounced<T>(value: T, delay = 250): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

const PINCODE_KEY = "instamed.pincode";
const listeners = new Set<() => void>();

function readPincode(): string {
  try {
    return window.localStorage.getItem(PINCODE_KEY) ?? "";
  } catch {
    return "";
  }
}

/** The customer's pincode, remembered in localStorage and shared by every component. */
export function usePincode(): [string, (value: string) => void] {
  const pincode = useSyncExternalStore(
    (onChange) => {
      listeners.add(onChange);
      return () => listeners.delete(onChange);
    },
    readPincode,
    () => "", // server render: unknown until the browser takes over
  );
  const setPincode = (value: string) => {
    try {
      window.localStorage.setItem(PINCODE_KEY, value);
    } catch {
      // storage blocked: the value still updates below for this page view
    }
    listeners.forEach((notify) => notify());
  };
  return [pincode, setPincode];
}
