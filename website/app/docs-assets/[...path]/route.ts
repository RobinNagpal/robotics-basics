import fs from 'node:fs/promises';
import path from 'node:path';
import { DOCS_DIR } from '@/lib/content';

// Serves the images and other files that the docs link to, straight from docs/.

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
