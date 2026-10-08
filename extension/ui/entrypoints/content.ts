import { highlights, pageKey, remove, save, user, visible } from '@/lib/store';
import { COLORS, validPage, type Highlight } from '@/lib/types';

// The parts of a docs page that can be highlighted: the page title, which the
// site puts in the header above the text, and the text itself with its headings.
const REGIONS = 'header.doc-header h1, article.prose';
// The '#' link the site adds to each heading. It is not part of the words.
const SKIP = '.heading-anchor';
const CONTEXT = 32; // characters kept on each side to find the text again

export default defineContentScript({
  matches: ['https://docs.dodao.io/*'],
  main(ctx) {
    document.head.append(Object.assign(document.createElement('style'), { textContent: CSS }));
    const bar = div('dh-bar');
    const pop = div('dh-pop');
    document.body.append(bar, pop);

    // Removes every mark and draws them again. Two draws must never overlap: the
    // second would wrap the first one's marks again, and each highlight would be
    // drawn twice. So a draw asked for while one runs waits, and runs once after.
    const draw = async () => {
      const roots = regions();
      if (!roots.length) return;
      unwrapAll(roots);
      const { book, chapter, page } = pageKey(location.href);
      for (const h of visible(await highlights.getValue())) {
        if (h.book === book && h.chapter === chapter && h.page === page) wrap(roots, h);
      }
    };
    let running: Promise<void> | null = null;
    let again = false;
    const render = (): Promise<void> => {
      if (running) return ((again = true), running);
      return (running = (async () => {
        do {
          again = false;
          await draw();
        } while (again);
        running = null;
      })());
    };
    render();
    highlights.watch(render);
    ctx.addEventListener(window, 'wxt:locationchange', () => setTimeout(render, 500));

    // Selecting text shows a small bar of colours.
    ctx.addEventListener(document, 'mouseup', async (e) => {
      if (bar.contains(e.target as Node) || pop.contains(e.target as Node)) return;
      bar.style.display = 'none';
      const sel = getSelection();
      const roots = regions();
      const author = await user.getValue();
      // Only a page with a book, a chapter and a page in its address can be
      // stored, so nothing can be highlighted on any other page.
      if (!sel || sel.isCollapsed || !roots.length || !author || !validPage(pageKey(location.href))) return;
      const range = sel.getRangeAt(0);
      const inside = (n: Node) => roots.some((r) => r.contains(n));
      if (!inside(range.startContainer) || !inside(range.endContainer) || !range.toString().trim()) return;

      bar.replaceChildren(
        ...COLORS.map((color) => button('', () => create(color), color)),
        button('💬', async () => openNote(await create(COLORS[0]))),
      );
      place(bar, range.getBoundingClientRect());

      async function create(color: string) {
        const nodes = textNodes(roots);
        const full = nodes.map((n) => n.data).join('');
        const start = position(nodes, range.startContainer, range.startOffset);
        const end = position(nodes, range.endContainer, range.endOffset);
        const h: Highlight = {
          id: crypto.randomUUID(),
          ...pageKey(location.href),
          section: sectionOf(range.startContainer),
          url: location.href,
          text: full.slice(start, end),
          prefix: full.slice(Math.max(0, start - CONTEXT), start),
          suffix: full.slice(end, end + CONTEXT),
          color,
          note: '',
          author: author!,
          createdAt: Date.now(),
          updatedAt: Date.now(),
        };
        sel!.removeAllRanges();
        bar.style.display = 'none';
        await save(h);
        await render(); // so openNote finds the new <mark>
        return h;
      }
    });

    // Clicking a highlight opens its note.
    ctx.addEventListener(document, 'click', async (e) => {
      const mark = (e.target as HTMLElement).closest?.('mark[data-hl]') as HTMLElement | null;
      const h = mark && (await highlights.getValue())[mark.dataset.hl!];
      if (h) return openNote(h);
      if (!pop.contains(e.target as Node)) pop.style.display = 'none';
    });

    function openNote(original: Highlight) {
      // A colour click changes this copy, so a later Save keeps the new colour.
      let h = original;
      const mark = document.querySelector(`mark[data-hl="${h.id}"]`);
      if (!mark) return;
      const note = Object.assign(document.createElement('textarea'), {
        value: h.note,
        placeholder: 'Add a comment…',
      });
      pop.replaceChildren(
        note,
        div('dh-row', [
          ...COLORS.map((color) => button('', () => save((h = { ...h, color })), color)),
          button('Delete', () => (remove(h.id), (pop.style.display = 'none'))),
          button('Save', () => (save({ ...h, note: note.value }), (pop.style.display = 'none'))),
        ]),
      );
      place(pop, mark.getBoundingClientRect());
      note.focus();
    }
  },
});

