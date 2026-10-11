// What the API stores and what the extension sends it. This file belongs to the
// API, so that a change to it redeploys the API; the extension imports it from here.

// Where a comment stands. A comment is made 'new' and nothing happens to it
// until somebody asks for it: selecting comments in the popup and pressing
// "Address feedback" makes them 'queued'. The feedback worker then takes a whole
// batch of queued comments, marks them 'working' just before it invokes Claude
// Code, and sets the last three when Claude has finished with them: 'changed'
// when Claude changed the docs, 'answered' when Claude replied without changing
// them, and 'failed' when the run went wrong.
export const STATUSES = ['new', 'queued', 'working', 'changed', 'answered', 'failed'] as const;
export type FeedbackStatus = (typeof STATUSES)[number];

// The statuses the browser may ask for, and what the comment has to be in now.
// Everything else is the worker's to write. Queueing is the one status change a
// reader makes, so it is the one the API accepts from the extension.
export const QUEUE_FROM: FeedbackStatus = 'new';
export const QUEUE_TO: FeedbackStatus = 'queued';

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
}

// A comment made before the status field existed has none, and one made before
// queueing existed may say 'open', which was the old name for waiting work.
// Both read as 'new', so nothing is addressed until somebody asks for it.
export const statusOf = (h: Pick<Highlight, 'status'>): FeedbackStatus =>
  h.status && (STATUSES as readonly string[]).includes(h.status) ? h.status : 'new';

// A highlight with a comment asks something; one without it only marks text.
export const isFeedback = (h: Pick<Highlight, 'note'>) => Boolean(h.note.trim());

// Book, chapter and page become a file path on the server, so each must be one
// plain path segment. The extension refuses to highlight anywhere else, and the
// server refuses a sync that breaks the rule.
const SEGMENT = /^[a-z0-9][a-z0-9_-]*$/i;
export const validPage = (p: Pick<Highlight, 'book' | 'chapter' | 'page'>) =>
  [p.book, p.chapter, p.page].every((s) => SEGMENT.test(s ?? ''));

// Enough to find a highlight's page file on the server, which is all a delete or
// a queue request needs.
export type HighlightRef = Pick<Highlight, 'id' | 'book' | 'chapter' | 'page'>;
