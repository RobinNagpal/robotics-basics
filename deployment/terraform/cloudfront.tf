# CloudFront is what makes a private S3 bucket serveable over HTTPS on a name
# of our own. S3 alone cannot do it: its REST endpoint has a certificate for
# amazonaws.com, and its website endpoint — the only one that resolves index
# documents — speaks plain HTTP and nothing else. So the distribution earns its
# place on TLS and routing alone; the caching it also gives is free on top, and
# is on, because holding an object at an edge is not something CloudFront bills
# for. Freshness is paid for by invalidating on deploy instead.

# Managed policies rather than hand-written ones. These two are the whole
# decision: hold nothing, or hold it with sensible defaults. Looking them up by
# name keeps their ids out of this file.
data "aws_cloudfront_cache_policy" "disabled" {
  name = "Managed-CachingDisabled"
}

data "aws_cloudfront_cache_policy" "optimized" {
  name = "Managed-CachingOptimized"
}

locals {
  pages_cache_policy_id  = var.cache_pages ? data.aws_cloudfront_cache_policy.optimized.id : data.aws_cloudfront_cache_policy.disabled.id
  assets_cache_policy_id = var.cache_immutable_assets ? data.aws_cloudfront_cache_policy.optimized.id : data.aws_cloudfront_cache_policy.disabled.id
}

# Lets the distribution read a bucket that blocks all public access. The bucket
# policy (s3.tf) names this distribution specifically, so nothing else can read
# it either.
resource "aws_cloudfront_origin_access_control" "web" {
  name                              = "${var.app_name}-oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# Runs at the edge on every request, before the cache is consulted. See the
# file itself for what it does and why the redirect is a redirect.
resource "aws_cloudfront_function" "viewer_request" {
  name    = "${var.app_name}-viewer-request"
  runtime = "cloudfront-js-2.0"
  comment = "Map trailing-slash URLs onto the export's index.html files."
  publish = true
  code    = file("${path.module}/functions/viewer-request.js")
}

resource "aws_cloudfront_distribution" "web" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "${var.app_name} docs — ${var.site_host}"
  default_root_object = "index.html"
  price_class         = var.price_class
  aliases             = [var.site_host]

  origin {
    origin_id                = "s3-web"
    domain_name              = aws_s3_bucket.web.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.web.id
  }

  default_cache_behavior {
    target_origin_id       = "s3-web"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true
    cache_policy_id        = local.pages_cache_policy_id

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.viewer_request.arn
    }
  }

  # Everything under here is named by a hash of its own contents, so a changed
  # file is a changed URL and a held copy can never be stale. It has a
  # behaviour of its own so that caching can be turned off for the pages —
  # while chasing a staleness problem, say — without giving up the caching of
  # the assets, which cannot be the cause of one and is where most of the bytes
  # are.
  ordered_cache_behavior {
    path_pattern           = "/_next/static/*"
    target_origin_id       = "s3-web"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true
    cache_policy_id        = local.assets_cache_policy_id
  }

  # A missing object in a private bucket is a 403, not a 404: the distribution
  # is granted GetObject and not ListBucket, so S3 will not admit whether the
  # key exists. Both are mapped to the export's own 404 page, and the status is
  # rewritten to 404 so the answer is honest.
  #
  # error_caching_min_ttl is 0 deliberately, and is not covered by cache_pages.
  # A 404 is the one answer worth never holding: a page that exists now must
  # not keep being denied because it did not exist when someone first asked,
  # and a deploy that adds a page issues no signal an edge could act on beyond
  # the invalidation.
  custom_error_response {
    error_code            = 403
    response_code         = 404
    response_page_path    = "/404.html"
    error_caching_min_ttl = 0
  }

  custom_error_response {
    error_code            = 404
    response_code         = 404
    response_page_path    = "/404.html"
    error_caching_min_ttl = 0
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn = aws_acm_certificate_validation.web.certificate_arn
    ssl_support_method  = "sni-only"
    # TLS 1.2 is the floor. Anything older is long past supported, and the
    # readership is developers with current browsers.
    minimum_protocol_version = "TLSv1.2_2021"
  }
}
