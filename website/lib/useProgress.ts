'use client';

import { useEffect, useState } from 'react';
import { getDepth, getLast, getRead, onProgressChange, type LastRead } from './progress';

/**
 * The pages that have been read, updated live.
 *
 * Empty until the component has mounted, so that the HTML the server built and the
 * HTML the browser first draws are the same. Storage is not readable while the page
 * is being built, and a mismatch here would make React discard the page and draw it
 * again.
 */
export function useRead(): Record<string, number> {
  const [read, setRead] = useState<Record<string, number>>({});
  useEffect(() => {
    const update = () => setRead(getRead());
    update();
    return onProgressChange(update);
  }, []);
  return read;
}

/** How much of each page has been read, from 0 to 1, for the pages that were started. */
export function useDepth(): Record<string, number> {
  const [depth, setDepth] = useState<Record<string, number>>({});
  useEffect(() => {
    const update = () => setDepth(getDepth());
    update();
    return onProgressChange(update);
  }, []);
  return depth;
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
