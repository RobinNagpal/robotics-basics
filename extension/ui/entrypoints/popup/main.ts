import { signIn, signOut } from '@/lib/auth';
import { queueFeedback } from '@/lib/queue';
import { apiUrl, batches, focused, highlights, lastSync, pageKey, remove, removeMany, user, visible } from '@/lib/store';
import {
  batchLabel,
  batchSize,
  canQueue,
  isDone,
  isOpen,
  shownStatus,
  statusLabel,
  type Batch,
  type LocalHighlight,
} from '@/lib/types';

const app = document.querySelector('#app')!;
// The popup has two lists: the comments themselves, and the batches of work that
// have been asked for. One is open at a time.
let view: 'comments' | 'batches' = 'comments';
let book = '';
let chapter = '';
let error = '';
// What the next "Address feedback" press will send, by comment id. Pressing the
// button, changing a filter or signing out empties it.
const picked = new Set<string>();
let queueing = false;
let queued = '';
// Deleting the comments Claude has finished with asks first, and this is the
// answer being waited for. It is dropped whenever anything else changes, so the
// question is never left standing over a list that has moved on.
let confirmingDelete = false;

// Start on the book and chapter of the page that is open. The tab is also where
// a comment's "open this text" link sends the reader, so it is kept.
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
  const list = await batches.getValue();

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
    tabBar(shown.length, list),
    el('div', sync
      ? `${sync.error ? `Sync failed: ${sync.error}` : 'Synced'} at ${new Date(sync.at).toLocaleTimeString()} · ${pending} waiting`
      : 'Not synced yet', sync?.error ? 'status err' : 'status'),
    ...(view === 'comments'
      ? [
          el('div', [
            select('All books', books, book, (v) => ((book = v), (chapter = ''), picked.clear(), (confirmingDelete = false), render())),
            select('All chapters', chapters, chapter, (v) => ((chapter = v), picked.clear(), (confirmingDelete = false), render())),
          ], 'filters'),
          ...batchBar([...selectable.values()]),
          ...doneBar(shown),
          ...(queued ? [el('div', queued, 'queued')] : []),
          el('ul', shown.length ? shown.map(row) : [el('li', 'No highlights here yet.')]),
        ]
      : batchList(list)),
  );
}

