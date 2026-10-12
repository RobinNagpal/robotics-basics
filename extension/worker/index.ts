import { Cron } from 'croner';
import type { Batch, Highlight } from '../api/types';
import { runTurn } from './claude';
import { config } from './config';
import { batchFeedback, byPage, claim, finishBatch, giveBack, nextBatch, record, startBatch } from './feedback';
import { ensureClone, pullLatest, pushBatch, status } from './git';
import { acquire } from './lock';
import { batchPrompt, repairPrompt, RESULT_SCHEMA, type Reply, type Result } from './prompt';
import { loadSession, saveSession, type State } from './session';

const log = (...a: unknown[]) => console.log(new Date().toISOString(), ...a);
const firstLine = (e: unknown) => {
  const err = e as { stderr?: string; message?: string };
  return String(err.stderr || err.message || e).trim().split('\n')[0];
};

// One run: take the oldest batch a reader has asked for and address all of it.
// A run works on one batch only, so a batch asked for while another is being
// worked on waits its turn and is taken by a later run. Nothing is addressed
// unless somebody asked for it in the extension, so a run with no batch waiting
// costs nothing.
async function cycle() {
  const batch = await nextBatch();
  if (!batch) return log('nothing queued');

  // Which comments the batch holds is read before anything is marked, because a
  // batch whose comments have all been edited or deleted has no work left in it
  // and has to be closed rather than left in the way of the batches behind it.
  const queued = await batchFeedback(batch);
  if (!queued.length) return closeEmpty(batch);

  const session = loadSession();
  // Compacting replaces the conversation so far with a summary of it. The
  // session keeps its ID and what it learned, without growing every run.
  if (session.created) {
    const r = await runTurn(session, '/compact');
    log(r.isError ? `compact failed: ${r.text}` : 'session compacted');
  }

  // A clone that cannot be brought up to date leaves the batch waiting, and the
  // next run tries again. This happens before the batch is marked, so a pull
  // that fails does not spend one of the batch's tries.
  if (!(await latest(session))) return log(`skipped batch ${batch.number}: the clone could not pull main`);

  // Marking the batch 'working' is the last thing before Claude is invoked, so
  // anyone watching the extension sees it change from waiting to working at the
  // moment the work starts. A comment edited in that moment drops out of the
  // batch and keeps the status it had.
  const attempts = await startBatch(batch);
  const comments = await claim(queued);
  if (!comments.length) return closeEmpty(batch);
  const pages = [...byPage(comments).values()];
  log(`batch ${batch.number}, try ${attempts}: addressing ${comments.length} comment(s) on ${pages.length} page(s)`);

  await addressBatch(session, batch, attempts, comments, pages);
}

// A batch with nothing left in it is finished rather than left waiting, because
// the worker takes the oldest unfinished batch and would otherwise read this one
// again on every run and never reach the batches behind it.
async function closeEmpty(batch: Batch) {
  await finishBatch(batch, 'done', [
    'Nothing was left to address in this batch.',
    'Every comment in it was rewritten or deleted before the work started.',
  ]);
  log(`batch ${batch.number} had nothing left in it, so it is closed`);
}

// Every turn goes to the one session, and the first turn creates it.
async function turn(session: State, prompt: string, schema?: object) {
  const r = await runTurn(session, prompt, schema);
  if (!session.created) {
    session.created = true;
    saveSession(session);
  }
  return r;
}

// Makes sure the clone is on the latest main before Claude works. When git
// cannot pull, Claude is asked to put the clone right, and the pull is tried
// once more. Returns false if the clone still cannot be brought up to date.
async function latest(session: State) {
  ensureClone();
  let error = pullLatest();
  if (!error) return true;
  log(`pull failed, asking Claude to fix the clone: ${error.split('\n')[0]}`);
  const r = await turn(session, repairPrompt(error, status()));
  log(r.isError ? `repair turn failed: ${r.text}` : `Claude: ${r.text.split('\n')[0]}`);
  error = pullLatest();
  if (error) log(`pull still fails: ${error.split('\n')[0]}`);
  return !error;
}

