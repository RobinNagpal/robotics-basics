import path from 'node:path';
import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkGfm from 'remark-gfm';
import remarkRehype from 'remark-rehype';
import rehypeRaw from 'rehype-raw';
import rehypeSlug from 'rehype-slug';
import rehypeHighlight from 'rehype-highlight';
import rehypeStringify from 'rehype-stringify';
import { visit, SKIP } from 'unist-util-visit';
import type { Root, Element, ElementContent } from 'hast';
import { getLibrary, readSource, plainInline, type Section } from './content';

export type TocItem = { id: string; text: string; depth: 2 | 3 };

export type Rendered = { html: string; toc: TocItem[] };

const posix = path.posix;

function textOf(node: ElementContent | Element): string {
  if (node.type === 'text') return node.value;
  if (node.type === 'element') return node.children.map(textOf).join('');
  return '';
}

function assetUrl(docsRel: string): string {
  return '/docs-assets/' + docsRel.split('/').map(encodeURIComponent).join('/');
}

/**
 * The embed address for a YouTube watch link, keeping its start time, or null
 * if the link is not a YouTube video. Accepts youtube.com/watch?v= and youtu.be/.
 */
function youtubeEmbed(href: string): string | null {
  let url: URL;
  try {
    url = new URL(href);
  } catch {
    return null;
  }
  const host = url.hostname.replace(/^(www\.|m\.)/, '');
  let id: string | null = null;
  if (host === 'youtube.com' && url.pathname === '/watch') id = url.searchParams.get('v');
  else if (host === 'youtu.be') id = url.pathname.slice(1);
  if (!id || !/^[\w-]{11}$/.test(id)) return null;
  // t is either plain seconds ("3959", "3959s") or "1h5m59s".
  const t = url.searchParams.get('t') ?? '';
  const parts = t.match(/^(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s?)?$/);
  const start = parts ? Number(parts[1] ?? 0) * 3600 + Number(parts[2] ?? 0) * 60 + Number(parts[3] ?? 0) : 0;
  return `https://www.youtube-nocookie.com/embed/${id}` + (start > 0 ? `?start=${start}` : '');
}

/**
 * The address of a film a doc asks to be played in the page, or null if the
 * link is not one.
 *
 * A film is too large to commit, so it is uploaded to the same bucket the site
 * is served from, under `/videos/`, exactly as a recording is. The doc links to
 * it by its full address, which means the link still works when the Markdown is
 * read on GitHub, where no player is built. Only the two formats every browser
 * can play are accepted, so a link to something else stays a plain link rather
 * than becoming a player that shows nothing.
 */
