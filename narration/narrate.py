#!/usr/bin/env python3
"""Turn the pages of a book into spoken narration, one section at a time.

The site presents the Markdown in `docs/` as books, chapters and pages. This
script gives each page an audio recording, so that the same material can be
followed by someone who is not looking at a screen.

It runs in two stages, and the stages are separate on purpose.

First a text model reads the page and writes a **transcript**: the words to be
spoken. This is not the page read out. A page holds diagrams, code, tables and
links, none of which mean anything aloud, so the model is asked to say what the
diagram shows, to explain what the code does rather than recite it, and to skip
the table of contents entirely. The instruction it is given lives beside this
file, so it can be read and changed without touching the code.

Then a speech model reads that transcript aloud. Transcripts are kept in the
repository because they are the part worth checking: if a recording says
something wrong, the transcript is where the mistake is, and fixing it costs one
speech call rather than two model calls. Audio is not kept in the repository,
because it is large and can be made again from the transcript.

Work happens per section rather than per page. A section here is one `##`
heading block inside a page, plus the text before the first heading, which is
called the lead. Each section gets its own transcript and its own MP3, the MP3s
are joined into the single file the player asks for, and a state file records
what was made, how long each section is and where each one starts. The reason is
cost: when one paragraph of a page changes, only the section holding it has to be
written and spoken again.

Two shapes therefore exist side by side. A page narrated before this change has
one whole-page transcript, one MP3 and no state file, and this script leaves such
a page exactly as it is. `--v1` converts one to the sectioned shape, which costs
a full set of model calls, so it is asked for rather than assumed.

    python narration/narrate.py --book 05                 # a whole book
    python narration/narrate.py --book 05 --chapter 04    # one chapter
    python narration/narrate.py --doc docs/05_.../02_ransac.md
    python narration/narrate.py --doc docs/08_.../01_the-cell.md --v1
    python narration/narrate.py --book 05 --stage transcript   # stop after the words
    python narration/narrate.py --book 08 --upload            # and push to S3

Credentials come from `.env` at the repository root.
"""

from __future__ import annotations

import argparse
import base64
import concurrent.futures
import dataclasses
import hashlib
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
STATE = HERE / "state"
MANIFEST = HERE / "manifest.json"

# The instruction for narrating one section, and the older one for narrating a
# whole page. The whole-page instruction is still used by pages that have not
# been converted.
SECTION_PROMPT = HERE / "prompt-section.md"
PAGE_PROMPT = HERE / "prompt.md"

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
# A section longer than this is still split into blocks, and those blocks join
# into that one section's file.
CHUNK_CHARS = 2600

# The line written in front of each section's words in the transcript file. It
# is a Markdown comment, so the file still reads as prose, and it is what lets
# the words of one section be found again when only that section has changed.
MARKER = re.compile(r"^<!--\s*section:\s*([^|]+?)\s*\|\s*(.*?)\s*-->\s*$", re.M)

# The heading whose section is never narrated. It is a list of links to the rest
# of the page, and a listener cannot click a link.
CONTENTS_ID = "contents"

# The page-level `version` in the state file. A page counts as sectioned only
# when it says exactly this, so a page whose audio is not complete yet says
# something else and the player falls back to its old behaviour.
VERSION = "v1"
DRAFT_VERSION = "v1-draft"


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
    # The AWS keys are here because `--upload` runs the `aws` command, which
    # reads them from its own environment and not from this file.
    for key in ("GOOGLE_API_KEY", "GEMINI_MODEL", "GEMINI_API_KEY",
                "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION",
                "AWS_SESSION_TOKEN"):
        if os.environ.get(key):
            values[key] = os.environ[key]
    return values


def slug(name: str) -> str:
    """`03_arm` becomes `arm`, which is what the site puts in the URL."""
    return re.sub(r"^\d+_", "", name).removesuffix(".md")


