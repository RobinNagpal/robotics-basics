import { Hono } from 'hono';
import {
  isFeedback,
  QUEUE_TO,
  QUEUEABLE,
  statusOf,
  validPage,
  type Highlight,
  type HighlightRef,
} from './types';
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

  const pages = new Map<string, { upserts: Highlight[]; deletes: Set<string> }>();
  const slot = (k: string) => pages.get(k) ?? pages.set(k, { upserts: [], deletes: new Set() }).get(k)!;
  for (const h of upserts) slot(pageKeyOf(h)).upserts.push({ ...h, author: c.get('name') });
  for (const d of deletes) slot(pageKeyOf(d)).deletes.add(d.id);

  await Promise.all(
    [...pages].map(([key, change]) =>
      updatePage(key, (items) => {
        const byId = new Map(items.filter((h) => !change.deletes.has(h.id)).map((h) => [h.id, h]));
        for (const h of change.upserts) {
          const old = byId.get(h.id);
          // The status and Claude's response belong to the server, so whatever
          // the browser sends for them is replaced. A new comment waits until
          // somebody queues it.
          if (!old) byId.set(h.id, { ...h, status: 'new', attempts: 0, claudeResponse: '', respondedAt: undefined });
          else if (old.updatedAt < h.updatedAt) {
            // A changed comment is new feedback, so it has to be queued again.
            const reopened =
              h.note !== old.note ? { status: 'new' as const, attempts: 0, claudeResponse: '', respondedAt: undefined } : {};
            byId.set(h.id, { ...old, color: h.color, note: h.note, updatedAt: h.updatedAt, ...reopened });
          }
        }
        return [...byId.values()];
      }),
    ),
  );
  return c.json(await readAll());
});

// Asks for a batch of comments to be addressed. This is the one status change
// the extension makes: it moves a comment to 'queued', and the feedback worker
// takes every queued comment on its next run. Only a comment that is waiting or
// has failed can be queued; anything else is left alone and counted as skipped,
// so pressing the button twice queues nothing the second time.
app.post('/queue', async (c) => {
  const { refs = [] } = await c.req.json<{ refs: HighlightRef[] }>();
  if (!refs.every(validPage)) return c.json({ error: 'Bad book, chapter or page' }, 400);

  // Grouped by page, so each page file is read and written once.
  const wantedByPage = new Map<string, Set<string>>();
  for (const r of refs) {
    const key = pageKeyOf(r);
    wantedByPage.set(key, (wantedByPage.get(key) ?? new Set()).add(r.id));
  }

  let queued = 0;
  await Promise.all(
    [...wantedByPage].map(([key, wanted]) =>
      updatePage(key, (items) =>
        items.map((h) => {
          // A highlight with no comment asks nothing, so it cannot be queued.
          if (!wanted.has(h.id) || !QUEUEABLE.includes(statusOf(h)) || !isFeedback(h)) return h;
          queued++;
          // Asking is a fresh start, so a comment that failed before gets its
          // full count of tries back and loses the message from the run that
          // failed. The reader then sees it waiting rather than failed.
          return { ...h, status: QUEUE_TO, attempts: 0, claudeResponse: '', respondedAt: undefined };
        }),
      ),
    ),
  );
  return c.json({ queued, skipped: refs.length - queued });
});