const regions = () => [...document.querySelectorAll<HTMLElement>(REGIONS)];

// Every text node in the regions, in page order, leaving out the heading links.
// Positions in a highlight count characters along this list.
function textNodes(roots: HTMLElement[]) {
  const nodes: Text[] = [];
  for (const root of roots) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: (n) => (n.parentElement?.closest(SKIP) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT),
    });
    while (walker.nextNode()) nodes.push(walker.currentNode as Text);
  }
  return nodes;
}

// How many characters of the list come before a point in the page. The point is
// where a selection starts or ends, and it may sit in a text node or between two
// elements; comparing it with each text node handles both.
function position(nodes: Text[], node: Node, off: number) {
  let pos = 0;
  const r = document.createRange();
  for (const t of nodes) {
    r.selectNodeContents(t);
    const where = r.comparePoint(node, off);
    if (where < 0) break; // the point is before this text node
    if (where === 0) return pos + (node === t ? off : 0);
    pos += t.length;
  }
  return pos;
}

// The text of the last heading before node, so a comment says which section of the
// page it is about. Text above the first heading, and the page title, have no section.
function sectionOf(node: Node) {
  let found = '';
  for (const h of document.querySelectorAll('article.prose :is(h2, h3, h4)')) {
    if (!(h.compareDocumentPosition(node) & Node.DOCUMENT_POSITION_FOLLOWING)) break;
    found = textNodes([h as HTMLElement]).map((n) => n.data).join('').trim();
  }
  return found;
}

// Find the highlight's text on the page and wrap it, one <mark> per text node.
function wrap(roots: HTMLElement[], h: Highlight) {
  const nodes = textNodes(roots);
  const full = nodes.map((n) => n.data).join('');
  let start = full.indexOf(h.prefix + h.text + h.suffix);
  start = start >= 0 ? start + h.prefix.length : full.indexOf(h.text);
  if (start < 0 || !h.text) return;
  const end = start + h.text.length;

  let pos = 0;
  for (const node of nodes) {
    const a = Math.max(start, pos) - pos;
    const b = Math.min(end, pos + node.length) - pos;
    pos += node.length;
    if (a >= b) continue;
    const piece = node.splitText(a);
    piece.splitText(b - a);
    // The line breaks between two blocks are part of a selection that crosses
    // them, but a mark there would show nothing, and inside a list it is not
    // allowed at all.
    if (!piece.data.trim()) continue;
    const mark = document.createElement('mark');
    mark.dataset.hl = h.id;
    mark.style.background = h.color;
    if (h.note) mark.title = h.note;
    piece.replaceWith(mark);
    mark.append(piece);
  }
}

function unwrapAll(roots: HTMLElement[]) {
  for (const root of roots) {
    root.querySelectorAll('mark[data-hl]').forEach((m) => m.replaceWith(...m.childNodes));
    root.normalize();
  }
}

function div(cls: string, children: Node[] = []) {
  const el = document.createElement('div');
  el.className = cls;
  el.append(...children);
  return el;
}

function button(label: string, onClick: () => unknown, color?: string) {
  const b = document.createElement('button');
  b.textContent = label;
  if (color) Object.assign(b.style, { background: color }), (b.className = 'dh-dot');
  b.onclick = (e) => (e.stopPropagation(), onClick());
  return b;
}

function place(el: HTMLElement, rect: DOMRect) {
  el.style.display = 'flex';
  el.style.top = `${rect.bottom + scrollY + 6}px`;
  el.style.left = `${rect.left + scrollX}px`;
}

const CSS = `
mark[data-hl] { color: inherit; cursor: pointer; border-radius: 2px; }
.dh-bar, .dh-pop { position: absolute; z-index: 2147483647; display: none; gap: 6px; padding: 6px;
  background: #fff; border: 1px solid #ddd; border-radius: 8px; box-shadow: 0 4px 16px #0002;
  font: 13px system-ui, sans-serif; color: #111; }
.dh-pop { flex-direction: column; width: 260px; }
.dh-pop textarea { height: 70px; resize: vertical; font: inherit; padding: 4px; }
.dh-row { display: flex; gap: 6px; align-items: center; }
.dh-bar button, .dh-pop button { border: 1px solid #ccc; border-radius: 6px; background: #f6f6f6; cursor: pointer; font: inherit; }
.dh-dot { width: 20px; height: 20px; border-radius: 50% !important; padding: 0; }
`;
