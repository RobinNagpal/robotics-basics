import { signIn, signOut } from '@/lib/auth';
import { queueFeedback } from '@/lib/queue';
import { apiUrl, highlights, lastSync, pageKey, remove, user, visible } from '@/lib/store';
import { canQueue, shownStatus, statusLabel, type LocalHighlight } from '@/lib/types';

const app = document.querySelector('#app')!;
let book = '';
let chapter = '';
let error = '';
// What the next "Address feedback" press will send, by comment id. Pressing the
// button, changing a filter or signing out empties it.
const picked = new Set<string>();
let queueing = false;
let queued = '';

// Start on the book and chapter of the page that is open.
const [tab] = await browser.tabs.query({ active: true, currentWindow: true });
if (tab?.url?.startsWith('https://docs.dodao.io/')) ({ book, chapter } = pageKey(tab.url));

async function render() {
  const email = await user.getValue();
  if (!email) {
    const url = input('Server URL', 'url', (await apiUrl.getValue()) ?? '');
    const key = input('API key', 'password');
    const form = el('form', [url, key, el('button', 'Sign in')], 'signin');
    form.onsubmit = async (e) => {
      e.preventDefault();
      try { await signIn(url.value, key.value); error = ''; browser.runtime.sendMessage('sync'); } catch (e) { error = (e as Error).message; }
      render();
    };
    app.replaceChildren(form, el('p', error, 'error'));
    (url.value ? key : url).focus();
    return;
  }

  const all = visible(await highlights.getValue());
  const books = [...new Set(all.map((h) => h.book))].sort();
  const chapters = [...new Set(all.filter((h) => h.book === book).map((h) => h.chapter))].sort();
  const shown = all
    .filter((h) => (!book || h.book === book) && (!chapter || h.chapter === chapter))
    .sort((a, b) => a.page.localeCompare(b.page) || a.createdAt - b.createdAt);
  const sync = await lastSync.getValue();
  const pending = Object.values(await highlights.getValue()).filter((h) => h.dirty).length;

  // A comment that has been queued, answered or deleted since it was ticked is
  // no longer selectable, so it drops out of the selection on its own.
  const selectable = new Map(shown.filter(canQueue).map((h) => [h.id, h]));
  for (const id of [...picked]) if (!selectable.has(id)) picked.delete(id);

  app.replaceChildren(
    el('header', [
      el('span', email),
      el('button', 'Sync', () => browser.runtime.sendMessage('sync')),
      el('button', 'Sign out', async () => (picked.clear(), await signOut(), render())),
    ]),
    el('div', [
      select('All books', books, book, (v) => ((book = v), (chapter = ''), picked.clear(), render())),
      select('All chapters', chapters, chapter, (v) => ((chapter = v), picked.clear(), render())),
    ], 'filters'),
    el('div', sync
      ? `${sync.error ? `Sync failed: ${sync.error}` : 'Synced'} at ${new Date(sync.at).toLocaleTimeString()} · ${pending} waiting`
      : 'Not synced yet', sync?.error ? 'status err' : 'status'),
    ...batchBar([...selectable.values()]),
    ...(queued ? [el('div', queued, 'queued')] : []),
    el('ul', shown.length ? shown.map(row) : [el('li', 'No highlights here yet.')]),
  );
}

// The bar that asks for a batch. It appears only when there is something here
// that can be asked for, so a list of comments Claude has already answered shows
// no bar at all.
function batchBar(selectable: LocalHighlight[]) {
  if (!selectable.length) return [];
  const allPicked = picked.size === selectable.length;
  const tickAll = checkbox(allPicked, () => {
    picked.clear();
    if (!allPicked) for (const h of selectable) picked.add(h.id);
    render();
  });
  const label = el('label', [tickAll, el('span', `Select all ${selectable.length}`)], 'pick-all');

  const button = el('button', queueing ? 'Sending…' : `Address feedback (${picked.size})`, 'primary');
  button.disabled = queueing || picked.size === 0;
  button.onclick = async () => {
    const refs = selectable.filter((h) => picked.has(h.id));
    queueing = true;
    queued = '';
    render();
    try {
      const r = await queueFeedback(refs);
      picked.clear();
      queued = `${r.queued} comment${r.queued === 1 ? '' : 's'} queued${r.skipped ? `, ${r.skipped} skipped` : ''}. The worker takes them as one batch on its next run.`;
    } catch (e) {
      queued = `Could not queue: ${(e as Error).message}`;
    } finally {
      queueing = false;
      render();
      browser.runtime.sendMessage('sync');
    }
  };
  return [el('div', [label, button], 'batch')];
}

function row(h: LocalHighlight) {
  const status = shownStatus(h);
  const li = el('li', [
    el('button', '✕', () => remove(h.id)),
    ...(canQueue(h)
      ? [checkbox(picked.has(h.id), () => ((picked.has(h.id) ? picked.delete(h.id) : picked.add(h.id)), render()))]
      : []),
    Object.assign(el('a', [el('small', h.section ? `${h.page} · ${h.section}` : h.page), el('div', h.text)]), { href: h.url, target: '_blank' }),
    ...(h.note ? [el('div', h.note, 'note')] : []),
    el('small', h.author, 'author'),
    ...(status ? [el('span', statusLabel(h), `badge ${status}`)] : []),
    ...(h.claudeResponse ? [el('div', h.claudeResponse, 'response')] : []),
  ]);
  li.style.borderColor = h.color;
  return li;
}

function el<K extends keyof HTMLElementTagNameMap>(tag: K, content: string | Node[], extra?: string | (() => unknown)) {
  const e = document.createElement(tag);
  typeof content === 'string' ? (e.textContent = content) : e.append(...content);
  if (typeof extra === 'function') e.onclick = extra;
  else if (extra) e.className = extra;
  return e;
}

function checkbox(checked: boolean, onChange: () => unknown) {
  const c = Object.assign(document.createElement('input'), { type: 'checkbox', checked, className: 'pick' });
  c.onchange = onChange;
  return c;
}

function input(placeholder: string, type: string, value = '') {
  return Object.assign(document.createElement('input'), { placeholder, type, value, required: true });
}

function select(all: string, options: string[], value: string, onChange: (v: string) => void) {
  const s = document.createElement('select');
  s.append(new Option(all, ''), ...options.map((o) => new Option(o, o, false, o === value)));
  s.onchange = () => onChange(s.value);
  return s;
}

render();
highlights.watch(render);
lastSync.watch(render);
user.watch(render);
