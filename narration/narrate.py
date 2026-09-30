#!/usr/bin/env python3
"""Turn the pages of a book into spoken narration.

The site presents the Markdown in `docs/` as books, chapters and sections. This
script gives each of those sections an audio recording, so that the same
material can be followed by someone who is not looking at a screen.

It runs in two stages, and the stages are separate on purpose.

First a text model reads the page and writes a **transcript**: the words to be
spoken. This is not the page read out. A page holds diagrams, code, tables and
links, none of which mean anything aloud, so the model is asked to say what the
diagram shows, to explain what the code does rather than recite it, and to skip
the table of contents entirely. The instruction it is given is in `prompt.md`,
beside this file, so it can be read and changed without touching the code.

Then a speech model reads that transcript aloud. Transcripts are kept in the
repository because they are the part worth checking: if a recording says
something wrong, the transcript is where the mistake is, and fixing it costs one
speech call rather than two model calls. Audio is not kept in the repository,
because it is large and can be made again from the transcript.

    python narration/narrate.py --book 05                 # a whole book
    python narration/narrate.py --book 05 --chapter 04    # one chapter
    python narration/narrate.py --doc docs/05_.../02_ransac.md
    python narration/narrate.py --book 05 --stage transcript   # stop after the words
    python narration/narrate.py --book 06 --upload            # and push to S3

Credentials come from `.env` at the repository root.
"""

from __future__ import annotations

import argparse
import base64
import concurrent.futures
import json
import os
import pathlib
import re
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
HERE = ROOT / "narration"
TRANSCRIPTS = HERE / "transcripts"
AUDIO = HERE / "audio"
MANIFEST = HERE / "manifest.json"

ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models"

# The speech model is a Pro one rather than a Flash one: this is read once and
# listened to many times, so the quality of the reading outlasts its cost.
SPEECH_MODEL = "gemini-2.5-pro-preview-tts"

# The same voice the interestled project narrates with. Even and unhurried,
# which is what a long technical page needs.
VOICE = "Erinome"

# Speech comes back as raw 16-bit mono samples with no container. MP3 at this
# rate is about a sixth of the size and is indistinguishable for a single voice,
# which matters when a book is a hundred pages long.
MP3_BITRATE = "48k"

# How much transcript goes into one speech call. The model has an output
# ceiling, and a request that crosses it comes back truncated rather than
# refused, so chunks are kept well inside it and the audio is joined afterwards.
# Splitting happens at paragraph boundaries, so no sentence is ever cut in two.
CHUNK_CHARS = 2600


# --------------------------------------------------------------------------- #
# The repository's own structure
# --------------------------------------------------------------------------- #

def env() -> dict[str, str]:
    """Read .env at the repository root. No dependency, and no shell needed."""
    values: dict[str, str] = {}
    path = ROOT / ".env"
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip().strip('"').strip("'")
    # A real environment variable wins, so a CI run needs no file on disk.
    for key in ("GOOGLE_API_KEY", "GEMINI_MODEL", "GEMINI_API_KEY"):
        if os.environ.get(key):
            values[key] = os.environ[key]
    return values


def slug(name: str) -> str:
    """`03_arm` becomes `arm`, which is what the site puts in the URL."""
    return re.sub(r"^\d+_", "", name).removesuffix(".md")


def pages(book: str | None, chapter: str | None, doc: str | None) -> list[pathlib.Path]:
    """Every section to narrate, in reading order.

    A section is one Markdown file. Overviews are included, because a listener
    working through a chapter needs the page that says what the chapter is for
    just as much as a reader does.
    """
    if doc is not None:
        return [pathlib.Path(doc).resolve()]
    if book is None:
        raise SystemExit("give --book, or --doc for a single page")

    books = sorted(p for p in DOCS.iterdir() if p.is_dir() and p.name.startswith(book))
    if not books:
        raise SystemExit(f"no book in docs/ starts with {book!r}")

    found: list[pathlib.Path] = []
    for b in books:
        for p in sorted(b.rglob("*.md")):
            if chapter is not None:
                # The chapter is the first folder under the book.
                rel = p.relative_to(b)
                if not rel.parts or not rel.parts[0].startswith(chapter):
                    continue
            found.append(p)
    return found


