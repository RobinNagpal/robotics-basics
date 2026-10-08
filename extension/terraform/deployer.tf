# CI uploads the API's code as the docs site's deployer user. This policy lets
# that user replace the code of this one function and wait for the update, and
# change nothing else about it.
data "aws_iam_policy_document" "deployer" {
  statement {
    actions = [
      "lambda:UpdateFunctionCode",
      "lambda:GetFunction",
      "lambda:GetFunctionConfiguration",
    ]
    resources = [aws_lambda_function.feedback_api.arn]
  }
}

resource "aws_iam_user_policy" "deployer" {
  name   = "${var.app_name}-feedback-api-deploy"
  user   = var.deployer_user
  policy = data.aws_iam_policy_document.deployer.json
}
