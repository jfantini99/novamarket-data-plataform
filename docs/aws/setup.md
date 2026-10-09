# Setup da AWS (dev)

Objetivo: ter uma conta AWS segura, com alerta de custo, e aplicar o Terraform de `dev`. Custo esperado: centavos por mês. Confira os termos de free tier vigentes no momento do cadastro.

## 1. Criar a conta

1. Crie a conta em aws.amazon.com (exige cartão). Use uma conta **só do laboratório**.
2. Entre como *root* **uma única vez** para: ativar **MFA** no root e ativar "IAM user and role access to Billing information" (Account > Billing preferences).
3. Depois disso **não use mais o root**.

## 2. Criar seu usuário de trabalho

1. IAM > Users > Create user: `joao-lab-admin`, sem console se preferir só CLI.
2. Permissão: `AdministratorAccess` **nesta conta de laboratório** (é quem provisiona a infraestrutura). Os pipelines **não** usam este usuário: eles assumem a role de privilégio mínimo criada pelo Terraform.
3. Ative **MFA** no usuário.
4. Crie uma *access key* (caso de uso: CLI).

## 3. Configurar o profile (os segredos ficam só na sua máquina)

```powershell
aws configure --profile novamarket-dev
# Access Key ID:     (cole)
# Secret Access Key: (cole)
# Default region:    sa-east-1
# Output format:     json
aws sts get-caller-identity --profile novamarket-dev
```

Digite as chaves **diretamente no terminal**. Nunca cole em chat, arquivo do projeto ou Git.

## 4. Alerta de custo (antes de qualquer recurso)

Console > Billing > Budgets > Create budget (Cost budget, mensal, US$ 5, alerta em 50% e 100%). O Terraform também cria um budget se você informar `alert_emails`; use um dos dois para não duplicar.

## 5. Aplicar o Terraform de dev

```powershell
cd infrastructure/terraform/environments/dev
copy terraform.tfvars.example terraform.tfvars   # edite o ARN do seu usuário e o e-mail
terraform init
terraform validate
terraform plan -out tfplan      # leia o que será criado
terraform apply tfplan          # só depois de revisar
```

Será criado: 1 bucket S3, 1 role + 1 policy IAM, 1 log group (retenção 7 dias) e, se informado, 1 budget. Nada cobrado por hora.

## 6. Segredos na nuvem (SSM Parameter Store)

```powershell
aws ssm put-parameter --profile novamarket-dev --name /novamarket/dev/mock-api-key --type SecureString --value "<valor>"
```

A policy do pipeline só lê `/novamarket/dev/*`.

## 7. Usar a role dos pipelines

Em `~/.aws/config`:

```ini
[profile novamarket-pipeline-dev]
role_arn = <output pipeline_role_arn>
source_profile = novamarket-dev
region = sa-east-1
```

Teste: `aws s3 ls s3://<bucket> --profile novamarket-pipeline-dev`.

## 8. Fim de sessão e desligamento

Veja o checklist em `docs/cost-control.md`. Para remover tudo: esvazie o bucket e rode `terraform destroy` (somente com confirmação explícita).
