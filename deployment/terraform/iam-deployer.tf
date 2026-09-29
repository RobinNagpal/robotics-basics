# CI deploy user for GitHub Actions, scoped to exactly what a deploy does to
# AWS: write the docs bucket, and read it back. It can touch nothing else in
# the account.
#
# The other half of a deploy uses no AWS credentials at all. Getting the files
# onto the shared host is an rsync over SSH, authorised by the SSH_PRIVATE_KEY
# secret that the shared-host stack issues — which is why this policy has no
# Lightsail permissions in it, and why nothing here can disturb the two other
# applications on that box.
resource "aws_iam_user" "deployer" {
  name = "${var.app_name}-deployer"
  path = "/${var.app_name}/"

  # Empty means no boundary; see the variable for why this stack does not
  # require one where courtpot's does.
  permissions_boundary = var.permissions_boundary_arn != "" ? var.permissions_boundary_arn : null
}

data "aws_iam_policy_document" "deployer" {
  # ListBucket is on the bucket itself rather than its contents, and `aws s3
  # sync` needs it: without it the sync cannot see what is already there and
  # has nothing to compare against, so it uploads everything every time.
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
