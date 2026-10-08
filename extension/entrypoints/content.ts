import { highlights, pageKey, remove, save, user, visible } from '@/lib/store';
import { COLORS, type Highlight } from '@/lib/types';

const ROOT = 'article.prose'; // where the site puts the page text
const CONTEXT = 32; // characters kept on each side to find the text again

export default defineContentScript({
  matches: ['https://docs.dodao.io/*'],
  main(ctx) {
    document.head.append(Object.assign(document.createElement('style'), { textContent: CSS }));
    const bar = div('dh-bar');
    const pop = div('dh-pop');
    document.body.append(bar, pop);

    const render = async () => {
      const root = document.querySelector<HTMLElement>(ROOT);
      if (!root) return;
      unwrapAll(root);
      const { book, chapter, page } = pageKey(location.href);
      for (const h of visible(await highlights.getValue())) {
        if (h.book === book && h.chapter === chapter && h.page === page) wrap(root, h);
      }
    };
    render();
    highlights.watch(render);
    ctx.addEventListener(window, 'wxt:locationchange', () => setTimeout(render, 500));

    // Selecting text shows a small bar of colours.
    ctx.addEventListener(document, 'mouseup', async (e) => {
      if (bar.contains(e.target as Node) || pop.contains(e.target as Node)) return;
      bar.style.display = 'none';
      const sel = getSelection();
      const root = document.querySelector<HTMLElement>(ROOT);
      const author = await user.getValue();
      if (!sel || sel.isCollapsed || !root || !author) return;
      const range = sel.getRangeAt(0);
      if (!root.contains(range.commonAncestorContainer) || !range.toString().trim()) return;

      bar.replaceChildren(
        ...COLORS.map((color) => button('', () => create(color), color)),
        button('💬', async () => openNote(await create(COLORS[0]))),
      );
      place(bar, range.getBoundingClientRect());

      async function create(color: string) {
        const full = textOf(root!);
        const start = offset(root!, range.startContainer, range.startOffset);
        const end = offset(root!, range.endContainer, range.endOffset);
        const h: Highlight = {
          id: crypto.randomUUID(),
          ...pageKey(location.href),
          section: sectionOf(root!, range.startContainer),
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

    function openNote(h: Highlight) {
      const mark = document.querySelector(`mark[data-hl="${h.id}"]`);
      if (!mark) return;
      const note = Object.assign(document.createElement('textarea'), {
        value: h.note,
        placeholder: 'Add a comment…',
      });
      pop.replaceChildren(
        note,
        div('dh-row', [
          ...COLORS.map((color) => button('', () => save({ ...h, color }), color)),
          button('Delete', () => (remove(h.id), (pop.style.display = 'none'))),
          button('Save', () => (save({ ...h, note: note.value }), (pop.style.display = 'none'))),
        ]),
      );
      place(pop, mark.getBoundingClientRect());
      note.focus();
    }
  },
});

// All the text under root, in the same order Range.toString() reads it.
function textNodes(root: Node) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const nodes: Text[] = [];
  while (walker.nextNode()) nodes.push(walker.currentNode as Text);
  return nodes;
}
// The text of the last heading before node, so a comment says which section of the
// page it is about. Text above the first heading has no section.
function sectionOf(root: HTMLElement, node: Node) {
  let found = '';
  for (const h of root.querySelectorAll('h1, h2, h3, h4')) {
    if (h.compareDocumentPosition(node) & Node.DOCUMENT_POSITION_FOLLOWING) found = h.textContent?.trim() ?? '';
    else break;
  }
  return found;
}

const textOf = (root: Node) => textNodes(root).map((n) => n.data).join('');

function offset(root: Node, node: Node, off: number) {
  const r = document.createRange();
  r.setStart(root, 0);
  r.setEnd(node, off);
  return r.toString().length;
}

// Find the highlight's text on the page and wrap it, one <mark> per text node.
function wrap(root: HTMLElement, h: Highlight) {
  const full = textOf(root);
  let start = full.indexOf(h.prefix + h.text + h.suffix);
  start = start >= 0 ? start + h.prefix.length : full.indexOf(h.text);
  if (start < 0 || !h.text) return;
  const end = start + h.text.length;

  let pos = 0;
  for (const node of textNodes(root)) {
    const a = Math.max(start, pos) - pos;
    const b = Math.min(end, pos + node.length) - pos;
    pos += node.length;
    if (a >= b) continue;
    const piece = node.splitText(a);
    piece.splitText(b - a);
    const mark = document.createElement('mark');
    mark.dataset.hl = h.id;
    mark.style.background = h.color;
    if (h.note) mark.title = h.note;
    piece.replaceWith(mark);
    mark.append(piece);
  }
}

function unwrapAll(root: HTMLElement) {
  root.querySelectorAll('mark[data-hl]').forEach((m) => m.replaceWith(...m.childNodes));
  root.normalize();
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
