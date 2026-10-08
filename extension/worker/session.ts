import { randomUUID } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, join } from 'node:path';
import { config } from './config';

// The worker always talks to one Claude Code session, so Claude keeps what it
// learned about the docs from one piece of feedback to the next. The session's
// ID is kept in a file. Until the first run has made the session, the ID is a
// new one that the first run creates the session with.
export interface State {
  sessionId: string;
  created: boolean;
}

export function loadSession(): State {
  const state: State = existsSync(config.stateFile)
    ? JSON.parse(readFileSync(config.stateFile, 'utf8'))
    : { sessionId: randomUUID(), created: false };
  // Claude Code keeps each session as a file under the folder's own name in
  // ~/.claude/projects. If that file exists the session was made, even if the
  // run that made it was stopped before the worker could note it.
  state.created ||= existsSync(sessionFile(state.sessionId));
  if (!existsSync(config.stateFile)) saveSession(state);
  return state;
}

function sessionFile(id: string) {
  return join(homedir(), '.claude', 'projects', config.repoDir.replace(/[^a-zA-Z0-9]/g, '-'), `${id}.jsonl`);
}

export function saveSession(state: State) {
  mkdirSync(dirname(config.stateFile), { recursive: true });
  writeFileSync(config.stateFile, JSON.stringify(state, null, 2) + '\n');
}
