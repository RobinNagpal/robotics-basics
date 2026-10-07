# DoDAO Highlighter

This folder holds a Chrome extension for highlighting and commenting on
[docs.dodao.io](https://docs.dodao.io). It also holds the small server that
stores the highlights in a Postgres database. This page is for whoever sets up
the extension and runs the server.

## Contents

- [How it works](#how-it-works)
- [Why these tools](#why-these-tools)
- [Setting up Google sign-in](#setting-up-google-sign-in)
- [Running it](#running-it)
- [Files](#files)

## How it works

When you select text on a docs page, a small bar of four colours appears under it.
Clicking a colour highlights the text. The speech-bubble button highlights the
text and opens a comment box. Clicking a highlight later opens the same box. In
it you can change the colour, edit the comment or delete the highlight.

The browser holds the real copy of every highlight, in `chrome.storage.local`, so
the extension works with no server at all. Each highlight records its book,
chapter and page. These come from the page address, which has the shape
`/<book>/<chapter>/<page>/`.

The background script keeps the database in step with the browser. It runs a
sync shortly after every change, once a minute, and when you press **Sync**. A
sync is one request. It sends the highlights that changed in the browser, and the
server answers with every highlight it holds. The browser then applies three
rules to each highlight:

1. If a highlight changed in the browser while the request was out, the browser
   keeps its own version. The next sync sends it.
2. Otherwise the server's version replaces the browser's.
3. If the server does not return a highlight, the browser removes it.

Deleting a highlight in the browser marks it deleted and hides it. The next sync
deletes it on the server, and then rule 3 removes the marked copy. Deleting a row
in the database removes the highlight from the browser by the same rule. When two
edits to one highlight meet, the later one wins.

The popup opens from the toolbar icon. It shows who is signed in, whether the last
sync worked, and the highlights. The two lists at the top choose a book and a
chapter.

Only the addresses in `lib/allowed.ts` can sign in. The popup checks the list at
sign-in. The server checks it again on every request, by asking Google who owns
the access token it was sent.

## Why these tools

[WXT](https://wxt.dev) builds the extension. It turns the files in `entrypoints/`
into a Manifest V3 extension, compiles the TypeScript, and reloads the extension
while you edit. The obvious alternative is Plasmo. WXT was chosen because it is
more actively maintained and does not require React, so the pages here are plain
TypeScript. It costs a build step and one more dependency to keep up to date.

[Hono](https://hono.dev) runs the server. It routes requests, parses the request
body and answers in JSON in a few lines. The obvious alternative is Express. Hono
was chosen because it is written in TypeScript and has types for requests and
middleware built in. It is younger than Express and has fewer third-party
plugins, but this server needs none.

The server talks to the database through the `postgres` package, where a query is
written as a tagged template string. An ORM (object-relational mapper) such as
Prisma would add a schema file and a code generation step for a single table.

## Setting up Google sign-in

Chrome signs the user in through `chrome.identity`. That needs a Google OAuth
client tied to the extension's ID. The ID must not change, so the extension is
given a fixed key.

1. Make a key. Then read off the manifest key and the extension ID it produces:

   ```bash
   openssl genrsa 2048 | openssl pkcs8 -topk8 -nocrypt -out key.pem
   # WXT_MANIFEST_KEY:
   openssl rsa -in key.pem -pubout -outform DER | openssl base64 -A
   # extension ID:
   openssl rsa -in key.pem -pubout -outform DER | sha256sum | head -c32 | tr 0-9a-f a-p
   ```

2. In the [Google Cloud console](https://console.cloud.google.com/apis/credentials),
   create an OAuth client ID of type **Chrome Extension**, and paste in the
   extension ID. Put the client ID it gives you in `WXT_GOOGLE_CLIENT_ID`.
3. On the OAuth consent screen, add `robinnagpal.tiet@gmail.com` as a test user
   while the app is in testing.

Keep `key.pem` out of the repository.

## Running it

Copy `.env.example` to `.env` and fill it in. The extension reads the `WXT_`
values when it is built. The server reads `DATABASE_URL` and `PORT` when it
starts.

```bash
npm install
npm run server   # starts the server; it creates the table if it is missing
npm run build    # writes the extension to .output/chrome-mv3
```

To load the extension, open `chrome://extensions`, turn on developer mode, choose
**Load unpacked** and pick `.output/chrome-mv3`. During development,
`npm run dev` opens a Chrome with the extension loaded and rebuilds it on every
save. If the server runs anywhere other than your own machine, `WXT_API_URL` must
be its HTTPS address.

To let another person in, add their address to `lib/allowed.ts`, rebuild the
extension and restart the server.

## Files

- `entrypoints/content.ts` draws the highlights on the page and shows the colour
  bar and the comment box.
- `entrypoints/background.ts` runs the sync.
- `entrypoints/popup/` is the popup.
- `lib/store.ts` reads and writes the browser copy.
- `lib/auth.ts` signs in and out with Google.
- `lib/allowed.ts` is the list of people who may sign in.
- `server/index.ts` is the server.
