// What a batch of feedback goes through, from the moment a reader asks for it to
// the moment Claude's answer is written down. These are the status changes, and
// they are tested against a store held in memory rather than S3, because what
// can go wrong here is the rules about which comment and which batch may change
// state, not the writing of a file. Run them with `npm test`.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { MAX_ATTEMPTS, statusOf, type Batch, type Highlight } from '../api/types';
import {
  batchFeedback,
  byPage,
  claim,
  finishBatch,
  giveBack,
  nextBatch,
  record,
  startBatch,
  type Store,
} from './feedback';

// A store of the same shape as the API's, holding the page files and the batch
// records in objects. It sorts on write, as the real one does, so the order a
// test reads back is the order the real store would give.
type Memory = Store & { pages: Record<string, Highlight[]>; batches: Batch[] };

function memory(pages: Record<string, Highlight[]>, batches: Batch[] = []): Memory {
  const store: Memory = {
    pages,
    batches,
    pageKeyOf: (p) => `feedback/${p.book}/${p.chapter}/${p.page}.json`,
    readAll: async () => Object.values(store.pages).flat(),
    updatePage: async (key, change) =>
      (store.pages[key] = change(store.pages[key] ?? []).sort((a, b) => a.createdAt - b.createdAt)),
    readBatches: async () => store.batches,
    updateBatches: async (change) => (store.batches = change(store.batches).sort((a, b) => a.number - b.number)),
  };
  return store;
}

const comment = (over: Partial<Highlight>): Highlight => ({
  id: 'x', book: 'b', chapter: 'c', page: 'p', section: '', url: 'u', text: 'some text',
  prefix: '', suffix: '', color: '#fde047', note: 'say this more plainly',
  author: 'robin', createdAt: 1, updatedAt: 1, ...over,
});

const batch = (over: Partial<Batch> = {}): Batch => ({
  number: 1, status: 'waiting', size: 1, pages: ['b/c/p'], askedBy: 'robin',
  createdAt: 1, attempts: 0, summary: [], ...over,
});

// One bucket covering every state a comment can be in when a run starts, with
// two batches in it: batch 1 is the one a run should take, and batch 2 was asked
// for afterwards and has to wait for it.
function bucket() {
  return memory(
    {
      'feedback/b/c/p1.json': [
        comment({ id: 'notasked', page: 'p1', status: 'new' }),
        comment({ id: 'legacy', page: 'p1', status: 'open' as never }), // made before queueing existed
        comment({ id: 'asked', page: 'p1', status: 'queued', batch: 1, createdAt: 5 }),
        comment({ id: 'blank', page: 'p1', status: 'queued', batch: 1, note: '   ' }), // marks text, asks nothing
      ],
      'feedback/b/c/p2.json': [
        comment({ id: 'asked2', page: 'p2', status: 'queued', batch: 1, createdAt: 2 }),
        comment({ id: 'leftover', page: 'p2', status: 'working', batch: 1, createdAt: 3 }), // a run died on it
        comment({ id: 'done', page: 'p2', status: 'answered', batch: 1 }),
        comment({ id: 'later', page: 'p2', status: 'queued', batch: 2, createdAt: 9 }), // the batch behind
      ],
    },
    [
      batch({ number: 1, size: 3, pages: ['b/c/p1', 'b/c/p2'] }),
      batch({ number: 2, size: 1, pages: ['b/c/p2'], createdAt: 9 }),
    ],
  );
}

const find = (store: Memory, id: string) => Object.values(store.pages).flat().find((h) => h.id === id);
const statusIn = (store: Memory, id: string) => find(store, id)?.status;
const batchIn = (store: Memory, n: number) => store.batches.find((b) => b.number === n)!;

test('a run takes the oldest batch, and the one asked for after it waits', async () => {
  const store = bucket();
  assert.equal((await nextBatch(store))!.number, 1);
  // Batch 2 is reached only once batch 1 is finished with, which is what makes
  // one batch wait for the one in front of it.
  await finishBatch(batch({ number: 1 }), 'done', ['Rewrote two pages.'], store);
  assert.equal((await nextBatch(store))!.number, 2);
  await finishBatch(batch({ number: 2 }), 'done', ['Answered one question.'], store);
  assert.equal(await nextBatch(store), null);
});

test('a batch left in progress by a run that died is taken again before a newer one', async () => {
  // Only one run uses the session at a time, so a batch still marked 'working'
  // when a run starts was left there by a run that died. Taking it again rather
  // than moving on keeps the work in the order the reader asked for it.
  const store = memory({}, [batch({ number: 1, status: 'working' }), batch({ number: 2 })]);
  assert.equal((await nextBatch(store))!.number, 1);
});

test('a run takes the comments of its own batch, and nothing else', async () => {
  const store = bucket();
  const queued = await batchFeedback(batch({ number: 1 }), store);
  // Oldest first, so the page whose feedback has waited longest is dealt with
  // first. 'leftover' comes with them, because no other run can be holding it.
  assert.deepEqual(queued.map((h) => h.id), ['asked2', 'leftover', 'asked']);
  // A comment nobody asked for is not in it, nor one already answered, nor one
  // that holds no words, nor one belonging to the batch behind this one.
  assert.equal(queued.some((h) => ['notasked', 'legacy', 'blank', 'done', 'later'].includes(h.id)), false);
});

