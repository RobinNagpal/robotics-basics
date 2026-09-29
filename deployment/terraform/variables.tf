variable "app_name" {
  description = "Prefix for every resource name."
  type        = string
  default     = "robotics-basics"
}

variable "aws_region" {
  description = "Region for the bucket. The certificate is pinned to us-east-1 regardless; see providers.tf."
  type        = string
  default     = "us-east-1"
}

variable "zone_name" {
  description = <<-EOT
    The hosted zone the site's record goes in. This apex already exists in
    Route 53 and holds a great many other records; nothing here creates or
    manages the zone itself.
  EOT
  type        = string
  default     = "dodao.io"
}

variable "site_host" {
  description = "Where the docs are served. The only name this stack adds to the zone."
  type        = string
  default     = "docs.dodao.io"
}

variable "cache_pages" {
  description = <<-EOT
    Whether CloudFront caches the pages.

    On. Caching costs nothing extra — CloudFront charges for transfer and
    requests, never for holding an object at an edge, and caching lowers both
    by keeping requests away from S3. What it costs is freshness, and that is
    paid for by invalidating rather than by not caching: every deploy issues
    one `/*` invalidation, which counts as a single path against a free
    allowance of 1,000 a month.

    Set it to false to make every request reach S3, which is the setting to
    reach for if a deploy ever appears not to have landed and you want to rule
    the cache out.
  EOT
  type        = bool
  default     = true
}

variable "cache_immutable_assets" {
  description = <<-EOT
    Whether CloudFront caches /_next/static/*, separately from the pages.

    These filenames contain a hash of their own contents, so a changed file is
    a changed URL and a held copy can never be stale. It is therefore safe to
    leave on even when cache_pages is turned off to chase a staleness problem —
    this is not where one can come from.
  EOT
  type        = bool
  default     = true
}

variable "price_class" {
  description = <<-EOT
    Which edge locations serve the site. PriceClass_100 is North America and
    Europe, and is the cheapest; the whole estate is in us-east-1 and the
    readership is not global enough to pay for the other two.
  EOT
  type        = string
  default     = "PriceClass_100"
}

variable "create_deployer_access_key" {
  description = <<-EOT
    Create an access key for the CI deployer user and expose it as (sensitive)
    outputs. Set to false to mint the key yourself in the IAM console instead;
    a key created here is also stored in the Terraform state.
  EOT
  type        = bool
  default     = true
}

variable "permissions_boundary_arn" {
  description = <<-EOT
    Optional ceiling on the IAM user this stack creates.

    courtpot applies its stack as a scoped infra user with a boundary, because
    a stack that can create IAM users and access keys can otherwise mint itself
    an administrator. This stack is smaller — one deployer whose whole policy is
    "write one bucket, invalidate one distribution" — so it is written to be
    applied by an administrator and the boundary is optional. Set it if you add
    an infra-identity stack for this project later.
  EOT
  type        = string
  default     = ""
}
