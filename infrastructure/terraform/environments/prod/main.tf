# PROD: preparado arquiteturalmente, NÃO aplicado. Mesma composição de dev, com valores de prod.
# A variável confirm_prod impede um apply acidental (a validação falha por padrão).

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
  log_retention_days = 90
  monthly_budget_usd = var.monthly_budget_usd
  alert_emails       = var.alert_emails
}

module "s3" {
  source = "../../modules/s3"

  bucket_name               = local.bucket_name
  raw_retention_days        = 0 # prod não expira raw automaticamente
  quarantine_retention_days = 90
  noncurrent_retention_days = 90
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
