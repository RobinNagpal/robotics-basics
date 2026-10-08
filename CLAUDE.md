# Project rules

## Layout

The repo has five folders. `docs/` holds the docs. `code/` holds `src/`, the
Makefile and the pixi environment; run every `make` and `pixi` command from inside
`code/`, and a diagram script as `pixi run python ../docs/diagrams/<name>.py`.
`website/` is the Next.js site that reads `docs/` directly. `narration/` turns
pages into spoken recordings: `narrate.py` asks a model for a transcript and then
reads it aloud, the transcripts are committed because they are the part worth
checking, and the recordings themselves go to S3 rather than into the repository. `extension/` is a Chrome extension, built
with WXT, for leaving feedback on docs.dodao.io. Everything it needs is in that
folder: the extension in `extension/ui/`, the API in `extension/api/` that stores
the comments in S3 and runs on AWS Lambda, and the Terraform for both. Each of
`ui/` and `api/` is its own package, and its deploy runs only when that folder
changes. The one exception is its deploy workflow,
which GitHub reads only from `.github/workflows/`. Its README says how to set it up,
and how to work through the comments.
The folders in `docs/`
are its structure, so moving a doc moves it on the site too;
`website/lib/books.config.ts` only holds display text such as book titles, and the
list of parts.

## IMPORTANT: naming inside `docs/`

**Every document and every folder inside `docs/` must start with a two-digit number
prefix that gives its reading order.**

The shape is `NN_lower-hyphen-separated-name`. The prefix uses an **underscore**
after the number. The name itself uses **hyphens** between words, all lower case.

```
docs/02_perception/02_object-perception/01_overview.md
docs/02_perception/02_object-perception/03_programmed-methods.md
docs/02_perception/01_camera/03_one-box-intro.md
docs/03_frameworks/07_stone-stacking.md
```

`docs/` has three levels, and the website reads them as they are:

- A top-level folder is a **book**: `01_robotics-intro`, `02_perception`,
  `03_frameworks`, `04_ros-and-rviz`, `05_neural-networks`,
  `06_programming-techniques`, `07_learned-models`, `08_seeing-the-glasses`,
  `09_pushing-the-glasses-apart`.
- A folder inside a book is a **chapter**, and each `.md` file in it is a
  **section**. A `.md` file directly inside a book is a chapter with one section.
- A folder inside a chapter, such as `07_case-study/`, shows as a labelled group of
  sections in that chapter.

The point is that a reader opening the folder can see what to read first without
having to guess. The numbers are the reading order, not an alphabetical accident.

**When you add a new doc or folder:**

1. Work out where it belongs in the reading order.
2. Give it the next free number at that position.
3. If it belongs in the middle, renumber the ones after it. Use `git mv` so the
   history follows the file.
4. Fix every link that pointed at a renumbered file. Resolve each link against the
   file's old location, map it to the new one, and re-relativise it from the new
   location. Then run the link check below.

**Numbers do not need to be contiguous across a rename**, but they must be
increasing and unique within their folder. Leave a gap rather than renumbering the
world if the insert is cosmetic.

**Two exceptions, both deliberate:**

- `docs/images/` and `docs/diagrams/` keep their plain names, and so do the folders
  inside them. Nobody reads those in an order; they are referenced by path from the
  docs and from the diagram scripts. Prefixing them would break every image link for
  no reader benefit.
- Image folders are named after the *document* they belong to, without its number:
  `docs/images/one-arm-training/overview/` holds the pictures for
  `docs/03_frameworks/04_one-arm-training/01_overview.md`. This keeps image paths
  stable when a document is renumbered or moved to another book.

## Parts: the books are grouped

The books are grouped into **parts**, and a part is a shelf of the library rather
than a folder. Nothing in `docs/` says which part a book is in. The list is in
`website/lib/books.config.ts`, under `PARTS`, and it names each part's books by
folder name with the number prefix left off.

The groups are called parts and not sections, because a section already means one
document inside a chapter. Keep those two words apart everywhere, in the site and
in the docs.

