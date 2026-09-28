'use client';

import { useEffect, useState } from 'react';
import type { TocItem } from '@/lib/markdown';

/** The headings of the current section. With `spy`, highlights the one you are reading. */
export default function Toc({ items, spy = false }: { items: TocItem[]; spy?: boolean }) {
  const [active, setActive] = useState<string | undefined>();

  useEffect(() => {
    if (!spy) return;
    const headings = items
      .map((i) => document.getElementById(i.id))
      .filter((el): el is HTMLElement => Boolean(el));
    let frame = 0;
    const update = () => {
      frame = 0;
      let current = headings[0]?.id;
      for (const h of headings) {
        if (h.getBoundingClientRect().top <= 120) current = h.id;
        else break;
      }
      setActive(current);
    };
    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(update);
    };
    update();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => {
      window.removeEventListener('scroll', onScroll);
      if (frame) cancelAnimationFrame(frame);
    };
  }, [items, spy]);

  return (
    <ul className="toc">
      {items.map((item) => (
        <li key={item.id} className={`toc-depth-${item.depth}`}>
          <a href={`#${item.id}`} className={active === item.id ? 'is-active' : undefined}>
            {item.text}
          </a>
        </li>
      ))}
    </ul>
  );
}
