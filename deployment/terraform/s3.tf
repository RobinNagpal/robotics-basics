# Where the generated docs live, and what is actually served.
#
# The site is a static export — `next build` with `output: 'export'` writes a
# directory of plain files — and this bucket holds it. It is the origin rather
# than a staging area: what is in here is what the world gets, and versioning
# means a bad build can be undone by syncing an earlier version back out.
#
# It is private, with every public-access block on. CloudFront reads it through
# Origin Access Control and nothing else can — see cloudfront.tf for why a
# distribution is needed at all, which is TLS rather than caching.
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

# The only reader is this distribution, named specifically. Origin Access
# Control signs CloudFront's requests to S3, so the bucket can keep every
# public-access block on and still be served to the world over HTTPS — which
# is the arrangement that makes a distribution worth having in front of it.
data "aws_iam_policy_document" "web_bucket" {
  statement {
    sid       = "AllowCloudFrontRead"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.web.arn}/*"]

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    # Without this any CloudFront distribution in any account could read the
    # bucket: the service principal alone does not say whose distribution.
    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.web.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "web" {
  bucket = aws_s3_bucket.web.id
  policy = data.aws_iam_policy_document.web_bucket.json

  # The access block has to land first, or the policy is briefly the only thing
  # standing between the bucket and the internet.
  depends_on = [aws_s3_bucket_public_access_block.web]
}
