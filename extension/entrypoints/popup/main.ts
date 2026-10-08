import { signIn, signOut } from '@/lib/auth';
import { highlights, lastSync, pageKey, remove, user, visible } from '@/lib/store';

const app = document.querySelector('#app')!;
let book = '';
let chapter = '';
let error = '';

// Start on the book and chapter of the page that is open.
const [tab] = await browser.tabs.query({ active: true, currentWindow: true });
if (tab?.url?.startsWith('https://docs.dodao.io/')) ({ book, chapter } = pageKey(tab.url));

async function render() {
  const email = await user.getValue();
  if (!email) {
    const key = Object.assign(document.createElement('input'), { type: 'password', placeholder: 'API key' });
    const form = el('form', [key, el('button', 'Sign in')], 'signin');
    form.onsubmit = async (e) => {
      e.preventDefault();
      try { await signIn(key.value); error = ''; browser.runtime.sendMessage('sync'); } catch (e) { error = (e as Error).message; }
      render();
    };
    app.replaceChildren(form, el('p', error));
    key.focus();
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

  app.replaceChildren(
    el('header', [
      el('span', email),
      el('button', 'Sync', () => browser.runtime.sendMessage('sync')),
      el('button', 'Sign out', async () => (await signOut(), render())),
    ]),
    el('div', [
      select('All books', books, book, (v) => ((book = v), (chapter = ''), render())),
      select('All chapters', chapters, chapter, (v) => ((chapter = v), render())),
    ], 'filters'),
    el('div', sync
      ? `${sync.error ? `Sync failed: ${sync.error}` : 'Synced'} at ${new Date(sync.at).toLocaleTimeString()} · ${pending} waiting`
      : 'Not synced yet', sync?.error ? 'status err' : 'status'),
    el('ul', shown.length ? shown.map((h) => {
      const li = el('li', [
        el('button', '✕', () => remove(h.id)),
        Object.assign(el('a', [el('small', h.section ? `${h.page} · ${h.section}` : h.page), el('div', h.text)]), { href: h.url, target: '_blank' }),
        ...(h.note ? [el('div', h.note, 'note')] : []),
        el('small', h.author, 'author'),
      ]);
      li.style.borderColor = h.color;
      return li;
    }) : [el('li', 'No highlights here yet.')]),
  );
}

function el<K extends keyof HTMLElementTagNameMap>(tag: K, content: string | Node[], extra?: string | (() => unknown)) {
  const e = document.createElement(tag);
  typeof content === 'string' ? (e.textContent = content) : e.append(...content);
  if (typeof extra === 'function') e.onclick = extra;
  else if (extra) e.className = extra;
  return e;
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
