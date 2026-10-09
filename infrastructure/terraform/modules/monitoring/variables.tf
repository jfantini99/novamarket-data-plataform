variable "environment" {
  type = string
}

variable "log_retention_days" {
  type    = number
  default = 7
}

variable "monthly_budget_usd" {
  description = "Orçamento mensal em USD que dispara alertas."
  type        = number
  default     = 5
}

variable "alert_emails" {
  description = "E-mails que recebem alertas de custo. Vazio = sem budget."
  type        = list(string)
  default     = []
}
