provider "aws" {
  region  = var.region
  profile = var.aws_profile

  default_tags {
    tags = {
      Project     = "novamarket"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

data "aws_caller_identity" "current" {}

locals {
  bucket_name = "novamarket-data-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

module "monitoring" {
  source             = "../../modules/monitoring"
  environment        = var.environment
  monthly_budget_usd = var.monthly_budget_usd
  alert_emails       = var.alert_emails
}

module "s3" {
  source = "../../modules/s3"

  bucket_name        = local.bucket_name
  raw_retention_days = 60 # dev: limita custo
}

module "iam" {
  source = "../../modules/iam"

  environment            = var.environment
  region                 = var.region
  account_id             = data.aws_caller_identity.current.account_id
  bucket_arn             = module.s3.bucket_arn
  log_group_arn          = module.monitoring.log_group_arn
  trusted_principal_arns = var.trusted_principal_arns
}

# NÃO incluídos de propósito em dev (custo por hora): módulos networking e rds.
