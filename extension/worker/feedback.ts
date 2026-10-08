import { pageKeyOf, readAll, updatePage } from '../api/store';
import type { FeedbackStatus, Highlight } from '../api/types';

// Feedback is a highlight with a comment. A highlight with no comment marks
// text but asks nothing, so it is left alone.
export async function openFeedback(): Promise<Highlight[]> {
  return (await readAll())
    .filter((h) => h.note.trim() && (h.status ?? 'open') === 'open')
    .sort((a, b) => a.createdAt - b.createdAt);
}

// Writes the outcome into the comment's page file, with the same conditional
// write the API uses, so a sync that happens at the same moment is not lost.
// It writes only if the comment is still there, still open and still says what
// Claude was shown. A comment edited meanwhile stays open for the next run.
export async function record(h: Highlight, status: FeedbackStatus, claudeResponse: string) {
  let written = false;
  await updatePage(pageKeyOf(h), (items) =>
    items.map((x) => {
      if (x.id !== h.id || x.note !== h.note || (x.status ?? 'open') !== 'open') return x;
      written = true;
      return { ...x, status, claudeResponse, respondedAt: Date.now() };
    }),
  );
  return written;
}
