'use client';

export default function MobileNavToggle() {
  return (
    <>
      <button
        type="button"
        className="mobile-nav-toggle"
        aria-controls="reader-nav"
        onClick={() => document.body.classList.toggle('nav-open')}
      >
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <path d="M4 6h16M4 12h16M4 18h10" />
        </svg>
        Chapters
      </button>
      <div className="nav-scrim" onClick={() => document.body.classList.remove('nav-open')} aria-hidden />
    </>
  );
}
