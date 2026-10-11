// What a batch of feedback goes through, from the moment a reader asks for it to
// the moment Claude's answer is written down. These are the status changes, and
// they are tested against a store held in memory rather than S3, because what
// can go wrong here is the rules about which comment may change state, not the
// writing of a file. Run them with `npm test`.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { MAX_ATTEMPTS, statusOf, type Highlight } from '../api/types';
import { byPage, claim, giveBack, queuedFeedback, record, type Store } from './feedback';

// A store of the same shape as the API's, holding the page files in an object.
// It sorts on write, as the real one does, so the order a test reads back is the
// order the real store would give.
function memory(pages: Record<string, Highlight[]>): Store & { pages: typeof pages } {
  return {
    pages,
    pageKeyOf: (p) => `feedback/${p.book}/${p.chapter}/${p.page}.json`,
    readAll: async () => Object.values(pages).flat(),
    updatePage: async (key, change) => {
      pages[key] = change(pages[key] ?? []).sort((a, b) => a.createdAt - b.createdAt);
    },
  };
}

const comment = (over: Partial<Highlight>): Highlight => ({
  id: 'x', book: 'b', chapter: 'c', page: 'p', section: '', url: 'u', text: 'some text',
  prefix: '', suffix: '', color: '#fde047', note: 'say this more plainly',
  author: 'robin', createdAt: 1, updatedAt: 1, ...over,
});

// One bucket covering every state a comment can be in when a run starts.
function bucket() {
  return memory({
    'feedback/b/c/p1.json': [
      comment({ id: 'notasked', page: 'p1', status: 'new' }),
      comment({ id: 'legacy', page: 'p1', status: 'open' as never }), // made before queueing existed
      comment({ id: 'asked', page: 'p1', status: 'queued', createdAt: 5 }),
      comment({ id: 'blank', page: 'p1', status: 'queued', note: '   ' }), // marks text, asks nothing
    ],
    'feedback/b/c/p2.json': [
      comment({ id: 'asked2', page: 'p2', status: 'queued', createdAt: 2 }),
      comment({ id: 'leftover', page: 'p2', status: 'working', createdAt: 3 }), // a run died on it
      comment({ id: 'done', page: 'p2', status: 'answered' }),
    ],
  });
}

const find = (store: ReturnType<typeof memory>, id: string) =>
  Object.values(store.pages).flat().find((h) => h.id === id);
const statusIn = (store: ReturnType<typeof memory>, id: string) => find(store, id)?.status;

test('a run takes the comments that were asked for, and nothing else', async () => {
  const store = bucket();
  const queued = await queuedFeedback(store);
  // Oldest first, so the page whose feedback has waited longest is dealt with
  // first. 'leftover' comes with them, because no other run can be holding it.
  assert.deepEqual(queued.map((h) => h.id), ['asked2', 'leftover', 'asked']);
  // A comment nobody asked for is not in it, and neither is one already answered
  // or one that holds no words.
  assert.equal(queued.some((h) => ['notasked', 'legacy', 'blank', 'done'].includes(h.id)), false);
});

test('a comment stored before queueing existed reads as new', async () => {
  // 'open' was the old name for work waiting to be done, and a comment older
  // still has no status at all. Both have to read as 'new': that is what keeps
  // everything already in the bucket from being acted on without being asked
  // for, and it is also what lets the popup offer a tick box for them.
  assert.equal(statusOf({ status: 'open' as never }), 'new');
  assert.equal(statusOf({ status: undefined }), 'new');
  const store = memory({ 'feedback/b/c/p.json': [comment({ id: 'legacy', status: 'open' as never })] });
  assert.deepEqual((await queuedFeedback(store)).map((h) => h.id), []);
});

test('claiming marks exactly the batch, grouped by the page file', async () => {
  const store = bucket();
  const batch = await claim(await queuedFeedback(store), store);
  assert.deepEqual(batch.map((h) => h.id), ['asked2', 'leftover', 'asked']);
  for (const id of ['asked', 'asked2', 'leftover']) assert.equal(statusIn(store, id), 'working');
  // Everything the batch did not include keeps the status it had.
  assert.equal(statusIn(store, 'notasked'), 'new');
  assert.equal(statusIn(store, 'blank'), 'queued');
  assert.equal(statusIn(store, 'done'), 'answered');
  assert.deepEqual([...byPage(batch, store).keys()], ['feedback/b/c/p2.json', 'feedback/b/c/p1.json']);
});

test('a comment edited between being read and being claimed drops out', async () => {
  const store = memory({ 'feedback/b/c/p.json': [comment({ id: 'edited', status: 'queued' })] });
  const read = await queuedFeedback(store);
  // The reader rewrites the comment in the moment before the batch starts, which
  // sends it back to 'new'. Claude must not be shown the text it no longer says.
  store.pages['feedback/b/c/p.json'] = [comment({ id: 'edited', status: 'new', note: 'rewritten' })];
  assert.deepEqual((await claim(read, store)).map((h) => h.id), []);
  assert.equal(statusIn(store, 'edited'), 'new');
});

