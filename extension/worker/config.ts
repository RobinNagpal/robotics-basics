import { homedir } from 'node:os';
import { join } from 'node:path';

// Every setting comes from worker/.env; see .env.example.
const env = process.env;

export const config = {
  // How often to look for a batch somebody has asked for, as a cron pattern.
  // This is not how often the worker works: a run with nothing queued reads the
  // bucket and stops. '*/2 * * * *' is every 2 minutes, which makes the button
  // in the extension feel immediate; '*/30 * * * *' is every 30 minutes.
  schedule: env.SCHEDULE ?? '*/2 * * * *',
  // The clone of this repository that Claude works in. It is separate from any
  // clone a person works in, so the two never edit the same files.
  repoDir: env.REPO_DIR ?? join(homedir(), 'feedback-worker', 'robotics-basics'),
  repoUrl: env.REPO_URL ?? 'git@github.com:RobinNagpal/robotics-basics.git',
  claudeBin: env.CLAUDE_BIN ?? 'claude',
  // The model every Claude turn runs on. 'sonnet' is the latest Sonnet.
  model: env.CLAUDE_MODEL || 'sonnet',
  // One Claude turn that takes longer than this is stopped, and every comment in
  // that batch is marked failed. A larger batch needs a longer limit.
  timeoutMinutes: Number(env.TIMEOUT_MINUTES ?? 60),
  // A run that is due while another is still working waits this long for it to
  // finish, and is skipped if it is still going.
  waitMinutes: Number(env.WAIT_MINUTES ?? 60),
  // Where the worker keeps the ID of its Claude Code session.
  stateFile: join(import.meta.dirname, '.state', 'session.json'),
};
