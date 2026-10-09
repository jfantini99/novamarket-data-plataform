resource "aws_cloudwatch_log_group" "pipelines" {
  name              = "/novamarket/${var.environment}/pipelines"
  retention_in_days = var.log_retention_days # retenção curta = custo baixo
}

# Alerta de custo. O AWS Budgets tem os 2 primeiros orçamentos gratuitos.
resource "aws_budgets_budget" "monthly" {
  count        = length(var.alert_emails) > 0 ? 1 : 0
  name         = "novamarket-${var.environment}-monthly"
  budget_type  = "COST"
  limit_amount = tostring(var.monthly_budget_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 50
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = var.alert_emails
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = var.alert_emails
  }
}
