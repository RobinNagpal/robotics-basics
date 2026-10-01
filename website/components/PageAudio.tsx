'use client';

import { useEffect, useRef, useState, type CSSProperties } from 'react';
import { readTimeline, timelineFor, type NarrationSection } from '@/lib/audio';

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
 * A recording made section by section is uploaded with a timeline beside it,
 * which says where each `##` section of the page starts inside the recording.
 * The player asks for that file at runtime too. When it arrives the bar gets a
 * mark at each section's start, the section being played is named under the
 * bar, and two more buttons step between sections. When it does not arrive, or
 * is not the version this player understands, none of that appears and the
 * player is what it has always been.
 *
 * Everything is kept in one row at the top of the page, because a listener
 * reaches for it before reading rather than after.
 *
 * Once the reader actually starts the recording, that row begins to follow the
 * screen, so pause, speed and the position bar stay in reach while they scroll
 * through the page they are listening to. It only starts following after a
 * play, because a reader who is not listening should get the whole width of the
 * screen for the text, and it goes back to sitting still on the next page.
 */

const SPEEDS = [0.75, 1, 1.25, 1.5, 1.75, 2] as const;

/** Remembered across pages, since a listener who wants 1.5 wants it every time. */
const SPEED_KEY = 'robotics-basics:narration-speed';

/**
 * How long after a section starts the previous-section button still means "the
 * section before this one". A music player's back button works this way, and
 * three seconds is long enough to use it as an undo for a mis-aimed jump.
 */
const SECTION_RESTART = 3;

function clock(seconds: number): string {
  if (!Number.isFinite(seconds)) return '--:--';
  const whole = Math.floor(seconds);
  return `${Math.floor(whole / 60)}:${String(whole % 60).padStart(2, '0')}`;
}

/**
 * Which section is playing at `time`.
 *
 * The sections cover the recording end to end, so the answer is the last one
 * that has already started. The small tolerance stops a jump landing on a
 * section's own start from being read as still being in the one before, which
 * happens because a browser rounds the time it was given.
 */
