'use client';

import { useEffect, useState } from 'react';
import { getDepth, saveDepth } from './progress';

/**
 * How much of an article a person has actually read.
 *
 * The obvious way to measure this is how far down the page they scrolled, and it
 * is wrong. Dragging the scroll bar to the bottom takes a quarter of a second and
 * would score 100 per cent, so the page would be marked read by somebody who saw
 * none of it. What this measures instead is how long each part of the article
 * spent in front of the reader.
 *
 * The article is cut into bands of equal height. Several times a second the hook
 * asks which bands are on screen, and adds that time to each of them. A band counts
 * as read once it has been on screen for `DWELL_MS` in total, which need not be in
 * one go: looking at a band, scrolling away and coming back adds up. The depth is
 * then the fraction of bands that reached that total.
 *
 * This is what makes a fast scroll score nothing. Flicking from top to bottom gives
 * every band a few tens of milliseconds, far below the threshold, so no band counts
 * and the depth stays where it was.
 */

/** How many pieces the article is cut into. Twenty gives five per cent each. */
const BANDS = 20;

/**
 * How long a band has to be on screen before it counts as read.
 *
 * This is the "human lag" figure, and it is deliberately short. It is not meant to
 * be the time needed to read a band, which depends on how much text is in it and
 * would punish somebody who already knows the material. It is meant to be longer
 * than scrolling past, and a second and a half is many times longer than any band
 * survives during a fast scroll.
 */
const DWELL_MS = 1500;

/** How often to look. Short enough to feel immediate, long enough to cost nothing. */
const TICK_MS = 250;

export function useReadingDepth(url: string, selector = '.prose'): number {
  const [depth, setDepth] = useState(0);

  useEffect(() => {
    const article = document.querySelector(selector);
    if (!(article instanceof HTMLElement)) return;

    // Whatever was read before, so a second visit carries on rather than restarting.
    let best = getDepth()[url] ?? 0;
    setDepth(best);

    const dwell = new Array<number>(BANDS).fill(0);
    let last = Date.now();
    let saved = best;

    const tick = () => {
      const now = Date.now();
      const elapsed = now - last;
      last = now;

      // A tab in the background still runs timers, slowly, and a laptop that was
      // asleep comes back with an enormous gap. Neither is reading, so a tick that
      // is far longer than it should be is dropped rather than credited.
      if (document.hidden || elapsed > TICK_MS * 4) return;

      const box = article.getBoundingClientRect();
      const height = box.height;
      if (height <= 0) return;

      const top = -box.top;                       // how far into the article the viewport starts
      const bottom = top + window.innerHeight;
      const band = height / BANDS;

      let counted = 0;
      for (let i = 0; i < BANDS; i += 1) {
        const start = i * band;
        const end = start + band;
        if (end > top && start < bottom) dwell[i] += elapsed;
        if (dwell[i] >= DWELL_MS) counted += 1;
      }

      const now_depth = counted / BANDS;
      if (now_depth > best) {
        best = now_depth;
        setDepth(best);
        // Writing to storage on every tick would be wasteful, so it waits until the
        // figure has moved by a band or has reached the end.
        if (best - saved >= 1 / BANDS - 1e-9 || best >= 1) {
          saved = best;
          saveDepth(url, best);
        }
      }
    };

    const timer = window.setInterval(tick, TICK_MS);
    // Coming back to the tab should not be credited with the time it was away.
    const wake = () => (last = Date.now());
    document.addEventListener('visibilitychange', wake);
    window.addEventListener('focus', wake);

    // Leaving the page is the last chance to keep what was read on this visit.
    const flush = () => {
      if (best > saved) {
        saved = best;
        saveDepth(url, best);
      }
    };
    window.addEventListener('pagehide', flush);

    return () => {
      window.clearInterval(timer);
      document.removeEventListener('visibilitychange', wake);
      window.removeEventListener('focus', wake);
      window.removeEventListener('pagehide', flush);
      flush();
    };
  }, [url, selector]);

  return depth;
}