def pages(book: str | None, chapter: str | None, doc: str | None) -> list[pathlib.Path]:
    """Every page to narrate, in reading order.

    A page is one Markdown file. Overviews are included, because a listener
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

    A book is a folder, a chapter is a folder inside it, and a page is a
    Markdown file. A folder inside a chapter, such as `02_most-used`, is a
    labelled group rather than a level of its own, so the site does not give it
    a path segment: it folds the group into the page's own slug with two
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
        # book / chapter / group / page
        return f"{parts[0]}/{parts[1]}/{parts[2]}--{parts[3]}"
    return "/".join(parts)


def stamp() -> str:
    """The time now, in UTC, written the one way the state file uses."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# --------------------------------------------------------------------------- #
# Splitting a page into sections
# --------------------------------------------------------------------------- #

def fenced(lines: list[str]) -> list[bool]:
    """Which of these lines sit inside a fenced code block.

    A fence opens with three or more backticks or tildes and closes with at
    least as many of the same character. This matters because a Python comment
    and a Markdown example both put a hash at the start of a line, and a hash
    inside a code block is not a heading. The fence lines themselves are counted
    as inside, since they are not headings either.
    """
    inside = [False] * len(lines)
    opener: str | None = None
    for index, line in enumerate(lines):
        match = re.match(r"^(`{3,}|~{3,})", line.strip())
        if opener is None:
            if match:
                opener = match.group(1)
                inside[index] = True
            continue
        inside[index] = True
        if match and match.group(1)[0] == opener[0] and len(match.group(1)) >= len(opener):
            opener = None
    return inside


def heading_slug(heading: str) -> str:
    """The anchor a heading gets, by the rule the repository's link check uses.

    Backticks go, a link becomes its own words, bold and italic markers go, then
    anything that is not a letter, a digit, a space, an underscore or a hyphen is
    removed and the spaces become hyphens. The rule is copied rather than
    improved on, because a different answer here would send a reader to an
    anchor that does not exist.
    """
    text = re.sub(r"`", "", heading)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\*\*?", "", text)
    return re.sub(r"[^a-z0-9\s_-]", "", text.lower().strip()).replace(" ", "-")


def heading_text(heading: str) -> str:
    """A heading with its Markdown removed, for showing and for saying aloud."""
    text = re.sub(r"`", "", heading)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\*\*?", "", text)
    # A pipe would be read as the end of the title in a marker line, and an
    # arrow would end the comment, so neither is allowed to survive.
    return text.replace("|", "/").replace("-->", "--").strip()


@dataclasses.dataclass
class Section:
    """One narrated part of a page.

    `markdown` is the part of the page this section covers, exactly as the page
    writes it, including the heading line. `source_sha` is taken over that text
    and is what decides whether the section has to be made again.
    """

    index: int
    id: str
    title: str
    anchor: str | None
    markdown: str

    @property
    def source_sha(self) -> str:
        return hashlib.sha256(self.markdown.encode()).hexdigest()


def page_title(text: str) -> str:
    """The page's own heading, which is the title of the lead section."""
    lines = text.splitlines()
    for line, within in zip(lines, fenced(lines)):
        if not within and line.startswith("# "):
            return heading_text(line[2:])
    return ""


def split_sections(text: str, title: str = "") -> list[Section]:
    """Cut a page into the parts that are narrated separately.

    The cut is made at every top-level `##` heading that is not inside a code
    block. Everything before the first such heading is the lead, which carries
    the page's own title and has no anchor of its own. The table of contents is
    dropped, because it is a list of links and means nothing aloud. A lead that
    holds nothing but the title line is dropped as well, since there would be
    nothing to say.

    The returned indexes count the sections that are kept, so they run from zero
    with no gaps even where a contents section was removed.

    Two headings on one page can read the same, and then they make the same name.
    The second one is given a number, the way a Markdown renderer numbers the
    second anchor of a repeated heading. Without that they would be one section
    to everything that follows, because the words, the hashes, the lengths and
    the files are all held by name: the later heading would quietly take the
    earlier one's place, and the earlier one's recording would be renamed out
    from under the joined page and lost.
    """
    lines = text.splitlines()
    inside = fenced(lines)
    starts = [
        index
        for index, line in enumerate(lines)
        if not inside[index] and (line.startswith("## ") or line.rstrip() == "##")
    ]
    if not title:
        title = page_title(text)

    blocks: list[tuple[str, str, str | None, str]] = []  # id, title, anchor, markdown
    first = starts[0] if starts else len(lines)
    lead = "\n".join(lines[:first]).strip()
    prose = "\n".join(line for line in lead.splitlines() if not line.startswith("# ")).strip()
    if prose:
        blocks.append(("lead", title, None, lead))

    seen: dict[str, int] = {}
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(lines)
        heading = lines[start].lstrip("#").strip()
        identifier = heading_slug(heading)
        if identifier == CONTENTS_ID:
            continue
        seen[identifier] = seen.get(identifier, 0) + 1
        if seen[identifier] > 1:
            identifier = f"{identifier}-{seen[identifier] - 1}"
        blocks.append((identifier, heading_text(heading), identifier,
                       "\n".join(lines[start:end]).strip()))

    return [
        Section(index=index, id=identifier, title=name, anchor=anchor, markdown=markdown)
        for index, (identifier, name, anchor, markdown) in enumerate(blocks)
    ]


