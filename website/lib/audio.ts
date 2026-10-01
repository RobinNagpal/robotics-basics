/**
 * Where a page's recording would be, if it has one.
 *
 * The site is a static export, but the recordings are not part of the build:
 * they are made by `narration/narrate.py` and uploaded to the same bucket the
 * site is served from, under `/audio/`. That means a page is built long before
 * anyone knows whether its recording exists.
 *
 * So this returns an address rather than a fact. Every page carries a player,
 * and the player asks the browser to load that address: if the file is there
 * the player appears, and if it is not the player stays hidden. Uploading a
 * recording is therefore enough to make it playable, with no rebuild and no
 * deploy, and removing one is enough to take it away again.
 *
 * The address is relative, so it is fetched from whatever origin served the
 * page and needs no cross-origin permission. It must match the key
 * `narrate.py` writes, which is the section's own URL.
 */
export function audioFor(url: string): string {
  return `/audio/${url.replace(/^\/+/, '')}.mp3`;
}

/**
 * Where that recording's timeline would be.
 *
 * A recording made section by section is uploaded as two files that sit beside
 * each other: `<url>.mp3` and `<url>.json`. The JSON is the state file
 * `narrate.py` writes, and it says where each section of the page starts inside
 * the recording. The player asks for it at runtime, for the same reason it asks
 * for the MP3 at runtime: neither file is part of the build, so uploading the
 * pair has to be enough to give a page a sectioned player.
 *
 * This takes the recording's address rather than the page's URL, because the
 * player is handed the recording's address and nothing else. Keeping the one
 * `/audio/` prefix in `audioFor` above means there is only one place that knows
 * where recordings live.
 */
export function timelineFor(audio: string): string {
  return audio.replace(/\.mp3(?=$|[?#])/, '.json');
}

/** One `##` section of a page, as the timeline describes it. */
export type NarrationSection = {
  /** Where the section's words start in the joined recording, in seconds. */
  start: number;
  /** How long the section's own audio runs, in seconds. */
  duration: number;
  /** The heading the section was made from, which is the name the player shows. */
  title: string;
  /** The heading's id on the page, and null for the words before the first heading. */
  anchor: string | null;
};

/**
 * Read a timeline, or decide there is not one.
 *
 * The text comes off the network, so it can be anything at all: a 404 page, a
 * half-written file, or a version of the format this player has never heard of.
 * Every one of those answers is null, and null means the player behaves exactly
 * as it did before timelines existed. Nothing here throws.
 *
 * A section is kept only if it says where it starts, how long it runs and what
 * it is called, because those three are what the player draws. A timeline with
 * fewer than two usable sections is also null: one section is the whole page, so
 * there is nothing to mark and nowhere to jump to.
 */
export function readTimeline(text: string): NarrationSection[] | null {
  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch {
    return null;
  }
  if (parsed === null || typeof parsed !== 'object') return null;
  const file = parsed as { version?: unknown; sections?: unknown };
  if (file.version !== 'v1') return null;
  if (!Array.isArray(file.sections)) return null;

  const sections: NarrationSection[] = [];
  for (const entry of file.sections) {
    if (entry === null || typeof entry !== 'object') continue;
    const row = entry as Record<string, unknown>;
    const start = Number(row.start);
    const duration = Number(row.duration);
    const title = typeof row.title === 'string' ? row.title.trim() : '';
    if (!Number.isFinite(start) || start < 0) continue;
    if (!Number.isFinite(duration) || duration <= 0) continue;
    if (title === '') continue;
    sections.push({
      start,
      duration,
      title,
      anchor: typeof row.anchor === 'string' && row.anchor !== '' ? row.anchor : null,
    });
  }
  if (sections.length < 2) return null;
  // The contract says the sections are already in order. Sorting them costs
  // nothing and means a hand-edited file cannot draw its marks out of order.
  sections.sort((a, b) => a.start - b.start);
  return sections;
}
