import fs from 'node:fs/promises';
import path from 'node:path';
import { DOCS_DIR } from '@/lib/content';

// Serves the images and other files that the docs link to, straight from docs/.
//
// The site is exported as static files, so this runs at build time rather than
// per request: generateStaticParams below lists every asset the docs hold, and
// each one is written out as a real file. Nothing here executes in production.

const TYPES: Record<string, string> = {
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.webp': 'image/webp',
  '.avif': 'image/avif',
  '.mp4': 'video/mp4',
  '.webm': 'video/webm',
  '.pdf': 'application/pdf',
  '.json': 'application/json',
  '.txt': 'text/plain; charset=utf-8',
};

export const dynamic = 'force-static';

/**
 * Every asset under docs/, as path segments.
 *
 * An export has to be told what to write, and a catch-all route is given no
 * list of its own. Walking the directory is that list, and it is the same
 * source of truth the rest of the site uses: add an image to docs/ and the
 * next build publishes it, with nothing to keep in step by hand.
 *
 * Only extensions in TYPES are returned. The Markdown itself is read by the
 * page routes and must not be published as a downloadable copy alongside them.
 */
export async function generateStaticParams(): Promise<{ path: string[] }[]> {
  const found: { path: string[] }[] = [];

  async function walk(dir: string, segments: string[]): Promise<void> {
    let entries;
    try {
      entries = await fs.readdir(dir, { withFileTypes: true });
    } catch {
      return; // a docs tree without this folder is not an error
    }

    for (const entry of entries) {
      // Leading dots are editor and VCS clutter, never linked from a doc.
      if (entry.name.startsWith('.')) continue;

      const next = [...segments, entry.name];
      if (entry.isDirectory()) {
        await walk(path.join(dir, entry.name), next);
      } else if (TYPES[path.extname(entry.name).toLowerCase()]) {
        found.push({ path: next });
      }
    }
  }

  await walk(DOCS_DIR, []);
  return found;
}

export async function GET(_req: Request, { params }: { params: Promise<{ path: string[] }> }) {
  const parts = (await params).path.map((p) => decodeURIComponent(p));
  const file = path.resolve(DOCS_DIR, ...parts);
  if (!file.startsWith(DOCS_DIR + path.sep)) return new Response('Not found', { status: 404 });

  const type = TYPES[path.extname(file).toLowerCase()];
  if (!type) return new Response('Not found', { status: 404 });

  try {
    const body = await fs.readFile(file);
    return new Response(new Uint8Array(body), {
      headers: {
        'Content-Type': type,
        'Cache-Control': 'public, max-age=3600, stale-while-revalidate=86400',
        // SVGs are served from the site's origin, so stop them running scripts.
        'Content-Security-Policy': "default-src 'none'; style-src 'unsafe-inline'; img-src data:; font-src data:",
      },
    });
  } catch {
    return new Response('Not found', { status: 404 });
  }
}
