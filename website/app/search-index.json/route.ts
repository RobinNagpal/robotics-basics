import { getLibrary, readSource } from '@/lib/content';
import { headingsOf, plainText } from '@/lib/markdown';

export const dynamic = 'force-static';

export type SearchDoc = {
  /** section title */ t: string;
  /** book title */ b: string;
  /** chapter title */ c: string;
  /** url */ u: string;
  /** accent */ a: string;
  /** headings */ h: string[];
  /** plain text */ x: string;
};

export function GET() {
  const docs: SearchDoc[] = getLibrary().books.flatMap((book) =>
    book.chapters.flatMap((chapter) =>
      chapter.sections.map((section) => {
        const src = readSource(section.rel);
        return {
          t: section.title,
          b: book.title,
          c: chapter.title,
          u: section.url,
          a: book.accent,
          h: headingsOf(src),
          x: plainText(src).slice(0, 20000),
        };
      }),
    ),
  );
  return Response.json(docs);
}
