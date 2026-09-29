variable "app_name" {
  description = <<-EOT
    Prefix for every resource name, and the key this application is known by on
    the shared host. It has to match the entry added to the `apps` map in the
    shared-host stack, because that map is what names the systemd unit
    (`robotics-basics-api.service`) and the directory the site is served from
    (`/srv/robotics-basics/current`).
  EOT
  type        = string
  default     = "robotics-basics"
}

variable "aws_region" {
  description = "Region for the bucket. Keep it with the rest of the estate and with the shared host."
  type        = string
  default     = "us-east-1"
}

variable "zone_name" {
  description = <<-EOT
    The hosted zone the site's record goes in. This is the apex that already
    exists in Route 53 — the site itself is a subdomain of it, named by
    `site_host` below. Nothing here creates or manages the zone.
  EOT
  type        = string
  default     = "dodao.io"
}

variable "site_host" {
  description = <<-EOT
    Where the docs are served. A plain A record to the shared host's static IP;
    Caddy on that host terminates TLS for this exact name with a Let's Encrypt
    certificate it obtains and renews itself.

    It must match the `api_host` of this application's entry in the shared-host
    `apps` map, because that string is what Caddy writes its site block for. A
    mismatch produces a certificate for one name and traffic arriving under
    another, which fails as a 404 from Caddy rather than as anything obvious.
  EOT
  type        = string
  default     = "docs.dodao.io"
}

variable "site_port" {
  description = <<-EOT
    The port this application's process listens on, behind Caddy, on the shared
    host. Recorded here so the stack that owns the DNS also documents the port
    the name resolves to, but it is NOT set from here: the shared-host stack's
    `apps` map is what actually opens it.

    7071 is courtpot and 7072 is interestled, so this is the next free one. Two
    applications sharing a port is the one failure the shared host cannot
    absorb, which is why the shared-host stack validates that they are distinct.
  EOT
  type        = number
  default     = 7073
}

variable "shared_host_state_bucket" {
  description = <<-EOT
    Terraform state bucket of the shared Lightsail host, read read-only to find
    the instance's static IP. The host belongs to none of the three
    applications on it, so its state lives under neither project's name.

    It is created by the shared-host stack, which lives in the courtpot
    repository at deployment/terraform/shared-host and is applied by an
    administrator. Nothing in this stack writes it.
  EOT
  type        = string
  default     = "shared-host-tfstate-729763663166"
}

variable "create_deployer_access_key" {
  description = <<-EOT
    Create an access key for the CI deployer user and expose it as (sensitive)
    outputs. Set to false to mint the key yourself in the IAM console instead;
    a key created here is also stored in the Terraform state.
  EOT
  type        = bool
  default     = true
}

variable "permissions_boundary_arn" {
  description = <<-EOT
    Optional ceiling on the IAM user this stack creates.

    courtpot applies its stack as a scoped `courtpot-infra` user and gives that
    user a boundary, because a stack that can create IAM users and access keys
    can otherwise mint itself an administrator. This stack is smaller — one
    deployer user whose whole policy is "write one bucket" — so it is written
    to be applied by an administrator, and the boundary is optional.

    Set it if you add an infra-identity stack for this project later. Leave it
    empty and the user is created without one.
  EOT
  type        = string
  default     = ""
}
