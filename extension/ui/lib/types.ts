import type { Highlight } from '../../api/types';

// The shapes the API stores, and the rule for a valid page, belong to the API.
export * from '../../api/types';

// The browser copy carries two extra flags the server never sees.
export interface LocalHighlight extends Highlight {
  dirty?: boolean; // changed here and not yet sent
  deleted?: boolean; // deleted here; removed once the server confirms
}

export const COLORS = ['#fde047', '#86efac', '#93c5fd', '#f9a8d4'] as const;

// How each status reads to the reader. A highlight with no comment is not
// feedback, so it shows no status at all.
const LABELS = { open: 'Waiting for Claude', changed: 'Docs changed', answered: 'Answered', failed: 'Failed' } as const;
export const statusOf = (h: Highlight) => (h.note.trim() ? (h.status ?? 'open') : null);
export const statusLabel = (h: Highlight) => {
  const s = statusOf(h);
  return s ? LABELS[s] : '';
};
