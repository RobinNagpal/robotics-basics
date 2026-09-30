'use client';

import { useEffect, useRef, useState } from 'react';

/**
 * The player that reads a page aloud.
 *
 * The recording is not the page read out word for word. A separate model wrote
 * a transcript first, which describes the diagrams, explains the code in
 * ordinary words and leaves out the table of contents, so that someone who
 * cannot see the screen still learns what the page teaches. That is why the
 * length shown here does not match the page's reading time.
 *
 * Every page carries this player, including pages that have no recording yet.
 * It renders nothing until the browser has actually loaded the audio's
 * metadata, and nothing ever again if that load fails. So a recording appearing
 * in the bucket is enough to make a page playable, with no rebuild and no
 * deploy, and the reader of a page without one sees no trace of it.
 *
 * Everything is kept in one row at the top of the page, because a listener
 * reaches for it before reading rather than after.
 */

const SPEEDS = [0.75, 1, 1.25, 1.5, 1.75, 2] as const;

/** Remembered across pages, since a listener who wants 1.5 wants it every time. */
const SPEED_KEY = 'robotics-basics:narration-speed';

function clock(seconds: number): string {
  if (!Number.isFinite(seconds)) return '--:--';
  const whole = Math.floor(seconds);
  return `${Math.floor(whole / 60)}:${String(whole % 60).padStart(2, '0')}`;
}

export default function PageAudio({ src, title }: { src: string; title: string }) {
  const audio = useRef<HTMLAudioElement | null>(null);
  const [playing, setPlaying] = useState(false);
  const [at, setAt] = useState(0);
  const [length, setLength] = useState(Number.NaN);
  const [speed, setSpeed] = useState(1);
  // Starts false and becomes true only when the browser reports a real
  // duration, which is the one signal that says the file is there and playable.
  const [present, setPresent] = useState(false);

  // Restore the chosen speed before the first play, so the opening words are
  // already at the speed the listener asked for on the previous page.
  useEffect(() => {
    try {
      const saved = Number(window.localStorage.getItem(SPEED_KEY));
      if (SPEEDS.includes(saved as (typeof SPEEDS)[number])) setSpeed(saved);
    } catch {
      // Private windows and blocked storage both throw. The default speed is
      // a perfectly good answer, so there is nothing to recover from.
    }
  }, []);

  useEffect(() => {
    if (audio.current !== null) audio.current.playbackRate = speed;
  }, [speed]);

  // A new page is a new recording: stop the old one rather than letting it play
  // on underneath a page it no longer describes, and go back to assuming there
  // is nothing there until this page's own file says otherwise.
  useEffect(() => {
    setPlaying(false);
    setAt(0);
    setLength(Number.NaN);
    setPresent(false);
  }, [src]);

  function toggle() {
    const element = audio.current;
    if (element === null) return;
    if (element.paused) {
      void element.play().catch(() => setPresent(false));
    } else {
      element.pause();
    }
  }

  function skip(by: number) {
    const element = audio.current;
    if (element === null) return;
    element.currentTime = Math.min(Math.max(0, element.currentTime + by), element.duration || 0);
  }

  function chooseSpeed(next: number) {
    setSpeed(next);
    try {
      window.localStorage.setItem(SPEED_KEY, String(next));
    } catch {
      // Not being able to remember the speed is not a reason to refuse to use it.
    }
  }

  return (
    <div className="page-audio" aria-label={`Listen to ${title}`} hidden={!present}>
      <audio
        ref={audio}
        src={src}
        preload="metadata"
        onLoadedMetadata={(e) => {
          const seconds = e.currentTarget.duration;
          setLength(seconds);
          // A duration of zero or NaN means the browser found something it
          // could not play, which counts as no recording rather than a broken one.
          setPresent(Number.isFinite(seconds) && seconds > 0);
        }}
        onTimeUpdate={(e) => setAt(e.currentTarget.currentTime)}
        onPlay={() => setPlaying(true)}
        onPause={() => setPlaying(false)}
        onEnded={() => setPlaying(false)}
        onError={() => setPresent(false)}
      />

      <button
        type="button"
        className="page-audio-play"
        onClick={toggle}
        aria-label={playing ? 'Pause' : 'Listen to this page'}
      >
        {playing ? (
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden>
            <rect x="6" y="5" width="4" height="14" rx="1" />
            <rect x="14" y="5" width="4" height="14" rx="1" />
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden>
            <path d="M8 5.5v13a1 1 0 0 0 1.5.87l11-6.5a1 1 0 0 0 0-1.74l-11-6.5A1 1 0 0 0 8 5.5Z" />
          </svg>
        )}
      </button>

      <div className="page-audio-body">
        <div className="page-audio-line">
          <span className="page-audio-label">{playing ? 'Playing' : 'Listen to this page'}</span>
          <span className="page-audio-time">
            {clock(at)} / {clock(length)}
          </span>
        </div>

        <input
          className="page-audio-seek"
          type="range"
          min={0}
          max={Number.isFinite(length) ? length : 0}
          step={1}
          value={at}
          onChange={(e) => {
            const to = Number(e.currentTarget.value);
            setAt(to);
            if (audio.current !== null) audio.current.currentTime = to;
          }}
          aria-label="Position"
        />
      </div>

      <div className="page-audio-controls">
        <button type="button" onClick={() => skip(-15)} aria-label="Back 15 seconds" title="Back 15 seconds">
          <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
            <path d="M11 5 5 9l6 4" />
            <path d="M5 9h8a6 6 0 1 1 0 12h-3" />
          </svg>
        </button>
        <button type="button" onClick={() => skip(15)} aria-label="Forward 15 seconds" title="Forward 15 seconds">
          <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
            <path d="m13 5 6 4-6 4" />
            <path d="M19 9h-8a6 6 0 1 0 0 12h3" />
          </svg>
        </button>

        <label className="page-audio-speed">
          <span className="visually-hidden">Speed</span>
          <select value={speed} onChange={(e) => chooseSpeed(Number(e.currentTarget.value))}>
            {SPEEDS.map((s) => (
              <option key={s} value={s}>
                {s}×
              </option>
            ))}
          </select>
        </label>
      </div>
    </div>
  );
}
