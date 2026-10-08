import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync } from 'node:fs';
import { dirname } from 'node:path';
import { config } from './config';

const git = (...args: string[]) =>
  execFileSync('git', ['-C', config.repoDir, ...args], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim();

// The clone is made once, the first time it is needed, and kept from then on.
export function ensureClone() {
  if (existsSync(config.repoDir)) return;
  mkdirSync(dirname(config.repoDir), { recursive: true });
  execFileSync('git', ['clone', config.repoUrl, config.repoDir], { stdio: 'ignore' });
}

// Brings the clone up to the latest main. Commits made here that are not on
// GitHub yet are kept, by rebasing them onto it. Returns null when that worked,
// or git's own explanation when it did not, such as uncommitted edits, a rebase
// that stopped part-way, or a conflict.
export function pullLatest(): string | null {
  try {
    git('checkout', '-q', 'main');
    git('pull', '-q', '--rebase', 'origin', 'main');
    return null;
  } catch (e) {
    const err = e as { stderr?: string; message: string };
    return (err.stderr || err.message).trim();
  }
}

export const status = () => git('status');

// Pushes what Claude committed for one page, and returns the short hash of the
// last commit, or null when there was nothing to push. Claude is asked to commit
// its work; anything it changed but left uncommitted is committed here, so no
// edit is lost. main may have moved while Claude worked, so the commits are
// rebased onto it first. If that fails, the error is thrown and the clone is
// left as it is, for the next run's pull to sort out.
export function pushPage(page: string): string | null {
  if (git('status', '--porcelain')) {
    git('add', '-A');
    git('commit', '-q', '-m', `Address reader feedback on ${page}`);
  }
  git('fetch', '-q', 'origin', 'main');
  if (git('rev-list', '--count', 'origin/main..HEAD') === '0') return null;
  git('pull', '-q', '--rebase', 'origin', 'main');
  git('push', '-q', 'origin', 'HEAD:main');
  return git('rev-parse', '--short', 'HEAD');
}
