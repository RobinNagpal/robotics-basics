import { apiKey, apiUrl } from './store';
import type { HighlightRef } from './types';

// Asks the server to address a batch of comments. This is the one status change
// the extension makes: the server makes a batch, moves each comment from 'new'
// to 'queued', and gives back the batch's number. The worker takes one batch at
// a time, oldest first, so a batch asked for now waits for the one before it to
// finish. The server counts the comments it queued, so one that somebody else
// queued or deleted in the meantime is reported as skipped rather than treated
// as an error, and a request that queued nothing makes no batch and comes back
// with no number.
export async function queueFeedback(
  refs: HighlightRef[],
): Promise<{ batch: number | null; queued: number; skipped: number }> {
  const [url, key] = [await apiUrl.getValue(), await apiKey.getValue()];
  if (!url || !key) throw new Error('Sign in first');
  let res: Response;
  try {
    res = await fetch(`${url}/queue`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ refs: refs.map(({ id, book, chapter, page }) => ({ id, book, chapter, page })) }),
    });
  } catch {
    throw new Error(`Could not reach ${url}`);
  }
  if (res.status === 401) throw new Error('The server no longer accepts this API key');
  if (!res.ok) throw new Error(`Server answered ${res.status}`);
  return res.json();
}
