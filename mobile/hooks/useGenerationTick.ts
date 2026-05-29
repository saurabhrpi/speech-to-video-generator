import { useEffect, useState } from 'react';

/**
 * Returns a value that increments every `intervalMs` while the component is
 * mounted. The increment itself isn't read directly — its purpose is to force
 * a re-render so that `Date.now()`-derived UI (countdown labels) refresh.
 *
 * Default tick = 30s. Short enough that "Ready in 4 mins → 3 mins" lands within
 * a minute of the actual transition, long enough that it doesn't keep the JS
 * thread hot when the user is idle on a screen for a while.
 */
export function useGenerationTick(intervalMs: number = 30_000): number {
  const [tick, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);
  return tick;
}