A book that no part lists still appears on the site, in a part of its own at the
end. So adding a book never makes it disappear, but it does need a line in `PARTS`
to sit where you meant it to.

## Numbers are reading order, never addresses

The number prefix on a folder or a file says what to read first. It is not part of
the address of anything.

The site strips it: `docs/06_programming-techniques/02_geometry-and-cameras/` is
served at `/programming-techniques/geometry-and-cameras/`. So **never write a book
number into a URL**, and never say "book 5" where a link would do, because books
get renumbered when one is inserted and the sentence then points at the wrong book.
Inside the docs, link to the file and let the site work out the address.

## Code lives in a folder named after its book

`code/src/` is split by book. Each folder under it is named after a book folder in
`docs/`, character for character, prefix and all:

```
docs/02_perception/              code/src/02_perception/
docs/06_programming-techniques/  code/src/06_programming-techniques/
docs/08_seeing-the-glasses/      code/src/08_seeing-the-glasses/
```

Inside that folder the code keeps its own areas, such as
`code/src/02_perception/camera/camera_basics/`. A book with no code has no folder.

The names match so that a reader with a document open can see which folder holds
its programs. The cost is that renumbering a book renames its code folder too, and
then three things have to follow it: the `make` targets in `code/Makefile`, every
path written in a document, and any path a program prints that a document quotes
back. Search for the old folder name before you call the rename done, and run one
of the moved programs to prove the paths still work.

A book whose code is not part of the ROS workspace needs an empty `COLCON_IGNORE`
file at the top of its folder, because `make build` hands the whole of `src/` to
colcon and colcon builds every package it finds.

## Adding a book

1. Make `docs/NN_name/` with the next free number, and fill it with chapters and
   sections under the usual naming rule.
2. Add the book to `BOOK_INFO` in `website/lib/books.config.ts`, with a title, a
   short title for the header, a subtitle, a description and an accent colour. A
   new accent needs its two colours in `app/globals.css`, in both the light and
   the dark block, and a `[data-accent='name']` line.
3. Add it to a part in `PARTS`, or make a new part.
4. Give it a drawing in `components/BookGlyph.tsx`, or it falls back to the arm.
5. Put its code in `code/src/NN_name/`, named the same.
6. Run the link check below, then build the site.
7. Narrate it when you want it narrated, under the rules below. A new book stays
   silent until somebody asks for it by number.

## Narration: what an edited page owes its recording

`narration/narrate.py` gives a page a spoken recording. It works in two stages. A
text model reads the Markdown and writes a transcript, which is the words to be
spoken rather than the page read out. Then a speech model reads that transcript
aloud. The transcripts are committed and the audio is not, because a wrong
recording is always a wrong transcript and the audio can be made again from it.
`narration/README.md` describes the folder and how to run the script. The rules
below are what an editor of `docs/` owes the recordings.

### v0 and v1

There are two generations of recording, and every narrated page is in one of them.

v0 makes one transcript and one recording for a whole page. Nothing inside the
recording is marked, so a listener can only play it from the beginning.

v1 splits the page at its `##` headings. Each of those parts gets its own
transcript and its own recording, and the recordings are joined into one file, so
the player still loads a single file. Where each part begins is written down, so
the player can name the part being played and jump between parts.

A page is v1 when `narration/state/<url>.json` exists and says `"version": "v1"`.
A page with no state file is v0. Nothing else decides it. A run that stopped after
the words writes `"version": "v1-draft"` instead, and the player treats that page
as v0 until the audio is made.

In those paths, `<url>` is the page's address on the site with the reading-order
numbers stripped, such as `seeing-the-glasses/the-cell/the-cell`. The transcript,
the state file and the audio all use that one name.

A v0 page does not become a v1 page on its own. The flag `--v1` asks for the
conversion, and without it the generator leaves such a page exactly as it is.

### The word "section" is narrower in narration

This file tells you above that a section is one Markdown document inside a
chapter. That stays true everywhere on the site and in `docs/`. Narration uses
the word for something smaller.

