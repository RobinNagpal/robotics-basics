import { spawn } from 'node:child_process';
import { config } from './config';
import type { State } from './session';

export interface ClaudeResult {
  isError: boolean;
  text: string;
  structured?: unknown;
  costUsd?: number;
}

// Runs one turn of the session without a terminal, with `claude -p`, and reads
// the result that --output-format json prints. The first turn creates the session
// with the stored ID, and every later turn resumes it, so all turns are one
// conversation.
export function runTurn(session: State, prompt: string, schema?: object): Promise<ClaudeResult> {
  const args = ['-p', prompt, '--output-format', 'json'];
  args.push(...(session.created ? ['--resume', session.sessionId] : ['--session-id', session.sessionId]));
  if (schema) args.push('--json-schema', JSON.stringify(schema));
  if (config.model) args.push('--model', config.model);
  // Nobody is there to answer a permission prompt, and Claude has to edit files,
  // run the link check and push. So it runs with every permission, in a clone
  // that exists only for this.
  args.push('--permission-mode', 'bypassPermissions');

  return new Promise((resolve, reject) => {
    const child = spawn(config.claudeBin, args, { cwd: config.repoDir, stdio: ['ignore', 'pipe', 'pipe'] });
    let out = '';
    let err = '';
    child.stdout.on('data', (d) => (out += d));
    child.stderr.on('data', (d) => (err += d));
    const timer = setTimeout(() => child.kill('SIGTERM'), config.timeoutMinutes * 60_000);
    child.on('error', (e) => (clearTimeout(timer), reject(e)));
    child.on('close', (code, signal) => {
      clearTimeout(timer);
      if (signal) return reject(new Error(`Claude was stopped after ${config.timeoutMinutes} minutes`));
      try {
        const r = JSON.parse(out);
        resolve({ isError: Boolean(r.is_error), text: String(r.result ?? ''), structured: r.structured_output, costUsd: r.total_cost_usd });
      } catch {
        reject(new Error(`Claude exited with ${code}: ${(err || out).trim().slice(0, 500)}`));
      }
    });
  });
}
