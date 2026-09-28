'use client';

import { useVisited } from '@/lib/useProgress';

export default function BookProgress({ urls, compact = false }: { urls: string[]; compact?: boolean }) {
  const visited = useVisited();
  const done = urls.filter((u) => visited[u]).length;
  const pct = urls.length ? Math.round((done / urls.length) * 100) : 0;
  return (
    <div className={`progress${compact ? ' progress-compact' : ''}`} title={`${done} of ${urls.length} sections read`}>
      <div className="progress-bar" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100} aria-label="Sections read">
        <span style={{ width: `${pct}%` }} />
      </div>
      <span className="progress-label">{compact ? `${pct}%` : `${done} of ${urls.length} sections read`}</span>
    </div>
  );
}