def transcript_text(sections: list[tuple[str, str, str]]) -> str:
    """The whole transcript file: a marker line and then the words, in order."""
    out = []
    for identifier, name, words in sections:
        out.append(f"<!-- section: {identifier} | {name} -->\n\n{words.strip()}")
    return "\n\n".join(out) + "\n"


def read_transcript(path: pathlib.Path) -> list[tuple[str, str, str]]:
    """The sections a transcript file holds, as id, title and words.

    A transcript written before this change has no marker lines, so nothing is
    found in it and an empty list comes back. That is how a page of the older
    shape is recognised from its transcript alone.
    """
    if not path.exists():
        return []
    text = path.read_text()
    found = list(MARKER.finditer(text))
    out: list[tuple[str, str, str]] = []
    for position, match in enumerate(found):
        end = found[position + 1].start() if position + 1 < len(found) else len(text)
        out.append((match.group(1), match.group(2), text[match.end():end].strip()))
    return out


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


def ask(instruction: str, content: str, key: str, model: str) -> str:
    """One text request, with the words of the reply joined into a string."""
    body = {
        "systemInstruction": {"parts": [{"text": instruction}]},
        "contents": [{"role": "user", "parts": [{"text": content}]}],
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


def write_transcript(page: pathlib.Path, key: str, model: str) -> str:
    """Ask the text model for the words for a whole page, as v0 pages are made."""
    return ask(PAGE_PROMPT.read_text(), page.read_text(), key, model)


def write_section_transcript(section: Section, title: str, previous: str | None,
                             key: str, model: str) -> str:
    """Ask the text model for the words for one section.

    The model is told the page's title, the heading it is narrating and the
    title of the section before it, so that it can carry on from where the last
    section stopped instead of introducing the page again.
    """
    lines = [f"Page title: {title}"]
    if section.anchor is None:
        lines.append("Section: the opening of the page, before the first heading.")
    else:
        lines.append(f"Section heading: {section.title}")
    if previous is None:
        lines.append("The section before this one: none, this is where the page starts.")
    else:
        lines.append(f"The section before this one: {previous}")
    lines.append("")
    lines.append("The Markdown of the section to narrate follows.")
    lines.append("")
    content = "\n".join(lines) + section.markdown
    return ask(SECTION_PROMPT.read_text(), content, key, model)


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
# Audio files
# --------------------------------------------------------------------------- #

def speak_all(blocks: list[str], key: str, workers: int) -> tuple[bytes, int]:
    """Every block of a transcript, spoken at once rather than one after another.

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


def to_mp3(pcm: bytes, rate: int, target: pathlib.Path) -> None:
    """Write samples out as the MP3 the player downloads."""
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = target.with_suffix(".wav")
    raw.write_bytes(wav(pcm, rate))
    subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-y", "-i", str(raw),
         "-codec:a", "libmp3lame", "-b:a", MP3_BITRATE, "-ac", "1", str(target)],
        check=True,
    )
    raw.unlink()


def duration(path: pathlib.Path) -> float:
    """How long an audio file really is, in seconds, asked of the file itself.

    The length is measured rather than worked out from the number of words,
    because a guess would put every section marker in the wrong place and the
    error would grow along the page.
    """
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return round(float(result.stdout.strip()), 2)


def join(parts: list[pathlib.Path], target: pathlib.Path) -> None:
    """Put the section files end to end into the one file the player asks for.

    The concat demuxer copies the compressed frames across without decoding and
    encoding them again, so joining a whole page costs a fraction of a second
    and the sound is the same sound.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    listing = target.parent / f".{target.stem}.concat"
    # A single quote inside a quoted path has to be closed, escaped and opened
    # again, which is the one piece of quoting this file format asks for.
    lines = [f"file '{str(p.resolve()).replace(chr(39), chr(39) + chr(92) + chr(39) + chr(39))}'" for p in parts]
    listing.write_text("\n".join(lines) + "\n")
    # The log level is lower here than anywhere else on purpose. Every MP3
    # carries a little silence at each end that the encoder put there, so at each
    # join ffmpeg sees one frame starting a shade before the last one ended and
    # says so. The file it writes is correct, and a real failure, such as a piece
    # that is missing, still prints and still fails.
    try:
        subprocess.run(
            ["ffmpeg", "-loglevel", "fatal", "-y", "-f", "concat", "-safe", "0",
             "-i", str(listing), "-c", "copy", str(target)],
            check=True,
        )
    finally:
        listing.unlink(missing_ok=True)


def offsets(durations: list[float]) -> list[float]:
    """Where each section starts, which is the sum of the ones before it."""
    out: list[float] = []
    running = 0.0
    for length in durations:
        out.append(round(running, 2))
        running += length
    return out


# --------------------------------------------------------------------------- #
# One page, the older whole-page way
# --------------------------------------------------------------------------- #

def narrate_page(page: pathlib.Path, key: str, model: str, stage: str, force: bool,
                 workers: int = 4) -> dict | None:
    """One page as a single transcript and a single MP3.

    This is how every page recorded before sections existed was made, and it is
    kept so that those recordings are not thrown away and remade for nothing.
    """
    address = url_path(page)
    transcript_file = TRANSCRIPTS / f"{address}.md"
    audio_file = AUDIO / f"{address}.mp3"

    # The transcript, which is the expensive and checkable half. It is rewritten
    # only when the transcript itself is what was asked for, because a
    # transcript is often corrected by hand after it has been read against the
    # page, and asking for the speech again must not throw those corrections
    # away. To replace the words, ask for the transcript stage.
    if transcript_file.exists() and not (force and stage == "transcript"):
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
    to_mp3(pcm, rate, audio_file)

    seconds = len(pcm) // (rate * 2)
    size = audio_file.stat().st_size
    print(f"   audio: {seconds // 60}m {seconds % 60}s, {size // 1024} KB", flush=True)
    return {"seconds": seconds, "bytes": size}


# --------------------------------------------------------------------------- #
# One page, section by section
# --------------------------------------------------------------------------- #

def existing_section_file(folder: pathlib.Path, identifier: str) -> pathlib.Path | None:
    """The MP3 already made for this section, whatever number it carries.

    A section's file name starts with its position on the page, so inserting a
    new section renames the files of everything after it. The audio itself has
    not changed, so the file is found by its id and renamed rather than spoken
    again.
    """
    if not folder.exists():
        return None
    wanted = re.compile(rf"\d\d+-{re.escape(identifier)}$")
    found = sorted(p for p in folder.glob("*.mp3") if wanted.fullmatch(p.stem))
    return found[0] if found else None


def state_is_current(before: dict, sections: list[Section], address: str) -> bool:
    """Whether the state file already describes exactly these sections.

    This is what lets a run over a book that has not changed cost nothing. If
    the record names the same sections in the same order, with the same source
    text, a measured length for each one and the file name each one should have,
    there is nothing to join and nothing to write.
    """
    if before.get("version") != VERSION or before.get("duration") is None:
        return False
    rows = before.get("sections", [])
    if len(rows) != len(sections):
        return False
    for row, section in zip(rows, sections):
        if row.get("id") != section.id or row.get("index") != section.index:
            return False
        if row.get("source_sha") != section.source_sha:
            return False
        if row.get("start") is None or row.get("duration") is None:
            return False
        if row.get("file") != f"{address}/{section.index:02d}-{section.id}.mp3":
            return False
    return True


def narrate_sections(page: pathlib.Path, key: str, model: str, stage: str, force: bool,
                     workers: int = 4) -> dict | None:
    """One page, written and spoken one section at a time.

    A section whose Markdown has not changed since it was last made keeps its
    words and its audio and is sent to no model. A section that is new or
    changed is written and spoken again, and a section that has gone takes its
    files with it. The page is then joined again and the state file written,
    because a changed section moves the start of every section after it.
    """
    address = url_path(page)
    source = page.read_text()
    title = page_title(source) or slug(page.name)
    sections = split_sections(source, title)
    if not sections:
        raise ModelError("nothing to narrate: the page has no prose outside its contents")

    transcript_file = TRANSCRIPTS / f"{address}.md"
    state_file = STATE / f"{address}.json"
    folder = AUDIO / address
    page_audio = AUDIO / f"{address}.mp3"

    before = json.loads(state_file.read_text()) if state_file.exists() else {}
    records = {record["id"]: dict(record) for record in before.get("sections", [])}
    held = {identifier: words for identifier, _name, words in read_transcript(transcript_file)}

    # --- the words ---------------------------------------------------------- #
    # A transcript is often corrected by hand after it has been read against the
    # page, so the words are rewritten only for a section whose Markdown has
    # changed, or when the transcript stage is forced.
    written: list[tuple[str, str, str]] = []
    rewritten: set[str] = set()
    previous: str | None = None
    for section in sections:
        record = records.get(section.id, {})
        keep_words = (
            record.get("source_sha") == section.source_sha
            and section.id in held
            and not (force and stage == "transcript")
        )
        if keep_words:
            words = held[section.id]
            when = record.get("text_updated") or stamp()
        else:
            print(f"   writing {section.index:02d} {section.id}", flush=True)
            words = write_section_transcript(section, title, previous, key, model)
            when = stamp()
            rewritten.add(section.id)
        written.append((section.id, section.title, words))
        record["source_sha"] = section.source_sha
        record["text_updated"] = when
        records[section.id] = record
        previous = section.title

    spoken = {identifier: words for identifier, _name, words in written}
    transcript_file.parent.mkdir(parents=True, exist_ok=True)
    before_text = transcript_file.read_text() if transcript_file.exists() else ""
    transcript_file.write_text(transcript_text(written))
    total_words = sum(len(words.split()) for words in spoken.values())
    verb = "written" if rewritten else "kept"
    print(f"   transcript: {verb}, {len(sections)} section(s), {total_words} words", flush=True)

    # Words that changed make the audio for them wrong, so that audio goes now
    # rather than being joined into the page as if it still matched.
    for identifier in rewritten:
        stale = existing_section_file(folder, identifier)
        if stale is not None:
            stale.unlink()

    # A section that has gone from the page takes its file with it.
    ids = {section.id for section in sections}
    dropped = False
    if folder.exists():
        for mp3 in sorted(folder.glob("*.mp3")):
            named = re.fullmatch(r"\d\d+-(.+)", mp3.stem)
            if named and named.group(1) in ids:
                continue
            print(f"   dropping {mp3.name}", flush=True)
            mp3.unlink()
            dropped = True

    if stage == "transcript":
        # The state file is written even now, because it is the only record of
        # which source text each section's words were written from. It says it is
        # a draft until the audio is there, so a player that finds it plays the
        # page as one piece instead of trusting lengths that do not exist yet.
        #
        # A page that was already spoken is the exception, and it has to be, because
        # this stage exists so that the words can be read before anything is spoken.
        # Writing a draft there would throw away the timings of a recording that
        # had not changed by one second, and the page would lose its marks for no
        # reason. So a section that kept its words and still has its own audio
        # keeps its measurements too.
        #
        # The page as a whole only stays measured when it is the same page: nothing
        # rewritten, nothing dropped, and the sections in the order the recording
        # was joined in. A section that merely moved leaves the joined file in the
        # old order, and its lengths would then describe a recording that no longer
        # matches, which is the one thing the state file must never claim.
        kept = {}
        for section in sections:
            length = records.get(section.id, {}).get("duration")
            if (section.id not in rewritten and length is not None
                    and existing_section_file(folder, section.id) is not None):
                kept[section.id] = length
        same_page = (
            not rewritten and not dropped and page_audio.exists()
            and [record["id"] for record in before.get("sections", [])] ==
                [section.id for section in sections]
        )
        whole = before.get("duration") if same_page and len(kept) == len(sections) else None
        write_state(page, address, title, sections, records, spoken,
                    measured=kept, total=whole,
                    generated=before.get("generated") if same_page else None)
        return None

    # --- the speech --------------------------------------------------------- #
    moved = False
    spoke = False
    for section in sections:
        target = folder / f"{section.index:02d}-{section.id}.mp3"
        already = existing_section_file(folder, section.id)
        if already is not None and already != target:
            # Only the section's place on the page moved, so the file it already
            # has is renamed rather than spoken again.
            already.rename(target)
            moved = True
        if force or not target.exists():
            blocks = chunks(spoken[section.id])
            print(f"   speaking {section.index:02d} {section.id}: "
                  f"{len(blocks)} block(s) on {workers} workers", flush=True)
            pcm, rate = speak_all(blocks, key, workers)
            to_mp3(pcm, rate, target)
            records[section.id]["audio_updated"] = stamp()
            spoke = True
        elif not records[section.id].get("audio_updated"):
            # This file was made before the state file kept a time for it, as
            # happens on the run that converts a page, so the time it was last
            # written on disk is used instead.
            records[section.id]["audio_updated"] = time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime(target.stat().st_mtime))

    unchanged = (
        not rewritten and not spoke and not moved and not dropped
        and before_text == transcript_file.read_text()
        and page_audio.exists() and state_is_current(before, sections, address)
    )
    if unchanged:
        print(f"   audio: kept, {len(sections)} section(s)", flush=True)
        return None

    parts = [folder / f"{section.index:02d}-{section.id}.mp3" for section in sections]
    join(parts, page_audio)
    measured = {section.id: duration(part) for section, part in zip(sections, parts)}
    total = duration(page_audio)
    state = write_state(page, address, title, sections, records, spoken, measured, total)

    size = page_audio.stat().st_size
    print(f"   audio: {int(total) // 60}m {int(total) % 60}s over {len(sections)} section(s), "
          f"{size // 1024} KB", flush=True)
    return {"seconds": total, "bytes": size, "sections": len(state["sections"])}


