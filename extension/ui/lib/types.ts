import { isFeedback, statusOf, type FeedbackStatus, type Highlight } from '../../api/types';

// The shapes the API stores, the rule for a valid page, and how a stored status
// is read all belong to the API.
export * from '../../api/types';

// The browser copy carries two extra flags the server never sees.
export interface LocalHighlight extends Highlight {
  dirty?: boolean; // changed here and not yet sent
  deleted?: boolean; // deleted here; removed once the server confirms
}

export const COLORS = ['#fde047', '#86efac', '#93c5fd', '#f9a8d4'] as const;

// How each status reads to the reader.
const LABELS: Record<FeedbackStatus, string> = {
  new: 'Not asked for yet',
  queued: 'Waiting for Claude',
  working: 'Claude is working on it',
  changed: 'Docs changed',
  answered: 'Answered',
  failed: 'Failed',
};

// A highlight with no comment is not feedback, so it shows no status at all.
export const shownStatus = (h: Highlight) => (isFeedback(h) ? statusOf(h) : null);
export const statusLabel = (h: Highlight) => {
  const s = shownStatus(h);
  return s ? LABELS[s] : '';
};

// A comment can be asked for only while it is new, and only once the server has
// it, because the server queues by id and would otherwise not find it. One
// waiting to be sent is queued after the next sync, which happens by itself.
export const canQueue = (h: LocalHighlight) => shownStatus(h) === 'new' && !h.dirty && !h.deleted;
