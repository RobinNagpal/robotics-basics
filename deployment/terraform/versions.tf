terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.80"
    }
  }

  # State lives in a private, versioned, SSE-encrypted S3 bucket created by
  # deployment/scripts/bootstrap-state-bucket.sh. The state records every
  # resource here, including the deployer's secret access key, so the bucket is
  # never public and always versioned.
  #
  # The bucket name carries the account id, which differs between accounts, so
  # it is supplied at init time rather than written here:
  #   terraform init -backend-config="bucket=robotics-basics-tfstate-<account-id>"
  backend "s3" {
    key     = "robotics-basics/terraform.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
}
