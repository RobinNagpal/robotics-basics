# The zone already exists and is shared with a great many other subdomains.
# This stack reads it, adds one name to it, and manages nothing else in it.
data "aws_route53_zone" "main" {
  name         = "${var.zone_name}."
  private_zone = false
}

# Issued in us-east-1 because CloudFront accepts certificates from nowhere
# else. Covers exactly the one name — there is no www for a docs subdomain.
resource "aws_acm_certificate" "web" {
  provider = aws.us_east_1

  domain_name       = var.site_host
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

# allow_overwrite because a re-issued certificate reuses the same validation
# record name, and the second apply would otherwise fail on a record it owns.
resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.web.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  zone_id         = data.aws_route53_zone.main.zone_id
  name            = each.value.name
  type            = each.value.type
  records         = [each.value.record]
  ttl             = 300
  allow_overwrite = true
}

# Blocks until the certificate is issued, so the distribution is never built
# against one still pending. This is most of the first apply's running time.
resource "aws_acm_certificate_validation" "web" {
  provider = aws.us_east_1

  certificate_arn         = aws_acm_certificate.web.arn
  validation_record_fqdns = [for r in aws_route53_record.cert_validation : r.fqdn]
}
