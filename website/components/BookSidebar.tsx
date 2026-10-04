'use client';

import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';
import { useRead } from '@/lib/useProgress';

export type SidebarChapter = {
  slug: string;
  number: number;
  title: string;
  sections: { title: string; url: string; group?: string }[];
};

type Props = {
  book: { title: string; number: number; url: string };
  chapters: SidebarChapter[];
  currentUrl: string;
};

export default function BookSidebar({ book, chapters, currentUrl }: Props) {
  const read = useRead();
  const currentChapter = chapters.find((c) => c.sections.some((s) => s.url === currentUrl))?.slug;
  const [open, setOpen] = useState<Record<string, boolean>>(() => (currentChapter ? { [currentChapter]: true } : {}));
  const activeRef = useRef<HTMLAnchorElement>(null);

  // Keep the current chapter open and the current section in view as you move through the book.
  useEffect(() => {
    if (currentChapter) setOpen((o) => ({ ...o, [currentChapter]: true }));
    activeRef.current?.scrollIntoView({ block: 'nearest' });
    document.body.classList.remove('nav-open');
  }, [currentUrl, currentChapter]);

  const total = chapters.reduce((n, c) => n + c.sections.length, 0);
  const done = chapters.reduce((n, c) => n + c.sections.filter((s) => read[s.url]).length, 0);

  return (
    <div className="sidebar">
      <Link href={book.url} className="sidebar-book">
        <span className="sidebar-book-num">Book {book.number}</span>
        <span className="sidebar-book-title">{book.title}</span>
        <span className="sidebar-book-progress">
          <span className="progress-bar">
            <span style={{ width: `${total ? (done / total) * 100 : 0}%` }} />
          </span>
          <span>
            {done}/{total}
          </span>
        </span>
      </Link>

      <ol className="sidebar-chapters">
        {chapters.map((c) => {
          const isOpen = Boolean(open[c.slug]);
          const chapterDone = c.sections.every((s) => read[s.url]);
          let lastGroup: string | undefined;
          return (
            <li key={c.slug} className={c.slug === currentChapter ? 'is-current' : undefined}>
              <button
                type="button"
                className="sidebar-chapter"
                aria-expanded={isOpen}
                onClick={() => setOpen((o) => ({ ...o, [c.slug]: !isOpen }))}
              >
                <span className={`sidebar-chapter-num${chapterDone ? ' is-done' : ''}`}>{c.number}</span>
                <span className="sidebar-chapter-title">{c.title}</span>
                <svg className="chevron" viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="m6 4 4 4-4 4" />
                </svg>
              </button>
              {isOpen && (
                <ol className="sidebar-sections">
                  {c.sections.map((s) => {
                    const active = s.url === currentUrl;
                    const showGroup = s.group && s.group !== lastGroup;
                    lastGroup = s.group;
                    return (
                      <li key={s.url}>
                        {showGroup && <span className="sidebar-group">{s.group}</span>}
                        <Link
                          href={s.url}
                          ref={active ? activeRef : undefined}
                          className={`sidebar-section${active ? ' is-active' : ''}${read[s.url] ? ' is-read' : ''}${s.group ? ' is-nested' : ''}`}
                          aria-current={active ? 'page' : undefined}
                        >
                          <span className="dot" aria-hidden />
                          {s.title}
                        </Link>
                      </li>
                    );
                  })}
                </ol>
              )}
            </li>
          );
        })}
      </ol>
    </div>
  );
}
