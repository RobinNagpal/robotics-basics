import { storage } from '#imports';
import type { Batch, Highlight, LocalHighlight } from './types';

// The browser holds the real copy. The server is a backup that the background
// script keeps in step with it.
export const highlights = storage.defineItem<Record<string, LocalHighlight>>('local:highlights', {
  fallback: {},
});
// The batches of work that have been asked for, newest first. These belong to
// the server: a batch is made when the popup asks for one, and the worker writes
// what became of it. The browser only keeps the last copy it was given, so the
// list of batches can be shown without waiting for a request.
export const batches = storage.defineItem<Batch[]>('local:batches', { fallback: [] });
// The server's URL and the API key the user typed in, and the name the server
// gave the key.
export const apiUrl = storage.defineItem<string | null>('local:apiUrl', { fallback: null });
export const apiKey = storage.defineItem<string | null>('local:apiKey', { fallback: null });
export const user = storage.defineItem<string | null>('local:user', { fallback: null });
export const lastSync = storage.defineItem<{ at: number; error?: string } | null>('local:lastSync', {
  fallback: null,
});
// The highlight the reader asked to be taken to. The popup writes it and then
// sends the tab to the page; the content script scrolls to that highlight once
// it has drawn it, and clears this. The time is kept so that an old request,
// left behind because the page never loaded, is ignored rather than acted on
// much later.
export const focused = storage.defineItem<{ id: string; at: number } | null>('local:focused', {
  fallback: null,
});

export async function save(h: Highlight) {
  const all = await highlights.getValue();
  all[h.id] = { ...h, updatedAt: Date.now(), dirty: true };
  await highlights.setValue(all);
}

export async function remove(id: string) {
  await removeMany([id]);
}

// Deleting several comments at once writes the store once, so the background
// script sends one sync for the lot rather than one for each.
export async function removeMany(ids: string[]) {
  const all = await highlights.getValue();
  for (const id of ids) {
    if (all[id]) all[id] = { ...all[id], updatedAt: Date.now(), deleted: true, dirty: true };
  }
  await highlights.setValue(all);
}

export const visible = (all: Record<string, LocalHighlight>) =>
  Object.values(all).filter((h) => !h.deleted);

// docs.dodao.io/<book>/<chapter>/<page>/. A chapter with one page has no third part.
export function pageKey(url: string) {
  const [book = '', chapter = '', page = chapter] = new URL(url).pathname.split('/').filter(Boolean);
  return { book, chapter, page };
}
