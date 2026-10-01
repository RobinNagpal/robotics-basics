import Link from 'next/link';
import SearchDialog from './SearchDialog';
import ThemeToggle from './ThemeToggle';
import HeaderNav from './HeaderNav';
import type { Accent } from '@/lib/books.config';

type Props = { books: { slug: string; title: string; shortTitle: string; number: number; accent: Accent; partSlug: string; partTitle: string }[] };

export default function Header({ books }: Props) {
  return (
    <header className="site-header">
      <div className="site-header-inner">
        <Link href="/" className="brand" aria-label="Robotics Docs home">
          <span className="brand-mark" aria-hidden>
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="5" cy="19" r="2" />
              <path d="M6.5 17.5 12 9" />
              <circle cx="12" cy="8" r="2" />
              <path d="M13.5 7 19 5" />
              <path d="m19 5 1.5 3M19 5l2-1" />
            </svg>
          </span>
          <span className="brand-name">Robotics Docs</span>
        </Link>
        <HeaderNav books={books} />
        <div className="header-actions">
          <SearchDialog />
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