def url_path(page: pathlib.Path) -> str:
    """The site's own URL for a page, which is how audio is matched to it.

    A book is a folder, a chapter is a folder inside it, and a section is a
    Markdown file. A folder inside a chapter, such as `02_most-used`, is a
    labelled group rather than a level of its own, so the site does not give it
    a path segment: it folds the group into the section's own slug with two
    dashes, which is why the address ends `most-used--ransac` and not
    `most-used/ransac`.

        docs/05_x/02_y/02_most-used/03_z.md  ->  x/y/most-used--z
        docs/05_x/02_y/01_overview.md        ->  x/y/overview
        docs/03_x/07_y.md                    ->  x/y/y

    This has to agree exactly with `lib/content.ts`, because a mismatch does not
    fail: it produces a recording that no page ever asks for, and a page that
    quietly shows no player.
    """
    parts = [slug(part) for part in page.relative_to(DOCS).parts]
    if len(parts) == 2:
        # A Markdown file straight inside a book is a chapter with one section,
        # and that section takes the chapter's own slug.
        return f"{parts[0]}/{parts[1]}/{parts[1]}"
    if len(parts) == 4:
        # book / chapter / group / section
        return f"{parts[0]}/{parts[1]}/{parts[2]}--{parts[3]}"
    return "/".join(parts)


# --------------------------------------------------------------------------- #
# Talking to the model
# --------------------------------------------------------------------------- #

class ModelError(RuntimeError):
    pass


def call(model: str, body: dict, key: str, attempts: int = 4) -> dict:
    """One request, retried on the failures that are worth retrying.

    A rate limit or a server error is temporary and the same request will
    usually work a moment later, so those are retried with a widening wait. A
    refusal is not temporary, so it is raised at once rather than repeated three
    more times at the same cost.
    """
    request = urllib.request.Request(
        f"{ENDPOINT}/{model}:generateContent",
        data=json.dumps(body).encode(),
        headers={"content-type": "application/json", "x-goog-api-key": key},
    )
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=900) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            detail = error.read().decode()[:300]
            if error.code in (429, 500, 502, 503, 504) and attempt < attempts - 1:
                wait = 5 * (2**attempt)
                print(f"      {error.code}; waiting {wait}s", flush=True)
                time.sleep(wait)
                continue
            raise ModelError(f"HTTP {error.code}: {detail}") from error
        except (urllib.error.URLError, TimeoutError) as error:
            if attempt < attempts - 1:
                time.sleep(5 * (2**attempt))
                continue
            raise ModelError(str(error)) from error
    raise ModelError("gave up")


def write_transcript(page: pathlib.Path, key: str, model: str) -> str:
    """Ask the text model for the words to be spoken."""
    instruction = (HERE / "prompt.md").read_text()
    body = {
        "systemInstruction": {"parts": [{"text": instruction}]},
        "contents": [{"role": "user", "parts": [{"text": page.read_text()}]}],
        # Deliberately low: this is a faithful retelling of a page that already
        # exists, and invention is the failure to avoid.
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 32000},
    }
    reply = call(model, body, key)
    candidate = reply["candidates"][0]
    parts = candidate.get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts).strip()
    if not text:
        raise ModelError(f"no transcript returned (finish: {candidate.get('finishReason')})")
    return text


def chunks(text: str, limit: int = CHUNK_CHARS) -> list[str]:
    """Split a transcript for speech, never inside a sentence.

    Paragraphs first, because a paragraph break is a natural pause the listener
    will not notice. A paragraph longer than the limit is split at sentence ends
    instead, which is still a place a voice can stop without sounding cut off.
    """
    out: list[str] = []
    current = ""
    for paragraph in [p.strip() for p in text.split("\n\n") if p.strip()]:
        if len(paragraph) > limit:
            for sentence in re.split(r"(?<=[.!?])\s+", paragraph):
                if len(current) + len(sentence) + 1 > limit and current:
                    out.append(current.strip())
                    current = ""
                current += sentence + " "
            continue
        if len(current) + len(paragraph) + 2 > limit and current:
            out.append(current.strip())
            current = ""
        current += paragraph + "\n\n"
    if current.strip():
        out.append(current.strip())
    return out


