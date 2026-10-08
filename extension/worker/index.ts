import { Cron } from 'croner';
import { pageKeyOf } from '../api/store';
import type { Highlight } from '../api/types';
import { runTurn } from './claude';
import { config } from './config';
import { openFeedback, record } from './feedback';
import { ensureClone, pullLatest, pushPage, status } from './git';
import { pagePrompt, repairPrompt, RESULT_SCHEMA, type Reply } from './prompt';
import { loadSession, saveSession, type State } from './session';

const log = (...a: unknown[]) => console.log(new Date().toISOString(), ...a);
const firstLine = (e: unknown) => {
  const err = e as { stderr?: string; message?: string };
  return String(err.stderr || err.message || e).trim().split('\n')[0];
};

// One run: find the open feedback, compact the session, then work through it a
// page at a time, oldest page first.
async function cycle() {
  const pending = await openFeedback();
  if (!pending.length) return log('no open feedback');

  // openFeedback returns the oldest comment first, so the pages come out in the
  // order their first comment was written.
  const pages = new Map<string, Highlight[]>();
  for (const h of pending) pages.set(pageKeyOf(h), [...(pages.get(pageKeyOf(h)) ?? []), h]);
  log(`${pending.length} open feedback on ${pages.size} page(s)`);

  const session = loadSession();
  // Compacting replaces the conversation so far with a summary of it. The
  // session keeps its ID and what it learned, without growing every run.
  if (session.created) {
    const r = await runTurn(session, '/compact');
    log(r.isError ? `compact failed: ${r.text}` : 'session compacted');
  }

  for (const comments of pages.values()) await addressPage(session, comments);
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

// Makes sure the clone is on the latest main before Claude works on a page. When
// git cannot pull, Claude is asked to put the clone right, and the pull is tried
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

// Claude makes every change one page needs in one turn and commits it. Then the
// worker pushes, and only after that records each comment's reply, so a comment
// marked 'changed' is one whose change is already on main.
async function addressPage(session: State, comments: Highlight[]) {
  const page = `${comments[0].book}/${comments[0].chapter}/${comments[0].page}`;
  // A clone that cannot be brought up to date leaves the comments open, and the
  // next run tries again.
  if (!(await latest(session))) return log(`${page}: skipped, the clone could not pull main`);

  log(`addressing ${comments.length} comment(s) on ${page}`);
  let replies: Reply[];
  try {
    const r = await turn(session, pagePrompt(comments), RESULT_SCHEMA);
    const out = r.structured as { replies: Reply[] } | undefined;
    if (r.isError || !out) throw new Error(r.text || 'Claude gave no structured result');
    replies = out.replies;
    log(`${page}: Claude finished, $${r.costUsd?.toFixed(2) ?? '?'}`);
  } catch (e) {
    log(`${page}: failed: ${firstLine(e)}`);
    for (const h of comments) await record(h, 'failed', `The run failed: ${firstLine(e)}`).catch((e2) => log('could not record failure', e2));
    return;
  }

  // A push that fails leaves the comments open. Claude's commits stay in the
  // clone, the next run's pull puts them on top of main or asks Claude to, and
  // Claude then finds its own work already done and replies.
  let commit: string | null;
  try {
    commit = pushPage(page);
    log(`${page}: ${commit ? `pushed ${commit}` : 'nothing to push'}`);
  } catch (e) {
    return log(`${page}: push failed, the comments stay open: ${firstLine(e)}`);
  }

  for (const h of comments) {
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

if (process.argv.includes('--once')) {
  await cycle();
} else {
  // protect: a run that is still going when the next one is due makes that one
  // skip, instead of two runs working on the same clone at once.
  new Cron(config.schedule, { protect: true, catch: (e) => log('run failed', e) }, cycle);
  log(`feedback worker started, schedule "${config.schedule}", repo ${config.repoDir}`);
}
