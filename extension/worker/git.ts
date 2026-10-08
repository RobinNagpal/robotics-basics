import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync } from 'node:fs';
import { dirname } from 'node:path';
import { config } from './config';

const git = (...args: string[]) =>
  execFileSync('git', ['-C', config.repoDir, ...args], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim();

// Puts the clone exactly on main as it is on GitHub, making the clone first if
// it is missing. Anything a stopped or failed run left behind is thrown away, so
// each page starts clean. Ignored files, such as the .env, are kept.
export function resetToMain() {
  if (!existsSync(config.repoDir)) {
    mkdirSync(dirname(config.repoDir), { recursive: true });
    execFileSync('git', ['clone', config.repoUrl, config.repoDir], { stdio: 'ignore' });
  }
  git('fetch', 'origin', 'main');
  git('checkout', '-q', 'main');
  git('reset', '-q', '--hard', 'origin/main');
  git('clean', '-q', '-fd');
}

// Pushes what Claude committed for one page, and returns the short hash of the
// last commit, or null when there was nothing to push. Claude is asked to commit
// its work; anything it changed but left uncommitted is committed here, so no
// edit is lost. main may have moved while Claude worked, so the commits are
// rebased onto it first.
export function pushPage(page: string): string | null {
  if (git('status', '--porcelain')) {
    git('add', '-A');
    git('commit', '-q', '-m', `Address reader feedback on ${page}`);
  }
  if (git('rev-list', '--count', 'origin/main..HEAD') === '0') return null;
  git('pull', '-q', '--rebase', 'origin', 'main');
  git('push', '-q', 'origin', 'HEAD:main');
  return git('rev-parse', '--short', 'HEAD');
}
