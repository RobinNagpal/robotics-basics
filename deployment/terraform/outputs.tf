output "site_url" {
  description = "Where the docs are served."
  value       = "https://${var.site_host}"
}

output "web_bucket" {
  description = "S3 bucket holding the generated docs — the S3_BUCKET Actions variable."
  value       = aws_s3_bucket.web.bucket
}

output "cloudfront_distribution_id" {
  description = "The CLOUDFRONT_DISTRIBUTION_ID Actions variable, used to invalidate on deploy and by hand."
  value       = aws_cloudfront_distribution.web.id
}

output "cloudfront_domain_name" {
  description = "The distribution's own name. Useful for testing before the DNS record has propagated."
  value       = aws_cloudfront_distribution.web.domain_name
}

output "caching" {
  description = "What the distribution is currently holding, so `terraform output` answers it without reading the plan."
  value = {
    pages            = var.cache_pages ? "cached (Managed-CachingOptimized)" : "not cached (Managed-CachingDisabled)"
    immutable_assets = var.cache_immutable_assets ? "cached (Managed-CachingOptimized)" : "not cached (Managed-CachingDisabled)"
  }
}

output "deployer_access_key_id" {
  description = "Set as the AWS_ACCESS_KEY_ID Actions secret."
  value       = var.create_deployer_access_key ? aws_iam_access_key.deployer[0].id : null
}

output "deployer_secret_access_key" {
  description = "Set as the AWS_SECRET_ACCESS_KEY Actions secret."
  value       = var.create_deployer_access_key ? aws_iam_access_key.deployer[0].secret : null
  sensitive   = true
}
