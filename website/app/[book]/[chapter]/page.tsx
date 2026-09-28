import { notFound, redirect } from 'next/navigation';
import { findBook, getLibrary } from '@/lib/content';

type Params = { params: Promise<{ book: string; chapter: string }> };

export const dynamicParams = false;

export function generateStaticParams() {
  return getLibrary().books.flatMap((b) => b.chapters.map((c) => ({ book: b.slug, chapter: c.slug })));
}

// A chapter has no page of its own; it opens at its first section.
export default async function ChapterPage({ params }: Params) {
  const { book: bookSlug, chapter: chapterSlug } = await params;
  const chapter = findBook(bookSlug)?.chapters.find((c) => c.slug === chapterSlug);
  if (!chapter) notFound();
  redirect(chapter.sections[0].url);
}
