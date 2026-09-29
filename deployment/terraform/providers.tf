provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = var.app_name
      ManagedBy = "terraform"
    }
  }
}

# There is no second, us-east-1-pinned provider here, and that is the point of
# having no CloudFront: the only certificate this site uses is the one Caddy
# obtains on the host itself, so nothing in this stack is region-locked.

data "aws_caller_identity" "current" {}
