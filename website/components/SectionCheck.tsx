'use client';

import { useVisited } from '@/lib/useProgress';

export default function SectionCheck({ url }: { url: string }) {
  const visited = useVisited();
  const done = Boolean(visited[url]);
  return (
    <span className={`check${done ? ' is-done' : ''}`} aria-label={done ? 'Read' : 'Not read yet'}>
      {done && (
        <svg viewBox="0 0 16 16" width="10" height="10" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
          <path d="M3.5 8.5 6.5 11.5 12.5 4.5" />
        </svg>
      )}
    </span>
  );
}
