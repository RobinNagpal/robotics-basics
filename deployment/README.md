# Deployment

The docs are served at **https://docs.dodao.io** as a static site out of S3,
with CloudFront in front of it:

```
docs.dodao.io
   │  Route 53 alias (A and AAAA)
   ▼
CloudFront ── ACM certificate, us-east-1 ──────────► HTTPS
   │          viewer-request function: /a/b/ → /a/b/index.html
   │          403 and 404 → /404.html
   │  Origin Access Control (the bucket stays private)
   ▼
S3  robotics-basics-web-<account-id>
```

Nothing runs on a server. The site is a **static export** — `website/` is a
Next.js app built with `output: 'export'`, so `npm run build` writes a
directory of plain HTML, JSON and assets rather than something that has to be
kept running. Two consequences worth holding on to:

- **The docs are read at build time.** Editing Markdown under `docs/` changes
  the site on the next build, not on the next request, which is why the deploy
  workflow triggers on `docs/**` as well as on `website/**`.
- **The bucket is private.** CloudFront reads it through Origin Access Control
  and nothing else can, so there is no public bucket anywhere in this.

## Why CloudFront is here

Not for caching, though it does that too. S3 cannot serve HTTPS on a name of
our own: its REST endpoint carries a certificate for `amazonaws.com`, and its
website endpoint — the only one that resolves `index.html` inside a directory —
speaks plain HTTP and nothing else. A distribution is the supported way to have
both TLS and a private bucket, so it would be here even with every cache turned
off.

It also does the URL mapping the export needs. The site is built with
`trailingSlash: true`, so a page is a directory containing `index.html`, and
S3-as-an-origin has no notion of an index document. The
[viewer-request function](terraform/functions/viewer-request.js) maps `/a/b/`
onto `/a/b/index.html`, passes real files through untouched, and redirects
`/a/b` to `/a/b/` so each page has exactly one URL — which matters because a
relative link inside the page resolves differently under the two.

## What the caching costs, which is nothing

Caching is **on**, for the pages and for the hashed assets. It was briefly off
while the docs were changing daily, on the theory that holding pages at the
edge costs money. It does not, and the arithmetic is worth writing down because
it is the opposite of the intuition:

- **Holding an object at an edge is not billed.** CloudFront charges for data
  transferred out and for requests. Caching lowers both, by keeping requests
  away from S3 — so the cached arrangement is the cheaper one.
- **A full flush is one path.** `/*` counts as a single invalidation path
  however many objects it matches, and the first **1,000 paths a month are
  free**. Every deploy issues one `/*`, so thirty deploys a month spends thirty
  of the thousand.
- **Listing individual URLs is what costs.** Twenty URLs is twenty paths.
  Beyond the free thousand that is $0.005 each. There is no case here where
  naming URLs is cheaper than `/*` — only more precise.

So freshness is bought by invalidating, not by refusing to cache. Two flags in
[`variables.tf`](terraform/variables.tf) turn it off if you ever want to rule
the cache out while chasing something:

| Flag | Default | What it holds |
|---|---|---|
| `cache_pages` | `true` | the HTML, the search index, the doc assets |
| `cache_immutable_assets` | `true` | `/_next/static/*` |

The second is safe to leave on whatever the first is doing: those filenames
contain a hash of their own contents, so a changed file is a changed URL and a
held copy can never be stale. 404s are never cached at all, whatever either
flag says — a page that exists now must not keep being denied because it did
not exist when somebody first asked.

## One-time setup

Run Terraform with **admin** credentials. State lives in a private, versioned,
SSE-encrypted S3 bucket; create it first.

```sh
bash deployment/scripts/bootstrap-state-bucket.sh
cd deployment/terraform
terraform init -backend-config="bucket=robotics-basics-tfstate-<account-id>"
terraform apply
```

That creates the bucket, the certificate (DNS-validated in the existing
`dodao.io` zone), the distribution, the `docs.dodao.io` records, and a
`robotics-basics-deployer` IAM user scoped to exactly two things: writing that
bucket and invalidating that distribution.

> The first apply takes 5–10 minutes. Nearly all of it is waiting for the
> certificate to validate and the distribution to deploy.

Then wire up GitHub Actions (**Settings → Secrets and variables → Actions**):

| Kind | Name | From |
|---|---|---|
| Secret | `AWS_ACCESS_KEY_ID` | `terraform output -raw deployer_access_key_id` |
| Secret | `AWS_SECRET_ACCESS_KEY` | `terraform output -raw deployer_secret_access_key` |
| Variable | `S3_BUCKET` | `terraform output -raw web_bucket` |
| Variable | `CLOUDFRONT_DISTRIBUTION_ID` | `terraform output -raw cloudfront_distribution_id` |

## Every deploy after that

Push to `main` with a change under `docs/` or `website/`.
[`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml):

1. builds the export, and checks `out/index.html`, `out/search-index.json` and
   `out/404.html` all exist — a build that quietly stopped being static would
   otherwise be found by an empty bucket;
2. writes the commit SHA to `out/_build.txt`;
3. uploads `_next/static/` **first, without `--delete`**, with a one-year
   `Cache-Control`. Assets before pages, so a page never arrives referencing a
   bundle that is not there yet;
4. uploads everything else **with `--delete`** and `max-age=0,
   must-revalidate`, so pages are always revalidated and anything removed from
   the site leaves the bucket;
5. invalidates `/*` and waits for it to complete;
6. fetches `/_build.txt` and checks it matches the commit. Checking the SHA
   rather than a 200 is what catches a stale edge or a sync that uploaded
   nothing.

## Flushing the cache by hand

[`.github/workflows/flush-cache.yml`](../.github/workflows/flush-cache.yml) is
a manually-triggered job: **Actions → Flush the CDN cache → Run workflow**.
Anyone with write access to the repository can run it, which is the point —
nobody needs AWS credentials to clear the cache.

It takes what to flush (`/*` by default, which is everything and is billed as
one path) and an optional reason, and records both in the run summary along
with who asked, so the history explains itself. It waits for the invalidation
to complete rather than firing and forgetting.

An ordinary deploy already flushes everything, so this is for the times the
bucket changed without one: an object edited or rolled back by hand, a change
to the caching flags, or a page that looks stale and you want the cache ruled
out before looking further.

## Rolling back

The bucket is versioned, and old versions are kept for 30 days. To go back,
sync the previous build out and in again, then flush:

```sh
# what is there now, and when
aws s3api list-object-versions --bucket robotics-basics-web-<account-id> \
  --prefix index.html --query 'Versions[].{v:VersionId,t:LastModified}' --output table
```

Redeploying the previous commit through the workflow is usually simpler and
leaves a better trail: re-run the last good run from the Actions tab.

## Notes

- **Terraform state** lives in `robotics-basics-tfstate-<account-id>`, private,
  versioned and encrypted. It contains the deployer's secret access key.
- **Costs.** Effectively nothing. The site is ~30 MB, CloudFront's free tier
  covers 1 TB out and 10 M requests a month, invalidations are one path per
  deploy against a thousand free, S3 storage is pennies with old versions
  expiring after 30 days, and the hosted zone already exists.
- **`price_class`** is `PriceClass_100` — North America and Europe. The whole
  estate is in `us-east-1` and the readership is not global enough to pay for
  the other two; raising it is one variable.
- **This used to run on the shared Lightsail host** alongside courtpot and
  interestled, on port 7073 behind Caddy. That worked and gave HTTPS without a
  distribution, but it tied a static site to a box shared with two services.
  Nothing in this repository depends on that host any more.
