import {
  isFeedback,
  QUEUEABLE,
  statusOf,
  type Batch,
  type BatchStatus,
  type FeedbackStatus,
  type Highlight,
} from '../../api/types';

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

// A comment can be asked for while it is waiting, and again after a run failed,
// because a failure is usually one bad run rather than a comment nothing can
// answer. The server has to have the comment first, because it queues by id and
// would otherwise not find it. One waiting to be sent is queued after the next
// sync, which happens by itself.
export const canQueue = (h: LocalHighlight) => {
  const s = shownStatus(h);
  return s !== null && QUEUEABLE.includes(s) && !h.dirty && !h.deleted;
};

// How each batch status reads to the reader. A batch that is waiting says what
// it is waiting for, because the worker takes one batch at a time and the reader
// needs to see that their newest request is behind an older one rather than
// stuck. `inFront` is the number of the oldest batch the worker has not finished
// with, which is the batch this one is waiting for.
const BATCH_LABELS: Record<BatchStatus, string> = {
  waiting: 'Waiting its turn',
  working: 'Claude is working on it',
  done: 'Finished',
  failed: 'Failed',
};

export function batchLabel(b: Batch, inFront?: number): string {
  if (b.status === 'waiting') {
    return inFront && inFront !== b.number ? `Waiting for batch ${inFront}` : 'Next to be worked on';
  }
  return BATCH_LABELS[b.status];
}

// What a batch covers, in words, for the line under its number.
export const batchSize = (b: Batch) =>
  `${b.size} comment${b.size === 1 ? '' : 's'} on ${b.pages.length} page${b.pages.length === 1 ? '' : 's'}`;
