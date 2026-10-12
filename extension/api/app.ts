import { Hono } from 'hono';
import {
  isFeedback,
  pagePath,
  QUEUE_TO,
  QUEUEABLE,
  statusOf,
  validPage,
  type Batch,
  type Highlight,
  type HighlightRef,
} from './types';
import { nameForKey } from './keys';
import { pageKeyOf, readAll, readBatches, updateBatches, updatePage } from './store';

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
          // The status, Claude's response and the batch belong to the server, so
          // whatever the browser sends for them is replaced. A new comment waits
          // until somebody queues it.
          if (!old) byId.set(h.id, { ...h, status: 'new', batch: undefined, claudeResponse: '', respondedAt: undefined });
          else if (old.updatedAt < h.updatedAt) {
            // A changed comment is new feedback, so it has to be queued again,
            // and it leaves the batch that addressed the words it used to say.
            const reopened =
              h.note !== old.note
                ? { status: 'new' as const, batch: undefined, claudeResponse: '', respondedAt: undefined }
                : {};
            byId.set(h.id, { ...old, color: h.color, note: h.note, updatedAt: h.updatedAt, ...reopened });
          }
        }
        return [...byId.values()];
      }),
    ),
  );
  return c.json(await readAll());
});

// Every batch of work that has been asked for, newest first. The extension shows
// this as its own list, so a reader can see what is waiting, what Claude is on
// now, and what each finished batch did.
app.get('/batches', async (c) => c.json((await readBatches()).reverse()));

// Asks for a batch of comments to be addressed. This is the one status change
// the extension makes: it makes a batch, moves each comment to 'queued' and
// writes the batch's number on it. The worker takes one batch at a time, oldest
// first, so a batch asked for now waits for the batch before it to finish. Only
// a comment that is waiting or has failed can be queued; anything else is left
// alone and counted as skipped, so pressing the button twice queues nothing the
// second time.
app.post('/queue', async (c) => {
  const { refs = [] } = await c.req.json<{ refs: HighlightRef[] }>();
  if (!refs.every(validPage)) return c.json({ error: 'Bad book, chapter or page' }, 400);
  if (!refs.length) return c.json({ batch: null, queued: 0, skipped: 0 });

  // The record is written before any comment is stamped with its number, so a
  // comment can never end up queued into a batch that does not exist. The size
  // and the pages are what was asked for, and they are corrected below once the
  // comments say how much of it could be queued.
  const asked: Omit<Batch, 'number'> = {
    status: 'waiting',
    size: refs.length,
    pages: [...new Set(refs.map(pagePath))].sort(),
    askedBy: c.get('name'),
    createdAt: Date.now(),
    attempts: 0,
    summary: [],
  };
  // The number is one more than the highest ever given out, and it is worked out
  // inside the change so that a second request writing at the same moment makes
  // the write fail and the number be worked out again on the new list.
  let number = 0;
  await updateBatches((items) => {
    number = Math.max(0, ...items.map((b) => b.number)) + 1;
    return [...items, { ...asked, number }];
  });

  // Grouped by page, so each page file is read and written once.
  const wantedByPage = new Map<string, Set<string>>();
  for (const r of refs) {
    const key = pageKeyOf(r);
    wantedByPage.set(key, (wantedByPage.get(key) ?? new Set()).add(r.id));
  }

  const written = await Promise.all(
    [...wantedByPage].map(([key, wanted]) =>
      updatePage(key, (items) =>
        items.map((h) => {
          // A highlight with no comment asks nothing, so it cannot be queued.
          if (!wanted.has(h.id) || !QUEUEABLE.includes(statusOf(h)) || !isFeedback(h)) return h;
          // Asking is a fresh start, so a comment that failed before loses the
          // message from the run that failed. The reader then sees it waiting
          // rather than failed.
          return { ...h, status: QUEUE_TO, batch: number, claudeResponse: '', respondedAt: undefined };
        }),
      ),
    ),
  );
  // Which comments went in is read back from the pages as they were written,
  // not counted while writing them. The number is new, so a comment carrying it
  // is one this request queued and nothing else.
  const queued = written.flat().filter((h) => h.batch === number);

  // Now the record can say how large the batch really is. A press that queued
  // nothing leaves no batch at all, so the list is not filled with empty ones.
  await updateBatches((items) =>
    queued.length
      ? items.map((b) =>
          b.number === number
            ? { ...b, size: queued.length, pages: [...new Set(queued.map(pagePath))].sort() }
            : b,
        )
      : items.filter((b) => b.number !== number),
  );

  return c.json({
    batch: queued.length ? number : null,
    queued: queued.length,
    skipped: refs.length - queued.length,
  });
});
