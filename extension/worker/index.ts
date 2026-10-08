import { Cron } from 'croner';
import { pageKeyOf } from '../api/store';
import type { Highlight } from '../api/types';
import { runTurn } from './claude';
import { config } from './config';
import { openFeedback, record } from './feedback';
import { pushPage, resetToMain } from './git';
import { pagePrompt, RESULT_SCHEMA, type Reply } from './prompt';
import { loadSession, saveSession, type State } from './session';

const log = (...a: unknown[]) => console.log(new Date().toISOString(), ...a);

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

// Claude makes every change one page needs in one turn and commits it. Then the
// worker pushes, and only after that records each comment's reply, so a comment
// marked 'changed' is one whose change is already on main.
async function addressPage(session: State, comments: Highlight[]) {
  const page = `${comments[0].book}/${comments[0].chapter}/${comments[0].page}`;
  log(`addressing ${comments.length} comment(s) on ${page}`);
  let replies: Reply[];
  let commit: string | null;
  try {
    resetToMain();
    const r = await runTurn(session, pagePrompt(comments), RESULT_SCHEMA);
    if (!session.created) {
      session.created = true;
      saveSession(session);
    }
    const out = r.structured as { replies: Reply[] } | undefined;
    if (r.isError || !out) throw new Error(r.text || 'Claude gave no structured result');
    replies = out.replies;
    commit = pushPage(page);
    log(`${page}: ${commit ? `pushed ${commit}` : 'nothing to push'}, $${r.costUsd?.toFixed(2) ?? '?'}`);
  } catch (e) {
    const message = (e as Error).message.split('\n')[0];
    log(`${page}: failed: ${message}`);
    for (const h of comments) await record(h, 'failed', `The run failed: ${message}`).catch((e2) => log('could not record failure', e2));
    return;
  }

  for (const h of comments) {
    const reply = replies.find((x) => x.id === h.id);
    let status: Reply['status'] | 'failed' = reply?.status ?? 'failed';
    let response = reply?.response.join('\n') ?? 'Claude gave no reply to this comment.';
    if (status === 'changed' && !commit) {
      status = 'failed';
      response = `Claude said it changed the docs, but nothing was committed.\n${response}`;
    } else if (status === 'changed') {
      response += `\nPushed to main in commit ${commit}.`;
    }
    const written = await record(h, status, response);
    log(`${h.id}: ${status}${written ? '' : ' (not written: the comment changed meanwhile)'}`);
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
