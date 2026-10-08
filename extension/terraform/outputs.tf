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