def write_state(page: pathlib.Path, address: str, title: str, sections: list[Section],
                records: dict[str, dict], spoken: dict[str, str],
                measured: dict[str, float], total: float | None,
                generated: str | None = None) -> dict:
    """Write the record the player reads, and this script reads back next time.

    The page counts as sectioned only when every section has a measured length.
    A page whose words exist but whose audio does not yet is marked as a draft,
    so a player that finds it falls back to playing the page as one piece rather
    than trusting lengths that are not there.

    `generated` says when the recording was made, so a caller that made no
    recording passes the one already there. Stamping it with the time of a run
    that spoke nothing would put a change in the file for every run, and this
    file is committed, so that change would be read as the page having been
    made again.
    """
    complete = total is not None and all(section.id in measured for section in sections)
    starts = offsets([measured.get(section.id, 0.0) for section in sections])
    rows = []
    for section, start in zip(sections, starts):
        record = records.get(section.id, {})
        made = section.id in measured
        rows.append({
            "index": section.index,
            "id": section.id,
            "title": section.title,
            "anchor": section.anchor,
            "start": start if complete else None,
            "duration": measured.get(section.id) if made else None,
            "words": len(spoken.get(section.id, "").split()),
            "source_sha": record.get("source_sha", section.source_sha),
            "text_updated": record.get("text_updated"),
            "audio_updated": record.get("audio_updated"),
            "file": f"{address}/{section.index:02d}-{section.id}.mp3" if made else None,
        })
    state = {
        "version": VERSION if complete else DRAFT_VERSION,
        "url": address,
        "page": page.relative_to(ROOT).as_posix(),
        "title": title,
        "audio": f"{address}.mp3",
        "duration": total,
        "generated": generated or stamp(),
        "voice": VOICE,
        "speech_model": SPEECH_MODEL,
        "sections": rows,
    }
    state_file = STATE / f"{address}.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, indent=2) + "\n")
    return state