In narration, a page is one Markdown document, and a section is one `##` heading
block inside it: the heading line and the words under it, up to the next `##`. So
a chapter holds several documents, and one of those documents holds several
narration sections. Read "section" in the narrower sense in anything under
`narration/`, and in the narrower sense only there.

The words before the first `##` are narrated as well, under the name `lead`. The
page's own `## Contents` list is never narrated, because a table of contents means
nothing aloud.

### Changing a page that has been narrated

When you change a page that has a recording, the recording no longer matches the
page, and the state file for that page is out of date. The sections you touched
have to be made again. This is the most important rule here, because nothing on the
site tells a listener that the words they are hearing are the old ones.

You do not have to work out which sections those are. `narration/state/<url>.json`
holds a `sha256` hash of each section's Markdown as it stood when that section was
last made. The generator hashes the page's sections again and compares. A section
whose hash still matches keeps its words and its audio and is sent to no model. A
section whose hash differs gets a new transcript and new speech, and the page is
joined again, because a changed section moves the start of every section after it.
So your job is to run the generator on the page you edited and to commit the state
file it writes.

Do not edit that JSON by hand. A hash in it is a statement that one recording was
made from one set of words, and the generator believes the statement without
listening. Change a hash by hand and the file claims a section was spoken from
words nobody read aloud; the generator then skips that section for good, and the
page keeps a recording that says the old thing. Fix the page, run the generator,
and let it write the file.

A v0 page is the one case where running the generator again is not enough. It has
no hashes, so the generator keeps the transcript and the recording it already has,
and your edit reaches nobody listening. Convert the page with `--v1` instead. That
writes and speaks every section, which costs a full set of model calls, and the
page is sectioned from then on.

### Publishing a recording

A narrated page has two files in the bucket the site is served from:

- `audio/<url>.mp3`, the joined recording, with content type `audio/mpeg`.
- `audio/<url>.json`, a copy of the state file, with content type
  `application/json`.

Uploading those two files is all it takes for a page to gain a player. The site is
a static export, and the player asks the browser for both addresses while the page
is open, so no recording is part of the build. There is no rebuild and no deploy,
and nothing about narration may ever become a build-time dependency.

`--upload` does the upload in two syncs rather than one, because a sync sets one
content type for everything it carries. A browser handed the state file as
`audio/mpeg` will not parse it as JSON, and the page then looks to the player like
a page with no sections at all. The per-section MP3s stay on the machine that made
them, since the player never asks for them.

Both files go up with a cache life of a year, so after replacing a recording you
have to flush the edge cache for that page or readers keep the old one.

A page with no recording shows no player at all, because the player hides itself
when the browser answers that request with a 404. A page that has an MP3 but no v1
JSON gets the plain player it had before.

### The commands

Run these from the repository root. The key comes from `.env` there. The script
refuses to run without `--book` or `--doc`, which is why a new book stays silent
until somebody asks for it by number.

```bash
# one page
python narration/narrate.py --doc docs/08_seeing-the-glasses/01_the-cell.md

# one chapter
python narration/narrate.py --book 08 --chapter 02

# after editing a page: the same command, which remakes only the changed sections
python narration/narrate.py --doc docs/08_seeing-the-glasses/01_the-cell.md

# convert a page that is still v0 into the sectioned shape
python narration/narrate.py --doc docs/08_seeing-the-glasses/01_the-cell.md --v1

# make the recordings and put them in the bucket
python narration/narrate.py --book 08 --upload
```

Two more flags matter when something has gone wrong. `--stage transcript` stops
after the words, so that they can be read before anything is spoken. `--force`
redoes the work of the stage you asked for, which means it speaks an unchanged
transcript again rather than trusting the hashes.

## Bringing in work written elsewhere

Documents written for another project keep their words. What changes is the shape:
the reading-order numbers, the folder layout, one folder of pictures per document,
and the list of sections at the top.

Every link has to be resolved against the file's old home and written again from
its new one, including the links in the code that came with it. A link whose target
did not come across keeps its words and loses its link, rather than pointing at
nothing.

## Checking links after any rename

Run this from the repo root. It must print `ALL internal links and images OK`.

