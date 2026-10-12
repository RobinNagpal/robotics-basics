import { pageKeyOf, readAll, readBatches, updateBatches, updatePage } from '../api/store';
import {
  isFeedback,
  isOpen,
  MAX_ATTEMPTS,
  statusOf,
  type Batch,
  type BatchStatus,
  type FeedbackStatus,
  type Highlight,
} from '../api/types';

// The statuses a run takes work from. 'queued' is what the popup's "Address
// feedback" button writes. 'working' is picked up as well, because only one run
// uses the session at a time, so a comment still marked 'working' when a run
// starts was left there by a run that died before it could record an outcome.
const TAKEABLE: FeedbackStatus[] = ['queued', 'working'];

// Everything these functions need from wherever the comments are kept. The real
// one is the S3 store the API uses, and it is the default, so the worker calls
// every function here without mentioning it. A test hands in a store held in
// memory instead, which is the only reason this is a parameter and not an
// import: the status changes below are the part worth testing, and S3 is not.
export interface Store {
  pageKeyOf(p: Pick<Highlight, 'book' | 'chapter' | 'page'>): string;
  readAll(): Promise<Highlight[]>;
  updatePage(key: string, change: (items: Highlight[]) => Highlight[]): Promise<Highlight[]>;
  readBatches(): Promise<Batch[]>;
  updateBatches(change: (items: Batch[]) => Batch[]): Promise<Batch[]>;
}

const s3: Store = { pageKeyOf, readAll, updatePage, readBatches, updateBatches };

// The batch a run should work on: the oldest one the worker has not finished
// with. This is what makes batches wait for each other. A batch left 'working'
// by a run that died is the oldest unfinished one, so it is taken again before
// anything newer, and the work a reader asked for first is never overtaken.
export async function nextBatch(store: Store = s3): Promise<Batch | null> {
  const open = (await store.readBatches()).filter(isOpen).sort((a, b) => a.number - b.number);
  return open[0] ?? null;
}

// The comments of one batch that still need work, oldest first. Each comment
// carries its batch number, and that is what says which comments belong to the
// run, rather than anything in the batch record. A highlight with no comment
// marks text but asks nothing, so it is left alone.
export async function batchFeedback(batch: Batch, store: Store = s3): Promise<Highlight[]> {
  return (await store.readAll())
    .filter((h) => h.batch === batch.number && isFeedback(h) && TAKEABLE.includes(statusOf(h)))
    .sort((a, b) => a.createdAt - b.createdAt);
}

// Marks the batch record 'working' and counts one try against it. The count is
// raised here rather than when a run ends, so that a run killed part-way still
// spends a try and a batch that somehow kills every run runs out of them. What
// comes back is how many tries the batch has now had, including this one.
export async function startBatch(batch: Batch, store: Store = s3): Promise<number> {
  let attempts = batch.attempts + 1;
  await store.updateBatches((items) =>
    items.map((b) => {
      if (b.number !== batch.number || !isOpen(b)) return b;
      attempts = b.attempts + 1;
      return { ...b, status: 'working' as const, startedAt: Date.now(), attempts, summary: [] };
    }),
  );
  return attempts;
}

// Writes where a batch ended up, and the one or two lines that say what it did.
// It writes only while the batch is one the worker has not finished with, so an
// outcome can never be written over a batch that is already done or given up on.
export async function finishBatch(
  batch: Batch,
  status: BatchStatus,
  summary: string[],
  store: Store = s3,
): Promise<void> {
  const ended = status === 'done' || status === 'failed';
  await store.updateBatches((items) =>
    items.map((b) =>
      b.number === batch.number && isOpen(b)
        ? { ...b, status, summary, ...(ended ? { endedAt: Date.now() } : {}) }
        : b,
    ),
  );
}

