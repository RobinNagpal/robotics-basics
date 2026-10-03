# Narration

This folder turns the pages in `docs/` into spoken recordings, so that the same
material can be followed by somebody who is not looking at a screen. It answers
three questions for a developer who has just opened the folder: what the files
here are, which of them are committed, and which command to run. The rules that
bind an editor of `docs/` are in `CLAUDE.md` at the repository root, under the
narration heading. This page describes the folder itself.

## Contents

- [Page and section](#page-and-section)
- [The two stages](#the-two-stages)
- [What is committed and what is not](#what-is-committed-and-what-is-not)
- [What each file holds](#what-each-file-holds)
- [Narrating a page](#narrating-a-page)
- [Making a page again after an edit](#making-a-page-again-after-an-edit)
- [The state file](#the-state-file)

## Page and section

Two words are used here in a narrower way than in the rest of the repository, so
they are worth settling first.

A **page** is one Markdown file under `docs/`, which the site serves at one
address. The repository calls that a section of a chapter.

A **section**, in this folder only, is one `##` heading block inside a page: the
heading line and the words under it, up to the next `##`. One page therefore
holds several sections. The text before the first `##` is a section too, and it
is called the lead. The page's own `## Contents` list is never narrated, because
a table of contents means nothing aloud.

## The two stages

First a text model reads one page and writes a **transcript**, which is the words
to be spoken. A transcript is not the page read out. A page holds diagrams, code,
tables and links, and none of those carry over into speech, so the model is asked
to say what a diagram shows and to explain what code does rather than recite it.
The instruction it is given sits beside `narrate.py`, so the wording can be
changed without touching the code. There are two of those instruction files.
`prompt-section.md` is used for one section at a time, and `prompt.md` is the
older one, used for a page written as a single piece.

Then a speech model reads that transcript aloud, one section at a time. Each
section becomes its own MP3, and the MP3s are joined in order into one file,
which is what a reader plays.

The stages are separate because of what each one costs to put right. When a
recording says something wrong, the mistake is in the transcript, and correcting
the transcript costs one speech call rather than a text call and a speech call.
The `--stage transcript` flag stops after the words, so that somebody can read
them against the page before anything is spoken.

## What is committed and what is not

Transcripts and state files are committed. Audio is not, and `narration/audio/`
is listed in `.gitignore` at the repository root.

Transcripts are committed because they are the part worth checking. A wrong
recording is always a wrong transcript, and a transcript is something a person can
read, mark up and correct, which an MP3 is not. State files are committed because
they record which words were spoken and when, and the generator reads that record
to work out what it has to make again.

Audio is left out because it is large, several megabytes for one page, and
because it can be made again from the transcript whenever it is needed. The
recordings live in the S3 bucket the site is served from instead.

## What each file holds

In the table below, `<url>` is the page's address on the site with the
reading-order number prefixes stripped, for example
`robotics-by-example/the-cell/the-cell`. The same name is used for a page's
transcript, its state file and its audio, which is how the three are matched to
each other and to the page.

| Path | Committed | What it holds |
| --- | --- | --- |
| `narrate.py` | yes | the generator, which runs both stages |
| `prompt-section.md` | yes | the instruction given to the text model for one section |
| `prompt.md` | yes | the same, for a page written as a single piece |
| `transcripts/<url>.md` | yes | one page's words, with a marker line before each section |
| `state/<url>.json` | yes | what was made for that page, and from which words |
| `audio/<url>/NN-<id>.mp3` | no | one section's audio |
| `audio/<url>.mp3` | no | those sections joined, which is the file the player plays |
| `manifest.json` | yes | one line per page recording that exists, with its size |

The site does not read `manifest.json`. It exists so that somebody can see what
has been made without listing a bucket.

A transcript holds all of a page's sections in one file, with one marker line
before each section's words:

```
<!-- section: the-main-idea | The main idea -->
```

The id is the heading's anchor, the same one the site links to, and the generator
finds a section's existing words by it. So when you correct a transcript by hand,
change the words and leave the marker alone.

## Narrating a page

Run these from the repository root. The API key comes from `.env` there.

```bash
# one page
python narration/narrate.py --doc docs/08_robotics-by-example/01_the-cell.md

# one chapter
python narration/narrate.py --book 08 --chapter 02

# a whole book
python narration/narrate.py --book 08

# stop after the words, so that they can be read before anything is spoken
python narration/narrate.py --book 08 --stage transcript

# convert a page recorded as one piece into the section by section shape
python narration/narrate.py --doc docs/08_robotics-by-example/01_the-cell.md --v1

# make the recordings, then put them in the bucket
python narration/narrate.py --book 08 --upload
```

The script will not run without `--book` or `--doc`. There is no command that
narrates everything, so a new book stays silent until somebody asks for it by
number.

## Making a page again after an edit

Run exactly the same command you would use to narrate the page for the first
time. The generator compares each section of the page against the state file and
does the work only for the sections whose Markdown has changed, so an edit to one
heading costs one speech call rather than a whole page of them. A section that
has moved up or down the page keeps its audio and is renamed. A section that has
gone from the page takes its audio with it.

One kind of page is the exception. A page that still has no state file was
recorded as a single piece, and the generator keeps the transcript and the
recording it already has, so editing that page and running the command again
achieves nothing. Pass `--v1` to convert the page instead. The conversion writes
and speaks every section, which costs a full set of model calls, and that is why
it has to be asked for rather than being done by default.

If you want work done again anyway, `--force` redoes the stage you asked for. With
`--stage audio`, which is the default, it speaks the existing transcript again and
leaves the transcript alone. With `--stage transcript` it asks the text model for
the words again. The split is deliberate, because a transcript is often corrected
by hand after somebody has read it against the page, and asking for the speech
again must not throw those corrections away.

Correcting a transcript by hand therefore needs one extra step, because the
section's Markdown has not changed and the generator sees no reason to speak it
again. Delete that section's MP3 under `audio/<url>/` and run the command again,
which speaks the corrected section and leaves the rest of the page alone.

Whichever command you run, `--upload` sends two files per page to the bucket,
under `audio/`: the joined MP3 and a copy of the state file. It sends them in two
syncs, because one sync sets one content type, and a browser handed the state file
as `audio/mpeg` will not read it as JSON. Uploading those two files is the whole of
publishing a recording. The site is a static export and asks the browser for both
addresses while a page is open, so there is no rebuild and no deploy. Both files
are stored with a cache life of a year, so after replacing a recording you have to
flush the edge cache for that page.

## The state file

`state/<url>.json` is the record of what was made for one page. It serves two
readers. The generator reads it to decide which sections to make again. The
player reads a copy of it in the bucket to find out where each section starts, so
that it can name the section being played and let a reader jump between sections.

A page is treated as sectioned if and only if it has this file and the file says
`"version": "v1"`. A page with no state file gets the plain player it has always
had. A run that stopped at `--stage transcript` writes the file with
`"version": "v1-draft"` instead, because the words exist but their lengths do not
yet, and the player then plays the page as one piece rather than trusting lengths
that were never measured.

The fields are listed below. A name with `sections[]` in front of it is a field
of one entry in the `sections` list, and that list is in playing order.

| Field | What it says |
| --- | --- |
| `version` | `v1`, which is what tells the player the file is sectioned, or `v1-draft` while the audio is missing |
| `url` | the page's address, as above |
| `page` | the Markdown file this was made from, from the repository root |
| `title` | the page's own heading |
| `audio` | the joined MP3's path in the bucket, under `audio/` |
| `duration` | the whole recording's length in seconds |
| `generated` | when this run finished, in UTC as `YYYY-MM-DDTHH:MM:SSZ` |
| `voice`, `speech_model` | which voice and which speech model read it |
| `sections[].index` | the section's place in the page, counting from zero |
| `sections[].id` | the heading's anchor, or `lead` for the text before the first `##` |
| `sections[].title` | the heading as written, for the player to show |
| `sections[].anchor` | the heading to scroll the page to, and `null` for the lead |
| `sections[].start` | where the section begins in the joined MP3, in seconds |
| `sections[].duration` | how long the section lasts, in seconds |
| `sections[].words` | how many words its transcript holds |
| `sections[].source_sha` | `sha256` of the section's Markdown when it was last made |
| `sections[].text_updated` | when its transcript was last written |
| `sections[].audio_updated` | when it was last spoken |
| `sections[].file` | its own MP3, before the sections were joined |

`duration` is measured on the audio with `ffprobe` rather than estimated, and so
is the page's own `duration`. `start` is then the sum of the durations of the
sections before it, because nothing in the joined file marks where one section
ends and the next begins.

Those two ways of counting do not agree exactly. Joining MP3s adds a little of
the encoder's padding at each join, so a start runs a fraction of a second
behind where its words really begin, and the gap grows with the number of
sections. On the longest page recorded so far the sections add up to 1628.13
seconds against a joined file of 1628.61, so the last section's mark is about
half a second early out of twenty-seven minutes. That is close enough for
jumping to a section and too close to hear, but it is an estimate rather than a
measurement, which is why it is written down here.

In a draft, `start` and `duration` are `null`, along with `file`, because nothing
has been measured yet.

Do not edit this file by hand. `source_sha` is a statement that a particular
recording was made from particular words, and the generator believes it. Changing
a hash by hand makes the file claim that a section was spoken from words nobody
read aloud, and the generator then skips that section for good. Change the page,
run the generator, and commit the state file it writes.
