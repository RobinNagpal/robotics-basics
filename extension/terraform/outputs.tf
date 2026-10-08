output "feedback_api_url" {
  description = "The API's address. Put it, without the trailing slash, in WXT_API_URL when building the extension."
  value       = aws_lambda_function_url.feedback_api.function_url
}

output "feedback_bucket" {
  description = "Where the comments are kept, one JSON file per docs page under feedback/."
  value       = aws_s3_bucket.feedback.bucket
}

output "feedback_api_keys_parameter" {
  description = "The SSM parameter that holds the API keys."
  value       = aws_ssm_parameter.feedback_api_keys.name
}

output "install_page_url" {
  description = "The page that offers the extension for download."
  value       = "https://${aws_cloudfront_distribution.install.domain_name}/"
}

output "install_bucket" {
  description = "The bucket behind the install page."
  value       = aws_s3_bucket.install.bucket
}

output "install_distribution_id" {
  description = "The install page's CloudFront distribution, invalidated on every deploy."
  value       = aws_cloudfront_distribution.install.id
}
