'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import type { Accent } from '@/lib/books.config';

/**
 * The books, in the top bar.
 *
 * Seven books side by side filled the bar and told the reader nothing about how
 * they relate, so the bar now shows the three parts instead, and the books of a
 * part appear in a panel under its name. Three names fit comfortably, and a new
 * book changes nothing up here.
 *
 * The panel opens in two ways on purpose. A pointer opens it by hovering, which
 * is what a reader expects of a menu and costs no click. A click opens it too,
 * and keeps it open, which is the only way it can work on a touch screen and is
 * also what a keyboard gives us for free, because the name is a real button.
 */

type Book = {
  slug: string;
  title: string;
  shortTitle: string;
  subtitle: string;
  number: number;
  accent: Accent;
  partSlug: string;
  partTitle: string;
  partShortTitle: string;
};

type Part = { slug: string; title: string; shortTitle: string; books: Book[] };

/** The books in the order given, split where the part changes. */
function byPart(books: Book[]): Part[] {
  const parts: Part[] = [];
  for (const book of books) {
    const last = parts[parts.length - 1];
    if (last && last.slug === book.partSlug) last.books.push(book);
    else parts.push({ slug: book.partSlug, title: book.partTitle, shortTitle: book.partShortTitle, books: [book] });
  }
  return parts;
}

export default function HeaderNav({ books }: { books: Book[] }) {
  const pathname = usePathname();
  const [open, setOpen] = useState<string | null>(null);
  const nav = useRef<HTMLElement | null>(null);
  // A hover that opens a panel must not close it the moment the pointer crosses
  // the gap between the name and the panel below it, so closing waits a moment.
  const closing = useRef<ReturnType<typeof setTimeout> | null>(null);

  const parts = byPart(books);
  const here = books.find((b) => pathname === `/${b.slug}` || pathname.startsWith(`/${b.slug}/`));

  function show(slug: string) {
    if (closing.current !== null) clearTimeout(closing.current);
    setOpen(slug);
  }

  function hide() {
    if (closing.current !== null) clearTimeout(closing.current);
    closing.current = setTimeout(() => setOpen(null), 120);
  }

  // Opening a page is the end of the menu's job, so it closes itself rather
  // than staying open over the page the reader just chose.
  useEffect(() => setOpen(null), [pathname]);

  // A click anywhere else, or Escape, closes it. Without this a panel opened by
  // a click on a touch screen would have no way of being dismissed.
  useEffect(() => {
    if (open === null) return;
    function elsewhere(event: MouseEvent) {
      if (nav.current !== null && !nav.current.contains(event.target as Node)) setOpen(null);
    }
    function escape(event: KeyboardEvent) {
      if (event.key === 'Escape') setOpen(null);
    }
    document.addEventListener('pointerdown', elsewhere);
    document.addEventListener('keydown', escape);
    return () => {
      document.removeEventListener('pointerdown', elsewhere);
      document.removeEventListener('keydown', escape);
    };
  }, [open]);

  return (
    <nav className="header-nav" aria-label="Books" ref={nav}>
      {parts.map((part) => {
        const inside = here !== undefined && here.partSlug === part.slug;
        return (
          <div
            key={part.slug}
            className="header-part"
            onPointerEnter={(e) => e.pointerType !== 'touch' && show(part.slug)}
            onPointerLeave={(e) => e.pointerType !== 'touch' && hide()}
          >
            <button
              type="button"
              className="header-part-name"
              aria-expanded={open === part.slug}
              aria-haspopup="true"
              aria-current={inside ? 'true' : undefined}
              onClick={() => setOpen(open === part.slug ? null : part.slug)}
              title={part.title}
            >
              {part.shortTitle}
              <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                <path d="m6 9 6 6 6-6" />
              </svg>
            </button>

            <div className="header-part-panel" hidden={open !== part.slug}>
              <p className="header-part-title">{part.title}</p>
              {part.books.map((b) => {
                const active = pathname === `/${b.slug}` || pathname.startsWith(`/${b.slug}/`);
                return (
                  <Link
                    key={b.slug}
                    href={`/${b.slug}`}
                    className="header-part-book"
                    data-accent={b.accent}
                    aria-current={active ? 'page' : undefined}
                  >
                    <span className="header-nav-num">{b.number}</span>
                    <span className="header-part-book-text">
                      <span className="header-part-book-title">{b.title}</span>
                      <span className="header-part-book-sub">{b.subtitle}</span>
                    </span>
                  </Link>
                );
              })}
            </div>
          </div>
        );
      })}
    </nav>
  );
}
