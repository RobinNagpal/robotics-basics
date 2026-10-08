# The feedback worker runs on a machine of ours, not in AWS: it drives Claude Code
# in a clone of this repository. It needs to read the comments and write back
# each one's status and Claude's response, and nothing else. So it gets its own
# IAM user, limited to the feedback bucket, instead of an administrator's keys.
resource "aws_iam_user" "feedback_worker" {
  name = "${var.app_name}-feedback-worker"
  path = "/${var.app_name}/"
}

data "aws_iam_policy_document" "feedback_worker" {
  statement {
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.feedback.arn]
  }

  statement {
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = ["${aws_s3_bucket.feedback.arn}/*"]
  }
}

resource "aws_iam_user_policy" "feedback_worker" {
  name   = "${var.app_name}-feedback-worker"
  user   = aws_iam_user.feedback_worker.name
  policy = data.aws_iam_policy_document.feedback_worker.json
}

# The key is kept in the Terraform state, which is in a private, encrypted
# bucket. Copy it into extension/worker/.env with the commands in the README.
resource "aws_iam_access_key" "feedback_worker" {
  user = aws_iam_user.feedback_worker.name
}
