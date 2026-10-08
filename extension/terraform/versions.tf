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

  # The same state bucket as deployment/terraform, under its own key, so the
  # two stacks are applied separately and neither can change the other's
  # resources:
  #   terraform init -backend-config="bucket=robotics-basics-tfstate-<account-id>"
  backend "s3" {
    key     = "robotics-basics/feedback-api.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = var.app_name
      ManagedBy = "terraform"
    }
  }
}

data "aws_caller_identity" "current" {}
