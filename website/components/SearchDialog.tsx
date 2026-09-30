'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import type { SearchDoc } from '@/app/search-index.json/route';

type Hit = { doc: SearchDoc; score: number; heading?: string; snippet?: string };

let indexPromise: Promise<SearchDoc[]> | null = null;
function loadIndex(): Promise<SearchDoc[]> {
  indexPromise ??= fetch('/search-index.json')
    .then((r) => r.json() as Promise<SearchDoc[]>)
    .catch((e) => {
      indexPromise = null;
      throw e;
    });
  return indexPromise;
}

function slugify(s: string): string {
  return s
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\s_-]/g, '')
    .replace(/\s/g, '-');
}

function search(docs: SearchDoc[], query: string): Hit[] {
  const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
  if (!terms.length) return [];
  const hits: Hit[] = [];
  for (const doc of docs) {
    const title = doc.t.toLowerCase();
    const text = doc.x.toLowerCase();
    const headings = doc.h.map((h) => h.toLowerCase());
    let score = 0;
    let ok = true;
    for (const term of terms) {
      const inTitle = title.includes(term);
      const inHeading = headings.some((h) => h.includes(term));
      const inChapter = doc.c.toLowerCase().includes(term);
      const inText = text.includes(term);
      if (!inTitle && !inHeading && !inText && !inChapter) {
        ok = false;
        break;
      }
      score += (inTitle ? 12 : 0) + (inChapter ? 4 : 0) + (inHeading ? 5 : 0) + (inText ? 1 : 0);
    }
    if (!ok) continue;

    const hi = headings.findIndex((h) => terms.every((t) => h.includes(t)));
    const heading = hi >= 0 ? doc.h[hi] : undefined;
    if (heading) score += 6;

    let snippet: string | undefined;
    const pos = text.indexOf(terms[0]);
    if (pos >= 0) {
      const start = Math.max(0, pos - 60);
      snippet = (start > 0 ? '…' : '') + doc.x.slice(start, pos + 120).trim() + '…';
    }
    hits.push({ doc, score, heading, snippet });
  }
  return hits.sort((a, b) => b.score - a.score).slice(0, 25);
}

function Highlight({ text, terms }: { text: string; terms: string[] }) {
  if (!terms.length) return <>{text}</>;
  const re = new RegExp(`(${terms.map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`, 'gi');
  return (
    <>
      {text.split(re).map((part, i) => (i % 2 === 1 ? <mark key={i}>{part}</mark> : part))}
    </>
  );
}

export default function SearchDialog() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [docs, setDocs] = useState<SearchDoc[] | null>(null);
  const [error, setError] = useState(false);
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  const show = useCallback(() => {
    setOpen(true);
    setError(false);
    loadIndex().then(setDocs, () => setError(true));
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      const typing = target.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName);
      if ((e.key === 'k' && (e.metaKey || e.ctrlKey)) || (e.key === '/' && !typing)) {
        e.preventDefault();
        show();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [show]);

  useEffect(() => {
    if (!open) return;
    inputRef.current?.focus();
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = prev;
    };
  }, [open]);

  const terms = useMemo(() => query.toLowerCase().split(/\s+/).filter(Boolean), [query]);
  const hits = useMemo(() => (docs ? search(docs, query) : []), [docs, query]);

  useEffect(() => setActive(0), [query]);
  useEffect(() => {
    listRef.current?.querySelector<HTMLElement>(`[data-index="${active}"]`)?.scrollIntoView({ block: 'nearest' });
  }, [active]);

  const close = () => {
    setOpen(false);
    setQuery('');
  };

  const go = (hit: Hit) => {
    close();
    router.push(hit.heading ? `${hit.doc.u}#${slugify(hit.heading)}` : hit.doc.u);
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') close();
    else if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActive((a) => Math.min(a + 1, hits.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActive((a) => Math.max(a - 1, 0));
    } else if (e.key === 'Enter' && hits[active]) {
      go(hits[active]);
    }
  };

  return (
    <>
      <button type="button" className="search-trigger" onClick={show} aria-label="Search the docs">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <circle cx="11" cy="11" r="7" />
          <path d="m20 20-3.5-3.5" />
        </svg>
        <span className="search-trigger-label">Search</span>
        <kbd>⌘K</kbd>
      </button>

      {open && (
        <div className="search-overlay" onMouseDown={(e) => e.target === e.currentTarget && close()}>
          <div className="search-panel" role="dialog" aria-modal="true" aria-label="Search" onKeyDown={onKeyDown}>
            <div className="search-input-row">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <circle cx="11" cy="11" r="7" />
                <path d="m20 20-3.5-3.5" />
              </svg>
              <input
                ref={inputRef}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search frames, cameras, MuJoCo, grasping…"
                aria-label="Search query"
                spellCheck={false}
              />
              <kbd onClick={close}>Esc</kbd>
            </div>
            <ul className="search-results" ref={listRef}>
              {error && <li className="search-empty">Could not load the search index.</li>}
              {!error && !docs && <li className="search-empty">Loading…</li>}
              {docs && !query && <li className="search-empty">Type to search every section of all five books.</li>}
              {docs && query && hits.length === 0 && <li className="search-empty">No results for “{query}”.</li>}
              {hits.map((hit, i) => (
                <li key={hit.doc.u}>
                  <button
                    type="button"
                    data-index={i}
                    data-accent={hit.doc.a}
                    className={`search-hit${i === active ? ' is-active' : ''}`}
                    onMouseMove={() => setActive(i)}
                    onClick={() => go(hit)}
                  >
                    <span className="search-hit-path">
                      {hit.doc.b} › {hit.doc.c}
                    </span>
                    <span className="search-hit-title">
                      <Highlight text={hit.doc.t} terms={terms} />
                      {hit.heading && (
                        <span className="search-hit-heading">
                          {' '}
                          › <Highlight text={hit.heading} terms={terms} />
                        </span>
                      )}
                    </span>
                    {hit.snippet && (
                      <span className="search-hit-snippet">
                        <Highlight text={hit.snippet} terms={terms} />
                      </span>
                    )}
                  </button>
                </li>
              ))}
            </ul>
            <div className="search-footer">
              <span><kbd>↑</kbd><kbd>↓</kbd> move</span>
              <span><kbd>↵</kbd> open</span>
              <span><kbd>Esc</kbd> close</span>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
