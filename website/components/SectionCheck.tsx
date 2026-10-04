'use client';

import { READ_AT } from '@/lib/progress';
import { useDepth, useRead } from '@/lib/useProgress';

/**
 * The mark beside a section in the sidebar.
 *
 * It has three states rather than two, because a page is now read only once most
 * of it has been in front of you. A page you have not opened shows an empty
 * outline, a page you started shows a ring filled as far as you got, and a page
 * you finished shows a tick. The middle state is the point: without it, stopping
 * four fifths of the way through a long page looks exactly like never opening it.
 */
export default function SectionCheck({ url }: { url: string }) {
  const read = useRead();
  const depth = useDepth();
  const done = Boolean(read[url]);
  const part = done ? 1 : (depth[url] ?? 0);
  const percent = Math.round(part * 100);

  if (done) {
    return (
      <span className="check is-done" aria-label="Read">
        <svg viewBox="0 0 16 16" width="10" height="10" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
          <path d="M3.5 8.5 6.5 11.5 12.5 4.5" />
        </svg>
      </span>
    );
  }

  if (part <= 0) return <span className="check" aria-label="Not read yet" />;

  // The ring is drawn as one circle whose dashes are set so that the drawn part is
  // the fraction read. A circle of radius 6 has a circumference of 2 * pi * 6, and
  // starting it at twelve o'clock takes the quarter turn below.
  const circumference = 2 * Math.PI * 6;
  return (
    <span
      className="check is-part"
      aria-label={`${percent} per cent read, which is not yet the ${Math.round(READ_AT * 100)} per cent that counts as read`}
      title={`${percent}% read`}
    >
      <svg viewBox="0 0 16 16" width="12" height="12" aria-hidden>
        <circle className="check-ring-rest" cx="8" cy="8" r="6" fill="none" strokeWidth="2.2" />
        <circle
          className="check-ring-done"
          cx="8"
          cy="8"
          r="6"
          fill="none"
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeDasharray={`${circumference * part} ${circumference}`}
          transform="rotate(-90 8 8)"
        />
      </svg>
    </span>
  );
}
