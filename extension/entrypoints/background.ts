import { apiKey, apiUrl, highlights, lastSync } from '@/lib/store';
import type { Highlight, LocalHighlight } from '@/lib/types';

export default defineBackground(() => {
  browser.alarms.create('sync', { periodInMinutes: 1 });
  browser.alarms.onAlarm.addListener(() => sync());
  browser.runtime.onMessage.addListener((msg) => {
    if (msg === 'sync') return sync();
  });

  // Push local edits soon after they happen.
  let timer: ReturnType<typeof setTimeout>;
  highlights.watch((all) => {
    if (Object.values(all).some((h) => h.dirty)) {
      clearTimeout(timer);
      timer = setTimeout(sync, 1500);
    }
  });
  sync();
});

let running = false;

async function sync() {
  const [url, key] = [await apiUrl.getValue(), await apiKey.getValue()];
  if (running || !url || !key) return;
  running = true;
  try {
    const sent = await highlights.getValue();
    const dirty = Object.values(sent).filter((h) => h.dirty);
    const res = await fetch(`${url}/sync`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        upserts: dirty.filter((h) => !h.deleted).map(({ dirty, deleted, ...h }) => h),
        deletes: dirty.filter((h) => h.deleted).map(({ id, book, chapter, page }) => ({ id, book, chapter, page })),
      }),
    });
    // A key removed on the server stops working here too. The popup then shows the
    // error, and the user signs out and enters a new key.
    if (res.status === 401) throw new Error('The server no longer accepts this API key');
    if (!res.ok) throw new Error(`Server answered ${res.status}`);
    const server: Highlight[] = await res.json();

    // Merge into whatever the browser holds now, which may have changed while
    // the request was out. An item edited during the request keeps its local
    // version. Otherwise the server's copy wins, and an item the server no
    // longer has is gone: either our delete went through or it was deleted there.
    const now = await highlights.getValue();
    const byId = new Map(server.map((h) => [h.id, h]));
    const next: Record<string, LocalHighlight> = {};
    for (const id of new Set([...Object.keys(now), ...byId.keys()])) {
      const local = now[id];
      if (local && local.updatedAt !== sent[id]?.updatedAt) next[id] = local;
      else if (byId.has(id)) next[id] = byId.get(id)!;
    }
    await highlights.setValue(next);
    await lastSync.setValue({ at: Date.now() });
  } catch (e) {
    await lastSync.setValue({ at: Date.now(), error: String((e as Error).message ?? e) });
  } finally {
    running = false;
  }
}