def narrate(page: pathlib.Path, key: str, model: str, stage: str, force: bool,
            workers: int = 4, upgrade: bool = False) -> dict | None:
    """One page, in whichever shape it already has.

    A page with a state file is already sectioned, so it is kept that way. A page
    without one was recorded as a single piece, and it stays that way until
    `--v1` asks for the conversion, because converting costs a full set of model
    calls for a page that already has a recording that works.
    """
    address = url_path(page)
    if (STATE / f"{address}.json").exists() or upgrade:
        return narrate_sections(page, key, model, stage, force, workers)
    return narrate_page(page, key, model, stage, force, workers)


# --------------------------------------------------------------------------- #
# The record of what exists, and putting it where the site can read it
# --------------------------------------------------------------------------- #

def page_addresses() -> set[str]:
    """Every address a page of the site could have a recording at.

    This comes from `docs/`, which is the only source that is true whatever the
    generator happens to be in the middle of. Asking the state files instead
    answers wrongly while a page is being made: its sections are on disk and its
    state file is not written until the end, so every piece of a page in flight
    looks like a page of its own.
    """
    return {url_path(doc) for doc in DOCS.rglob("*.md")}


def page_files() -> list[pathlib.Path]:
    """The joined recordings, one per page, in a stable order."""
    if not AUDIO.exists():
        return []
    addresses = page_addresses()
    return sorted(
        mp3 for mp3 in AUDIO.rglob("*.mp3")
        if mp3.relative_to(AUDIO).with_suffix("").as_posix() in addresses
    )


