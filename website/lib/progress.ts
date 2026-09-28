'use client';

// Reading progress, kept in this browser only.

const KEY = 'rd-progress-v1';
const EVENT = 'rd-progress';

export type LastRead = { url: string; title: string; book: string; chapter: string; at: number };
type Store = { visited: Record<string, number>; last?: LastRead };

function read(): Store {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) return JSON.parse(raw) as Store;
  } catch {}
  return { visited: {} };
}

function write(store: Store) {
  try {
    localStorage.setItem(KEY, JSON.stringify(store));
  } catch {}
  window.dispatchEvent(new Event(EVENT));
}

export function markVisited(entry: Omit<LastRead, 'at'>) {
  const store = read();
  const at = Date.now();
  store.visited[entry.url] = at;
  store.last = { ...entry, at };
  write(store);
}

export function getVisited(): Record<string, number> {
  return read().visited;
}

export function getLast(): LastRead | undefined {
  return read().last;
}

export function resetProgress() {
  write({ visited: {} });
}

export function onProgressChange(fn: () => void): () => void {
  window.addEventListener(EVENT, fn);
  window.addEventListener('storage', fn);
  return () => {
    window.removeEventListener(EVENT, fn);
    window.removeEventListener('storage', fn);
  };
}
