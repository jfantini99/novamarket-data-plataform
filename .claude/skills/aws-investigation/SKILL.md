---
name: aws-investigation
description: Investigar problemas com S3/IAM/CloudWatch (local RustFS ou AWS real) sem alterar recursos. Use para objetos ausentes, AccessDenied ou custo.
---

# aws-investigation

**Regra do laboratório:** o engenheiro (João Victor) resolve o ticket. Investigue, faça perguntas, dê dicas graduais e revise. NÃO entregue a solução pronta nem leia `.novamarket/_sealed/` (causas raiz seladas), a menos que o engenheiro peça explicitamente a solução completa para estudo.

## Roteiro
1. Ambiente: local usa `AWS_ENDPOINT_URL=http://localhost:9000`; AWS real usa o profile `novamarket-dev`. Confirme qual.
2. Objetos: `aws s3 ls s3://<bucket>/<layer>/<domain>/<entity>/ --recursive` (adicione `--endpoint-url` no local). Confira o padrão `year=/month=/day=` e `<entity>_<YYYYMMDD>.<ext>`.
3. Permissões: leia `infrastructure/terraform/modules/iam` (há deny de delete em `archive/`). `aws sts get-caller-identity` mostra quem está agindo.
4. Logs: grupo `NOVAMARKET_CLOUDWATCH_LOG_GROUP`; apenas leitura.
5. Custo: `docs/cost-control.md`; nunca criar RDS/NAT/ECS sem aprovação.

## Proibido sem confirmação explícita
`terraform apply`, delete de objetos, mudanças de IAM. Apenas leitura por padrão.
