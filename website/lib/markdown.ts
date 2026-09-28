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

function isExternal(href: string): boolean {
  return /^[a-z][a-z0-9+.-]*:/i.test(href) || href.startsWith('//');
}

/**
 * Adapts the rendered doc to the site without touching its words:
 * rewrites links between docs to site URLs, points images at the docs folder,
 * lifts the H1 into the page header, collects the table of contents, and wraps
 * tables and lone images so they lay out well.
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
      if (tag === 'p') {
        const meaningful = node.children.filter((c) => !(c.type === 'text' && !c.value.trim()));
        const img = meaningful.length === 1 ? meaningful[0] : undefined;
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
