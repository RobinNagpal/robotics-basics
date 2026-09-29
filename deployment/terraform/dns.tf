# The shared Lightsail host, read read-only. This stack needs one value from
# it — the static IP the site's record points at — and must never write it:
# the host is shared with courtpot and interestled, and its stack is applied by
# an administrator from the courtpot repository.
data "terraform_remote_state" "shared_host" {
  backend = "s3"

  config = {
    bucket = var.shared_host_state_bucket
    key    = "shared-host/terraform.tfstate"
    region = var.aws_region
  }
}

# The zone already exists and holds a great many other records. This stack adds
# exactly one name to it and manages nothing else in it.
data "aws_route53_zone" "main" {
  name         = "${var.zone_name}."
  private_zone = false
}

# A plain A record, not an alias: the target is a Lightsail static IP, which is
# an address rather than an AWS-hosted zone target, so there is nothing to
# alias to. The address is static precisely so this record survives the
# instance being recreated.
#
# Caddy on that host answers for this name and serves the exported site from
# disk. There is no ACM certificate anywhere in this stack — Let's Encrypt
# issues one on the host, which is what removes the need for CloudFront.
resource "aws_route53_record" "site" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = var.site_host
  type    = "A"
  ttl     = 300
  records = [data.terraform_remote_state.shared_host.outputs.static_ip]
}
