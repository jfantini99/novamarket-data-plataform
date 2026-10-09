output "role_arn" {
  value = aws_iam_role.pipeline.arn
}

output "policy_arn" {
  value = aws_iam_policy.pipeline.arn
}