test('a comment stored before queueing existed reads as new', async () => {
  // 'open' was the old name for work waiting to be done, and a comment older
  // still has no status at all. Both have to read as 'new': that is what keeps
  // everything already in the bucket from being acted on without being asked
  // for, and it is also what lets the popup offer a tick box for them.
  assert.equal(statusOf({ status: 'open' as never }), 'new');
  assert.equal(statusOf({ status: undefined }), 'new');
  const store = memory({ 'feedback/b/c/p.json': [comment({ id: 'legacy', status: 'open' as never, batch: 1 })] });
  assert.deepEqual((await batchFeedback(batch(), store)).map((h) => h.id), []);
});

test('claiming marks exactly the batch, grouped by the page file', async () => {
  const store = bucket();
  const taken = await claim(await batchFeedback(batch({ number: 1 }), store), store);
  assert.deepEqual(taken.map((h) => h.id), ['asked2', 'leftover', 'asked']);
  for (const id of ['asked', 'asked2', 'leftover']) assert.equal(statusIn(store, id), 'working');
  // Everything the batch did not include keeps the status it had.
  assert.equal(statusIn(store, 'notasked'), 'new');
  assert.equal(statusIn(store, 'blank'), 'queued');
  assert.equal(statusIn(store, 'done'), 'answered');
  assert.equal(statusIn(store, 'later'), 'queued');
  assert.deepEqual([...byPage(taken, store).keys()], ['feedback/b/c/p2.json', 'feedback/b/c/p1.json']);
});

test('a comment edited between being read and being claimed drops out', async () => {
  const store = memory({ 'feedback/b/c/p.json': [comment({ id: 'edited', status: 'queued', batch: 1 })] });
  const read = await batchFeedback(batch(), store);
  // The reader rewrites the comment in the moment before the batch starts, which
  // sends it back to 'new'. Claude must not be shown the text it no longer says.
  store.pages['feedback/b/c/p.json'] = [comment({ id: 'edited', status: 'new', note: 'rewritten' })];
  assert.deepEqual((await claim(read, store)).map((h) => h.id), []);
  assert.equal(statusIn(store, 'edited'), 'new');
});

test('a comment whose text changed drops out even if it was asked for again', async () => {
  const store = memory({ 'feedback/b/c/p.json': [comment({ id: 'edited', status: 'queued', batch: 1 })] });
  const read = await batchFeedback(batch(), store);
  // The comment is edited, which sends it back to 'new', and then somebody asks
  // for it again, so it is 'queued' once more by the time the batch starts. The
  // status says it is ready, but the words are not the ones the run read, and
  // those are the words Claude would be given. So it waits for the next run,
  // which will read it as it now stands.
  store.pages['feedback/b/c/p.json'] = [comment({ id: 'edited', status: 'queued', batch: 2, note: 'rewritten' })];
  assert.deepEqual((await claim(read, store)).map((h) => h.id), []);
  assert.equal(statusIn(store, 'edited'), 'queued');
});

test('an outcome is written once, for a comment still being worked on', async () => {
  const store = bucket();
  const [first] = await claim(await batchFeedback(batch({ number: 1 }), store), store);
  assert.equal(await record(first, 'changed', 'Rewrote the section.', store), true);
  assert.equal(statusIn(store, first.id), 'changed');
  // A second write is refused, so a later run cannot overwrite the answer a
  // reader has already been given.
  assert.equal(await record(first, 'failed', 'no', store), false);
  assert.equal(statusIn(store, first.id), 'changed');
});

test('an outcome is refused for a comment edited while Claude worked', async () => {
  const store = bucket();
  const taken = await claim(await batchFeedback(batch({ number: 1 }), store), store);
  const target = taken.find((h) => h.id === 'asked')!;
  store.pages['feedback/b/c/p1.json'] = store.pages['feedback/b/c/p1.json'].map((h) =>
    h.id === 'asked' ? { ...h, note: 'changed my mind', status: 'new' as const } : h,
  );
  // The answer belongs to words the comment no longer says, so it is dropped and
  // the reader's new text waits to be asked for again.
  assert.equal(await record(target, 'answered', 'The docs are right here.', store), false);
  assert.equal(statusIn(store, 'asked'), 'new');
});

test('starting a batch marks it working and counts one try', async () => {
  const store = bucket();
  // The count has to be raised as the work starts, not when it ends, because a
  // run that is killed never gets to write anything down. So the count is what
  // the next run reads, and no batch can be taken for ever.
  assert.equal(await startBatch(batchIn(store, 1), store), 1);
  assert.equal(batchIn(store, 1).status, 'working');
  assert.ok(batchIn(store, 1).startedAt);
  // A second run over the same batch counts a second try, and reads the count
  // from the record rather than from the batch it was handed.
  assert.equal(await startBatch(batchIn(store, 1), store), 2);
  assert.equal(batchIn(store, 1).attempts, 2);
  // The batch behind it is not touched.
  assert.equal(batchIn(store, 2).status, 'waiting');
  assert.equal(batchIn(store, 2).attempts, 0);
});

