# Z2FDTNDATAQYW2 is CloudFront's own hosted zone id. It is the same fixed value
# for every distribution in every account, which is why it is a literal rather
# than something looked up.
locals {
  cloudfront_zone_id = "Z2FDTNDATAQYW2"
}

# An alias rather than a CNAME, so the name can be a subdomain and still
# resolve without the extra lookup a CNAME costs — and so Route 53 answers for
# it directly rather than handing out CloudFront's own name.
resource "aws_route53_record" "site_a" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = var.site_host
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.web.domain_name
    zone_id                = local.cloudfront_zone_id
    evaluate_target_health = false
  }
}

# The distribution answers on IPv6, so the record set should too. Without this
# an IPv6-only client cannot reach the site at all.
resource "aws_route53_record" "site_aaaa" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = var.site_host
  type    = "AAAA"

  alias {
    name                   = aws_cloudfront_distribution.web.domain_name
    zone_id                = local.cloudfront_zone_id
    evaluate_target_health = false
  }
}
