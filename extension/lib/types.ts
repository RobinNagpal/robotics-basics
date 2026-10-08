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
}

// Book, chapter and page become a file path on the server, so each must be one
// plain path segment. The extension refuses to highlight anywhere else, and the
// server refuses a sync that breaks the rule.
const SEGMENT = /^[a-z0-9][a-z0-9_-]*$/i;
export const validPage = (p: Pick<Highlight, 'book' | 'chapter' | 'page'>) =>
  [p.book, p.chapter, p.page].every((s) => SEGMENT.test(s ?? ''));

// Enough to find a highlight's page file on the server, which is all a delete needs.
export type HighlightRef = Pick<Highlight, 'id' | 'book' | 'chapter' | 'page'>;

// The browser copy carries two extra flags the server never sees.
export interface LocalHighlight extends Highlight {
  dirty?: boolean; // changed here and not yet sent
  deleted?: boolean; // deleted here; removed once the server confirms
}

export const COLORS = ['#fde047', '#86efac', '#93c5fd', '#f9a8d4'] as const;
