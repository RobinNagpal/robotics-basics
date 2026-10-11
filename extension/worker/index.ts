import { Cron } from 'croner';
import type { Highlight } from '../api/types';
import { runTurn } from './claude';
import { config } from './config';
import { byPage, claim, giveBack, queuedFeedback, record } from './feedback';
import { ensureClone, pullLatest, pushBatch, status } from './git';
import { acquire } from './lock';
import { batchPrompt, repairPrompt, RESULT_SCHEMA, type Reply } from './prompt';
import { loadSession, saveSession, type State } from './session';

const log = (...a: unknown[]) => console.log(new Date().toISOString(), ...a);
const firstLine = (e: unknown) => {
  const err = e as { stderr?: string; message?: string };
  return String(err.stderr || err.message || e).trim().split('\n')[0];
};

// One run: take every comment a reader has queued, and address the whole lot as
// one batch. Nothing is addressed unless somebody asked for it in the extension,
// so a run with an empty queue costs nothing.
async function cycle() {
  const queued = await queuedFeedback();
  if (!queued.length) return log('nothing queued');

  const session = loadSession();
  // Compacting replaces the conversation so far with a summary of it. The
  // session keeps its ID and what it learned, without growing every run.
  if (session.created) {
    const r = await runTurn(session, '/compact');
    log(r.isError ? `compact failed: ${r.text}` : 'session compacted');
  }

  // A clone that cannot be brought up to date leaves the batch queued, and the
  // next run tries again.
  if (!(await latest(session))) return log('skipped: the clone could not pull main');

  // Marking the batch 'working' is the last thing before Claude is invoked, so
  // anyone watching the extension sees the batch change from queued to working
  // at the moment the work starts. A comment edited in that moment drops out of
  // the batch and keeps the status it had.
  const batch = await claim(queued);
  if (!batch.length) return log('nothing left to do: every queued comment changed while the run started');
  const pages = [...byPage(batch).values()];
  log(`addressing ${batch.length} comment(s) on ${pages.length} page(s) as one batch`);

  await addressBatch(session, batch, pages);
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
async function addressBatch(session: State, batch: Highlight[], pages: Highlight[][]) {
  const what = pages.length === 1 ? `${pages[0][0].book}/${pages[0][0].chapter}/${pages[0][0].page}` : `${pages.length} pages`;

  let replies: Reply[];
  try {
    const r = await turn(session, batchPrompt(pages), RESULT_SCHEMA);
    const out = r.structured as { replies: Reply[] } | undefined;
    if (r.isError || !out) throw new Error(r.text || 'Claude gave no structured result');
    replies = out.replies;
    log(`Claude finished the batch, $${r.costUsd?.toFixed(2) ?? '?'}`);
  } catch (e) {
    // The batch is not thrown away. Everything in it goes back in the queue, so
    // the next run takes it again, and anything Claude did commit in the clone
    // is pushed by that run. Only a comment that has used up its tries is
    // marked failed here.
    log(`the batch failed: ${firstLine(e)}`);
    const back = await giveBack(batch, `The run failed: ${firstLine(e)}`).catch((e2) => {
      log('could not give the batch back, so it stays in progress for the next run', e2);
      return null;
    });
    if (back) log(`${back.retrying.length} comment(s) queued again for the next run, ${back.givenUp.length} given up on`);
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
    return log(`push failed, the batch stays in progress: ${firstLine(e)}`);
  }

  for (const h of batch) {
    const reply = replies.find((x) => x.id === h.id);
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
