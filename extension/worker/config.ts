import { homedir } from 'node:os';
import { join } from 'node:path';

// Every setting comes from worker/.env; see .env.example.
const env = process.env;

export const config = {
  // How often to look for new feedback, as a cron pattern. Every 2 minutes while
  // testing; '*/30 * * * *' is every 30 minutes.
  schedule: env.SCHEDULE ?? '*/30 * * * *',
  // The clone of this repository that Claude works in. It is separate from any
  // clone a person works in, so the two never edit the same files.
  repoDir: env.REPO_DIR ?? join(homedir(), 'feedback-worker', 'robotics-basics'),
  repoUrl: env.REPO_URL ?? 'git@github.com:RobinNagpal/robotics-basics.git',
  claudeBin: env.CLAUDE_BIN ?? 'claude',
  model: env.CLAUDE_MODEL || undefined,
  // One Claude turn that takes longer than this is stopped, and that page's
  // feedback marked failed.
  timeoutMinutes: Number(env.TIMEOUT_MINUTES ?? 60),
  // A run that is due while another is still working waits this long for it to
  // finish, and is skipped if it is still going.
  waitMinutes: Number(env.WAIT_MINUTES ?? 60),
  // Where the worker keeps the ID of its Claude Code session.
  stateFile: join(import.meta.dirname, '.state', 'session.json'),
};
