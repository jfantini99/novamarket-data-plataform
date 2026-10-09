variable "environment" {
  type = string
}

variable "region" {
  type = string
}

variable "account_id" {
  type = string
}

variable "bucket_arn" {
  type = string
}

variable "log_group_arn" {
  type = string
}

variable "trusted_principal_arns" {
  description = "Quem pode assumir a role (ex.: ARN do seu usuário IAM)."
  type        = list(string)
  validation {
    condition     = length(var.trusted_principal_arns) > 0
    error_message = "Informe ao menos um principal confiável."
  }
}
