resource "aws_s3_bucket" "this" {
  bucket        = var.bucket_name
  force_destroy = var.force_destroy # false por padrão: destruir exige esvaziar o bucket antes
}

resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "this" {
  bucket                  = aws_s3_bucket.this.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Controle de custo: limpa o que não precisa ficar.
resource "aws_s3_bucket_lifecycle_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    id     = "abort-incomplete-multipart"
    status = "Enabled"
    filter {}
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  rule {
    id     = "expire-noncurrent-versions"
    status = "Enabled"
    filter {}
    noncurrent_version_expiration {
      noncurrent_days = var.noncurrent_retention_days
    }
  }

  rule {
    id     = "expire-quarantine"
    status = "Enabled"
    filter {
      prefix = "quarantine/"
    }
    expiration {
      days = var.quarantine_retention_days
    }
  }

  dynamic "rule" {
    for_each = var.raw_retention_days > 0 ? [1] : []
    content {
      id     = "expire-raw"
      status = "Enabled"
      filter {
        prefix = "raw/"
      }
      expiration {
        days = var.raw_retention_days
      }
    }
  }

  depends_on = [aws_s3_bucket_versioning.this]
}

# Camadas do data lake (prefixos vazios que documentam a estrutura).
resource "aws_s3_object" "layers" {
  for_each = toset(var.layers)
  bucket   = aws_s3_bucket.this.id
  key      = "${each.key}/"
  content  = ""
}
