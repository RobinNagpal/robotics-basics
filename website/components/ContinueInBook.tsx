'use client';

import Link from 'next/link';
import { useRead } from '@/lib/useProgress';

/** Links to the first section in this book that has not been opened yet. */
export default function ContinueInBook({ urls }: { urls: string[] }) {
  const read = useRead();
  const started = urls.some((u) => read[u]);
  const next = urls.find((u) => !read[u]);
  if (!started || !next) return null;
  return (
    <Link href={next} className="button button-ghost">
      Continue where you stopped →
    </Link>
  );
}
