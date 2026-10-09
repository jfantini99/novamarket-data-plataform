variable "confirm_prod" {
  description = "Trava de segurança: PROD está só preparado. Para aplicar, defina exatamente 'I-ACCEPT-PROD-COSTS'."
  type        = string
  default     = "no"
  validation {
    condition     = var.confirm_prod == "I-ACCEPT-PROD-COSTS"
    error_message = "PROD está apenas preparado arquiteturalmente e não deve ser aplicado sem aprovação explícita."
  }
}

variable "aws_profile" {
  type    = string
  default = "novamarket-prod"
}

variable "region" {
  type    = string
  default = "sa-east-1"
}

variable "environment" {
  type    = string
  default = "prod"
}

variable "trusted_principal_arns" {
  type = list(string)
}

variable "alert_emails" {
  type    = list(string)
  default = []
}

variable "monthly_budget_usd" {
  type    = number
  default = 50
}
