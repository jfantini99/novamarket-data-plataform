# MÓDULO DE ESTUDO. NÃO APLICAR em dev: RDS cobra por hora mesmo parado (~US$ 15/mês no menor tipo).
# O ERP do laboratório roda em PostgreSQL local (Docker). Só aplique com aprovação explícita.

resource "aws_db_subnet_group" "this" {
  name       = "novamarket-${var.environment}"
  subnet_ids = var.subnet_ids
}

resource "aws_security_group" "db" {
  name_prefix = "novamarket-${var.environment}-db-"
  vpc_id      = var.vpc_id

  ingress {
    description     = "PostgreSQL somente dos security groups autorizados"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = var.allowed_security_group_ids
  }
}

resource "aws_db_instance" "this" {
  identifier        = "novamarket-${var.environment}-erp"
  engine            = "postgres"
  engine_version    = var.engine_version
  instance_class    = var.instance_class
  allocated_storage = var.allocated_storage_gb
  storage_encrypted = true

  db_name  = "erp"
  username = "erp_admin"
  # A senha é gerada e guardada no Secrets Manager pela AWS: nunca entra no código nem no state.
  manage_master_user_password = true

  db_subnet_group_name    = aws_db_subnet_group.this.name
  vpc_security_group_ids  = [aws_security_group.db.id]
  publicly_accessible     = false
  multi_az                = false
  backup_retention_period = 1
  skip_final_snapshot     = var.skip_final_snapshot
  deletion_protection     = var.deletion_protection
}