def section_files() -> set[pathlib.Path]:
    """Every MP3 that is one section of a page rather than a whole page.

    The state files say which those are, so the answer comes from the record
    rather than from guessing at file names.
    """
    out: set[pathlib.Path] = set()
    if not STATE.exists():
        return out
    for state in STATE.rglob("*.json"):
        try:
            data = json.loads(state.read_text())
        except json.JSONDecodeError:
            continue
        for section in data.get("sections", []):
            if section.get("file"):
                out.add(AUDIO / section["file"])
    return out


def rebuild_manifest() -> dict:
    """A record of which pages have been narrated, and how large each one is.

    The site does not read this. Every page carries a player that asks the
    browser for its own recording and shows itself only if one arrives, so a
    recording becomes playable by being uploaded and needs no rebuild. This file
    exists so that a person can see what has been made without listing a bucket,
    and it is built by looking at the files rather than by trusting this run.

    Only the file the player asks for is listed. The pieces a sectioned page is
    joined from are left out, because they are a working detail of how the page
    was made.
    """
    entries: dict[str, dict] = {}
    for mp3 in page_files():
        address = str(mp3.relative_to(AUDIO).with_suffix(""))
        entries[address] = {"bytes": mp3.stat().st_size}
    MANIFEST.write_text(json.dumps(entries, indent=2, sort_keys=True) + "\n")
    return entries


