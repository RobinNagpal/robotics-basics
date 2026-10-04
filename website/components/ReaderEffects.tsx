'use client';

import { useEffect, useState } from 'react';
import { READ_AT } from '@/lib/progress';
import { markOpened } from '@/lib/progress';
import { useReadingDepth } from '@/lib/useReadingDepth';

type Props = { url: string; title: string; book: string; chapter: string };

/**
 * Reading extras that need the browser: a scroll progress bar, remembering
 * what you have read, copy buttons on code blocks, and click-to-zoom images.
 */
export default function ReaderEffects({ url, title, book, chapter }: Props) {
  const [scrolled, setScrolled] = useState(0);
  const [zoom, setZoom] = useState<{ src: string; alt: string } | null>(null);

  // Opening a page is only worth remembering so that "continue reading" can offer
  // it again. Whether it was read is decided by how long its parts stayed on screen,
  // which is what the hook below measures.
  useEffect(() => {
    markOpened({ url, title, book, chapter });
  }, [url, title, book, chapter]);

  const depth = useReadingDepth(url);
  const done = depth >= READ_AT;
  const percent = Math.round(depth * 100);

  useEffect(() => {
    let frame = 0;
    const update = () => {
      frame = 0;
      const el = document.documentElement;
      const max = el.scrollHeight - el.clientHeight;
      setScrolled(max > 0 ? Math.min(1, el.scrollTop / max) : 0);
    };
    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(update);
    };
    update();
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll);
    return () => {
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('resize', onScroll);
      if (frame) cancelAnimationFrame(frame);
    };
  }, [url]);

  useEffect(() => {
    const article = document.querySelector('.prose');
    if (!article) return;

    const buttons: HTMLButtonElement[] = [];
    article.querySelectorAll('pre').forEach((pre) => {
      if (pre.querySelector('.copy-button')) return;
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'copy-button';
      btn.textContent = 'Copy';
      btn.addEventListener('click', async () => {
        const code = pre.querySelector('code')?.innerText ?? pre.innerText;
        try {
          await navigator.clipboard.writeText(code);
          btn.textContent = 'Copied';
        } catch {
          btn.textContent = 'Press ⌘C';
        }
        setTimeout(() => (btn.textContent = 'Copy'), 1600);
      });
      pre.appendChild(btn);
      buttons.push(btn);
    });

    const onClick = (e: Event) => {
      const img = (e.target as HTMLElement).closest('img');
      if (img && !img.closest('a')) setZoom({ src: img.currentSrc || img.src, alt: img.alt });
    };
    article.addEventListener('click', onClick);

    return () => {
      buttons.forEach((b) => b.remove());
      article.removeEventListener('click', onClick);
    };
  }, [url]);

  useEffect(() => {
    if (!zoom) return;
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setZoom(null);
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [zoom]);

  return (
    <>
      {/* Two different things, deliberately. The thin bar is where the scroll bar is,
          which answers "where am I". The dial answers "how much of this have I
          actually read", which is a smaller number whenever you skim, and the one
          that decides whether the page is marked read. */}
      <div className="read-progress" aria-hidden>
        <span style={{ transform: `scaleX(${scrolled})` }} />
      </div>
      <div
        className={`read-dial${done ? ' is-done' : ''}`}
        role="progressbar"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="How much of this page you have read"
        title={done ? 'Read' : `${percent}% read, and ${Math.round(READ_AT * 100)}% counts as read`}
      >
        <svg viewBox="0 0 36 36" width="36" height="36" aria-hidden>
          <circle className="read-dial-rest" cx="18" cy="18" r="15" fill="none" strokeWidth="3" />
          <circle
            className="read-dial-done"
            cx="18"
            cy="18"
            r="15"
            fill="none"
            strokeWidth="3"
            strokeLinecap="round"
            strokeDasharray={`${2 * Math.PI * 15 * Math.min(1, depth)} ${2 * Math.PI * 15}`}
            transform="rotate(-90 18 18)"
          />
        </svg>
        <span className="read-dial-label">
          {done ? (
            <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3.5 8.5 6.5 11.5 12.5 4.5" />
            </svg>
          ) : (
            `${percent}%`
          )}
        </span>
      </div>
      {zoom && (
        <div className="lightbox" role="dialog" aria-modal="true" aria-label={zoom.alt || 'Image'} onClick={() => setZoom(null)}>
          <figure>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={zoom.src} alt={zoom.alt} />
            {zoom.alt && <figcaption>{zoom.alt}</figcaption>}
          </figure>
          <button type="button" className="lightbox-close" aria-label="Close">
            ×
          </button>
        </div>
      )}
    </>
  );
}