test('a batch that failed goes back in the queue, and the next run takes it', async () => {
  const store = bucket();
  const tries = await startBatch(batchIn(store, 1), store);
  const taken = await claim(await batchFeedback(batchIn(store, 1), store), store);
  const back = await giveBack(taken, 'The run failed: Claude gave no structured result', tries, store);
  // Nothing is lost and nothing is marked failed, because one try is not enough
  // to say a batch cannot be addressed.
  assert.deepEqual(back.retrying.map((h) => h.id), ['asked2', 'leftover', 'asked']);
  assert.deepEqual(back.givenUp, []);
  await finishBatch(batchIn(store, 1), 'waiting', ['The run failed.'], store);
  // This is the part that makes it a retry: the next run reads the same batch,
  // with the same comments in it, before it reaches the batch behind.
  assert.equal((await nextBatch(store))!.number, 1);
  assert.deepEqual((await batchFeedback(batchIn(store, 1), store)).map((h) => h.id), ['asked2', 'leftover', 'asked']);
  for (const h of back.retrying) assert.equal(statusIn(store, h.id), 'queued');
});

test('a batch is given up on once it has used up its tries', async () => {
  const store = memory(
    { 'feedback/b/c/p.json': [comment({ id: 'doomed', status: 'queued', batch: 1 })] },
    [batch({ number: 1, attempts: MAX_ATTEMPTS - 1 }), batch({ number: 2, createdAt: 9 })],
  );
  const tries = await startBatch(batchIn(store, 1), store);
  assert.equal(tries, MAX_ATTEMPTS);
  const taken = await claim(await batchFeedback(batchIn(store, 1), store), store);
  const back = await giveBack(taken, 'The run failed: Claude was stopped after 60 minutes', tries, store);
  // The last try is spent, so retrying again would hold up every later batch
  // behind work that fails every time.
  assert.deepEqual(back.retrying, []);
  assert.deepEqual(back.givenUp.map((h) => h.id), ['doomed']);
  assert.equal(statusIn(store, 'doomed'), 'failed');
  // The reader is told why, and that asking again is possible.
  assert.match(find(store, 'doomed')!.claudeResponse!, /stopped after 60 minutes/);
  assert.match(find(store, 'doomed')!.claudeResponse!, new RegExp(`tried ${MAX_ATTEMPTS} times`));
  // The batch is closed, so the work behind it goes ahead.
  await finishBatch(batchIn(store, 1), 'failed', ['The run failed three times.'], store);
  assert.equal((await nextBatch(store))!.number, 2);
});

test('a comment edited while the failed run ran is not put back in the queue', async () => {
  const store = memory({ 'feedback/b/c/p.json': [comment({ id: 'edited', status: 'queued', batch: 1 })] });
  const taken = await claim(await batchFeedback(batch(), store), store);
  store.pages['feedback/b/c/p.json'] = [comment({ id: 'edited', status: 'new', note: 'rewritten' })];
  // Queueing it again would ask Claude to address words the reader has replaced,
  // so the edit stands and the reader asks for the new text when they want it.
  const back = await giveBack(taken, 'The run failed', 1, store);
  assert.deepEqual(back.retrying, []);
  assert.deepEqual(back.givenUp, []);
  assert.equal(statusIn(store, 'edited'), 'new');
});

test('a batch keeps the first outcome written for it, and its summary', async () => {
  const store = bucket();
  await startBatch(batchIn(store, 1), store);
  await finishBatch(batchIn(store, 1), 'done', ['Rewrote the opening of two pages.', 'Answered one question.'], store);
  assert.equal(batchIn(store, 1).status, 'done');
  assert.ok(batchIn(store, 1).endedAt);
  assert.deepEqual(batchIn(store, 1).summary, ['Rewrote the opening of two pages.', 'Answered one question.']);
  // A batch already finished with is never written again, so a run that lost its
  // turn cannot replace the summary a reader is looking at.
  await finishBatch(batchIn(store, 1), 'failed', ['nonsense'], store);
  assert.equal(batchIn(store, 1).status, 'done');
  assert.deepEqual(batchIn(store, 1).summary, ['Rewrote the opening of two pages.', 'Answered one question.']);
});

test('an empty batch can be closed, so it stops holding up the queue', async () => {
  // Every comment in the batch was rewritten or deleted before the run started,
  // so there is nothing to address. The batch is still waiting rather than
  // working, and it has to be possible to finish it from there.
  const store = memory({}, [batch({ number: 1 }), batch({ number: 2, createdAt: 9 })]);
  await finishBatch(batchIn(store, 1), 'done', ['Nothing was left to address in this batch.'], store);
  assert.equal(batchIn(store, 1).status, 'done');
  assert.equal((await nextBatch(store))!.number, 2);
});
