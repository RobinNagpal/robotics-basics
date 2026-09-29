# Where the generated docs live.
#
# The site is a static export — `next build` with `output: 'export'` writes a
# directory of plain files — and this bucket is the published copy of it. The
# deploy uploads here first and the shared host pulls from here, so the bucket
# is the record of what is live rather than a staging area: versioning means a
# bad build can be rolled back by re-syncing an earlier version, and the host
# holds no history of its own.
#
# It is private. Nothing reads it over the internet, because the site is served
# by Caddy from the host's disk — that is what gives it HTTPS without a
# CloudFront distribution in front of a public bucket.
resource "aws_s3_bucket" "web" {
  bucket = "${var.app_name}-web-${data.aws_caller_identity.current.account_id}"

  # Contents are a build artifact: every file can be regenerated from the
  # repository by running the build again.
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "web" {
  bucket = aws_s3_bucket.web.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Kept on so a broken export can be undone without rebuilding it, and so the
# bucket answers "what was live last Tuesday" — the host cannot, since each
# deploy replaces its copy wholesale.
resource "aws_s3_bucket_versioning" "web" {
  bucket = aws_s3_bucket.web.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "web" {
  bucket = aws_s3_bucket.web.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# Old versions are worth keeping for a rollback, not for ever. The export is
# ~30 MB and every deploy rewrites most of it, so without this the bucket grows
# by that much per deploy indefinitely.
resource "aws_s3_bucket_lifecycle_configuration" "web" {
  bucket = aws_s3_bucket.web.id

  rule {
    id     = "expire-old-versions"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = 30
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  depends_on = [aws_s3_bucket_versioning.web]
}
