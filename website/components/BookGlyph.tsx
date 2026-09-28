import type { Accent } from '@/lib/books.config';

// A small line drawing for each book's cover: frames, a camera view, an arm on a grid.
export default function BookGlyph({ accent }: { accent: Accent }) {
  const common = { fill: 'none', stroke: 'currentColor', strokeWidth: 1.6, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };
  if (accent === 'teal') {
    return (
      <svg className="book-glyph" viewBox="0 0 120 80" aria-hidden {...common}>
        <path d="M20 62 L20 22" />
        <path d="M20 62 L60 62" />
        <path d="M20 62 L4 74" opacity="0.5" />
        <path d="M17 26 L20 22 L23 26" />
        <path d="M56 59 L60 62 L56 65" />
        <g transform="translate(78 30) rotate(-25)">
          <path d="M0 0 L0 -22" />
          <path d="M0 0 L26 0" />
          <path d="M-3 -18 L0 -22 L3 -18" />
          <path d="M22 -3 L26 0 L22 3" />
        </g>
        <path d="M20 62 Q 50 40 78 30" strokeDasharray="3 4" opacity="0.6" />
        <circle cx="78" cy="30" r="2.5" fill="currentColor" />
      </svg>
    );
  }
  if (accent === 'violet') {
    return (
      <svg className="book-glyph" viewBox="0 0 120 80" aria-hidden {...common}>
        <rect x="6" y="30" width="18" height="14" rx="3" />
        <path d="M24 34 L30 31 L30 43 L24 40" />
        <path d="M30 37 L108 12" opacity="0.55" />
        <path d="M30 37 L108 66" opacity="0.55" />
        <rect x="70" y="30" width="22" height="18" rx="2" strokeDasharray="3 3" />
        <path d="M74 44 L81 36 L88 44 Z" />
        <circle cx="86" cy="35" r="2" fill="currentColor" />
      </svg>
    );
  }
  return (
    <svg className="book-glyph" viewBox="0 0 120 80" aria-hidden {...common}>
      <path d="M6 70 L114 70" opacity="0.5" />
      <path d="M14 76 L106 76" opacity="0.25" />
      <rect x="22" y="62" width="20" height="8" rx="2" />
      <circle cx="32" cy="56" r="4" />
      <path d="M32 56 L56 30" />
      <circle cx="56" cy="30" r="3.5" />
      <path d="M56 30 L84 40" />
      <path d="M84 40 L90 36 M84 40 L90 46" />
      <rect x="88" y="54" width="14" height="16" rx="1.5" />
    </svg>
  );
}
