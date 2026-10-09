# Terraform

Infraestrutura da NovaMarket organizada por módulos e ambientes.

```
modules/
  s3/          bucket do data lake (versionamento, criptografia, lifecycle, camadas)
  iam/         role e policy de privilégio mínimo para os pipelines
  monitoring/  log group (retenção curta) e budget com alertas de custo
  networking/  VPC sem NAT  (módulo de estudo, não usado em dev)
  rds/         PostgreSQL gerenciado (módulo de estudo, NÃO APLICAR: cobra por hora)
environments/
  dev/         o único ambiente aplicável
  prod/        preparado, travado por `confirm_prod`
```

## Regras

1. `terraform plan` primeiro, sempre. Leia o plano antes do `apply`.
2. `apply` e `destroy` só com confirmação explícita (veja `docs/cost-control.md`).
3. `terraform.tfvars` e o state **não vão para o Git**.
4. Em dev, networking e rds não entram, por custo.

## Fluxo seguro (a partir da conta AWS criada)

```powershell
cd infrastructure/terraform/environments/dev
terraform init
terraform validate
terraform plan -out tfplan      # leia
terraform apply tfplan          # só depois de revisar
```

O passo a passo de conta, usuário, profile e alerta de orçamento está em `docs/aws/setup.md`.
