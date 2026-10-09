# Controle de Custos

**Meta:** manter o laboratório inteiro abaixo de R$ 50. Idealmente perto de zero.

## Regras

1. Nenhum `terraform apply` sem revisar o `plan` e saber o que cobra.
2. Nenhum recurso cobrado por hora (RDS, NAT Gateway, EC2, ECS) sem aprovação explícita.
3. Billing alarm / AWS Budget configurado **antes** de criar qualquer recurso real (Fase 4).
4. Snowflake: warehouse XS, `AUTO_SUSPEND = 60`, resource monitor com limite de créditos.
5. Segredos em SSM Parameter Store (gratuito), não em Secrets Manager (cobra por segredo).

## Onde está o custo (e o que fazer)

| Serviço | Tratamento |
|---|---|
| S3 | Um bucket, lifecycle para expirar dados de teste. Centavos. |
| IAM | Grátis. |
| CloudWatch | Retenção de logs de 7 dias. |
| RDS | **Não aplicar.** Módulo existe só para estudo; Postgres local cobre o ERP. |
| VPC/NAT/ECS | **Não aplicar.** |
| Snowflake | Trial gratuito (verificar no cadastro). Criar só na Fase 6. |

## Checklist de fim de sessão (Fase 4+)

- [ ] Console AWS > Billing: custo do mês corrente
- [ ] `aws ec2 describe-instances` / `aws rds describe-db-instances`: nada rodando
- [ ] Snowflake: warehouses suspensos
- [ ] Docker local parado (`make down`) se não estiver usando

## Como desligar tudo

`terraform destroy` em `infrastructure/terraform/environments/dev`. **Só com confirmação explícita.**