def speak(text: str, key: str) -> tuple[bytes, int]:
    """One block of words, as raw samples and the rate they were made at."""
    body = {
        "contents": [{"role": "user", "parts": [{"text": text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE}}},
        },
    }
    reply = call(SPEECH_MODEL, body, key)
    candidate = reply["candidates"][0]
    inline = next(
        (p["inlineData"] for p in candidate.get("content", {}).get("parts", []) if "inlineData" in p),
        None,
    )
    if inline is None:
        raise ModelError(f"no audio returned (finish: {candidate.get('finishReason')})")
    rate_match = re.search(r"rate=(\d+)", inline.get("mimeType", ""))
    rate = int(rate_match.group(1)) if rate_match else 24000
    return base64.b64decode(inline["data"]), rate


def wav(pcm: bytes, rate: int) -> bytes:
    """A 44-byte RIFF header in front of the samples, so a player will take it."""
    header = (
        b"RIFF"
        + struct.pack("<I", 36 + len(pcm))
        + b"WAVEfmt "
        + struct.pack("<IHHIIHH", 16, 1, 1, rate, rate * 2, 2, 16)
        + b"data"
        + struct.pack("<I", len(pcm))
    )
    return header + pcm


# --------------------------------------------------------------------------- #
# Doing the work
# --------------------------------------------------------------------------- #

def speak_all(blocks: list[str], key: str, workers: int) -> tuple[bytes, int]:
    """Every block of a page, spoken at once rather than one after another.

    The speech model runs at roughly one and a half times real time, so a page
    that becomes twenty-five minutes of audio takes about seventeen minutes to
    make in a single line. The blocks do not depend on each other, so they are
    sent together and joined in order afterwards, which turns those seventeen
    minutes into about three.

    The joining is what makes this safe: results come back in whatever order
    they finish, and the list is indexed so the audio is reassembled in the
    order the words were written rather than the order the model answered.
    """
    done: list[bytes | None] = [None] * len(blocks)
    rate = 24000
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(speak, block, key): index for index, block in enumerate(blocks)}
        for future in concurrent.futures.as_completed(futures):
            index = futures[future]
            samples, rate = future.result()
            done[index] = samples
            print(f"      block {index + 1}/{len(blocks)} done", flush=True)
    missing = [i for i, part in enumerate(done) if part is None]
    if missing:
        raise ModelError(f"no audio for block(s) {missing}")
    return b"".join(part for part in done if part is not None), rate


def narrate(page: pathlib.Path, key: str, model: str, stage: str, force: bool,
            workers: int = 4) -> dict | None:
    """One page, from Markdown to an MP3 beside a transcript."""
    address = url_path(page)
    transcript_file = TRANSCRIPTS / f"{address}.md"
    audio_file = AUDIO / f"{address}.mp3"

    # The transcript, which is the expensive and checkable half.
    if transcript_file.exists() and not force:
        transcript = transcript_file.read_text()
        print(f"   transcript: kept ({len(transcript.split())} words)", flush=True)
    else:
        transcript = write_transcript(page, key, model)
        transcript_file.parent.mkdir(parents=True, exist_ok=True)
        transcript_file.write_text(transcript + "\n")
        print(f"   transcript: written ({len(transcript.split())} words)", flush=True)

    if stage == "transcript":
        return None

    if audio_file.exists() and not force:
        print("   audio: kept", flush=True)
        return None

    blocks = chunks(transcript)
    print(f"   speaking {len(blocks)} block(s) on {workers} workers", flush=True)
    pcm, rate = speak_all(blocks, key, workers)

    audio_file.parent.mkdir(parents=True, exist_ok=True)
    raw = audio_file.with_suffix(".wav")
    raw.write_bytes(wav(pcm, rate))
    subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-y", "-i", str(raw),
         "-codec:a", "libmp3lame", "-b:a", MP3_BITRATE, "-ac", "1", str(audio_file)],
        check=True,
    )
    raw.unlink()

    seconds = len(pcm) // (rate * 2)
    size = audio_file.stat().st_size
    print(f"   audio: {seconds // 60}m {seconds % 60}s, {size // 1024} KB", flush=True)
    return {"seconds": seconds, "bytes": size}


