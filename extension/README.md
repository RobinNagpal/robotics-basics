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

The comments are kept as files so that Claude can read them directly. One file is
one page's feedback, and each comment says which section it is about, quotes the
exact text it is about, and gives the page address. A program called the feedback
worker hands the comments to Claude Code and records what Claude did with each one.

### Status and response

Each comment carries two fields that say what has happened to it. The status is one
of four values:

- `open`: the comment is waiting for Claude.
- `changed`: Claude changed the docs to answer it.
- `answered`: Claude replied without changing the docs, for a question or for a
  comment it decided the docs already meet.
- `failed`: the run went wrong, and the response says how.

The response is what Claude says about the comment, written for the person who
left it, in 3 to 8 short lines. Claude sends the lines as a list, and the schema
allows only 3 to 7 of them, so a longer reply is refused rather than cut short
afterwards. The worker adds an eighth line naming the commit when the docs changed. The popup and the comment box on the page show the status and the
response under the comment.

Only the worker writes these two fields. The API sets a new comment to `open` and
ignores whatever the browser sends for them. If someone edits the text of a
comment, the API sets it back to `open` and clears the response, because the edited
comment is new feedback.

### What the worker does

The worker is a long-running TypeScript program in `worker/`. On a schedule it does
one run, and a run has these steps:

1. It reads every comment from the bucket, and keeps the ones that are `open` and
   have some text. A highlight with no comment asks nothing, so it is left alone.
2. It compacts the Claude Code session. Compacting replaces the conversation so far
   with a summary of it, so the session keeps what it learned about the docs
   without growing every run.
3. It works through the comments a page at a time, starting with the page whose
   oldest comment was written first. For each page, it puts the clone exactly on
   `main`, making the clone first if it is missing, and gives Claude all of that page's comments in one turn, so the page
   is changed in one go. Claude finds the source file, decides what each comment
   needs, makes the changes under the rules in `CLAUDE.md`, and commits them, but
   does not push.
4. When Claude has finished the page, the worker pushes. It commits anything
   Claude changed but left uncommitted, rebases the commits onto `main`, and
   pushes them.
5. Only then does it record a reply for each comment. Claude replies in a fixed
   shape, which Claude Code checks against a schema: one entry for each comment's
   ID, with a status and a response of 3 to 7 short lines. For a comment that
   changed the docs, the worker adds one more line naming the pushed commit,
   which Claude cannot know, because the rebase gives the commit a new hash. So
   every response is 3 to 8 lines, and a comment marked `changed` is one whose
   change is already on `main`. A comment Claude gave no reply to, or says it
   changed when nothing was committed, is marked `failed`.

Steps 2 to 5 happen only when there is open feedback, so a quiet run costs nothing.

Every run uses the same Claude Code session. The first run creates it with an ID
the worker chooses, and the worker keeps that ID in `worker/.state/session.json`.
Every later turn resumes the session by that ID. This works like one long
conversation that is summarised every run, rather than a new conversation for each
comment.

The worker writes an outcome only if the comment is still there, still `open`, and
still says what Claude was shown. A comment edited while Claude worked on it stays
`open`, and the next run picks up the new text.

Claude works in a clone of the repository that exists only for the worker, so it
never edits files that a person is editing. Nobody is there to answer a permission
prompt, so it runs with every permission. That is why it gets a clone of its own,
and why the comments are only ever written by someone holding an API key.

### Why these tools

