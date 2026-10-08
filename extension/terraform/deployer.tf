# CI deploys as the docs site's deployer user. This policy lets that user
# replace the code of the API function, write the install page's bucket, and
# flush the install page's cache, and change nothing else about any of them.
data "aws_iam_policy_document" "deployer" {
  statement {
    actions = [
      "lambda:UpdateFunctionCode",
      "lambda:GetFunction",
      "lambda:GetFunctionConfiguration",
    ]
    resources = [aws_lambda_function.feedback_api.arn]
  }

  # ListBucket lets `aws s3 sync` see what is already there.
  statement {
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.install.arn]
  }

  statement {
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = ["${aws_s3_bucket.install.arn}/*"]
  }

  statement {
    actions   = ["cloudfront:CreateInvalidation", "cloudfront:GetInvalidation"]
    resources = [aws_cloudfront_distribution.install.arn]
  }
}

resource "aws_iam_user_policy" "deployer" {
  name   = "${var.app_name}-feedback-api-deploy"
  user   = var.deployer_user
  policy = data.aws_iam_policy_document.deployer.json
}
