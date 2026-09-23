# Project rules

## IMPORTANT: naming inside `docs/`

**Every document and every folder inside `docs/` must start with a two-digit number
prefix that gives its reading order.**

The shape is `NN_lower-hyphen-separated-name`. The prefix uses an **underscore**
after the number. The name itself uses **hyphens** between words, all lower case.

```
docs/06_object-segmentation/01_overview.md
docs/06_object-segmentation/02_programmed-methods.md
docs/05_camera/03_one-box-intro.md
docs/11_stone-stacking.md
```

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
  `docs/09_one-arm-training/01_overview.md`. This keeps image paths stable when a
  document is renumbered.

## Checking links after any rename

Run this from the repo root. It must print `ALL internal links and images OK`.

```bash
python3 - <<'PY'
import pathlib, re, urllib.parse
def slug(h):
    h=re.sub(r'`','',h); h=re.sub(r'\[([^\]]*)\]\([^)]*\)',r'\1',h); h=re.sub(r'\*\*?','',h)
    return re.sub(r'[^a-z0-9\s_-]','',h.lower().strip()).replace(' ','-')
docs=sorted(pathlib.Path('docs').rglob('*.md'))+[pathlib.Path('README.md')]
anchors={p:{slug(m) for m in re.findall(r'^#{1,6}\s+(.*)$',p.read_text(),re.M)} for p in docs}
bad=[]
for p in docs:
    for _l,tg in re.findall(r'\[([^\]]*)\]\(([^)\s]+)\)',p.read_text()):
        if tg.startswith(('http','mailto:','#')): continue
        pp,_,fr=tg.partition('#'); fr=urllib.parse.unquote(fr)
        t2=pathlib.Path((p.parent/pp).resolve()) if pp else p
        if pp and not t2.exists(): bad.append(f'{p}: missing file -> {tg}'); continue
        if fr and t2.suffix=='.md':
            a=anchors.get(t2) or {slug(m) for m in re.findall(r'^#{1,6}\s+(.*)$',t2.read_text(),re.M)}
            if fr not in a: bad.append(f'{p}: missing anchor -> {tg}')
    for im in re.findall(r'!\[[^\]]*\]\(([^)\s]+)\)',p.read_text()):
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
- Check a diagram by rendering it to PNG and looking at it. Overlapping labels and
  lines passing through obstacles are the usual faults, and the SVG write succeeds
  either way.
- Verify every number against real output before writing it down.
- Verify every external link resolves before committing.
- Commit and push to `main` after every change.
