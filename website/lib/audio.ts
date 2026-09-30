import fs from 'node:fs';
import path from 'node:path';

/**
 * Which pages have a recording, and how big it is.
 *
 * The recordings themselves are not in this repository: they are made by
 * `narration/narrate.py` and uploaded to the same bucket the site is served
 * from, under `/audio/`. What is in the repository is the manifest that script
 * writes, which lists what exists.
 *
 * The site is a static export, so it has to know at build time whether a page
 * has a recording. Asking the network at build time would tie the build to the
 * bucket, and letting the browser try and fail would show a player that then
 * vanishes. Reading a committed manifest does neither.
 */

const MANIFEST = path.resolve(process.cwd(), '..', 'narration', 'manifest.json');

type Entry = { bytes: number };

let cached: Record<string, Entry> | null = null;

function manifest(): Record<string, Entry> {
  if (cached !== null) return cached;
  try {
    cached = JSON.parse(fs.readFileSync(MANIFEST, 'utf8')) as Record<string, Entry>;
  } catch {
    // No manifest yet, or an unreadable one. A book with no recordings is a
    // normal state, so the site renders without players rather than failing.
    cached = {};
  }
  return cached;
}

/**
 * The recording for a page, or null when there is none.
 *
 * `url` is the section's own address, such as `/programming-techniques/
 * fitting-and-estimation/ransac`, which is the key the narration script writes
 * the manifest under. The returned source is a relative path, so it is served
 * from whatever origin the page itself came from and needs no CORS permission.
 */
export function audioFor(url: string): { src: string; bytes: number } | null {
  const key = url.replace(/^\/+/, '');
  const entry = manifest()[key];
  if (entry === undefined) return null;
  return { src: `/audio/${key}.mp3`, bytes: entry.bytes };
}
