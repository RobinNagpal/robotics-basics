import Link from 'next/link';
import { getLibrary } from '@/lib/content';
import ContinueReading from '@/components/ContinueReading';
import BookProgress from '@/components/BookProgress';
import BookGlyph from '@/components/BookGlyph';
import { formatMinutes } from '@/lib/format';

export default function Home() {
  const { books } = getLibrary();
  const sections = books.reduce((n, b) => n + b.sectionCount, 0);
  const minutes = books.reduce((n, b) => n + b.minutes, 0);

  return (
    <main className="home">
      <section className="hero">
        <p className="eyebrow">Robotics, from first principles</p>
        <h1>
          Learn robotics in <span className="hero-accent">six short books</span>.
        </h1>
        <p className="hero-lede">
          Start with the basics of a robot arm, learn how a robot sees, then move on to the frameworks, simulators and
          methods used to make real arms work, the programming techniques they are built from, and the neural network
          models that learn what is hard to write. Every chapter comes from the robotics-basics docs and follows their
          reading order.
        </p>
        <div className="hero-stats">
          <span><strong>{books.length}</strong> books</span>
          <span><strong>{books.reduce((n, b) => n + b.chapters.length, 0)}</strong> chapters</span>
          <span><strong>{sections}</strong> sections</span>
          <span><strong>{formatMinutes(minutes)}</strong> of reading</span>
        </div>
        <div className="hero-actions">
          <Link href={books[0].chapters[0].sections[0].url} className="button button-primary">
            Start with Book 1
          </Link>
          <ContinueReading />
        </div>
      </section>

      <section className="book-grid" aria-label="Books">
        {books.map((book) => (
          <article key={book.slug} className="book-card" data-accent={book.accent}>
            <Link href={book.url} className="book-card-link" aria-label={`Book ${book.number}: ${book.title}`} />
            <div className="book-card-cover">
              <BookGlyph slug={book.slug} accent={book.accent} />
              <span className="book-card-num">Book {book.number}</span>
            </div>
            <div className="book-card-body">
              <h2>{book.title}</h2>
              <p className="book-card-sub">{book.subtitle}</p>
              <p className="book-card-desc">{book.description}</p>
              <ol className="book-card-chapters">
                {book.chapters.map((c) => (
                  <li key={c.slug}>
                    <Link href={c.sections[0].url}>{c.title}</Link>
                  </li>
                ))}
              </ol>
              <div className="book-card-foot">
                <span>
                  {book.chapters.length} chapters · {book.sectionCount} sections · {formatMinutes(book.minutes)}
                </span>
                <BookProgress urls={book.chapters.flatMap((c) => c.sections.map((s) => s.url))} compact />
              </div>
            </div>
          </article>
        ))}
      </section>

      <section className="how">
        <h2>How the books are organised</h2>
        <div className="how-grid">
          <div>
            <span className="how-step">1</span>
            <h3>Books</h3>
            <p>Six books, each covering one broad area. Read them in order, or go straight to the one you need.</p>
          </div>
          <div>
            <span className="how-step">2</span>
            <h3>Chapters</h3>
            <p>Each chapter is one topic from the docs, such as ROS, cameras or gripping, and keeps its original order.</p>
          </div>
          <div>
            <span className="how-step">3</span>
            <h3>Sections</h3>
            <p>Each section is one document. The site marks the sections you have opened, so you can pick up where you stopped.</p>
          </div>
        </div>
      </section>

      <footer className="site-footer">
        Content from the <code>robotics-basics</code> repository. Reading progress is stored only in this browser.
      </footer>
    </main>
  );
}
