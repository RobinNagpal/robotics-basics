import { pageKeyOf, readAll, updatePage } from '../api/store';
import { isFeedback, statusOf, type FeedbackStatus, type Highlight } from '../api/types';

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
  updatePage(key: string, change: (items: Highlight[]) => Highlight[]): Promise<void>;
}

const s3: Store = { pageKeyOf, readAll, updatePage };

// Every comment waiting to be addressed, oldest first. A highlight with no
// comment marks text but asks nothing, so it is left alone.
export async function queuedFeedback(store: Store = s3): Promise<Highlight[]> {
  return (await store.readAll())
    .filter((h) => isFeedback(h) && TAKEABLE.includes(statusOf(h)))
    .sort((a, b) => a.createdAt - b.createdAt);
}

// Marks a batch 'working', which is the last thing that happens before Claude
// Code is invoked. It writes a comment only while that comment is still there,
// still waiting, and still says what the run read, so a comment edited or
// deleted in the moment between is dropped from the batch rather than worked on
// from stale text. What comes back is the batch as it will be given to Claude.
export async function claim(comments: Highlight[], store: Store = s3): Promise<Highlight[]> {
  const claimed: Highlight[] = [];
  for (const [key, group] of byPage(comments, store)) {
    const mine = new Map(group.map((h) => [h.id, h]));
    await store.updatePage(key, (items) =>
      items.map((x) => {
        const h = mine.get(x.id);
        if (!h || x.note !== h.note || !TAKEABLE.includes(statusOf(x))) return x;
        claimed.push(h);
        return { ...x, status: 'working' };
      }),
    );
  }
  return claimed.sort((a, b) => a.createdAt - b.createdAt);
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
