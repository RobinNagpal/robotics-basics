# The feedback API: the server behind the highlighter extension in extension/.
#
# Readers select text on the docs, comment on it, and the extension sends the
# comments here. They are kept as one JSON file per docs page in a private
# bucket, which is where Claude reads them from to work on the docs.
#
# The API is one Lambda function with a function URL. Terraform owns the
# function's settings; the code is uploaded by
# .github/workflows/deploy-feedback-api.yml, so Terraform starts it with a
# placeholder and then leaves the code alone.

resource "aws_s3_bucket" "feedback" {
  bucket = "${var.app_name}-feedback-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_public_access_block" "feedback" {
  bucket = aws_s3_bucket.feedback.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# The comments are written by people and exist nowhere else, so every earlier
# version of a page file is kept. A bad sync can then be undone.
resource "aws_s3_bucket_versioning" "feedback" {
  bucket = aws_s3_bucket.feedback.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "feedback" {
  bucket = aws_s3_bucket.feedback.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# The API keys, as JSON: {"<name>": "<key>", ...}. Terraform creates the
# parameter empty and never reads the value back, so the keys stay out of the
# Terraform state. Set them with `aws ssm put-parameter`; see ../README.md.
resource "aws_ssm_parameter" "feedback_api_keys" {
  name  = "/${var.app_name}/feedback-api-keys"
  type  = "SecureString"
  value = "{}"

  lifecycle {
    ignore_changes = [value]
  }
}

data "aws_iam_policy_document" "feedback_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "feedback_api" {
  name               = "${var.app_name}-feedback-api"
  assume_role_policy = data.aws_iam_policy_document.feedback_assume.json
}

resource "aws_iam_role_policy_attachment" "feedback_api_logs" {
  role       = aws_iam_role.feedback_api.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# The function can read and write the feedback bucket and read the keys. The
# keys parameter is encrypted with the AWS-managed SSM key, which SSM decrypts
# for any caller allowed to read the parameter.
data "aws_iam_policy_document" "feedback_api" {
  statement {
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.feedback.arn]
  }

  statement {
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = ["${aws_s3_bucket.feedback.arn}/*"]
  }

  statement {
    actions   = ["ssm:GetParameter"]
    resources = [aws_ssm_parameter.feedback_api_keys.arn]
  }
}

resource "aws_iam_role_policy" "feedback_api" {
  name   = "${var.app_name}-feedback-api"
  role   = aws_iam_role.feedback_api.id
  policy = data.aws_iam_policy_document.feedback_api.json
}

resource "aws_cloudwatch_log_group" "feedback_api" {
  name              = "/aws/lambda/${var.app_name}-feedback-api"
  retention_in_days = 30
}

# A stand-in so the function can be created before CI has built anything.
data "archive_file" "feedback_placeholder" {
  type        = "zip"
  output_path = "${path.module}/.feedback-placeholder.zip"

  source {
    filename = "index.mjs"
    content  = "export const handler = async () => ({ statusCode: 503, body: 'Not deployed yet' });"
  }
}

resource "aws_lambda_function" "feedback_api" {
  function_name = "${var.app_name}-feedback-api"
  role          = aws_iam_role.feedback_api.arn
  runtime       = "nodejs22.x"
  architectures = ["arm64"]
  handler       = "index.handler"
  memory_size   = 512
  timeout       = 15
  filename      = data.archive_file.feedback_placeholder.output_path

  environment {
    variables = {
      FEEDBACK_BUCKET = aws_s3_bucket.feedback.bucket
      API_KEYS_PARAM  = aws_ssm_parameter.feedback_api_keys.name
    }
  }

  # CI uploads the real code. Without this, the next apply would put the
  # placeholder back.
  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }

  depends_on = [aws_cloudwatch_log_group.feedback_api, aws_iam_role_policy_attachment.feedback_api_logs]
}

# A function URL gives the function its own HTTPS address. Anyone can reach it;
# the function itself turns away any request without a known API key.
resource "aws_lambda_function_url" "feedback_api" {
  function_name      = aws_lambda_function.feedback_api.function_name
  authorization_type = "NONE"
}
