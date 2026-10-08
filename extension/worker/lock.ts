import { mkdirSync, openSync, readFileSync, unlinkSync, writeSync, closeSync } from 'node:fs';
import { dirname, join } from 'node:path';

// Only one run may use the Claude Code session at a time, whether it was started
// by the schedule or by hand with `npm run once`. A run holds this file while it
// works. The file holds the run's process ID, so a file left by a process that
// has died is recognised and removed.
const LOCK = join(import.meta.dirname, '.state', 'run.lock');
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

const alive = (pid: number) => {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
};

// Waits until no other run is in progress, for at most maxWaitMs. Returns a
// function that releases the lock, or null if the other run was still going when
// the time ran out.
export async function acquire(maxWaitMs: number, onWait: () => void): Promise<(() => void) | null> {
  mkdirSync(dirname(LOCK), { recursive: true });
  const until = Date.now() + maxWaitMs;
  let told = false;
  for (;;) {
    try {
      const fd = openSync(LOCK, 'wx');
      writeSync(fd, String(process.pid));
      closeSync(fd);
      return () => unlinkSync(LOCK);
    } catch (e) {
      if ((e as NodeJS.ErrnoException).code !== 'EEXIST') throw e;
    }
    const holder = Number(readFileSync(LOCK, 'utf8'));
    if (!alive(holder)) {
      unlinkSync(LOCK);
      continue;
    }
    if (Date.now() >= until) return null;
    if (!told) onWait(), (told = true);
    await sleep(10_000);
  }
}
