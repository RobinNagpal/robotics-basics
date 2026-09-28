'use client';

import Link from 'next/link';
import { useLastRead } from '@/lib/useProgress';

export default function ContinueReading() {
  const last = useLastRead();
  if (!last) return null;
  return (
    <Link href={last.url} className="button button-ghost continue">
      <span className="continue-label">Continue</span>
      <span className="continue-title">{last.title}</span>
      <span aria-hidden>→</span>
    </Link>
  );
}
