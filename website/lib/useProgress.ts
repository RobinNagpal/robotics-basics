'use client';

import { useEffect, useState } from 'react';
import { getLast, getVisited, onProgressChange, type LastRead } from './progress';

/** Visited section URLs, updated live. Empty until mounted, so server and client HTML match. */
export function useVisited(): Record<string, number> {
  const [visited, setVisited] = useState<Record<string, number>>({});
  useEffect(() => {
    const update = () => setVisited(getVisited());
    update();
    return onProgressChange(update);
  }, []);
  return visited;
}

export function useLastRead(): LastRead | undefined {
  const [last, setLast] = useState<LastRead | undefined>();
  useEffect(() => {
    const update = () => setLast(getLast());
    update();
    return onProgressChange(update);
  }, []);
  return last;
}
