// What the API stores and what the extension sends it. This file belongs to the
// API, so that a change to it redeploys the API; the extension imports it from here.

// Where a comment stands. The API sets 'open' when a comment is made, and again
// when its text is changed. The feedback worker sets the others after Claude has
// worked on it: 'changed' when Claude changed the docs, 'answered' when Claude
// replied without changing them, and 'failed' when the run went wrong.
export const STATUSES = ['open', 'changed', 'answered', 'failed'] as const;
export type FeedbackStatus = (typeof STATUSES)[number];

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
  // Written only by the feedback worker. The API ignores them in a sync.
  status?: FeedbackStatus; // missing on comments made before it existed, which means 'open'
  claudeResponse?: string;
  respondedAt?: number;
}

// Book, chapter and page become a file path on the server, so each must be one
// plain path segment. The extension refuses to highlight anywhere else, and the
// server refuses a sync that breaks the rule.
const SEGMENT = /^[a-z0-9][a-z0-9_-]*$/i;
export const validPage = (p: Pick<Highlight, 'book' | 'chapter' | 'page'>) =>
  [p.book, p.chapter, p.page].every((s) => SEGMENT.test(s ?? ''));

// Enough to find a highlight's page file on the server, which is all a delete needs.
export type HighlightRef = Pick<Highlight, 'id' | 'book' | 'chapter' | 'page'>;