function filmSrc(href: string): string | null {
  const path = href.split(/[?#]/)[0];
  if (!/\.(mp4|webm)$/i.test(path)) return null;
  return href;
}

function isExternal(href: string): boolean {
  return /^[a-z][a-z0-9+.-]*:/i.test(href) || href.startsWith('//');
}

/**
 * Adapts the rendered doc to the site without touching its words:
 * rewrites links between docs to site URLs, points images at the docs folder,
 * lifts the H1 into the page header, collects the table of contents, wraps
 * tables and lone images so they lay out well, and turns the films and the
 * YouTube videos a doc asks for into players.
 */
function rehypeDocs(opts: { rel: string; urlByRel: Map<string, string>; toc: TocItem[] }) {
  const dir = posix.dirname(opts.rel);

  const resolve = (target: string) => {
    const [p, ...rest] = target.split('#');
    const frag = rest.join('#');
    let decoded = p;
    try {
      decoded = decodeURIComponent(p);
    } catch {}
    const resolved = decoded ? posix.normalize(posix.join(dir, decoded)).replace(/\/$/, '') : opts.rel;
    return { resolved, frag };
  };

  return (tree: Root) => {
    let h1Done = false;

    visit(tree, 'element', (node, index, parent) => {
      const tag = node.tagName;

      if (tag === 'h1' && !h1Done && parent && typeof index === 'number') {
        h1Done = true;
        parent.children.splice(index, 1);
        return [SKIP, index];
      }

      if ((tag === 'h2' || tag === 'h3') && node.properties?.id) {
        const id = String(node.properties.id);
        opts.toc.push({ id, text: textOf(node).trim(), depth: tag === 'h2' ? 2 : 3 });
        node.children.push({
          type: 'element',
          tagName: 'a',
          properties: { href: `#${id}`, className: ['heading-anchor'], ariaLabel: 'Link to this heading' },
          children: [{ type: 'text', value: '#' }],
        });
        return;
      }

      // A paragraph holding only an image becomes a figure with its alt text as caption.
      // A paragraph holding only a link to a film titled "video", written
      // [Title](https://docs.dodao.io/videos/....mp4 "video"), becomes a player
      // with the link as its caption, so the film can be watched in the page and
      // still be a plain link on GitHub.
      // A paragraph holding only a YouTube link titled "embed", written
      // [Title](https://www.youtube.com/watch?v=... "embed"), becomes the video
      // itself with the link as its caption. On GitHub it stays a plain link.
      if (tag === 'p') {
        const meaningful = node.children.filter((c) => !(c.type === 'text' && !c.value.trim()));
        const img = meaningful.length === 1 ? meaningful[0] : undefined;
        if (img && img.type === 'element' && img.tagName === 'a' && img.properties?.title === 'video') {
          const src = filmSrc(String(img.properties.href ?? ''));
          if (src) {
            delete img.properties.title;
            node.tagName = 'figure';
            node.properties = { className: ['doc-figure', 'doc-film'] };
            node.children = [
              {
                type: 'element',
                tagName: 'video',
                properties: { src, controls: true, preload: 'metadata', playsInline: true },
                children: [],
              },
              { type: 'element', tagName: 'figcaption', properties: {}, children: [img] },
            ];
          }
          return;
        }
        if (img && img.type === 'element' && img.tagName === 'a' && img.properties?.title === 'embed') {
          const href = String(img.properties.href ?? '');
          const src = youtubeEmbed(href);
          if (src) {
            const title = textOf(img).trim();
            delete img.properties.title;
            node.tagName = 'figure';
            node.properties = { className: ['doc-figure', 'doc-video'] };
            node.children = [
              {
                type: 'element',
                tagName: 'div',
                properties: { className: ['video-frame'] },
                children: [
                  {
                    type: 'element',
                    tagName: 'iframe',
                    properties: {
                      src,
                      title,
                      loading: 'lazy',
                      allow: 'accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share',
                      allowFullScreen: true,
                      referrerPolicy: 'strict-origin-when-cross-origin',
                    },
                    children: [],
                  },
                ],
              },
              { type: 'element', tagName: 'figcaption', properties: {}, children: [img] },
            ];
          }
          return;
        }
        if (img && img.type === 'element' && img.tagName === 'img') {
          const alt = String(img.properties?.alt ?? '').trim();
          node.tagName = 'figure';
          node.properties = { className: ['doc-figure'] };
          node.children = [img];
          if (alt) {
            node.children.push({ type: 'element', tagName: 'figcaption', properties: {}, children: [{ type: 'text', value: alt }] });
          }
        }
        return;
      }

      if (tag === 'img') {
        const src = String(node.properties?.src ?? '');
        if (src && !isExternal(src) && !src.startsWith('data:')) {
          const { resolved } = resolve(src);
          if (!resolved.startsWith('..')) node.properties.src = assetUrl(resolved);
        }
        node.properties.loading = 'lazy';
        node.properties.decoding = 'async';
        return;
      }

      if (tag === 'a') {
        const href = String(node.properties?.href ?? '');
        if (!href || href.startsWith('#')) return;
        if (isExternal(href)) {
          node.properties.target = '_blank';
          node.properties.rel = ['noopener', 'noreferrer'];
          node.properties.className = ['external'];
          return;
        }
        const { resolved, frag } = resolve(href);
        const url = opts.urlByRel.get(resolved);
        if (url) {
          node.properties.href = url + (frag ? `#${frag}` : '');
        } else if (!resolved.startsWith('..') && !resolved.endsWith('.md')) {
          node.properties.href = assetUrl(resolved);
          node.properties.target = '_blank';
        } else {
          // Points at code or files elsewhere in the repo; show it, but not as a dead link.
          node.tagName = 'span';
          node.properties = {
            className: ['repo-ref'],
            title: `In the robotics-basics repository: ${posix.normalize(posix.join('docs', resolved))}`,
          };
        }
        return;
      }

      if (tag === 'table' && parent && typeof index === 'number') {
        parent.children[index] = {
          type: 'element',
          tagName: 'div',
          properties: { className: ['table-wrap'] },
          children: [node],
        };
        return [SKIP, index + 1];
      }
    });
  };
}

export async function renderSection(section: Section): Promise<Rendered> {
  const { urlByRel } = getLibrary();
  const toc: TocItem[] = [];
  const file = await unified()
    .use(remarkParse)
    .use(remarkGfm)
    .use(remarkRehype, { allowDangerousHtml: true })
    .use(rehypeRaw)
    .use(rehypeSlug)
    .use(rehypeDocs, { rel: section.rel, urlByRel, toc })
    .use(rehypeHighlight, { detect: false })
    .use(rehypeStringify)
    .process(readSource(section.rel));
  return { html: String(file), toc };
}

/** A plain-text version of a doc, for search. */
export function plainText(src: string): string {
  return plainInline(
    src
      .replace(/```[\s\S]*?```/g, ' ')
      .replace(/^#{1,6}\s+/gm, '')
      .replace(/^\s*[-*]\s+/gm, '')
      .replace(/\|/g, ' ')
      .replace(/-{3,}/g, ' '),
  );
}

export function headingsOf(src: string): string[] {
  return [...src.replace(/```[\s\S]*?```/g, '').matchAll(/^#{2,3}\s+(.+)$/gm)].map((m) => plainInline(m[1]));
}