// The two lists, and how to move between them. The number beside Batches is how
// many the worker has still to do, because that is the thing a reader is waiting
// for; when there are none it is the number of batches there have ever been.
function tabBar(comments: number, list: Batch[]) {
  const open = list.filter(isOpen).length;
  const choice = (id: typeof view, label: string) =>
    onClick(el('button', label, id === view ? 'tab on' : 'tab'), () => ((view = id), (confirmingDelete = false), render()));
  return el('div', [
    choice('comments', `Comments (${comments})`),
    choice('batches', open ? `Batches (${open} to do)` : `Batches (${list.length})`),
  ], 'tabs');
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
      queued = r.batch
        ? `${r.queued} comment${r.queued === 1 ? '' : 's'} went into batch ${r.batch}${r.skipped ? `, ${r.skipped} skipped` : ''}. The worker takes one batch at a time, so it is worked on after any batch in front of it.`
        : `Nothing was queued${r.skipped ? `, ${r.skipped} skipped` : ''}.`;
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

// Deleting the comments Claude has finished with. It works on what is shown, so
// a book or chapter filter narrows it, and the count on the button is the number
// it would delete. The reply goes with the comment, so it asks before deleting.
function doneBar(shown: LocalHighlight[]) {
  const done = shown.filter((h) => isDone(h) && !h.deleted);
  if (!done.length) return [];
  const many = done.length === 1 ? '' : 's';
  if (!confirmingDelete) {
    return [el('div', [
      el('span', `${done.length} comment${many} Claude has finished with`, 'done-count'),
      onClick(el('button', 'Delete done', 'danger'), () => ((confirmingDelete = true), render())),
    ], 'done-bar')];
  }
  return [el('div', [
    el('span', `Delete ${done.length} comment${many}, and Claude's repl${done.length === 1 ? 'y' : 'ies'}?`, 'done-count'),
    onClick(el('button', 'Keep them', 'plain'), () => ((confirmingDelete = false), render())),
    onClick(el('button', 'Delete', 'danger'), async () => {
      confirmingDelete = false;
      await removeMany(done.map((h) => h.id));
      render();
      browser.runtime.sendMessage('sync');
    }),
  ], 'done-bar confirm')];
}

function row(h: LocalHighlight) {
  const status = shownStatus(h);
  const li = el('li', [
    el('button', '✕', () => remove(h.id)),
    ...(canQueue(h)
      ? [checkbox(picked.has(h.id), () => ((picked.has(h.id) ? picked.delete(h.id) : picked.add(h.id)), render()))]
      : []),
    el('small', h.section ? `${h.page} · ${h.section}` : h.page, 'where'),
    el('div', h.text, 'quote'),
    onClick(el('a', 'Go to this text →', 'goto'), () => goTo(h)),
    ...(h.note ? [block('Comment', h.note, 'note')] : []),
    el('small', h.author, 'author'),
    ...(status ? [el('span', statusLabel(h), `badge ${status}`)] : []),
    ...(h.batch
      ? [onClick(el('span', `Batch ${h.batch}`, 'badge batch-tag'), () => ((view = 'batches'), render()))]
      : []),
    ...(h.claudeResponse ? [reply(h.claudeResponse, status === 'failed')] : []),
  ]);
  li.style.borderColor = h.color;
  return li;
}

// Where each batch stands, newest first, which is the order the server sends
// them in. The oldest batch the worker has not finished with is the one every
// waiting batch is waiting for, so it is worked out once and given to each row.
function batchList(list: Batch[]) {
  if (!list.length) return [el('p', 'No batch has been asked for yet.', 'empty')];
  const inFront = [...list].filter(isOpen).sort((a, b) => a.number - b.number)[0]?.number;
  return [el('ul', list.map((b) => batchRow(b, inFront)), 'batches')];
}

function batchRow(b: Batch, inFront?: number) {
  const tries = b.attempts > 1 ? ` · tried ${b.attempts} times` : '';
  const ended = b.endedAt ? `, finished ${when(b.endedAt)}` : '';
  return el('li', [
    el('div', [
      el('strong', `Batch ${b.number}`),
      el('span', batchLabel(b, inFront), `badge b-${b.status}`),
    ], 'batch-head'),
    el('small', batchSize(b), 'where'),
    ...(b.summary.length ? [reply(b.summary.join('\n'), b.status === 'failed')] : []),
    el('small', b.pages.join('\n'), 'pages'),
    el('small', `asked by ${b.askedBy} ${when(b.createdAt)}${ended}${tries}`, 'author'),
  ], `batch-row ${b.status}`);
}

// Sends the open tab to the page the highlight is on, and asks the content
// script to scroll to the highlight itself. The request is written down before
// the tab moves, because the page is loaded again and only the script running in
// it can find the text. A tab already on that page is not sent anywhere; writing
// the request is enough, since the script watches for it.
async function goTo(h: LocalHighlight) {
  await focused.setValue({ id: h.id, at: Date.now() });
  if (!tab?.id) await browser.tabs.create({ url: h.url });
  else if (tab.url !== h.url) await browser.tabs.update(tab.id, { url: h.url });
  window.close();
}

// A labelled block of words. The label matters because a comment holds three
// kinds of words at once: the text from the page, what the reader said about it,
// and what Claude answered. Each kind has its own colour as well.
const block = (who: string, words: string, cls: string) =>
  el('div', [el('span', who, 'who'), el('span', words)], cls);

// The last block of a comment or a batch. When the work failed, the words are
// the worker's account of what went wrong rather than Claude's answer, so they
// are labelled and coloured as the bad news they are.
const reply = (words: string, failed: boolean) =>
  block(failed ? 'What happened' : 'Claude', words, failed ? 'response bad' : 'response');

const when = (ts: number) =>
  new Date(ts).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });

function el<K extends keyof HTMLElementTagNameMap>(tag: K, content: string | Node[], extra?: string | (() => unknown)) {
  const e = document.createElement(tag);
  typeof content === 'string' ? (e.textContent = content) : e.append(...content);
  if (typeof extra === 'function') e.onclick = extra;
  else if (extra) e.className = extra;
  return e;
}

// For the elements that need a class and a click, which el takes one of.
const onClick = <T extends HTMLElement>(e: T, fn: () => unknown) => ((e.onclick = fn), e);

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
batches.watch(render);
lastSync.watch(render);
user.watch(render);
