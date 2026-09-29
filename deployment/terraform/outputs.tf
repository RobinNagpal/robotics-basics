output "site_url" {
  description = "Where the docs are served."
  value       = "https://${var.site_host}"
}

output "web_bucket" {
  description = "S3 bucket holding the generated docs — the S3_BUCKET Actions variable."
  value       = aws_s3_bucket.web.bucket
}

output "site_host" {
  description = "The name Caddy terminates TLS for. Must match api_host in the shared-host apps map."
  value       = var.site_host
}

output "site_port" {
  description = "The port this application listens on behind Caddy. Must match its port in the shared-host apps map."
  value       = var.site_port
}

output "shared_host_ip" {
  description = "Static IP of the shared Lightsail instance — the DEPLOY_HOST Actions variable."
  value       = data.terraform_remote_state.shared_host.outputs.static_ip
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

# The entry this application needs in the shared-host stack's `apps` map,
# printed rather than described so it can be pasted. That map lives in the
# courtpot repository and is applied by an administrator; this stack cannot
# write it, which is the whole reason for printing it here.
output "shared_host_apps_entry" {
  description = "Add this to the apps map in courtpot's deployment/terraform/shared-host/variables.tf."
  value = jsonencode({
    (var.app_name) = {
      port     = var.site_port
      api_host = var.site_host
    }
  })
}
