import { Hono } from 'hono';
import { validPage, type Highlight, type HighlightRef } from '../lib/types';
import { nameForKey } from './keys';
import { pageKeyOf, readAll, updatePage } from './store';

export const app = new Hono<{ Variables: { name: string } }>();

// The extension sends the API key the user typed in, as a bearer token. The
// server answers 401 unless the key is one of the keys it holds.
app.use(async (c, next) => {
  const key = (c.req.header('Authorization') ?? '').replace(/^Bearer\s+/i, '').trim();
  const name = await nameForKey(key);
  if (!name) return c.json({ error: 'Unknown API key' }, 401);
  c.set('name', name);
  await next();
});

// The popup calls this when a key is typed in, to check it and learn whose it is.
app.get('/me', (c) => c.json({ name: c.get('name') }));

// One round trip: apply the browser's changes, then return everything.
// An upsert only replaces a stored comment that was last changed earlier.
app.post('/sync', async (c) => {
  const { upserts = [], deletes = [] } = await c.req.json<{ upserts: Highlight[]; deletes: HighlightRef[] }>();
  if (![...upserts, ...deletes].every(validPage)) return c.json({ error: 'Bad book, chapter or page' }, 400);

  // Group the changes by page, so each page file is read and written once.
  const byPage = new Map<string, { upserts: Highlight[]; deletes: Set<string> }>();
  const slot = (k: string) => byPage.get(k) ?? byPage.set(k, { upserts: [], deletes: new Set() }).get(k)!;
  for (const h of upserts) slot(pageKeyOf(h)).upserts.push({ ...h, author: c.get('name') });
  for (const d of deletes) slot(pageKeyOf(d)).deletes.add(d.id);

  await Promise.all(
    [...byPage].map(([key, change]) =>
      updatePage(key, (items) => {
        const byId = new Map(items.filter((h) => !change.deletes.has(h.id)).map((h) => [h.id, h]));
        for (const h of change.upserts) {
          const old = byId.get(h.id);
          if (!old) byId.set(h.id, h);
          else if (old.updatedAt < h.updatedAt) byId.set(h.id, { ...old, color: h.color, note: h.note, updatedAt: h.updatedAt });
        }
        return [...byId.values()];
      }),
    ),
  );
  return c.json(await readAll());
});
