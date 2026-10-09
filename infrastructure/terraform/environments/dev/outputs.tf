output "bucket_name" {
  value = module.s3.bucket_name
}

output "pipeline_role_arn" {
  value = module.iam.role_arn
}

output "log_group_name" {
  value = module.monitoring.log_group_name
}
