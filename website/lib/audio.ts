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
