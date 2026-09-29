#!/usr/bin/env node
/**
 * Serves the exported docs site on the shared host.
 *
 * The site is a static export, so nothing here renders anything: this is a
 * file server over the `site/` directory that the deploy puts beside it. It
 * exists because the shared host's provisioning gives every application the
 * same shape — one Node process at /srv/<app>/current/index.js listening on
 * its own port, with Caddy terminating TLS and reverse-proxying to it — and
 * fitting that shape means the host needs no special case for this site, and
 * no change to the script that provisions it.
 *
 * No dependencies on purpose. The host installs Node and nothing else, and a
 * deploy that had to run `npm install` on a box shared with two other
 * applications would be a worse trade than the hundred lines below.
 *
 *   PORT=7073 node index.js
 */

'use strict';

const http = require('node:http');
const fs = require('node:fs');
const fsp = require('node:fs/promises');
const path = require('node:path');
const { createHash } = require('node:crypto');

const PORT = Number(process.env.PORT || 7073);
// Beside this file, not inside it: the deploy ships `index.js` and `site/`
// together into /srv/<app>/current, and swaps that directory into place whole.
const ROOT = path.resolve(__dirname, 'site');

const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8',
  '.xml': 'application/xml; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.webp': 'image/webp',
  '.avif': 'image/avif',
  '.ico': 'image/x-icon',
  '.mp4': 'video/mp4',
  '.webm': 'video/webm',
  '.pdf': 'application/pdf',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.ttf': 'font/ttf',
};

/**
 * Everything under /_next/static is content-addressed — the build puts a hash
 * in the filename — so it can be cached for as long as a browser likes. Nothing
 * else can be, because /a/b/index.html keeps its URL when its content changes.
 */
function cacheControl(urlPath) {
  if (urlPath.startsWith('/_next/static/')) return 'public, max-age=31536000, immutable';
  return 'public, max-age=0, must-revalidate';
}

/**
 * Resolve a URL path to a file inside ROOT, or null if it escapes.
 *
 * The check is on the resolved absolute path rather than on the URL, because
 * `..` is only one of the ways out: a URL-encoded separator, a symlink or a
 * backslash on some platforms all resolve to somewhere else, and only the
 * resolved path shows it.
 */
function resolveInsideRoot(urlPath) {
  let decoded;
  try {
    decoded = decodeURIComponent(urlPath);
  } catch {
    return null; // malformed percent-encoding
  }
  if (decoded.includes('\0')) return null;

  const file = path.resolve(ROOT, '.' + path.posix.normalize(decoded));
  if (file !== ROOT && !file.startsWith(ROOT + path.sep)) return null;
  return file;
}

async function statFile(file) {
  try {
    const s = await fsp.stat(file);
    return s.isFile() ? s : null;
  } catch {
    return null;
  }
}

function send(res, status, headers, body) {
  res.writeHead(status, headers);
  if (body === undefined) res.end();
  else res.end(body);
}

async function sendFile(req, res, file, stat, urlPath) {
  // Weak validator built from the things that change when the file does. The
  // export rewrites every file on each deploy, so mtime alone would invalidate
  // caches that are still good; size and inode make collisions unlikely enough.
  const etag =
    'W/"' +
    createHash('sha1')
      .update(`${stat.size}-${stat.mtimeMs}-${stat.ino}`)
      .digest('base64url')
      .slice(0, 27) +
    '"';

  const headers = {
    'Content-Type': TYPES[path.extname(file).toLowerCase()] || 'application/octet-stream',
    'Content-Length': stat.size,
    'Cache-Control': cacheControl(urlPath),
    ETag: etag,
    'Last-Modified': stat.mtime.toUTCString(),
    'X-Content-Type-Options': 'nosniff',
  };

  const known = req.headers['if-none-match'];
  if (known && known.split(',').some((t) => t.trim() === etag)) {
    delete headers['Content-Length'];
    return send(res, 304, headers);
  }

  if (req.method === 'HEAD') return send(res, 200, headers);

  const stream = fs.createReadStream(file);
  stream.on('error', () => {
    // The file vanished between stat and open — a deploy swapping the
    // directory underneath us. Nothing useful to say; drop the connection
    // rather than send a half body under a 200 that promised a length.
    res.destroy();
  });
  res.writeHead(200, headers);
  stream.pipe(res);
}

async function notFound(req, res) {
  const page = path.join(ROOT, '404.html');
  const stat = await statFile(page);
  const headers = { 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff' };

  if (!stat) return send(res, 404, { ...headers, 'Content-Type': 'text/plain; charset=utf-8' }, 'Not found');
  if (req.method === 'HEAD') {
    return send(res, 404, { ...headers, 'Content-Type': TYPES['.html'], 'Content-Length': stat.size });
  }

  const body = await fsp.readFile(page);
  send(res, 404, { ...headers, 'Content-Type': TYPES['.html'], 'Content-Length': body.length }, body);
}

const server = http.createServer(async (req, res) => {
  try {
    if (req.method !== 'GET' && req.method !== 'HEAD') {
      return send(res, 405, { Allow: 'GET, HEAD', 'Content-Type': 'text/plain; charset=utf-8' }, 'Method not allowed');
    }

    // Host and scheme come from Caddy; only the path matters here.
    const urlPath = new URL(req.url, 'http://localhost').pathname;

    // Liveness, on the application's own port. Answers before touching disk so
    // it stays true even if the directory is mid-swap.
    if (urlPath === '/_health') {
      return send(res, 200, { 'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'no-store' }, 'ok');
    }

    const file = resolveInsideRoot(urlPath);
    if (file === null) return notFound(req, res);

    // An exact file: assets, /search-index.json, /404.html.
    const direct = await statFile(file);
    if (direct) return sendFile(req, res, file, direct, urlPath);

    // The export is built with trailingSlash, so a page is a directory holding
    // index.html. A request without the slash is redirected rather than served,
    // so each page has one URL and relative links inside it resolve correctly.
    if (!urlPath.endsWith('/')) {
      const asDir = await statFile(path.join(file, 'index.html'));
      if (asDir) {
        const search = req.url.slice(urlPath.length);
        return send(res, 308, { Location: urlPath + '/' + search, 'Cache-Control': 'no-store' });
      }
      return notFound(req, res);
    }

    const index = path.join(file, 'index.html');
    const stat = await statFile(index);
    if (stat) return sendFile(req, res, index, stat, urlPath);

    return notFound(req, res);
  } catch (err) {
    process.stderr.write(`error serving ${req.url}: ${err && err.stack}\n`);
    if (!res.headersSent) {
      send(res, 500, { 'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'no-store' }, 'Internal error');
    } else {
      res.destroy();
    }
  }
});

// Loopback only. Caddy is the only thing that should reach this, and the
// Lightsail firewall does not expose the port either — two locks rather than
// one, because the box is shared with other applications.
server.listen(PORT, '127.0.0.1', () => {
  process.stdout.write(`serving ${ROOT} on 127.0.0.1:${PORT}\n`);
});

// systemd restarts the unit; finishing in-flight responses first means a deploy
// does not cut off a page that was already being sent.
for (const signal of ['SIGTERM', 'SIGINT']) {
  process.on(signal, () => server.close(() => process.exit(0)));
}
