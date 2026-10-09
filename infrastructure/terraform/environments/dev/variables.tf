variable "aws_profile" {
  description = "Profile do AWS CLI usado pelo Terraform."
  type        = string
  default     = "novamarket-dev"
}

variable "region" {
  type    = string
  default = "sa-east-1"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "trusted_principal_arns" {
  description = "ARNs que podem assumir a role do pipeline (ex.: seu usuário IAM)."
  type        = list(string)
}

variable "alert_emails" {
  description = "E-mails para alertas de custo."
  type        = list(string)
  default     = []
}

variable "monthly_budget_usd" {
  type    = number
  default = 5
}