def aws_credentials(values: dict[str, str]) -> dict[str, str]:
    """Work out which credentials the `aws` command should run with.

    The command finds its own credentials in several ways, and the best of them
    is `aws login`, which holds a short-lived token it refreshes by itself and
    keeps no secret on disk. So that is tried first, exactly as the command
    would do it, and if it answers then nothing is added to its environment.

    Only when it has none of its own are the keys in `.env` used. They are the
    older arrangement, and the one that fails quietly: a key written there stays
    there after it is rotated, and because an explicit key beats every other
    source the command finds, putting a stale one into the environment would
    break a login that was working. Hence this order, rather than the reverse.

    Either way the answer is checked before a file is sent, so a dead key is
    reported here rather than part way through a sync.
    """
    def works(where: dict[str, str]) -> bool:
        done = subprocess.run(["aws", "sts", "get-caller-identity"],
                              env=where, capture_output=True, text=True)
        return done.returncode == 0

    inherited = dict(os.environ)
    if works(inherited):
        return inherited

    from_file = dict(inherited)
    for key in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION",
                "AWS_SESSION_TOKEN"):
        if values.get(key):
            from_file[key] = values[key]
    if from_file != inherited and works(from_file):
        return from_file

    raise SystemExit(
        "no working AWS credentials, so there is nowhere to upload to.\n"
        "   Run `aws login` to get a short-lived set, which is the better way\n"
        "   and keeps no secret on disk. Keys in .env still work, but a rotated\n"
        "   key left in that file is rejected like any other."
    )


