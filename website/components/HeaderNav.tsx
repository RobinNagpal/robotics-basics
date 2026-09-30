'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import type { Accent } from '@/lib/books.config';

type Props = { books: { slug: string; title: string; shortTitle: string; number: number; accent: Accent }[] };

export default function HeaderNav({ books }: Props) {
  const pathname = usePathname();
  return (
    <nav className="header-nav" aria-label="Books">
      {books.map((b) => {
        const active = pathname === `/${b.slug}` || pathname.startsWith(`/${b.slug}/`);
        return (
          <Link key={b.slug} href={`/${b.slug}`} className="header-nav-link" data-accent={b.accent} aria-current={active ? 'page' : undefined} title={`Book ${b.number}: ${b.title}`}>
            <span className="header-nav-num">{b.number}</span>
            {b.shortTitle}
          </Link>
        );
      })}
    </nav>
  );
}
