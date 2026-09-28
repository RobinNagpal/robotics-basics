import fs from 'node:fs';
import path from 'node:path';
import { BOOKS, CHAPTER_TITLES, type Accent } from './books.config';

// The docs are read straight from ../docs in this repo, so the site always
// shows the current content. Override with ROBOTICS_DOCS_DIR if it lives elsewhere.
export const DOCS_DIR = process.env.ROBOTICS_DOCS_DIR
  ? path.resolve(process.env.ROBOTICS_DOCS_DIR)
  : path.resolve(process.cwd(), '..', 'docs');

// Folders in docs/ that hold assets rather than reading material.
const NON_READING_DIRS = new Set(['images', 'diagrams']);

const WORDS_PER_MINUTE = 220;

export type Section = {
  slug: string;
  title: string;
  /** Path relative to docs/, with forward slashes. */
  rel: string;
  /** Sub-folder label for sections nested one level deeper, e.g. "Case study". */
  group?: string;
  summary: string;
  words: number;
  minutes: number;
  url: string;
};

export type Chapter = {
  slug: string;
  number: number;
  title: string;
  summary: string;
  sections: Section[];
  minutes: number;
  url: string;
};

export type Book = {
  slug: string;
  number: number;
  title: string;
  subtitle: string;
  description: string;
  accent: Accent;
  chapters: Chapter[];
  sectionCount: number;
  minutes: number;
  url: string;
};

export type Library = {
  books: Book[];
  /** docs-relative path of a .md file or folder -> site URL */
  urlByRel: Map<string, string>;
};

export function stripNumber(name: string): string {
  return name.replace(/\.md$/i, '').replace(/^\d+_/, '');
}

function orderOf(name: string): number {
  const m = name.match(/^(\d+)_/);
  return m ? parseInt(m[1], 10) : Number.MAX_SAFE_INTEGER;
}

function byReadingOrder(a: string, b: string): number {
  return orderOf(a) - orderOf(b) || a.localeCompare(b);
}

