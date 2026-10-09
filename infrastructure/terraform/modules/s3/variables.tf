variable "bucket_name" {
  description = "Nome globalmente único do bucket do data lake."
  type        = string
}

variable "layers" {
  description = "Camadas do data lake (prefixos de primeiro nível)."
  type        = list(string)
  default     = ["raw", "staging", "processed", "curated", "quarantine", "archive"]
}

variable "force_destroy" {
  description = "Permite destruir o bucket mesmo com objetos. Mantenha false."
  type        = bool
  default     = false
}

variable "quarantine_retention_days" {
  description = "Dias até expirar objetos em quarantine/."
  type        = number
  default     = 30
}

variable "noncurrent_retention_days" {
  description = "Dias até expirar versões antigas de objetos."
  type        = number
  default     = 30
}

variable "raw_retention_days" {
  description = "Dias até expirar raw/ (0 desliga). Em dev, use um valor baixo para limitar custo."
  type        = number
  default     = 0
}
