'use client';

// Reading progress, kept in this browser only.
//
// Nothing here goes to a server, which is why the site can stay a set of static
// files. The cost is that your progress does not follow you to another browser or
// another machine, and clearing site data loses it.
//
// The store is version 2. Version 1 counted a page as read the moment you opened
// it, so its records cannot be translated into the depths this version keeps: a
// page it called read might have been open for one second. Rather than guess, this
// version starts from nothing and leaves the old key where it is.

const KEY = 'rd-progress-v2';
const EVENT = 'rd-progress';

/**
 * How much of a page has to be read before it counts as read.
 *
 * It is not 100 per cent, because the end of a page is a list of links to other
 * pages, and nobody reads those in order before moving on. Four fifths means you
 * reached the end of the prose.
 */
export const READ_AT = 0.8;

export type LastRead = { url: string; title: string; book: string; chapter: string; at: number };

type Store = {
  /** url -> when it passed READ_AT. */
  read: Record<string, number>;
  /** url -> the most of it ever read, from 0 to 1. */
  depth: Record<string, number>;
  last?: LastRead;
};

const EMPTY: Store = { read: {}, depth: {} };

function load(): Store {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return { ...EMPTY };
    const parsed = JSON.parse(raw) as Partial<Store>;
    // A stored file can be anything at all, including something another version of
    // this site wrote, so each field is checked rather than trusted.
    return {
      read: typeof parsed.read === 'object' && parsed.read ? parsed.read : {},
      depth: typeof parsed.depth === 'object' && parsed.depth ? parsed.depth : {},
      last: parsed.last,
    };
  } catch {
    // Private windows and blocked storage both throw, and so does half-written JSON.
    return { ...EMPTY };
  }
}

function save(store: Store) {
  try {
    localStorage.setItem(KEY, JSON.stringify(store));
  } catch {}
  window.dispatchEvent(new Event(EVENT));
}

/**
 * Remember that this page was opened, so "continue reading" can offer it again.
 *
 * Opening a page says nothing about whether it was read, so this does not touch
 * the depth or the read mark. That is what `saveDepth` is for.
 */
export function markOpened(entry: Omit<LastRead, 'at'>) {
  const store = load();
  store.last = { ...entry, at: Date.now() };
  save(store);
}

/**
 * Record how much of a page has been read, if it is more than before.
 *
 * The depth only ever grows, so coming back to a page you half read and leaving
 * again at the top does not undo the half you read. A page that reaches `READ_AT`
 * is marked read once and keeps that mark.
 */
export function saveDepth(url: string, depth: number) {
  const store = load();
  const best = Math.max(store.depth[url] ?? 0, Math.min(1, depth));
  if (best === (store.depth[url] ?? 0) && (best < READ_AT || store.read[url])) return;
  store.depth[url] = best;
  if (best >= READ_AT && !store.read[url]) store.read[url] = Date.now();
  save(store);
}

/** url -> when it was read. Only pages that passed READ_AT are in here. */
export function getRead(): Record<string, number> {
  return load().read;
}

/** url -> how much of it has been read, from 0 to 1. */
export function getDepth(): Record<string, number> {
  return load().depth;
}

export function getLast(): LastRead | undefined {
  return load().last;
}

export function resetProgress() {
  save({ ...EMPTY, read: {}, depth: {} });
}

export function onProgressChange(fn: () => void): () => void {
  window.addEventListener(EVENT, fn);
  // `storage` fires when another tab writes, so two open tabs agree.
  window.addEventListener('storage', fn);
  return () => {
    window.removeEventListener(EVENT, fn);
    window.removeEventListener('storage', fn);
  };
}
