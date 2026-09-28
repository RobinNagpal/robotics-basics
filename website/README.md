# website

A Next.js site that presents the docs in `../docs` as three mini books for
learning robotics.

```
npm install
npm run dev      # http://localhost:3000
npm run build    # static pages for every section
```

The site reads the Markdown and images directly from `../docs`. It does not
keep its own copy, so edits to the docs show up on the next refresh in
development, or on the next build. To read docs from somewhere else, set
`ROBOTICS_DOCS_DIR=/path/to/docs`.

## How the books are built

`lib/books.config.ts` is the only place the grouping lives.

| Book | Chapters (from `docs/`) |
| --- | --- |
| 1. Robotics Intro | ros, rviz, arm, numpy |
| 2. Perception | camera, object-perception |
| 3. Frameworks & Manipulation | tools-and-libraries, gripping, arm-movement, one-arm-training, two-arm-training, two-arm-manipulation, stone-stacking, frontier |

- A top-level folder in `docs/` is a **chapter**. Each `.md` file in it is a
  **section**, in the order its number prefix gives. Files in a sub-folder
  (such as `07_case-study/`) appear as a labelled group inside the chapter.
- A top-level `.md` file is a chapter with one section.
- Anything in `docs/` that is not listed in the config goes into the last book,
  so a new doc is never silently left out.

The doc content is not changed. When a doc is rendered, the site:

- moves its first heading into the page header
- rewrites links between docs to site URLs, keeping the `#anchor`
- serves images from `docs/` through `/docs-assets/...`
- shows links to code elsewhere in the repo as labelled text rather than
  broken links

## Features

- Home page with the three books, and a page per book listing its chapters
  and sections.
- Reader with a book sidebar, a table of contents that follows your scroll,
  previous and next links that carry on across books, and reading time.
- Search across every section (`⌘K` or `/`).
- Reading progress is saved in your browser: sections you opened are ticked,
  and "Continue" takes you back.
- Light and dark themes, copy buttons on code, click-to-zoom diagrams, and
  layouts that work on phones.
