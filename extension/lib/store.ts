import { storage } from '#imports';
import type { Highlight, LocalHighlight } from './types';

// The browser holds the real copy. The server is a backup that the background
// script keeps in step with it.
export const highlights = storage.defineItem<Record<string, LocalHighlight>>('local:highlights', {
  fallback: {},
});
export const user = storage.defineItem<string | null>('local:user', { fallback: null });
export const lastSync = storage.defineItem<{ at: number; error?: string } | null>('local:lastSync', {
  fallback: null,
});

export async function save(h: Highlight) {
  const all = await highlights.getValue();
  all[h.id] = { ...h, updatedAt: Date.now(), dirty: true };
  await highlights.setValue(all);
}

export async function remove(id: string) {
  const all = await highlights.getValue();
  if (all[id]) all[id] = { ...all[id], updatedAt: Date.now(), deleted: true, dirty: true };
  await highlights.setValue(all);
}

export const visible = (all: Record<string, LocalHighlight>) =>
  Object.values(all).filter((h) => !h.deleted);

// docs.dodao.io/<book>/<chapter>/<page>/. A chapter with one page has no third part.
export function pageKey(url: string) {
  const [book = '', chapter = '', page = chapter] = new URL(url).pathname.split('/').filter(Boolean);
  return { book, chapter, page };
}
