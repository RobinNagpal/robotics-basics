terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.80"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.7"
    }
  }

  # State lives in a private, versioned, SSE-encrypted S3 bucket created by
  # extension/scripts/bootstrap-state-bucket.sh. It is this application's own
  # bucket, not the docs site's, because the feedback API is a separate
  # application. The bucket name is account-specific, so init with:
  #   terraform init -backend-config="bucket=feedback-api-tfstate-<account-id>"
  backend "s3" {
    key     = "feedback-api/terraform.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
}