export function humanize(slug: string): string {
  const s = slug.replace(/[-_]+/g, ' ').trim();
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/** Strip inline Markdown so a heading or paragraph reads as plain text. */
export function plainInline(s: string): string {
  return s
    .replace(/!\[[^\]]*\]\([^)]*\)/g, '')
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/<[^>]+>/g, '')
    .replace(/[*_`]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function truncate(s: string, n: number): string {
  if (s.length <= n) return s;
  const cut = s.slice(0, n);
  return cut.slice(0, cut.lastIndexOf(' ')).replace(/[,;:.\s]+$/, '') + '…';
}

function readTitle(src: string, fallback: string): string {
  const m = src.match(/^#\s+(.+)$/m);
  return m ? plainInline(m[1]) : fallback;
}

function readSummary(src: string): string {
  const body = src.replace(/```[\s\S]*?```/g, '').replace(/^#\s+.+$/m, '');
  for (const para of body.split(/\n\s*\n/)) {
    const t = para.trim();
    if (!t || /^(#|-|\*|\||!|<|>|\d+\.|---)/.test(t)) continue;
    return truncate(plainInline(t), 230);
  }
  return '';
}

function countWords(src: string): number {
  return src.split(/\s+/).filter(Boolean).length;
}

export function readSource(rel: string): string {
  return fs.readFileSync(path.join(DOCS_DIR, rel), 'utf8');
}

type FoundFile = { rel: string; groupDir?: string };

/** Every .md file under a chapter folder, in reading order, one level of nesting. */
function walkChapter(relDir: string): FoundFile[] {
  const out: FoundFile[] = [];
  const walk = (dir: string, groupDir?: string) => {
    const entries = fs
      .readdirSync(path.join(DOCS_DIR, dir), { withFileTypes: true })
      .filter((e) => !e.name.startsWith('.'))
      .sort((a, b) => byReadingOrder(a.name, b.name));
    for (const e of entries) {
      const rel = `${dir}/${e.name}`;
      if (e.isDirectory()) walk(rel, groupDir ?? e.name);
      else if (e.name.toLowerCase().endsWith('.md')) out.push({ rel, groupDir });
    }
  };
  walk(relDir);
  return out;
}

function buildSection(file: FoundFile, chapterRel: string, url: (slug: string) => string): Section {
  const src = readSource(file.rel);
  // Nested files get a slug that keeps the folder, e.g. "case-study--place-glass".
  const inner = (chapterRel ? file.rel.slice(chapterRel.length + 1) : file.rel).split('/');
  const slug = inner.length === 1 ? stripNumber(inner[0]) : inner.map(stripNumber).join('--');
  const words = countWords(src);
  return {
    slug,
    title: readTitle(src, humanize(stripNumber(inner[inner.length - 1]))),
    rel: file.rel,
    group: file.groupDir ? humanize(stripNumber(file.groupDir)) : undefined,
    summary: readSummary(src),
    words,
    minutes: Math.max(1, Math.round(words / WORDS_PER_MINUTE)),
    url: url(slug),
  };
}

function scan(): Library {
  if (!fs.existsSync(DOCS_DIR)) {
    throw new Error(
      `Docs folder not found at ${DOCS_DIR}. Run the site from robotics-basics/website, or set ROBOTICS_DOCS_DIR.`,
    );
  }

  const top = fs
    .readdirSync(DOCS_DIR, { withFileTypes: true })
    .filter((e) => !e.name.startsWith('.') && !NON_READING_DIRS.has(e.name))
    .filter((e) => e.isDirectory() || e.name.toLowerCase().endsWith('.md'))
    .sort((a, b) => byReadingOrder(a.name, b.name));

  const lastBook = BOOKS[BOOKS.length - 1];
  const buckets = new Map(BOOKS.map((b) => [b.slug, [] as typeof top]));
  for (const e of top) {
    const key = stripNumber(e.name);
    const owner = BOOKS.find((b) => b.chapters.includes(key)) ?? lastBook;
    buckets.get(owner.slug)!.push(e);
  }

  const urlByRel = new Map<string, string>();

  const books: Book[] = BOOKS.map((cfg) => {
    // Configured chapters in configured order, then any unlisted ones by number.
    const entries = buckets.get(cfg.slug)!.sort((a, b) => {
      const ia = cfg.chapters.indexOf(stripNumber(a.name));
      const ib = cfg.chapters.indexOf(stripNumber(b.name));
      return (ia < 0 ? 1e6 : ia) - (ib < 0 ? 1e6 : ib) || byReadingOrder(a.name, b.name);
    });

    const chapters: Chapter[] = entries.map((e, i) => {
      const slug = stripNumber(e.name);
      const chapterUrl = `/${cfg.slug}/${slug}`;
      const files: FoundFile[] = e.isDirectory() ? walkChapter(e.name) : [{ rel: e.name }];
      const chapterRel = e.isDirectory() ? e.name : '';
      const sections = files.map((f) =>
        e.isDirectory()
          ? buildSection(f, chapterRel, (s) => `${chapterUrl}/${s}`)
          : buildSection({ rel: f.rel }, '', () => `${chapterUrl}/${slug}`),
      );
      // A single-file chapter uses the chapter slug for its only section.
      if (!e.isDirectory()) sections[0].slug = slug;

      for (const s of sections) urlByRel.set(s.rel, s.url);
      if (e.isDirectory() && sections[0]) {
        urlByRel.set(e.name, sections[0].url);
        // Nested folders link to their first file too.
        for (const s of sections) {
          const dir = path.posix.dirname(s.rel);
          if (!urlByRel.has(dir)) urlByRel.set(dir, s.url);
        }
      }

      return {
        slug,
        number: i + 1,
        title: CHAPTER_TITLES[slug] ?? sections[0]?.title ?? humanize(slug),
        summary: sections[0]?.summary ?? '',
        sections,
        minutes: sections.reduce((n, s) => n + s.minutes, 0),
        url: chapterUrl,
      };
    });

    return {
      slug: cfg.slug,
      number: cfg.number,
      title: cfg.title,
      subtitle: cfg.subtitle,
      description: cfg.description,
      accent: cfg.accent,
      chapters: chapters.filter((c) => c.sections.length > 0),
      sectionCount: chapters.reduce((n, c) => n + c.sections.length, 0),
      minutes: chapters.reduce((n, c) => n + c.minutes, 0),
      url: `/${cfg.slug}`,
    };
  }).filter((b) => b.chapters.length > 0);

  return { books, urlByRel };
}

let cached: Library | null = null;

export function getLibrary(): Library {
  // Re-scan in development so edits to the docs show up on refresh.
  if (cached && process.env.NODE_ENV === 'production') return cached;
  cached = scan();
  return cached;
}

export function findBook(slug: string): Book | undefined {
  return getLibrary().books.find((b) => b.slug === slug);
}

export type Located = {
  book: Book;
  chapter: Chapter;
  section: Section;
  /** Position of the section across the whole book, 0-based. */
  index: number;
  total: number;
  prev?: { section: Section; chapter: Chapter; book: Book };
  next?: { section: Section; chapter: Chapter; book: Book };
};

export function locate(bookSlug: string, chapterSlug: string, sectionSlug: string): Located | undefined {
  const { books } = getLibrary();
  const flat = books.flatMap((book) =>
    book.chapters.flatMap((chapter) => chapter.sections.map((section) => ({ book, chapter, section }))),
  );
  const i = flat.findIndex(
    (x) => x.book.slug === bookSlug && x.chapter.slug === chapterSlug && x.section.slug === sectionSlug,
  );
  if (i < 0) return undefined;
  const { book, chapter, section } = flat[i];
  const inBook = flat.filter((x) => x.book === book);
  return {
    book,
    chapter,
    section,
    index: inBook.findIndex((x) => x.section === section),
    total: inBook.length,
    prev: flat[i - 1],
    next: flat[i + 1],
  };
}
