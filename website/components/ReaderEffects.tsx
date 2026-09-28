'use client';

import { useEffect, useState } from 'react';
import { markVisited } from '@/lib/progress';

type Props = { url: string; title: string; book: string; chapter: string };

/**
 * Reading extras that need the browser: a scroll progress bar, remembering
 * what you have read, copy buttons on code blocks, and click-to-zoom images.
 */
export default function ReaderEffects({ url, title, book, chapter }: Props) {
  const [scrolled, setScrolled] = useState(0);
  const [zoom, setZoom] = useState<{ src: string; alt: string } | null>(null);

  useEffect(() => {
    markVisited({ url, title, book, chapter });
  }, [url, title, book, chapter]);

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
      <div className="read-progress" aria-hidden>
        <span style={{ transform: `scaleX(${scrolled})` }} />
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
