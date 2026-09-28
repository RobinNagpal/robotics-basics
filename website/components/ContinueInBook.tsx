'use client';

import Link from 'next/link';
import { useVisited } from '@/lib/useProgress';

/** Links to the first section in this book that has not been opened yet. */
export default function ContinueInBook({ urls }: { urls: string[] }) {
  const visited = useVisited();
  const started = urls.some((u) => visited[u]);
  const next = urls.find((u) => !visited[u]);
  if (!started || !next) return null;
  return (
    <Link href={next} className="button button-ghost">
      Continue where you stopped →
    </Link>
  );
}
