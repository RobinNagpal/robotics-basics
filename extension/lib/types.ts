import type { Highlight } from '../api/types';

// The shapes the API stores, and the rule for a valid page, belong to the API.
export * from '../api/types';

// The browser copy carries two extra flags the server never sees.
export interface LocalHighlight extends Highlight {
  dirty?: boolean; // changed here and not yet sent
  deleted?: boolean; // deleted here; removed once the server confirms
}

export const COLORS = ['#fde047', '#86efac', '#93c5fd', '#f9a8d4'] as const;
