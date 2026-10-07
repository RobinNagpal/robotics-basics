export interface Highlight {
  id: string;
  book: string;
  chapter: string;
  page: string;
  url: string;
  text: string;
  prefix: string;
  suffix: string;
  color: string;
  note: string;
  userEmail: string;
  createdAt: number;
  updatedAt: number;
}

// The browser copy carries two extra flags the server never sees.
export interface LocalHighlight extends Highlight {
  dirty?: boolean; // changed here and not yet sent
  deleted?: boolean; // deleted here; removed once the server confirms
}

export const COLORS = ['#fde047', '#86efac', '#93c5fd', '#f9a8d4'] as const;