function sectionAt(sections: NarrationSection[], time: number): number {
  let found = 0;
  for (let i = 0; i < sections.length; i += 1) {
    if (sections[i].start <= time + 0.01) found = i;
  }
  return found;
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
  // The page's sections, once the timeline has been fetched and understood.
  // Null covers every other case at once: not fetched yet, no such file, a 404
  // page served as HTML, a half-written file, a version this player does not
  // know. The section controls are drawn only when this is an array, so they
  // appear once and never flicker back out while a slow timeline is in flight.
  const [sections, setSections] = useState<NarrationSection[] | null>(null);
  // True from the first play on this page onwards, which is what makes the row
  // follow the screen. Pausing does not turn it off, since someone who paused
  // is usually about to carry on.
  const [following, setFollowing] = useState(false);
  const row = useRef<HTMLDivElement | null>(null);

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

  // The browser can learn the recording's length before React has finished
  // mounting, above all when the file is already in the browser's cache, and in
  // that case the event announcing it has already gone past. So the length is
  // read from the element itself as well as from the event, and this function
  // is what both ways call.
  //
  // It only ever turns the player on. A length of zero or NaN is what an
  // element reports while it is still loading as well as when there is nothing
  // to load, so treating it as proof of absence would hide a player that is
  // about to work. Absence is reported by onError and by a refused play
  // instead.
  function readLength() {
    const element = audio.current;
    if (element === null) return;
    const seconds = element.duration;
    if (!Number.isFinite(seconds) || seconds <= 0) return;
    setLength(seconds);
    setPresent(true);
  }

  // A new page is a new recording: stop the old one rather than letting it play
  // on underneath a page it no longer describes, and go back to assuming there
  // is nothing there until this page's own file says otherwise. Changing the
  // address empties the element's own length too, so reading it straight after
  // the reset can only find this page's recording, never the last page's.
  useEffect(() => {
    setPlaying(false);
    setAt(0);
    setLength(Number.NaN);
    setPresent(false);
    setFollowing(false);
    readLength();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [src]);

  // Ask for the timeline that sits beside the recording. This has to stay a
  // runtime fetch: the site is a static export and the recordings are uploaded
  // afterwards, so uploading the MP3 and the JSON must be enough to give a page
  // a sectioned player. Every way this can fail ends in the same place, which
  // is sections staying null and the player behaving as it did before.
  useEffect(() => {
    setSections(null);
    const stop = new AbortController();
    fetch(timelineFor(src), { signal: stop.signal })
      .then((answer) => (answer.ok ? answer.text() : null))
      .then((text) => {
        if (text !== null) setSections(readTimeline(text));
      })
      .catch(() => {
        // A missing file, a refused request and the abort above all land here.
        // There is nothing to tell the reader: a page without a timeline is an
        // ordinary page with an ordinary player.
      });
    return () => stop.abort();
  }, [src]);

  // A heading reached from the table of contents stops below the site header,
  // and while the row is following the screen it would stop behind the row
  // instead. So the row's own height is published to the page as a custom
  // property, and the stylesheet adds it to that stopping distance. The height
  // is measured rather than guessed because the row grows taller on a narrow
  // screen, where the controls move below the position bar, and taller again
  // when a timeline adds the section's name under the bar.
  useEffect(() => {
    const element = row.current;
    const page = document.documentElement;
    if (!following || element === null) {
      delete page.dataset.audioFollowing;
      page.style.removeProperty('--page-audio-h');
      return;
    }
    const measure = () => page.style.setProperty('--page-audio-h', `${element.offsetHeight}px`);
    measure();
    page.dataset.audioFollowing = 'true';
    const watcher = new ResizeObserver(measure);
    watcher.observe(element);
    return () => {
      watcher.disconnect();
      delete page.dataset.audioFollowing;
      page.style.removeProperty('--page-audio-h');
    };
  }, [following]);

  function toggle() {
    const element = audio.current;
    if (element === null) return;
    if (element.paused) {
      void element.play().catch(() => setPresent(false));
    } else {
      element.pause();
    }
  }

  // Seeking goes through one place, so that the displayed time changes with the
  // same click that moves the recording. Waiting for the browser's own time
  // report would leave the bar and the section name a moment behind the jump.
  function seekTo(seconds: number) {
    const element = audio.current;
    if (element === null) return;
    const end = Number.isFinite(element.duration) ? element.duration : length;
    const to = Math.max(0, Number.isFinite(end) ? Math.min(seconds, end) : seconds);
    element.currentTime = to;
    setAt(to);
  }

  function skip(by: number) {
    const element = audio.current;
    if (element === null) return;
    seekTo(element.currentTime + by);
  }

  function chooseSpeed(next: number) {
    setSpeed(next);
    try {
      window.localStorage.setItem(SPEED_KEY, String(next));
    } catch {
      // Not being able to remember the speed is not a reason to refuse to use it.
    }
  }

  // The recording is the truth and the timeline is a description of it, so where
  // the two disagree the recording wins. A section that claims to start at or
  // after the real end is dropped rather than drawn as a mark past the end of
  // the bar, and the last kept section simply runs to wherever the audio stops.
  // If that leaves one section or none there is nothing to navigate, so the
  // player goes back to its plain form.
  const kept =
    sections !== null && Number.isFinite(length) && length > 0
      ? sections.filter((s) => s.start < length - 0.5)
      : [];
  const list = kept.length > 1 ? kept : [];
  const sectioned = list.length > 1;
  const now = sectioned ? sectionAt(list, at) : -1;
  const played = Number.isFinite(length) && length > 0 ? Math.min(100, (at / length) * 100) : 0;

  // Within the first few seconds of a section, previous means the section
  // before it, the way a music player's back button does. Later in a section it
  // means the start of the section being played, so a listener who missed a
  // sentence can hear it again without losing their place in the page.
  function toPreviousSection() {
    if (!sectioned) return;
    const here = list[now];
    if (now === 0 || at - here.start > SECTION_RESTART) seekTo(here.start);
    else seekTo(list[now - 1].start);
  }

  function toNextSection() {
    if (!sectioned || now + 1 >= list.length) return;
    seekTo(list[now + 1].start);
  }

  return (
    <>
      {/* The element that does the loading. It is outside the row, and stays in
          the page whether or not there is anything to play, because its own
          report of a duration is what decides that there is.

          The row below it is rendered only once that report arrives. An earlier
          version always rendered the row and set the `hidden` attribute on it,
          which did not work: `hidden` hides an element through a rule in the
          browser's own stylesheet, and any rule in this project's stylesheet
          beats the browser's whatever its specificity, so `.page-audio {
          display: flex }` put a dead player back on every page that has no
          recording. Not rendering the row cannot be undone by a stylesheet, so
          a `display` rule added later cannot bring the dead player back. */}
      <audio
        className="page-audio-source"
        ref={audio}
        src={src}
        preload="metadata"
        onLoadedMetadata={readLength}
        onDurationChange={readLength}
        onCanPlay={readLength}
        onTimeUpdate={(e) => setAt(e.currentTarget.currentTime)}
        onPlay={() => {
          setPlaying(true);
          setFollowing(true);
        }}
        onPause={() => setPlaying(false)}
        onEnded={() => setPlaying(false)}
        onError={() => setPresent(false)}
      />

      {present && (
        <div
          ref={row}
          className={following ? 'page-audio page-audio-following' : 'page-audio'}
          aria-label={`Listen to ${title}`}
        >
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

            {/* The played fraction is handed to the stylesheet as a custom
                property, because the bar behind the slider is drawn here rather
                than by the browser. The cast is only to satisfy the type of
                `style`, which does not list custom properties. */}
            <div
              className="page-audio-track"
              style={{ '--page-audio-played': `${played}%` } as CSSProperties}
            >
              <div className="page-audio-rail" aria-hidden />

              {sectioned && (
                <div className="page-audio-marks">
                  {list.map((section, i) => (
                    <button
                      key={`${i}-${section.start}`}
                      type="button"
                      className={i === now ? 'page-audio-mark page-audio-mark-now' : 'page-audio-mark'}
                      style={{ left: `${(section.start / length) * 100}%` }}
                      onClick={() => seekTo(section.start)}
                      title={`${section.title} · ${clock(section.start)}`}
                      aria-label={`Play section ${i + 1} of ${list.length}, ${section.title}, at ${clock(section.start)}`}
                    />
                  ))}
                </div>
              )}

              <input
                className="page-audio-seek"
                type="range"
                min={0}
                max={Number.isFinite(length) ? length : 0}
                step={1}
                value={at}
                onChange={(e) => seekTo(Number(e.currentTarget.value))}
                aria-label="Position"
              />
            </div>

            {sectioned && (
              <button
                type="button"
                className="page-audio-now"
                onClick={() => seekTo(list[now].start)}
                aria-label={`Play section ${now + 1} of ${list.length} from its start, ${list[now].title}`}
              >
                <span className="page-audio-now-count">
                  {now + 1}/{list.length}
                </span>
                <span className="page-audio-now-title">{list[now].title}</span>
              </button>
            )}
          </div>

          <div className="page-audio-controls">
            {sectioned && (
              <button
                type="button"
                onClick={toPreviousSection}
                disabled={now === 0 && at <= 0.05}
                aria-label="Previous section"
                title="Previous section"
              >
                <svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor" aria-hidden>
                  <rect x="5" y="5" width="2.5" height="14" rx="1" />
                  <path d="M19 6.2v11.6a1 1 0 0 1-1.55.83l-8.2-5.8a1 1 0 0 1 0-1.66l8.2-5.8A1 1 0 0 1 19 6.2Z" />
                </svg>
              </button>
            )}

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

            {sectioned && (
              <button
                type="button"
                onClick={toNextSection}
                disabled={now + 1 >= list.length}
                aria-label="Next section"
                title="Next section"
              >
                <svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor" aria-hidden>
                  <path d="M5 6.2v11.6a1 1 0 0 0 1.55.83l8.2-5.8a1 1 0 0 0 0-1.66l-8.2-5.8A1 1 0 0 0 5 6.2Z" />
                  <rect x="16.5" y="5" width="2.5" height="14" rx="1" />
                </svg>
              </button>
            )}

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
      )}
    </>
  );
}
