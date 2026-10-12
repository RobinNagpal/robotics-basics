import { focused, highlights, pageKey, remove, save, user, visible } from '@/lib/store';
import { COLORS, QUEUEABLE, shownStatus, statusLabel, validPage, type Highlight } from '@/lib/types';

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
        await goToFocused();
      })());
    };
    render();
    highlights.watch(render);
    // The popup writes down which highlight the reader asked to be taken to, and
    // then sends this tab to the page. Scrolling to it can only happen here,
    // because only this script knows where the text ended up on the page.
    focused.watch(() => goToFocused());
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
        className: 'dh-note',
      });
      // Where the comment stands, under it, and what Claude said once it has
      // been through a batch.
      const status = shownStatus(h);
      const answer = status
        ? [
            div('dh-row', [
              div(`dh-status dh-${status}`, [text(statusLabel(h))]),
              ...(h.batch ? [div('dh-status dh-batch', [text(`Batch ${h.batch}`)])] : []),
            ]),
            ...(h.claudeResponse
              ? [div(`dh-response${status === 'failed' ? ' dh-bad' : ''}`, [text(h.claudeResponse)])]
              : []),
          ]
        : [];
      pop.replaceChildren(
        note,
        ...answer,
        // Nothing happens to a comment until a reader asks for it, and a comment
        // that failed can be asked for again, so both say where to do that.
        ...(status && QUEUEABLE.includes(status)
          ? [div('dh-hint', [text(`Open the extension to select this comment and ${status === 'failed' ? 'try again' : 'address it'}.`)])]
          : []),
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

// Scrolls to the highlight the reader picked in the extension, and flashes it so
// that they can see which of the marks on the page it was. The request is
// cleared as soon as it is acted on, and one older than a minute is ignored: it
// was left behind by a page that never finished loading, and scrolling the
// reader somewhere else long afterwards would be worse than doing nothing.
async function goToFocused() {
  const want = await focused.getValue();
  if (!want || Date.now() - want.at > 60_000) return;
  const mark = document.querySelector<HTMLElement>(`mark[data-hl="${want.id}"]`);
  if (!mark) return;
  await focused.setValue(null);
  mark.scrollIntoView({ block: 'center', behavior: 'smooth' });
  mark.classList.add('dh-flash');
  setTimeout(() => mark.classList.remove('dh-flash'), 2000);
}

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

const text = (s: string) => document.createTextNode(s);

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

// Under the text, and moved left if it would run past the window's right edge.
function place(el: HTMLElement, rect: DOMRect) {
  el.style.display = 'flex';
  el.style.top = `${rect.bottom + scrollY + 6}px`;
  const left = Math.min(rect.left, document.documentElement.clientWidth - el.offsetWidth - 8);
  el.style.left = `${Math.max(8, left) + scrollX}px`;
}

const CSS = `
mark[data-hl] { color: #111; cursor: pointer; border-radius: 2px; } /* the colours are pale, so the text is dark even on a dark page */
/* The mark the reader came to from the extension, so they can see which it is. */
mark[data-hl].dh-flash { outline: 3px solid #2563eb; outline-offset: 2px; animation: dh-pulse 0.6s ease-in-out 3; }
@keyframes dh-pulse { 0%, 100% { outline-color: transparent; } 50% { outline-color: #2563eb; } }
.dh-bar, .dh-pop { position: absolute; z-index: 2147483647; display: none; gap: 6px; padding: 6px;
  background: #fff; border: 1px solid #ddd; border-radius: 8px; box-shadow: 0 4px 16px #0002;
  font: 13px system-ui, sans-serif; color: #111; }
.dh-pop { flex-direction: column; width: 260px; }
/* The reader's own comment and Claude's reply, each in its own colour, the same
   two colours the extension's list uses. */
.dh-pop textarea.dh-note { height: 70px; resize: vertical; font: inherit; padding: 4px;
  border: 1px solid #fcd34d; border-left: 3px solid #f59e0b; border-radius: 0 4px 4px 0; background: #fffbeb; color: #78350f; }
.dh-row { display: flex; gap: 6px; align-items: center; }
.dh-bar button, .dh-pop button { border: 1px solid #ccc; border-radius: 6px; background: #f6f6f6; cursor: pointer; font: inherit; }
.dh-status { font-size: 11px; font-weight: 600; align-self: flex-start; padding: 1px 6px; border-radius: 999px; background: #eef; color: #334; }
.dh-new { background: #f3f4f6; color: #374151; }
.dh-queued { background: #fef3c7; color: #78350f; }
.dh-working { background: #ede9fe; color: #4c1d95; }
.dh-changed { background: #dcfce7; color: #14532d; }
.dh-answered { background: #dbeafe; color: #1e3a8a; }
.dh-failed { background: #fee2e2; color: #7f1d1d; }
.dh-hint { font-size: 11px; color: #555; }
.dh-response { white-space: pre-wrap; max-height: 180px; overflow-y: auto; padding: 6px;
  border-left: 3px solid #22c55e; border-radius: 0 4px 4px 0; background: #f0fdf4; color: #14532d; }
.dh-response.dh-bad { border-left-color: #ef4444; background: #fef2f2; color: #7f1d1d; }
.dh-batch { background: #e5e7eb; color: #374151; }
.dh-dot { width: 20px; height: 20px; border-radius: 50% !important; padding: 0; }
`;