[PM2](https://pm2.keymetrics.io) runs the worker. It is a process manager for
Node programs: it starts the worker, restarts it if it crashes, keeps its logs, and
can start it again when the machine restarts. The obvious alternative is a service
file written by hand for the system's own service manager, such as `launchd` on a
Mac. PM2 was chosen because the same commands work on a Mac and on a Linux server,
and because it shows the worker's state and logs with one command each. It costs
one more tool to install, and its configuration file has to be JavaScript, because
PM2 reads only JavaScript or JSON.

[Croner](https://croner.56k.guru) decides when a run starts, from a cron pattern
such as `*/2 * * * *` for every two minutes. The obvious alternative is a plain
timer in the program. Croner was chosen because of its `protect` option: when a run
is still going at the next start time, that start is skipped. One comment can keep
Claude busy for longer than two minutes, and without this two runs would work in
the same clone at once. It costs one small dependency.

### Setting it up

The worker needs its own AWS keys, which can only read and write the feedback
bucket. `terraform/worker.tf` makes an IAM user for it.

```bash
cd worker
npm install
cd ../api && npm install && cd ../worker   # the worker uses the API's S3 code
cp .env.example .env                       # then fill it in
npm run once      # one run now, to see that it works
npm run start     # start it under PM2
npm run logs      # watch it
```

The keys come from `terraform output -raw worker_access_key_id` and
`terraform output -raw worker_secret_access_key` in `terraform/`. `SCHEDULE` in
`.env` sets how often it runs. It is every two minutes while the worker is being
tested. To change it to every thirty minutes, set `SCHEDULE=*/30 * * * *` and run
`npm run restart`. To start the worker again after the machine restarts, run
`npx pm2 save` and then `npx pm2 startup`, and run the command it prints.

The clone needs whatever `CLAUDE.md` asks Claude to use. Copy the repository's
root `.env` into the clone if Claude should be able to make narration again for
the pages it changes.

## Why these tools

[WXT](https://wxt.dev) builds the extension. It turns the files in `ui/entrypoints/`
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

The extension is a package of its own in `ui/`. It needs no settings to build,
because the server URL and the key are typed into its popup.

```bash
cd ui
npm install
npm run build    # writes the extension to ui/.output/chrome-mv3
```

To load the extension, open `chrome://extensions`, turn on developer mode, choose
**Load unpacked** and pick `ui/.output/chrome-mv3`. Then open the popup and enter the
server URL and the API key. `terraform output -raw feedback_api_url` in `terraform/`
prints the server URL. During development, `npm run dev` opens a Chrome with the extension loaded
and rebuilds it on every save.

The API is a separate package in `api/`, with its own dependencies. `npm install`
and then `npm run dev` inside `api/` run it on your own machine, on port 8787. Copy
`api/.env.example` to `api/.env` and fill it in first. The local API uses
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

`npm run build:install` in `ui/` puts both files in `ui/.install/`. It zips the
extension, and then writes the page from `ui/install-page/index.html` with the version, the date and the
server URL filled in. The server URL comes from `FEEDBACK_API_URL`.

The workflow `.github/workflows/deploy-extension.yml` publishes them on a push to
`main` only when something in `ui/` has changed, or `api/types.ts`. The extension
is built with that one file from the API, so a change to it changes the extension
too. Everything else the extension is built from is inside `ui/`, in the same way
that everything the API is built from is inside `api/`. It uploads the zip first and the
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
one of the two files for this extension outside this folder, because GitHub reads
workflows only from `.github/workflows/`. It runs on a push to `main` only when
something in `api/` has changed, and it can also be run by hand from the Actions
tab. It replaces the code of the same function every time, so the server URL never
changes.

That rule is safe because `api/` holds everything the function is built from. It
is a package of its own, with its own `package.json` and lock file, and the shapes
it shares with the extension are in `api/types.ts`. The extension imports that
file from `api/`, not the other way round. So no change outside `api/` can change
the function, and every change inside it redeploys the function. It type-checks the code, bundles the API into one file with
esbuild, uploads it to the function, and then checks that a request without a key
is refused with 401. A placeholder or a broken bundle answers differently, so the
check fails if the new code is not running.

The workflow uses the same AWS credentials as the docs deploy. Those belong to the
docs site's deployer user, and `terraform/deployer.tf` adds a policy to that user
which lets it replace this function's code, write the install page's bucket and
flush its cache, and nothing else.

## Files

- `ui/` is the extension, as a package of its own, and the folder its deploy
  watches.
- `ui/entrypoints/content.ts` draws the highlights on the page and shows the colour
  bar and the comment box.
- `ui/entrypoints/background.ts` runs the sync.
- `ui/entrypoints/popup/` is the popup, including the form for the server URL and
  the API key.
- `ui/lib/store.ts` reads and writes the browser copy, and holds the server URL and
  the API key.
- `ui/lib/auth.ts` checks the server URL and the key with the API, and signs out.
- `api/` is the API, as a package of its own, and the folder its deploy watches.
- `api/types.ts` is what the API stores, which the extension imports too.
- `api/app.ts` is the API: the key check, `GET /me` and `POST /sync`.
- `api/keys.ts` reads the keys from Parameter Store.
- `api/store.ts` reads and writes the page files in S3.
- `api/lambda.ts` and `api/local.ts` run the API on Lambda and on your own
  machine.
- `ui/install-page/index.html` is the install page, before its values are filled in.
- `ui/scripts/build-install.ts` builds the install page and the zip.
- `worker/index.ts` is the feedback worker: the schedule and one run.
- `worker/claude.ts` runs one turn of the Claude Code session.
- `worker/prompt.ts` is what Claude is told about a page's comments, and the
  shape of its replies.
- `worker/feedback.ts` reads the open comments and records each outcome.
- `worker/git.ts` resets the clone before each page and pushes after it.
- `worker/ecosystem.config.cjs` tells PM2 how to run the worker.
- `terraform/` creates the AWS resources.
- `scripts/bootstrap-state-bucket.sh` creates the bucket that holds the
  Terraform state.