test('a comment whose text changed drops out even if it was asked for again', async () => {
  const store = memory({ 'feedback/b/c/p.json': [comment({ id: 'edited', status: 'queued' })] });
  const read = await queuedFeedback(store);
  // The comment is edited, which sends it back to 'new', and then somebody asks
  // for it again, so it is 'queued' once more by the time the batch starts. The
  // status says it is ready, but the words are not the ones the run read, and
  // those are the words Claude would be given. So it waits for the next run,
  // which will read it as it now stands.
  store.pages['feedback/b/c/p.json'] = [comment({ id: 'edited', status: 'queued', note: 'rewritten' })];
  assert.deepEqual((await claim(read, store)).map((h) => h.id), []);
  assert.equal(statusIn(store, 'edited'), 'queued');
});

test('an outcome is written once, for a comment still being worked on', async () => {
  const store = bucket();
  const [first] = await claim(await queuedFeedback(store), store);
  assert.equal(await record(first, 'changed', 'Rewrote the section.', store), true);
  assert.equal(statusIn(store, first.id), 'changed');
  // A second write is refused, so a later run cannot overwrite the answer a
  // reader has already been given.
  assert.equal(await record(first, 'failed', 'no', store), false);
  assert.equal(statusIn(store, first.id), 'changed');
});

test('an outcome is refused for a comment edited while Claude worked', async () => {
  const store = bucket();
  const batch = await claim(await queuedFeedback(store), store);
  const target = batch.find((h) => h.id === 'asked')!;
  store.pages['feedback/b/c/p1.json'] = store.pages['feedback/b/c/p1.json'].map((h) =>
    h.id === 'asked' ? { ...h, note: 'changed my mind', status: 'new' as const } : h,
  );
  // The answer belongs to words the comment no longer says, so it is dropped and
  // the reader's new text waits to be asked for again.
  assert.equal(await record(target, 'answered', 'The docs are right here.', store), false);
  assert.equal(statusIn(store, 'asked'), 'new');
});

test('claiming counts one try against every comment it takes', async () => {
  const store = bucket();
  // The count has to be raised as the work starts, not when it ends, because a
  // run that is killed never gets to write anything down. So the count is what
  // the next run reads, and nothing can be taken for ever.
  const batch = await claim(await queuedFeedback(store), store);
  for (const h of batch) assert.equal(find(store, h.id)?.attempts, 1);
  // The batch handed to the caller carries the new count, so the run that failed
  // knows how many tries this comment has already had.
  assert.deepEqual(batch.map((h) => h.attempts), batch.map(() => 1));
  // A second run over the same comments counts a second try.
  const again = await claim(await queuedFeedback(store), store);
  for (const h of again) assert.equal(find(store, h.id)?.attempts, 2);
});

test('a batch that failed goes back in the queue, and the next run takes it', async () => {
  const store = bucket();
  const batch = await claim(await queuedFeedback(store), store);
  const back = await giveBack(batch, 'The run failed: Claude gave no structured result', store);
  // Nothing is lost and nothing is marked failed, because one try is not enough
  // to say a comment cannot be addressed.
  assert.deepEqual(back.retrying.map((h) => h.id), ['asked2', 'leftover', 'asked']);
  assert.deepEqual(back.givenUp, []);
  // This is the part that makes it a retry: the next run reads the same batch.
  assert.deepEqual((await queuedFeedback(store)).map((h) => h.id), ['asked2', 'leftover', 'asked']);
  for (const h of back.retrying) assert.equal(statusIn(store, h.id), 'queued');
});

test('a comment is given up on once it has used up its tries', async () => {
  const store = memory({ 'feedback/b/c/p.json': [comment({ id: 'doomed', status: 'queued', attempts: MAX_ATTEMPTS - 1 })] });
  const batch = await claim(await queuedFeedback(store), store);
  const back = await giveBack(batch, 'The run failed: Claude was stopped after 60 minutes', store);
  // The last try is spent, so retrying again would hold up every later batch
  // behind work that fails every time.
  assert.deepEqual(back.retrying, []);
  assert.deepEqual(back.givenUp.map((h) => h.id), ['doomed']);
  assert.equal(statusIn(store, 'doomed'), 'failed');
  // The reader is told why, and that asking again is possible.
  assert.match(find(store, 'doomed')!.claudeResponse!, /stopped after 60 minutes/);
  assert.match(find(store, 'doomed')!.claudeResponse!, new RegExp(`tried ${MAX_ATTEMPTS} times`));
  // A comment given up on is not taken by the next run.
  assert.deepEqual(await queuedFeedback(store), []);
});

test('a comment edited while the failed run ran is not put back in the queue', async () => {
  const store = memory({ 'feedback/b/c/p.json': [comment({ id: 'edited', status: 'queued' })] });
  const batch = await claim(await queuedFeedback(store), store);
  store.pages['feedback/b/c/p.json'] = [comment({ id: 'edited', status: 'new', note: 'rewritten', attempts: 0 })];
  // Queueing it again would ask Claude to address words the reader has replaced,
  // so the edit stands and the reader asks for the new text when they want it.
  const back = await giveBack(batch, 'The run failed', store);
  assert.deepEqual(back.retrying, []);
  assert.deepEqual(back.givenUp, []);
  assert.equal(statusIn(store, 'edited'), 'new');
});