```bash
python3 - <<'PY'
import pathlib, re, urllib.parse
def slug(h):
    h=re.sub(r'`','',h); h=re.sub(r'\[([^\]]*)\]\([^)]*\)',r'\1',h); h=re.sub(r'\*\*?','',h)
    # Keep letters of any alphabet, because the site's own slug generator does: a
    # heading with a Greek letter in a model's name becomes an id containing that
    # letter. Stripping it here made the checker reject links that work.
    return re.sub(r'[^\w\s-]','',h.lower().strip(),flags=re.UNICODE).replace(' ','-')
docs=sorted(pathlib.Path('docs').rglob('*.md'))+[pathlib.Path('README.md')]
anchors={p:{slug(m) for m in re.findall(r'^#{1,6}\s+(.*)$',p.read_text(),re.M)} for p in docs}
# Code is not prose: a Python line such as d["k"](x) looks exactly like a
# markdown link, so fenced blocks are removed before anything is checked.
body={p:re.sub(r'^```.*?^```','',p.read_text(),flags=re.S|re.M) for p in docs}
bad=[]
for p in docs:
    for _l,tg in re.findall(r'\[([^\]]*)\]\(([^)\s]+)\)',body[p]):
        if tg.startswith(('http','mailto:')): continue
        pp,_,fr=tg.partition('#'); fr=urllib.parse.unquote(fr)
        t2=pathlib.Path((p.parent/pp).resolve()) if pp else p
        if pp and not t2.exists(): bad.append(f'{p}: missing file -> {tg}'); continue
        if fr and t2.suffix=='.md':
            a=anchors.get(t2) or {slug(m) for m in re.findall(r'^#{1,6}\s+(.*)$',t2.read_text(),re.M)}
            if fr not in a: bad.append(f'{p}: missing anchor -> {tg}')
    for im in re.findall(r'!\[[^\]]*\]\(([^)\s]+)\)',body[p]):
        if im.startswith('http'): continue
        if not (p.parent/im).exists(): bad.append(f'{p}: missing image -> {im}')
print('\n'.join(bad) if bad else 'ALL internal links and images OK')
PY
```

## Writing style

Plain English, in complete sentences.

- One idea per sentence. Subject, verb, object. Active voice.
- Short sentences are good. Fragments and bolded labels standing in for reasoning
  are not. `**Reason:** terse claim` is the thing to avoid.
- No figurative language. Describe the thing instead.
- Explain a term where it first appears, in ordinary words.
- Say things in the order they happen.
- Every document opens with a real introduction: what it answers, who it is for.
- A table needs a sentence before it saying how to read it.

When explaining a tool or a framework, answer four questions: what it is, what it
does for you, **why this one rather than the obvious alternative**, and what it
costs you. Naming the rejected alternative is the part that carries the value.

## Other standing rules

- Use the full form of an abbreviation the first time it appears.
- Put a table of contents at the top of any document with sections.
- Give each concept its own diagram. Diagram scripts live in `docs/diagrams/`, one
  per area, and write to `docs/images/<area>/<doc-name>/`.
- A diagram must illustrate one specific idea from its own document. A reusable
  box-and-arrow chart is not acceptable.
- **One picture shows one thing.** Do not put two or three separate ideas side by
  side in one image. Two panels belong together only when they are the same thing
  seen differently: the same scene from two camera positions, or the same picture
  with two different measurements marked on it. Anything else is two pictures.
- **Never put two flow charts in one image.** A flow chart is a whole argument on
  its own, and a second one beside it halves the size of both.
- **Keep the text in a picture short.** A picture crowded with sentences is harder
  to read than the paragraph it was meant to replace. Put the explanation in the
  prose under the picture and leave the picture to carry the shape of the idea.
  If a label needs more than a line or two, the picture is doing the prose's job.
- Check a diagram by rendering it to PNG and looking at it. Overlapping labels and
  lines passing through obstacles are the usual faults, and the SVG write succeeds
  either way.
- Verify every number against real output before writing it down.
- Verify every external link resolves before committing.
- Commit and push to `main` after every change.
