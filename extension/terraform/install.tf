# The install page: one HTML page and the built extension, served over HTTPS.
#
# The files sit in a private bucket and CloudFront serves them, the same
# arrangement as the docs site in deployment/terraform. CloudFront is what
# gives the page HTTPS while the bucket stays private. The page uses
# CloudFront's own *.cloudfront.net address, so no certificate or DNS record is
# needed. .github/workflows/deploy-extension.yml uploads the files.

resource "aws_s3_bucket" "install" {
  bucket = "${var.app_name}-highlighter-install-${data.aws_caller_identity.current.account_id}"

  # Everything in it is rebuilt from the repository on every deploy.
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "install" {
  bucket = aws_s3_bucket.install.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "install" {
  bucket = aws_s3_bucket.install.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_cloudfront_origin_access_control" "install" {
  name                              = "${var.app_name}-highlighter-install"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

data "aws_cloudfront_cache_policy" "optimized" {
  name = "Managed-CachingOptimized"
}

resource "aws_cloudfront_distribution" "install" {
  enabled             = true
  comment             = "DoDAO Highlighter install page"
  default_root_object = "index.html"
  price_class         = "PriceClass_100"

  origin {
    origin_id                = "install"
    domain_name              = aws_s3_bucket.install.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.install.id
  }

  # Cached at the edge. Each deploy invalidates /*, so a new build shows at once.
  default_cache_behavior {
    target_origin_id       = "install"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    cache_policy_id        = data.aws_cloudfront_cache_policy.optimized.id
    compress               = true
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}

# Only this distribution may read the bucket.
data "aws_iam_policy_document" "install_bucket" {
  statement {
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.install.arn}/*"]

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.install.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "install" {
  bucket     = aws_s3_bucket.install.id
  policy     = data.aws_iam_policy_document.install_bucket.json
  depends_on = [aws_s3_bucket_public_access_block.install]
}