def upload(bucket: str, values: dict[str, str]) -> None:
    """Put the recordings and their records where the site can read them.

    They go under `audio/` in the same bucket the site is served from, so a page
    and its recording come from one origin and the browser needs no permission
    to fetch across one. The deploy workflow excludes that prefix from its own
    sync, so shipping the site never deletes the recordings.

    Two syncs rather than one, because the content type is set for a whole sync
    and the two kinds of file need different ones. A browser handed the state
    file as `audio/mpeg` refuses to parse it as JSON, and then a sectioned page
    looks to the player exactly like a page with no sections at all.

    The pieces a page is joined from stay on this machine. The player asks for
    the joined file and the state file, so those are the only two per page worth
    the transfer.

    Both are stored with a long cache life, so whoever runs this has to flush
    the edge cache for a page whose recording has been replaced.
    """
    cache = "public, max-age=31536000, immutable"
    where = aws_credentials(values)
    # The joined pages are named one by one rather than matched by a pattern, and
    # the names come from `docs/` rather than from anything the generator wrote.
    # Two earlier ways of choosing them were both wrong. A pattern that excluded
    # names beginning with two digits and a hyphen also excluded a page whose own
    # title began with a number. Taking everything that the state files did not
    # call a piece uploaded every section of a page that was still being made,
    # because its state file is not written until it finishes. A page's address
    # is a fact about `docs/`, so that is what is asked.
    pages = page_files()
    if not pages:
        print("   nothing to upload: no recordings on disk", flush=True)
        return
    named: list[str] = ["--exclude", "*"]
    for mp3 in pages:
        named += ["--include", mp3.relative_to(AUDIO).as_posix()]
    subprocess.run(
        ["aws", "s3", "sync", str(AUDIO), f"s3://{bucket}/audio/", "--no-progress",
         *named, "--content-type", "audio/mpeg", "--cache-control", cache],
        check=True, env=where,
    )
    if STATE.exists():
        subprocess.run(
            ["aws", "s3", "sync", str(STATE), f"s3://{bucket}/audio/", "--no-progress",
             "--exclude", "*", "--include", "*.json",
             "--content-type", "application/json", "--cache-control", cache],
            check=True, env=where,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--book", help="book folder prefix, such as 05")
    parser.add_argument("--chapter", help="chapter folder prefix inside the book, such as 04")
    parser.add_argument("--doc", help="one Markdown file, instead of --book")
    parser.add_argument("--stage", choices=("transcript", "audio"), default="audio",
                        help="stop after the transcript, or go on to the speech")
    parser.add_argument("--force", action="store_true",
                        help="redo the work of the stage asked for: with --stage audio it "
                             "speaks the transcript again and leaves the transcript alone")
    parser.add_argument("--v1", "--upgrade", dest="v1", action="store_true",
                        help="convert a page recorded as one piece into the section by "
                             "section shape: split it at its headings, write and speak each "
                             "section, join them and write a state file. Without this, such a "
                             "page is left exactly as it is, because converting it costs a "
                             "full set of model calls. A page that already has a state file "
                             "is worked on section by section whether this is given or not")
    parser.add_argument("--upload", action="store_true", help="sync the audio to S3 afterwards")
    parser.add_argument("--bucket", default="robotics-basics-web-729763663166")
    parser.add_argument("--workers", type=int, default=4,
                        help="speech calls to keep in flight at once for one section")
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
            narrate(page, key, model, args.stage, args.force, args.workers, args.v1)
        except (ModelError, subprocess.CalledProcessError) as error:
            print(f"   FAILED: {error}", flush=True)
            failed.append((page, str(error)))

    entries = rebuild_manifest()
    print(f"\nmanifest: {len(entries)} recording(s)")

    if args.upload:
        upload(args.bucket, values)
        print(f"uploaded to s3://{args.bucket}/audio/")

    if failed:
        print(f"\n{len(failed)} page(s) failed:")
        for page, error in failed:
            print(f"   {page.relative_to(ROOT)}: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
