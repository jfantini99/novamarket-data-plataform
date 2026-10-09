data "aws_iam_policy_document" "pipeline" {
  statement {
    sid       = "ListLake"
    actions   = ["s3:ListBucket", "s3:GetBucketLocation"]
    resources = [var.bucket_arn]
  }

  statement {
    sid       = "ReadWriteLake"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = ["${var.bucket_arn}/*"]
  }

  # Ninguém apaga o archive por acidente: o deny vence o allow acima.
  statement {
    sid       = "ProtectArchive"
    effect    = "Deny"
    actions   = ["s3:DeleteObject", "s3:DeleteObjectVersion"]
    resources = ["${var.bucket_arn}/archive/*"]
  }

  statement {
    sid       = "ReadOwnParameters"
    actions   = ["ssm:GetParameter", "ssm:GetParameters", "ssm:GetParametersByPath"]
    resources = ["arn:aws:ssm:${var.region}:${var.account_id}:parameter/novamarket/${var.environment}/*"]
  }

  statement {
    sid       = "WriteLogs"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents", "logs:DescribeLogStreams"]
    resources = [var.log_group_arn, "${var.log_group_arn}:*"]
  }
}

resource "aws_iam_policy" "pipeline" {
  name   = "novamarket-pipeline-${var.environment}"
  policy = data.aws_iam_policy_document.pipeline.json
}

# O engenheiro (ou o Airflow) assume esta role em vez de usar permissões diretas.
data "aws_iam_policy_document" "trust" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "AWS"
      identifiers = var.trusted_principal_arns
    }
  }
}

resource "aws_iam_role" "pipeline" {
  name                 = "novamarket-pipeline-${var.environment}"
  assume_role_policy   = data.aws_iam_policy_document.trust.json
  max_session_duration = 3600
}

resource "aws_iam_role_policy_attachment" "pipeline" {
  role       = aws_iam_role.pipeline.name
  policy_arn = aws_iam_policy.pipeline.arn
}
