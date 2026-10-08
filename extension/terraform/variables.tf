variable "app_name" {
  description = "Prefix for every resource name. The same as in deployment/terraform."
  type        = string
  default     = "robotics-basics"
}

variable "aws_region" {
  description = "Region for the function, the bucket and the key parameter."
  type        = string
  default     = "us-east-1"
}

variable "deployer_user" {
  description = <<-EOT
    The IAM user GitHub Actions deploys as. deployment/terraform creates it for
    the docs site; this stack only adds a policy to it, so the existing Actions
    secrets also deploy the API.
  EOT
  type        = string
  default     = "robotics-basics-deployer"
}
