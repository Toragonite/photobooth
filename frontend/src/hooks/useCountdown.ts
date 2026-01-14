import { useState, useCallback, useRef, useEffect } from "react";

interface UseCountdownOptions {
  onComplete?: () => void;
  onTick?: (remaining: number) => void;
  autoStart?: boolean;
  interval?: number;
}

interface UseCountdownReturn {
  count: number;
  isRunning: boolean;
  isComplete: boolean;
  start: (from?: number) => void;
  pause: () => void;
  resume: () => void;
  reset: () => void;
}

export function useCountdown(
  initialValue: number,
  options: UseCountdownOptions = {},
): UseCountdownReturn {
  const {
    onComplete,
    onTick,
    autoStart = false,
    interval = 1000,
  } = options;

  const [count, setCount] = useState(initialValue);
  const [isRunning, setIsRunning] = useState(autoStart);
  const [isComplete, setIsComplete] = useState(false);

  const intervalRef = useRef<number | null>(null);
  const initialValueRef = useRef(initialValue);
  const onCompleteRef = useRef(onComplete);
  const onTickRef = useRef(onTick);

  // Keep refs updated
  onCompleteRef.current = onComplete;
  onTickRef.current = onTick;

  const clearTimer = useCallback(() => {
    if (intervalRef.current !== null) {
      window.clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const start = useCallback(
    (from?: number) => {
      const startValue = from ?? initialValueRef.current;
      setCount(startValue);
      setIsComplete(false);
      setIsRunning(true);
    },
    [],
  );

  const pause = useCallback(() => {
    setIsRunning(false);
  }, []);

  const resume = useCallback(() => {
    if (!isComplete && count > 0) {
      setIsRunning(true);
    }
  }, [isComplete, count]);

  const reset = useCallback(() => {
    clearTimer();
    setCount(initialValueRef.current);
    setIsRunning(false);
    setIsComplete(false);
  }, [clearTimer]);

  // Handle countdown logic
  useEffect(() => {
    if (!isRunning) {
      clearTimer();
      return;
    }

    intervalRef.current = window.setInterval(() => {
      setCount((prevCount) => {
        const newCount = prevCount - 1;

        if (newCount <= 0) {
          setIsRunning(false);
          setIsComplete(true);
          onCompleteRef.current?.();
          return 0;
        }

        onTickRef.current?.(newCount);
        return newCount;
      });
    }, interval);

    return clearTimer;
  }, [isRunning, interval, clearTimer]);

  // Cleanup on unmount
  useEffect(() => {
    return clearTimer;
  }, [clearTimer]);

  return {
    count,
    isRunning,
    isComplete,
    start,
    pause,
    resume,
    reset,
  };
}
