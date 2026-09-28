import Link from 'next/link';
import { notFound } from 'next/navigation';
import type { Metadata } from 'next';
import { findBook, getLibrary } from '@/lib/content';
import BookProgress from '@/components/BookProgress';
import BookGlyph from '@/components/BookGlyph';
import SectionCheck from '@/components/SectionCheck';
import ContinueInBook from '@/components/ContinueInBook';
import { formatMinutes } from '@/lib/format';

type Params = { params: Promise<{ book: string }> };

export const dynamicParams = false;

export function generateStaticParams() {
  return getLibrary().books.map((b) => ({ book: b.slug }));
}

export async function generateMetadata({ params }: Params): Promise<Metadata> {
  const book = findBook((await params).book);
  return book ? { title: book.title, description: book.description } : {};
}

export default async function BookPage({ params }: Params) {
  const book = findBook((await params).book);
  if (!book) notFound();
  const { books } = getLibrary();
  const urls = book.chapters.flatMap((c) => c.sections.map((s) => s.url));
  const nextBook = books.find((b) => b.number === book.number + 1);

  return (
    <main className="book-page" data-accent={book.accent}>
      <section className="book-hero">
        <div className="book-hero-text">
          <nav className="crumbs" aria-label="Breadcrumb">
            <Link href="/">Library</Link>
            <span aria-hidden>/</span>
            <span>Book {book.number}</span>
          </nav>
          <h1>{book.title}</h1>
          <p className="book-hero-sub">{book.subtitle}</p>
          <p className="book-hero-desc">{book.description}</p>
          <div className="book-hero-meta">
            <span>{book.chapters.length} chapters</span>
            <span>{book.sectionCount} sections</span>
            <span>{formatMinutes(book.minutes)} of reading</span>
          </div>
          <BookProgress urls={urls} />
          <div className="hero-actions">
            <Link href={urls[0]} className="button button-primary">
              Start reading
            </Link>
            <ContinueInBook urls={urls} />
          </div>
        </div>
        <div className="book-hero-art">
          <BookGlyph accent={book.accent} />
        </div>
      </section>

      <ol className="chapter-list">
        {book.chapters.map((chapter) => {
          let lastGroup: string | undefined;
          return (
            <li key={chapter.slug} className="chapter-card" id={chapter.slug}>
              <div className="chapter-card-head">
                <span className="chapter-num">{String(chapter.number).padStart(2, '0')}</span>
                <div>
                  <h2>
                    <Link href={chapter.sections[0].url}>{chapter.title}</Link>
                  </h2>
                  {chapter.summary && <p className="chapter-summary">{chapter.summary}</p>}
                  <p className="chapter-meta">
                    {chapter.sections.length} {chapter.sections.length === 1 ? 'section' : 'sections'} · {formatMinutes(chapter.minutes)}
                  </p>
                </div>
              </div>
              <ol className="section-list">
                {chapter.sections.map((s, i) => {
                  const showGroup = s.group && s.group !== lastGroup;
                  lastGroup = s.group;
                  return (
                    <li key={s.slug} className={s.group ? 'is-nested' : undefined}>
                      {showGroup && <span className="section-group">{s.group}</span>}
                      <Link href={s.url} className="section-row">
                        <SectionCheck url={s.url} />
                        <span className="section-index">{chapter.number}.{i + 1}</span>
                        <span className="section-title">{s.title}</span>
                        <span className="section-time">{s.minutes} min</span>
                      </Link>
                    </li>
                  );
                })}
              </ol>
            </li>
          );
        })}
      </ol>

      {nextBook && (
        <Link href={nextBook.url} className="next-book" data-accent={nextBook.accent}>
          <span className="next-book-label">Next book</span>
          <span className="next-book-title">
            Book {nextBook.number}: {nextBook.title}
          </span>
          <span className="next-book-sub">{nextBook.subtitle}</span>
        </Link>
      )}
    </main>
  );
}