def rebuild_manifest() -> dict:
    """A record of which pages have been narrated, and how large each one is.

    The site does not read this. Every page carries a player that asks the
    browser for its own recording and shows itself only if one arrives, so a
    recording becomes playable by being uploaded and needs no rebuild. This file
    exists so that a person can see what has been made without listing a bucket,
    and it is built by looking at the files rather than by trusting this run.
    """
    entries: dict[str, dict] = {}
    if AUDIO.exists():
        for mp3 in sorted(AUDIO.rglob("*.mp3")):
            address = str(mp3.relative_to(AUDIO).with_suffix(""))
            entries[address] = {"bytes": mp3.stat().st_size}
    MANIFEST.write_text(json.dumps(entries, indent=2, sort_keys=True) + "\n")
    return entries


def upload(bucket: str) -> None:
    """Put the recordings where the site can read them.

    They go under `audio/` in the same bucket the site is served from, so a page
    and its recording come from one origin and the browser needs no permission
    to fetch across one. The deploy workflow excludes that prefix from its own
    sync, so shipping the site never deletes the recordings.

    Uploading is all it takes for a page to gain a player: the page already asks
    for this address on every visit, and a missing file is answered with a 404
    that CloudFront is configured never to cache.
    """
    subprocess.run(
        ["aws", "s3", "sync", str(AUDIO), f"s3://{bucket}/audio/",
         "--no-progress", "--content-type", "audio/mpeg",
         "--cache-control", "public, max-age=31536000, immutable"],
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--book", help="book folder prefix, such as 05")
    parser.add_argument("--chapter", help="chapter folder prefix inside the book, such as 04")
    parser.add_argument("--doc", help="one Markdown file, instead of --book")
    parser.add_argument("--stage", choices=("transcript", "audio"), default="audio",
                        help="stop after the transcript, or go on to the speech")
    parser.add_argument("--force", action="store_true", help="redo work that is already done")
    parser.add_argument("--upload", action="store_true", help="sync the audio to S3 afterwards")
    parser.add_argument("--bucket", default="robotics-basics-web-729763663166")
    parser.add_argument("--workers", type=int, default=4,
                        help="speech calls to keep in flight at once for one page")
    args = parser.parse_args()

    values = env()
    key = values.get("GOOGLE_API_KEY") or values.get("GEMINI_API_KEY")
    if not key:
        raise SystemExit("no GOOGLE_API_KEY in .env or the environment")
    model = values.get("GEMINI_MODEL", "gemini-3.1-pro-preview")

    todo = pages(args.book, args.chapter, args.doc)
    print(f"{len(todo)} page(s); transcript model {model}, speech model {SPEECH_MODEL}\n")

    failed: list[tuple[pathlib.Path, str]] = []
    for number, page in enumerate(todo, 1):
        print(f"[{number}/{len(todo)}] {page.relative_to(ROOT)}", flush=True)
        try:
            narrate(page, key, model, args.stage, args.force, args.workers)
        except (ModelError, subprocess.CalledProcessError) as error:
            print(f"   FAILED: {error}", flush=True)
            failed.append((page, str(error)))

    entries = rebuild_manifest()
    print(f"\nmanifest: {len(entries)} recording(s)")

    if args.upload:
        upload(args.bucket)
        print(f"uploaded to s3://{args.bucket}/audio/")

    if failed:
        print(f"\n{len(failed)} page(s) failed:")
        for page, error in failed:
            print(f"   {page.relative_to(ROOT)}: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
