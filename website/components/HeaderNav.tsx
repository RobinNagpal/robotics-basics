'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import type { Accent } from '@/lib/books.config';

type Book = { slug: string; title: string; shortTitle: string; number: number; accent: Accent; partSlug: string; partTitle: string };

type Props = { books: Book[] };

/** The books in the order given, split where the part changes. */
function byPart(books: Book[]): Book[][] {
  const groups: Book[][] = [];
  for (const book of books) {
    const last = groups[groups.length - 1];
    if (last && last[0].partSlug === book.partSlug) last.push(book);
    else groups.push([book]);
  }
  return groups;
}

export default function HeaderNav({ books }: Props) {
  const pathname = usePathname();
  // One group per part, so the three shelves of the library stay visible up
  // here as well as on the front page. The books inside a group keep their
  // reading-order number, which runs across the whole library rather than
  // restarting in each part.
  return (
    <nav className="header-nav" aria-label="Books">
      {byPart(books).map((group) => (
        <span key={group[0].partSlug} className="header-nav-part" aria-label={group[0].partTitle}>
          {group.map((b) => {
            const active = pathname === `/${b.slug}` || pathname.startsWith(`/${b.slug}/`);
            return (
              <Link key={b.slug} href={`/${b.slug}`} className="header-nav-link" data-accent={b.accent} aria-current={active ? 'page' : undefined} title={`${b.partTitle} · Book ${b.number}: ${b.title}`}>
                <span className="header-nav-num">{b.number}</span>
                {b.shortTitle}
              </Link>
            );
          })}
        </span>
      ))}
    </nav>
  );
}