// Marks a batch's comments 'working', which is the last thing that happens
// before Claude Code is invoked. It writes a comment only while that comment is
// still there, still waiting, and still says what the run read, so a comment
// edited or deleted in the moment between is dropped from the batch rather than
// worked on from stale text. What comes back is the batch as it will be given to
// Claude.
export async function claim(comments: Highlight[], store: Store = s3): Promise<Highlight[]> {
  const claimed: Highlight[] = [];
  for (const [key, group] of byPage(comments, store)) {
    const mine = new Map(group.map((h) => [h.id, h]));
    const written = await store.updatePage(key, (items) =>
      items.map((x) => {
        const h = mine.get(x.id);
        if (!h || x.note !== h.note || !TAKEABLE.includes(statusOf(x))) return x;
        return { ...x, status: 'working' };
      }),
    );
    // What was taken is read back from the page as it was written, because the
    // change above runs again whenever S3 refuses the write, and a list built
    // inside it would hold the same comment twice.
    for (const x of written) {
      const h = mine.get(x.id);
      if (h && x.note === h.note && statusOf(x) === 'working') claimed.push(h);
    }
  }
  return claimed.sort((a, b) => a.createdAt - b.createdAt);
}

// Hands a claimed batch back after the run that took it failed. Each comment
// goes to 'queued' again, so the very next run takes the same batch and the
// failure costs a wait rather than the work. Once the batch has used up its
// tries the comments are marked 'failed' instead, with the reason, so that
// something nothing can address stops being retried and stops holding up the
// batches behind it; a reader can still select those comments in the extension
// and ask again, which makes a new batch with a fresh count. The write is
// conditional in the same way as every other write here, so a comment edited
// while the run ran keeps the edit and stays out of the queue.
export async function giveBack(comments: Highlight[], reason: string, tries: number, store: Store = s3) {
  const again = tries < MAX_ATTEMPTS;
  const retrying: Highlight[] = [];
  const givenUp: Highlight[] = [];
  for (const [key, group] of byPage(comments, store)) {
    const mine = new Map(group.map((h) => [h.id, h]));
    const written = await store.updatePage(key, (items) =>
      items.map((x) => {
        const h = mine.get(x.id);
        if (!h || x.note !== h.note || statusOf(x) !== 'working') return x;
        if (again) return { ...x, status: 'queued' as const };
        return {
          ...x,
          status: 'failed' as const,
          claudeResponse: `${reason}\nThis was tried ${tries} times. Select it in the extension to ask again.`,
          respondedAt: Date.now(),
        };
      }),
    );
    // Which comments went which way is read back from the page as it was
    // written, for the same reason as in claim above.
    for (const x of written) {
      const h = mine.get(x.id);
      if (!h || x.note !== h.note) continue;
      if (statusOf(x) === 'queued') retrying.push(h);
      else if (statusOf(x) === 'failed') givenUp.push(h);
    }
  }
  return { retrying, givenUp };
}

// Writes the outcome into the comment's page file, with the same conditional
// write the API uses, so a sync that happens at the same moment is not lost. It
// writes only while the comment is still there, still 'working' and still says
// what Claude was shown. A comment edited while Claude worked on it is left as
// the edit made it, which is 'new', so the reader can ask for the new text again.
export async function record(
  h: Highlight,
  status: FeedbackStatus,
  claudeResponse: string,
  store: Store = s3,
) {
  let written = false;
  await store.updatePage(store.pageKeyOf(h), (items) =>
    items.map((x) => {
      if (x.id !== h.id || x.note !== h.note || statusOf(x) !== 'working') return x;
      written = true;
      return { ...x, status, claudeResponse, respondedAt: Date.now() };
    }),
  );
  return written;
}

// The comments of one batch, grouped into the page files that hold them, so each
// file is read and written once.
export function byPage(comments: Highlight[], store: Store = s3): Map<string, Highlight[]> {
  const pages = new Map<string, Highlight[]>();
  for (const h of comments) {
    const key = store.pageKeyOf(h);
    pages.set(key, [...(pages.get(key) ?? []), h]);
  }
  return pages;
}
