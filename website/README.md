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

The folders in `docs/` are the structure. There is no separate list to keep in
sync: add, move or renumber a doc and the site follows on the next refresh.

```
docs/01_robotics-intro/        book       -> /robotics-intro
  03_arm/                      chapter    -> /robotics-intro/arm
    01_overview.md             section    -> /robotics-intro/arm/overview
docs/03_frameworks/
  01_tools-and-libraries.md    a chapter with one section
  04_one-arm-training/
    07_case-study/             a labelled group of sections in the chapter
```

- Books, chapters and sections are ordered by their number prefix. The number
  is dropped from the URL, so renumbering does not change links.
- `docs/images/` and `docs/diagrams/` are not books.
- `lib/books.config.ts` holds only display text: each book's title, subtitle,
  description and colour, and friendlier chapter names. A book or chapter that
  is not listed there still appears, with a title taken from its folder name or
  its first doc.

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
