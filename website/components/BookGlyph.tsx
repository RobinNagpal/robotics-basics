import type { Accent } from '@/lib/books.config';

// A small line drawing for each book's cover, chosen by the book's folder name.
// A book without its own drawing falls back to the arm on a grid.
export default function BookGlyph({ slug }: { slug: string; accent: Accent }) {
  const common = { fill: 'none', stroke: 'currentColor', strokeWidth: 1.6, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };

  // Book 1: two frames, and a transform from one to the other.
  if (slug === 'robotics-intro') {
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

  // Book 2: a camera, its field of view, and a box found in the picture.
  if (slug === 'perception') {
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

  // Book 4: programs as nodes, joined by the topics they talk over.
  if (slug === 'ros-and-rviz') {
    return (
      <svg className="book-glyph" viewBox="0 0 120 80" aria-hidden {...common}>
        <rect x="8" y="12" width="26" height="16" rx="4" />
        <rect x="8" y="52" width="26" height="16" rx="4" />
        <rect x="86" y="32" width="26" height="16" rx="4" />
        <path d="M34 20 Q 60 20 72 34" opacity="0.7" />
        <path d="M34 60 Q 60 60 72 46" opacity="0.7" />
        <path d="M72 40 L86 40" />
        <path d="M82 37 L86 40 L82 43" />
        <circle cx="72" cy="40" r="3" fill="currentColor" />
      </svg>
    );
  }

  // Book 5: a grid with obstacles and the shortest path found around them.
  if (slug === 'programming-techniques') {
    return (
      <svg className="book-glyph" viewBox="0 0 120 80" aria-hidden {...common}>
        <g opacity="0.3" strokeWidth="1">
          <path d="M10 10 H110 M10 25 H110 M10 40 H110 M10 55 H110 M10 70 H110" />
          <path d="M10 10 V70 M30 10 V70 M50 10 V70 M70 10 V70 M90 10 V70 M110 10 V70" />
        </g>
        <rect x="50" y="25" width="20" height="30" fill="currentColor" opacity="0.25" stroke="none" />
        <rect x="30" y="55" width="20" height="15" fill="currentColor" opacity="0.25" stroke="none" />
        <path d="M20 62 L20 47 L40 47 L40 17 L80 17 L80 32 L100 32" strokeWidth="2.2" />
        <circle cx="20" cy="62" r="3" fill="currentColor" />
        <circle cx="100" cy="32" r="4" />
      </svg>
    );
  }

  // Book 6: a small neural network, three layers of neurons joined by weights.
  if (slug === 'learned-models') {
    const left = [18, 40, 62];
    const mid = [12, 30, 50, 68];
    const right = [28, 52];
    return (
      <svg className="book-glyph" viewBox="0 0 120 80" aria-hidden {...common}>
        <g opacity="0.35" strokeWidth="1">
          {left.flatMap((a) => mid.map((b) => <path key={`l${a}-${b}`} d={`M26 ${a} L56 ${b}`} />))}
          {mid.flatMap((a) => right.map((b) => <path key={`r${a}-${b}`} d={`M64 ${a} L92 ${b}`} />))}
        </g>
        {left.map((y) => <circle key={`a${y}`} cx="22" cy={y} r="4" />)}
        {mid.map((y) => <circle key={`b${y}`} cx="60" cy={y} r="4" />)}
        {right.map((y) => <circle key={`c${y}`} cx="96" cy={y} r="4" fill="currentColor" />)}
      </svg>
    );
  }

  // Book 3, and the fallback: an arm on a grid, reaching for a part.
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