// Claude makes every change the batch needs in one turn and commits it. Then the
// worker pushes once, and only after that records each comment's reply, so a
// comment marked 'changed' is one whose change is already on main. Nothing is
// pushed until Claude has replied in the shape the worker asked for, so a turn
// that ends any other way leaves its commits in the clone for the next run.
async function addressBatch(
  session: State,
  batch: Batch,
  attempts: number,
  comments: Highlight[],
  pages: Highlight[][],
) {
  const what = pages.length === 1 ? `${pages[0][0].book}/${pages[0][0].chapter}/${pages[0][0].page}` : `${pages.length} pages`;

  let result: Result;
  try {
    const r = await turn(session, batchPrompt(pages, batch.number), RESULT_SCHEMA);
    const out = r.structured as Result | undefined;
    if (r.isError || !out) throw new Error(r.text || 'Claude gave no structured result');
    result = out;
    log(`Claude finished batch ${batch.number}, $${r.costUsd?.toFixed(2) ?? '?'}`);
  } catch (e) {
    // The batch is not thrown away. Everything in it goes back in the queue, so
    // the next run takes it again, and anything Claude did commit in the clone
    // is pushed by that run. Only a batch that has used up its tries is marked
    // failed here.
    const reason = `The run failed: ${firstLine(e)}`;
    log(`batch ${batch.number} failed: ${firstLine(e)}`);
    const back = await giveBack(comments, reason, attempts).catch((e2) => {
      log('could not give the batch back, so it stays in progress for the next run', e2);
      return null;
    });
    if (!back) return;
    log(`${back.retrying.length} comment(s) queued again for the next run, ${back.givenUp.length} given up on`);
    if (back.retrying.length) {
      await finishBatch(batch, 'waiting', [reason, 'The next run takes this batch again.']);
    } else if (back.givenUp.length) {
      await finishBatch(batch, 'failed', [reason, `It was tried ${attempts} times, so the worker gave up on it.`]);
    } else {
      await closeEmpty(batch);
    }
    return;
  }

  // A push that fails leaves the batch 'working'. Claude's commits stay in the
  // clone, the next run's pull puts them on top of main or asks Claude to, and
  // Claude then finds its own work already done and replies.
  let commit: string | null;
  try {
    commit = pushBatch(what);
    log(commit ? `pushed ${commit}` : 'nothing to push');
  } catch (e) {
    const reason = `The work was done, but pushing it to GitHub failed: ${firstLine(e)}`;
    log(`push failed, batch ${batch.number} stays in progress: ${firstLine(e)}`);
    return finishBatch(batch, 'working', [reason, 'The next run pushes it and finishes the batch.']);
  }

  for (const h of comments) {
    const reply = result.replies.find((x) => x.id === h.id);
    let state: Reply['status'] | 'failed' = reply?.status ?? 'failed';
    let response = reply?.response.join('\n') ?? 'Claude gave no reply to this comment.';
    if (state === 'changed' && !commit) {
      state = 'failed';
      response = `Claude said it changed the docs, but nothing was committed.\n${response}`;
    } else if (state === 'changed') {
      response += `\nPushed to main in commit ${commit}.`;
    }
    const written = await record(h, state, response);
    log(`${h.id}: ${state}${written ? '' : ' (not written: the comment changed meanwhile)'}`);
  }

  // The batch is finished last, so the extension shows it as done only once
  // every comment in it carries its reply.
  await finishBatch(batch, 'done', result.summary);
}

// A run that is due while another is still using the session waits for it, for
// at most waitMinutes. Only one run waits at a time: on a short schedule a long
// run would otherwise collect a queue of waiting runs, all doing the same thing.
let waiting = false;
async function run() {
  if (waiting) return log('skipped: a run is already waiting for the session');
  waiting = true;
  let release: (() => void) | null;
  try {
    release = await acquire(config.waitMinutes * 60_000, () => log('the session is in use, waiting for it'));
  } finally {
    waiting = false;
  }
  if (!release) return log(`skipped: the session was still in use after ${config.waitMinutes} minutes`);
  try {
    await cycle();
  } finally {
    release();
  }
}

if (process.argv.includes('--once')) {
  await run();
} else {
  new Cron(config.schedule, { catch: (e) => log('run failed', e) }, run);
  log(`feedback worker started, schedule "${config.schedule}", repo ${config.repoDir}`);
}
