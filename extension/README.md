# DoDAO Highlighter

This folder holds a Chrome extension for leaving feedback on
[docs.dodao.io](https://docs.dodao.io). A reader selects a sentence on a docs page,
highlights it and writes a comment about it. The comments are stored in Amazon S3,
one file per docs page, so that Claude can read them later and change the docs to
answer them. The folder also holds the small API that stores the comments, and the
Terraform that creates the AWS resources the API runs on. This page is for whoever
uses the extension, deploys the API, or asks Claude to work through the feedback.

## Contents

- [How it works](#how-it-works)
- [Signing in with an API key](#signing-in-with-an-api-key)
- [Where the comments are kept](#where-the-comments-are-kept)
- [Working on the feedback with Claude](#working-on-the-feedback-with-claude)
- [Why these tools](#why-these-tools)
- [Running it](#running-it)
- [The install page](#the-install-page)
- [Deploying the API](#deploying-the-api)
- [Files](#files)

## How it works

When you select text on a docs page, a small bar of four colours appears under it.
Clicking a colour highlights the text. The speech-bubble button highlights the
text and opens a comment box. Clicking a highlight later opens the same box. In it
you can change the colour, edit the comment or delete the highlight.

Each highlight records where it is. The book, the chapter and the page come from
the page address, which has the shape `/<book>/<chapter>/<page>/`. The section is
the nearest heading above the selected text. The highlight also keeps the selected
text and a few characters on each side of it, so the extension can find the same
text again when the page is opened later.

The browser holds its own copy of every highlight, in `chrome.storage.local`. So
the extension keeps working when the API cannot be reached, and the changes are
sent when it can. The background script does the sending. It runs a sync shortly
after every change, once a minute, and when you press **Sync** in the popup. A sync
is one request. It sends the highlights that changed in the browser, and the API
answers with every highlight it holds. The browser then applies three rules to
each highlight:

1. If a highlight changed in the browser while the request was out, the browser
   keeps its own version. The next sync sends it.
2. Otherwise the API's version replaces the browser's.
3. If the API does not return a highlight, the browser removes it.

Deleting a highlight in the browser marks it deleted and hides it. The next sync
deletes it on the API, and then rule 3 removes the marked copy. When two edits to
one highlight meet, the later one wins.

The popup opens from the toolbar icon. It shows who is signed in, whether the last
sync worked, and the highlights. The two lists at the top choose a book and a
chapter.

## Signing in with an API key

The popup asks for two things before it does anything else: the server URL and an
API key. The server URL says where the API is. It is the function URL of the
Lambda function that runs the API, which looks like
`https://<id>.lambda-url.us-east-1.on.aws`. Because the URL is typed in rather
than written into the extension when it is built, one build of the extension can be
pointed at any copy of the API.

The extension needs to prove to the API that its user is allowed to write
comments. It does this with an API key. An API key is a long random string that the
API knows in advance, in the same way a password is.

The API holds its keys in one encrypted value in AWS Systems Manager Parameter
Store, which is the AWS service for keeping small settings and secrets. The value
is a JSON object that maps a name to a key, such as `{"robin": "<key>"}`. The name
is who the key belongs to, and the API writes it on every comment made with that
key. At the moment there is one key, a random UUID. A copy of it is in the `.env` file
at the root of the repository as `FEEDBACK_API_KEY`, next to the server URL as
`FEEDBACK_API_URL`.

You type both into the popup once. The popup sends the key to the server URL and
asks whose key it is. If the server knows the key, the popup stores the URL and the
key and shows the name, and from then on every request goes to that URL and carries
that key. If the server cannot be reached, or does not know the key, the popup says
so and stores nothing. Signing out forgets the key but keeps the URL, so signing in
again only needs the key.

A Chrome extension may call only the addresses its manifest lists, and the
manifest is fixed when the extension is built. So the manifest lists every Lambda
function URL, and `localhost` for the API run on your own machine, and the popup
refuses any other server URL. That is a wider permission than one exact address,
but it only lets the extension send requests to those addresses, and it is the
price of choosing the server in the popup. The API reads the keys again every five minutes, so a key that is
added or removed takes effect without a deploy. A removed key makes the next sync
fail, and the popup shows that error until you sign out and enter a new key.

To change the keys, write the whole object again:

```bash
aws ssm put-parameter --name /robotics-basics/feedback-api-keys \
  --type SecureString --overwrite --value '{"robin": "<key>"}'
```

## Where the comments are kept

The comments are kept in a private S3 bucket, `robotics-basics-feedback-<account-id>`.
Each docs page that has comments has one JSON file, at
`feedback/<book>/<chapter>/<page>.json`. The file is a list of that page's
comments in the order they were made. A file disappears when its last comment is
deleted, so the files that exist are exactly the pages with feedback on them.

Two people can sync changes to the same page at the same moment. Each one reads the
page file, changes it and writes it back. If both wrote without checking, the
second write would erase the first one's change. So the API writes a page file only
if it is unchanged since it was read. S3 checks this with the file's version tag,
and refuses the write when the file has changed. The API then reads the file again
and repeats the change on the new copy. This is the same idea as a compare-and-swap
loop in concurrent programming.

The bucket keeps every earlier version of every file. So a wrong edit or a deleted
comment can be brought back from the version history.

## Working on the feedback with Claude

The reason for keeping the comments as files is that Claude can read them directly.
One file is one page's feedback, and each comment says which section it is about,
quotes the exact text it is about, and gives the page address. To work through the
feedback, copy the files to your machine and ask Claude to go through them:

```bash
aws s3 sync s3://robotics-basics-feedback-<account-id>/feedback/ feedback/
```

The page address leaves out the reading-order numbers, so Claude finds the source
file by matching each part of the address to a folder or file in `docs/` with the
number removed. When a comment has been dealt with, delete its highlight in the
popup, and the next sync removes it from the bucket.

## Why these tools

[WXT](https://wxt.dev) builds the extension. It turns the files in `entrypoints/`
into a Manifest V3 extension, compiles the TypeScript, and reloads the extension
while you edit. The obvious alternative is Plasmo. WXT was chosen because it is
more actively maintained and does not require React, so the pages here are plain
TypeScript. It costs a build step and one more dependency to keep up to date.

[Hono](https://hono.dev) runs the API. It routes requests and answers in JSON in a
few lines, and the same app runs on AWS Lambda and on your own machine. The obvious
alternative is Express. Hono was chosen because it has a Lambda adapter built in
and is written in TypeScript. It is younger than Express and has fewer third-party
plugins, but this API needs none.

The API runs on AWS Lambda, which runs a function when a request arrives and
charges only for the time it runs. The obvious alternative is a small server that
runs all the time. A few readers leaving comments make a few requests a minute at
most, so a server would sit idle almost all the time and still cost money every
hour. Lambda costs nothing at this level of use. What it costs is a short delay on
the first request after a quiet period, while AWS starts the function.

The function is reached through a function URL, which is an HTTPS address that
Lambda gives a function directly. The obvious alternative is Amazon API Gateway in
front of the function. API Gateway adds request limits, custom domains and its own
authorizers, and the API needs none of these, because it checks the key itself.

The comments are stored in S3 rather than a database. A database such as Postgres
would answer queries, but nobody queries the comments. They are read one page at a
time, by a person or by Claude, and a file per page is the easiest form for that.
S3 also needs no server, and keeps old versions without any extra work. What it
costs is that S3 cannot change part of a file, so every change rewrites the whole
page file and needs the conditional write described above.

## Running it

The extension needs no settings to build, because the server URL and the key are
typed into its popup.

```bash
npm install
npm run build    # writes the extension to .output/chrome-mv3
```

To load the extension, open `chrome://extensions`, turn on developer mode, choose
**Load unpacked** and pick `.output/chrome-mv3`. Then open the popup and enter the
server URL and the API key. `terraform output -raw feedback_api_url` in `terraform/`
prints the server URL. During development, `npm run dev` opens a Chrome with the extension loaded
and rebuilds it on every save.

`npm run server` runs the same API on your own machine, on port 8787. Copy
`.env.example` to `.env` in this folder and fill it in first. The local API uses
your own AWS credentials, and the bucket and parameter named in `.env`, so it reads
and writes the real comments. To use it, sign out in the popup and sign in with
`http://localhost:8787` as the server URL.

## The install page

People who only want to use the extension get it from the install page,
https://d18wv231p6lnln.cloudfront.net/. The page has one download button and the
steps to load the extension into Chrome. It also shows the server URL, with a
button that copies it, because the popup asks for it.

The page cannot install the extension in one click. Chrome allows a one-click
install only from the Chrome Web Store, and it refuses to install an extension
file downloaded from any other website. So the page offers the zip, and the reader
loads it with **Load unpacked** in developer mode. Publishing the extension in the
Chrome Web Store, as an unlisted item that only people with the link can find,
would give a real one-click install. That costs a one-time developer fee and a
review of every new version, which takes from a day to a few days.

The page and the zip are kept in a private bucket, and CloudFront serves them over
HTTPS, in the same way as the docs site. The zip always has the same name,
`dodao-highlighter.zip`, so a new version replaces the old one and the download
link never changes. The bucket keeps no old versions, because every version can be
built again from the repository.

`npm run build:install` puts both files in `.install/`. It zips the extension, and
then writes the page from `install/index.html` with the version, the date and the
server URL filled in. The server URL comes from `FEEDBACK_API_URL`.

The workflow `.github/workflows/deploy-extension.yml` publishes them on every push
to `main` that changes the extension or the page. It uploads the zip first and the
page second, so the page never offers a file that is not there yet. Then it flushes
the CloudFront cache, downloads the zip from the live page, and checks that it is
the file it has just built.

## Deploying the API

The API has two parts that change at different speeds. The AWS resources are
created once by Terraform, and the code is uploaded by GitHub Actions on every
change.

The Terraform in `terraform/` creates the bucket, the key parameter, the Lambda
function, its function URL, and the role the function runs as. It also creates the
install page's bucket and CloudFront distribution. Terraform records
what it has created in a state file. This stack keeps that file in a state bucket
of its own, `feedback-api-tfstate-<account-id>`, rather than in the docs site's.
That is the same rule the courtpot and interestled projects follow: each
application has its own private, versioned and encrypted state bucket, made once
by a script. The feedback API is a separate application, so it gets its own bucket,
and the docs site's Terraform can never change it by accident.

Run it with administrator credentials. The script is safe to run again, so running
it on an account that already has the bucket does nothing:

```bash
bash scripts/bootstrap-state-bucket.sh
cd terraform
terraform init -backend-config="bucket=feedback-api-tfstate-<account-id>"
terraform apply
```

Terraform creates the key parameter empty, and creates the function with a
placeholder that answers every request with 503. It never reads the key back or
changes the code afterwards. So the keys stay out of the Terraform state, and a
later `terraform apply` does not undo a code deploy.

The workflow `.github/workflows/deploy-feedback-api.yml` uploads the code. It is
the one file for this extension outside this folder, because GitHub reads
workflows only from that folder. It runs on every push to `main` that changes
`server/`, `lib/types.ts` or the package files, and it can also be run by hand from
the Actions tab. It type-checks the code, bundles the API into one file with
esbuild, uploads it to the function, and then checks that a request without a key
is refused with 401. A placeholder or a broken bundle answers differently, so the
check fails if the new code is not running.

The workflow uses the same AWS credentials as the docs deploy. Those belong to the
docs site's deployer user, and `terraform/deployer.tf` adds a policy to that user
which lets it replace this function's code, write the install page's bucket and
flush its cache, and nothing else.

## Files

- `entrypoints/content.ts` draws the highlights on the page and shows the colour
  bar and the comment box.
- `entrypoints/background.ts` runs the sync.
- `entrypoints/popup/` is the popup, including the form for the server URL and
  the API key.
- `lib/store.ts` reads and writes the browser copy, and holds the server URL and
  the API key.
- `lib/auth.ts` checks the server URL and the key with the API, and signs out.
- `server/app.ts` is the API: the key check, `GET /me` and `POST /sync`.
- `server/keys.ts` reads the keys from Parameter Store.
- `server/store.ts` reads and writes the page files in S3.
- `server/lambda.ts` and `server/local.ts` run the API on Lambda and on your own
  machine.
- `install/index.html` is the install page, before its values are filled in.
- `scripts/build-install.mjs` builds the install page and the zip.
- `terraform/` creates the AWS resources.
- `scripts/bootstrap-state-bucket.sh` creates the bucket that holds the
  Terraform state.
