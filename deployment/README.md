# Deployment

The docs are served at **https://docs.dodao.io** from the same Lightsail
instance that already runs [courtpot](https://github.com/RobinNagpal/courtpot)
and [interestled](https://github.com/RobinNagpal/interestled) — one box, one
application per port:

```
                    shared Lightsail instance  (13.216.34.24, medium_3_0)
                    ┌──────────────────────────────────────────────┐
docs.dodao.io    ──▶│ Caddy :443   api.courtpot.com     → :7071     │
  Route 53 A        │  (Let's       api.interestled.com → :7072     │
                    │   Encrypt)    docs.dodao.io       → :7073     │
                    │                                              │
                    │ systemd  courtpot-api.service       :7071     │
                    │ systemd  interestled-api.service    :7072     │
                    │ systemd  robotics-basics-api.service :7073    │
                    └──────────────────────────────────────────────┘

s3://robotics-basics-web-<account-id>/current/   the generated docs, versioned
```

**There is no CloudFront here, and that is deliberate.** The other two projects
put a distribution in front of a private S3 bucket because a bucket cannot
serve HTTPS on a custom domain by itself. This site does not need one: Caddy is
already terminating TLS on that host for two other names, so adding a third
costs nothing and gives the same certificate handling, obtained and renewed by
the host. A distribution would be a second place to invalidate and a second
thing to debug for no gain at this size.

## What is deployed

The site is a **static export**. `website/` is a Next.js app, but it is built
with `output: 'export'`, so `npm run build` writes a directory of plain HTML,
JSON and assets rather than producing a server to run. Two consequences worth
knowing:

- **The docs are read at build time.** Editing Markdown under `docs/` changes
  the site on the next build, not on the next request. The workflow therefore
  triggers on `docs/**` as well as on `website/**`.
- **Nothing renders in production.** What runs on the host is
  [`scripts/serve-static.js`](scripts/serve-static.js), a dependency-free file
  server over the exported directory. It exists only so this site has the same
  shape as every other application on that host — one Node process at
  `/srv/<app>/current/index.js` on its own port — which is what lets it be
  added without changing how the host is provisioned.

S3 holds the published export and is the rollback point. The bucket is
versioned, so a bad build can be recovered by syncing an earlier version back
out; the host keeps only the current copy and the one before it.

## The entry this needs on the shared host

**This lives in the courtpot repository**, because the shared host belongs to
none of the three applications on it and its stack is applied by an
administrator. It is one entry in the `apps` map in
`deployment/terraform/shared-host/variables.tf`:

```hcl
robotics-basics = {
  port     = 7073
  api_host = "docs.dodao.io"
}
```

`terraform output -raw shared_host_apps_entry` prints it as JSON if you would
rather paste than type.

`api_host` is a slightly wrong name for a docs site, and the systemd unit it
produces is `robotics-basics-api.service`. Both are the shared host's naming,
kept rather than special-cased: the alternative is a change to `provision.sh`,
which every application on the box shares.

**Apply it by re-running the provisioning script over SSH, not with
`terraform apply`.** The map is part of `user_data`, and changing `user_data`
destroys and recreates the instance — which would take the other two
applications down with it:

```sh
ssh -i ~/.ssh/shared-apps.pem ubuntu@13.216.34.24 \
  "sudo APPS_JSON='<the new map as JSON>' \
        DEPLOY_PUBLIC_KEY=\"\$(cat /home/deploy/.ssh/authorized_keys)\" \
        bash /root/provision.sh"
```

`provision.sh` is idempotent and derives everything from `APPS_JSON`, so a
re-run converges: it adds the third systemd unit and the third Caddy site and
leaves the other two alone. Commit the `variables.tf` change too, so the next
instance is built with all three.

> Caddy will try to obtain a certificate for `docs.dodao.io` as soon as the
> site block exists, so create the DNS record first — `terraform apply` in this
> repository — or the HTTP-01 challenge fails and Caddy backs off before
> retrying.

## One-time setup

Run Terraform with **admin** credentials. State lives in a private, versioned,
SSE-encrypted S3 bucket; create it first.

```sh
bash deployment/scripts/bootstrap-state-bucket.sh
cd deployment/terraform
terraform init -backend-config="bucket=robotics-basics-tfstate-<account-id>"
terraform apply
```

That creates the docs bucket, the `docs.dodao.io` A record pointing at the
shared host's static IP, and a `robotics-basics-deployer` IAM user scoped to
exactly one thing: writing that bucket. It reads the shared host's state
read-only to find the IP, and can change nothing about the host — getting files
onto the box is SSH, not AWS.

Then wire up GitHub Actions (**Settings → Secrets and variables → Actions**):

| Kind | Name | From |
|---|---|---|
| Secret | `AWS_ACCESS_KEY_ID` | `terraform output -raw deployer_access_key_id` |
| Secret | `AWS_SECRET_ACCESS_KEY` | `terraform output -raw deployer_secret_access_key` |
| Secret | `SSH_PRIVATE_KEY` | shared-host stack: `terraform output -raw deploy_private_key` |
| Variable | `S3_BUCKET` | `terraform output -raw web_bucket` |
| Variable | `DEPLOY_HOST` | `terraform output -raw shared_host_ip` |
| Variable | `SSH_HOST_KEY` | `ssh-keyscan -t rsa,ecdsa,ed25519 13.216.34.24` |

`SSH_HOST_KEY` is **pinned** rather than accepted on first use, so a hijacked
record cannot collect a key that reaches a box running three applications.
Recreating the instance changes it — re-run `ssh-keyscan` and update the
variable, or every deploy fails at the SSH step.

There is no `CLOUDFRONT_DISTRIBUTION_ID` and no `DATABASE_URL`: no
distribution, and the site has no database.

## Every deploy after that

Push to `main` with a change under `docs/`, `website/` or the server script.
[`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml):

1. builds the export and checks `out/index.html` and `out/search-index.json`
   both exist, which is how a server build that silently stopped being static
   would be caught;
2. assembles `index.js` + `site/` — exactly what `/srv/robotics-basics/current`
   holds — so the copy in S3 and the copy on the host are identical by
   construction;
3. syncs that tree to `s3://<bucket>/current/` with `--delete`;
4. rsyncs it to `/srv/robotics-basics/next` on the host, rotates `current` to
   `previous`, swaps `next` into `current`, and restarts the service;
5. polls `https://docs.dodao.io/` until it answers 200, and dumps the service's
   journal if it never does.

Staging and swapping matters for the same reason it does in the other two
projects: the service must not be able to restart into a half-transferred tree.

## Operating it

```sh
ssh -i ~/.ssh/shared-apps.pem ubuntu@13.216.34.24

sudo journalctl -u robotics-basics-api -f   # this site's logs
sudo journalctl -u caddy -f                 # TLS and routing for all three
curl localhost:8080                         # host liveness, no certificate involved
curl localhost:7073/_health                 # this site, bypassing Caddy
curl -I localhost:7073/                     # and its actual output
cat /srv/robotics-basics/current/site/_build.txt   # which commit is live
```

**Rolling back** is the previous tree, still on disk:

```sh
ssh deploy@13.216.34.24 \
  'rm -rf /srv/robotics-basics/current && \
   mv /srv/robotics-basics/previous /srv/robotics-basics/current && \
   sudo systemctl restart robotics-basics-api'
```

Further back than that is S3: the bucket is versioned, so an earlier export can
be synced out and rsynced up. Nothing is lost by recreating the instance either
— the site is a build artifact and CI rebuilds it — but all three applications
are down until each project's workflow runs again, and `SSH_HOST_KEY` must be
updated in all three repositories.

## Notes

- **Terraform state** lives in `robotics-basics-tfstate-<account-id>`, private,
  versioned and encrypted. It contains the deployer's secret access key.
- **Costs.** This adds no recurring cost worth naming. The instance is already
  paid for and shared; the bucket holds ~30 MB and its old versions expire
  after 30 days; `docs.dodao.io` sits in a hosted zone that already exists.
  Serving from the shared host rather than from CloudFront is also what keeps
  it at zero.
- **Ports.** 7071 courtpot, 7072 interestled, 7073 here. The shared-host stack
  validates that no two applications share one, which is the single failure
  that arrangement cannot absorb.
