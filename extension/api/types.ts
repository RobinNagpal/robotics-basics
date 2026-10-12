// What the API stores and what the extension sends it. This file belongs to the
// API, so that a change to it redeploys the API; the extension imports it from here.

// Where a comment stands. A comment is made 'new' and nothing happens to it
// until somebody asks for it: selecting comments in the popup and pressing
// "Address feedback" puts them in a batch and makes them 'queued'. The feedback
// worker then takes one whole batch, marks its comments 'working' just before it
// invokes Claude Code, and sets the last three when Claude has finished with
// them: 'changed' when Claude changed the docs, 'answered' when Claude replied
// without changing them, and 'failed' when the run went wrong.
export const STATUSES = ['new', 'queued', 'working', 'changed', 'answered', 'failed'] as const;
export type FeedbackStatus = (typeof STATUSES)[number];

// The statuses a reader may ask to have addressed, and what asking sets them to.
// Everything else is the worker's to write. Queueing is the one status change a
// reader makes, so it is the one the API accepts from the extension. A comment
// that failed is in the list too, because a failure is usually one run that went
// wrong rather than a comment nothing can answer, so asking again is reasonable.
export const QUEUEABLE: FeedbackStatus[] = ['new', 'failed'];
export const QUEUE_TO: FeedbackStatus = 'queued';

// The statuses that mean Claude has finished with a comment and has written a
// reply to it. These are the ones the popup's "Delete done" button removes,
// because the reader has read the reply and no longer needs the comment.
export const DONE: FeedbackStatus[] = ['changed', 'answered'];

// How many runs may try one batch before the worker gives up on it. A run that
// fails puts its whole batch back to 'waiting', so the next run tries it again
// without anybody asking. This number is what stops a batch that fails every
// time from being retried for ever and holding up every batch behind it.
export const MAX_ATTEMPTS = 3;

export interface Highlight {
  id: string;
  book: string;
  chapter: string;
  page: string;
  section: string; // the nearest heading above the text, or '' above the first one
  url: string;
  text: string;
  prefix: string;
  suffix: string;
  color: string;
  note: string;
  author: string; // the name the server gave the API key that wrote it
  createdAt: number;
  updatedAt: number;
  // Written by the API when a comment is made, queued or edited, and by the
  // feedback worker while it works. A sync never carries them in from the browser.
  status?: FeedbackStatus;
  claudeResponse?: string;
  respondedAt?: number;
  // The number of the batch this comment was last put in. The batch is the unit
  // of work, so this is also what says which comments one run addresses: a run
  // takes the comments that point at the batch it is working on. A comment that
  // has never been asked for has no batch number.
  batch?: number;
}

// Where a batch of work stands. A reader's "Address feedback" press makes one
// 'waiting' batch. The worker takes the oldest batch that is not finished, so a
// batch asked for while another is being worked on waits its turn. 'done' means
// the run finished and every comment in it has a reply; 'failed' means the run
// went wrong often enough that the worker gave up on it.
export const BATCH_STATUSES = ['waiting', 'working', 'done', 'failed'] as const;
export type BatchStatus = (typeof BATCH_STATUSES)[number];

// One press of "Address feedback". The record exists so that a reader can see
// where their request stands without reading each comment, and so that Claude
// can say in two lines what the whole batch did. Which comments are in it is not
// stored here: each comment carries the batch number, and that is the one source
// of truth, so a record that lists the wrong size can never send the worker to
// the wrong comments.
export interface Batch {
  number: number; // counts up from 1, and is what the reader sees
  status: BatchStatus;
  size: number; // how many comments were queued into it
  pages: string[]; // 'book/chapter/page' for each page it touches
  askedBy: string; // the name the server gave the API key that asked for it
  createdAt: number;
  startedAt?: number;
  endedAt?: number;
  // How many runs have taken this batch. The worker counts a try the moment it
  // starts one, so a run that dies without writing anything is still counted.
  attempts: number;
  // One or two lines from Claude saying what the batch did, written when the
  // batch finishes. A batch that failed carries the reason here instead.
  summary: string[];
}

// A comment made before the status field existed has none, and one made before
// queueing existed may say 'open', which was the old name for waiting work.
// Both read as 'new', so nothing is addressed until somebody asks for it.
export const statusOf = (h: Pick<Highlight, 'status'>): FeedbackStatus =>
  h.status && (STATUSES as readonly string[]).includes(h.status) ? h.status : 'new';

// A highlight with a comment asks something; one without it only marks text.
export const isFeedback = (h: Pick<Highlight, 'note'>) => Boolean(h.note.trim());

// A comment Claude has finished with and replied to.
export const isDone = (h: Pick<Highlight, 'note' | 'status'>) =>
  isFeedback(h) && DONE.includes(statusOf(h));

// A batch the worker has not finished with. These are the ones it works through,
// oldest first, and the ones that make a later batch wait.
export const isOpen = (b: Pick<Batch, 'status'>) => b.status === 'waiting' || b.status === 'working';

// Book, chapter and page become a file path on the server, so each must be one
// plain path segment. The extension refuses to highlight anywhere else, and the
// server refuses a sync that breaks the rule.
const SEGMENT = /^[a-z0-9][a-z0-9_-]*$/i;
export const validPage = (p: Pick<Highlight, 'book' | 'chapter' | 'page'>) =>
  [p.book, p.chapter, p.page].every((s) => SEGMENT.test(s ?? ''));

// Where a comment's page is, written as one line for a batch record.
export const pagePath = (p: Pick<Highlight, 'book' | 'chapter' | 'page'>) =>
  `${p.book}/${p.chapter}/${p.page}`;

// Enough to find a highlight's page file on the server, which is all a delete or
// a queue request needs.
export type HighlightRef = Pick<Highlight, 'id' | 'book' | 'chapter' | 'page'>;
