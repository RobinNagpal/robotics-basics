import { Cron } from 'croner';
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync } from 'node:fs';
import { dirname } from 'node:path';
import { runTurn } from './claude';
import { config } from './config';
import { openFeedback, record } from './feedback';
import { feedbackPrompt, RESULT_SCHEMA } from './prompt';
import { loadSession, saveSession } from './session';

const log = (...a: unknown[]) => console.log(new Date().toISOString(), ...a);

// Brings the clone up to date with main, making it first if it is missing.
function updateRepo() {
  if (!existsSync(config.repoDir)) {
    mkdirSync(dirname(config.repoDir), { recursive: true });
    execFileSync('git', ['clone', config.repoUrl, config.repoDir], { stdio: 'inherit' });
  }
  execFileSync('git', ['-C', config.repoDir, 'pull', '--ff-only'], { stdio: 'inherit' });
}

// One run: find the open feedback, compact the session, then hand Claude the
// feedback one piece at a time, in the order it was written, and record each
// outcome as soon as it is known.
async function cycle() {
  const pending = await openFeedback();
  if (!pending.length) return log('no open feedback');
  log(`${pending.length} open feedback`);
  updateRepo();

  const session = loadSession();
  // Compacting replaces the conversation so far with a summary of it. The
  // session keeps its ID and what it learned, without growing every run.
  if (session.created) {
    const r = await runTurn(session, '/compact');
    log(r.isError ? `compact failed: ${r.text}` : 'session compacted');
  }

  for (const h of pending) {
    log(`addressing ${h.id} on ${h.book}/${h.chapter}/${h.page}`);
    try {
      const r = await runTurn(session, feedbackPrompt(h), RESULT_SCHEMA);
      if (!session.created) {
        session.created = true;
        saveSession(session);
      }
      const out = r.structured as { status: 'changed' | 'answered'; response: string[] } | undefined;
      if (r.isError || !out) throw new Error(r.text || 'Claude gave no structured result');
      const written = await record(h, out.status, out.response.join('\n'));
      log(`${h.id}: ${out.status}${written ? '' : ' (not written: the comment changed meanwhile)'} $${r.costUsd?.toFixed(2) ?? '?'}`);
    } catch (e) {
      const message = (e as Error).message;
      log(`${h.id}: failed: ${message}`);
      await record(h, 'failed', `The run failed: ${message}`).catch((e2) => log('could not record failure', e2));
    }
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
