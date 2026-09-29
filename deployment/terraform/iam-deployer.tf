# CI deploy user for GitHub Actions, scoped to exactly what a deploy does:
# write the docs bucket, and invalidate the one distribution in front of it. It
# can touch nothing else in the account, and in particular it cannot change the
# distribution, the certificate or the DNS — those are Terraform's, applied by
# an administrator.
resource "aws_iam_user" "deployer" {
  name = "${var.app_name}-deployer"
  path = "/${var.app_name}/"

  # Empty means no boundary; see the variable for why this stack does not
  # require one where courtpot's does.
  permissions_boundary = var.permissions_boundary_arn != "" ? var.permissions_boundary_arn : null
}

data "aws_iam_policy_document" "deployer" {
  # ListBucket is on the bucket itself rather than its contents, and `aws s3
  # sync` needs it: without it the sync cannot see what is already there, so it
  # has nothing to compare against and uploads every file every time.
  statement {
    sid       = "WebBucketList"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.web.arn]
  }

  statement {
    sid = "WebBucketWrite"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
    ]
    resources = ["${aws_s3_bucket.web.arn}/*"]
  }

  # Deploying uploads new bytes under URLs that have not changed, so without
  # this the edges would go on serving the previous build until their own TTLs
  # ran out. GetInvalidation is included so the workflow can wait for one and
  # report honestly rather than assuming it worked.
  statement {
    sid = "InvalidateCache"
    actions = [
      "cloudfront:CreateInvalidation",
      "cloudfront:GetInvalidation",
      "cloudfront:ListInvalidations",
    ]
    resources = [aws_cloudfront_distribution.web.arn]
  }
}

resource "aws_iam_user_policy" "deployer" {
  name   = "${var.app_name}-deploy"
  user   = aws_iam_user.deployer.name
  policy = data.aws_iam_policy_document.deployer.json
}

resource "aws_iam_access_key" "deployer" {
  count = var.create_deployer_access_key ? 1 : 0
  user  = aws_iam_user.deployer.name
}
