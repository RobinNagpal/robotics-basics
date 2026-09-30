import Link from 'next/link';
import { notFound } from 'next/navigation';
import type { Metadata } from 'next';
import { getLibrary, locate } from '@/lib/content';
import { audioFor } from '@/lib/audio';
import { renderSection } from '@/lib/markdown';
import BookSidebar, { type SidebarChapter } from '@/components/BookSidebar';
import Toc from '@/components/Toc';
import ReaderEffects from '@/components/ReaderEffects';
import MobileNavToggle from '@/components/MobileNavToggle';
import PageAudio from '@/components/PageAudio';

type Params = { params: Promise<{ book: string; chapter: string; section: string }> };

export const dynamicParams = false;

export function generateStaticParams() {
  return getLibrary().books.flatMap((b) =>
    b.chapters.flatMap((c) => c.sections.map((s) => ({ book: b.slug, chapter: c.slug, section: s.slug }))),
  );
}

export async function generateMetadata({ params }: Params): Promise<Metadata> {
  const p = await params;
  const found = locate(p.book, p.chapter, p.section);
  return found ? { title: found.section.title, description: found.section.summary || found.chapter.summary } : {};
}

export default async function SectionPage({ params }: Params) {
  const p = await params;
  const found = locate(p.book, p.chapter, p.section);
  if (!found) notFound();
  const { book, chapter, section, index, total, prev, next } = found;
  const { html, toc } = await renderSection(section);
  const sectionNumber = chapter.sections.indexOf(section) + 1;
  // Where this page's recording would be. Every page gets a player; the player
  // shows itself only if that file actually loads, so uploading a recording is
  // enough to make a page playable without rebuilding the site.
  const narration = audioFor(section.url);

  const sidebar: SidebarChapter[] = book.chapters.map((c) => ({
    slug: c.slug,
    number: c.number,
    title: c.title,
    sections: c.sections.map((s) => ({ title: s.title, url: s.url, group: s.group })),
  }));

  return (
    <div className="reader" data-accent={book.accent}>
      <ReaderEffects
        url={section.url}
        title={section.title}
        book={book.title}
        chapter={chapter.title}
      />

      <aside className="reader-nav" id="reader-nav" aria-label={`${book.title} contents`}>
        <BookSidebar
          book={{ title: book.title, number: book.number, url: book.url }}
          chapters={sidebar}
          currentUrl={section.url}
        />
      </aside>

      <main className="reader-main">
        <div className="reader-topbar">
          <MobileNavToggle />
          <nav className="crumbs" aria-label="Breadcrumb">
            <Link href="/">Library</Link>
            <span aria-hidden>/</span>
            <Link href={book.url}>{book.title}</Link>
            <span aria-hidden>/</span>
            <Link href={`${book.url}#${chapter.slug}`}>{chapter.title}</Link>
          </nav>
        </div>

        <header className="doc-header">
          <p className="eyebrow">
            Chapter {chapter.number} · Section {sectionNumber} of {chapter.sections.length}
            {section.group ? ` · ${section.group}` : ''}
          </p>
          <h1>{section.title}</h1>
          <div className="doc-meta">
            <span>
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <circle cx="12" cy="12" r="9" />
                <path d="M12 7v5l3 2" />
              </svg>
              {section.minutes} min read
            </span>
            <span>
              {index + 1} of {total} in {book.title}
            </span>
          </div>
        </header>

        <PageAudio src={narration} title={section.title} />

        {toc.length > 2 && (
          <details className="toc-inline">
            <summary>On this page</summary>
            <Toc items={toc} />
          </details>
        )}

        <article className="prose" dangerouslySetInnerHTML={{ __html: html }} />

        <nav className="pager" aria-label="Previous and next">
          {prev ? (
            <Link href={prev.section.url} className="pager-link pager-prev">
              <span className="pager-dir">← Previous{prev.book !== book ? ` · ${prev.book.title}` : ''}</span>
              <span className="pager-title">{prev.section.title}</span>
              <span className="pager-chapter">{prev.chapter.title}</span>
            </Link>
          ) : (
            <span />
          )}
          {next ? (
            <Link href={next.section.url} className="pager-link pager-next" data-accent={next.book.accent}>
              <span className="pager-dir">
                {next.book !== book ? `Next book · ${next.book.title}` : 'Next'} →
              </span>
              <span className="pager-title">{next.section.title}</span>
              <span className="pager-chapter">{next.chapter.title}</span>
            </Link>
          ) : (
            <Link href="/" className="pager-link pager-next">
              <span className="pager-dir">Finished →</span>
              <span className="pager-title">Back to the library</span>
            </Link>
          )}
        </nav>
      </main>

      <aside className="reader-toc" aria-label="On this page">
        {toc.length > 0 && (
          <>
            <p className="reader-toc-title">On this page</p>
            <Toc items={toc} spy />
          </>
        )}
      </aside>
    </div>
  );
}
