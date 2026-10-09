# Arquitetura

Documento vivo. As seções marcadas como *(planejado)* ainda não existem.

## Visão geral

```
FONTES                               INGESTÃO / ORQUESTRAÇÃO        LAKE                    WAREHOUSE
E-commerce API  (REST)   ─┐                                         S3 (RustFS em dev)        Snowflake
ERP PostgreSQL           ─┤                                         raw/                      RAW
Logística CSV            ─┼──►  Airflow + Python  ───────────────►  staging/        ───────►  STAGING
Marketing API            ─┤                                         processed/                CORE
Customer Service         ─┘                                         curated/                  MART
                                                                     quarantine/
Data Quality + Observabilidade (logs JSON, CloudWatch)               archive/
```

## Camadas do lake *(convenções definidas na Fase 4)*

| Camada | Propósito |
|---|---|
| raw | Dado como veio da fonte, imutável |
| staging | Tipado e padronizado |
| processed | Limpo e deduplicado |
| curated | Pronto para consumo |
| quarantine | Registros rejeitados por qualidade |
| archive | Retenção de longo prazo |

Particionamento: `raw/<domain>/<entity>/year=YYYY/month=MM/day=DD/`.

## Camadas do warehouse *(planejado, Fase 6)*

`RAW` → `STAGING` → `CORE` (modelo dimensional) → `MART` (consumo).

## Ambientes

| Ambiente | Estado |
|---|---|
| local | Docker Compose: Postgres, S3 local (RustFS), Airflow e APIs simuladas |
| dev | AWS mínima via Terraform (S3, IAM, CloudWatch, SSM) |
| prod | Preparado arquiteturalmente, não aplicado |

## Decisões

Registradas em `.novamarket/state.yaml` e, quando relevantes, em `docs/architecture/`. Resumo:

- Airflow com `LocalExecutor` em Docker (limite de RAM da máquina).
- Um bucket S3 com prefixos por camada.
- Escala simulada por parâmetro (`NOVAMARKET_DATA_SCALE`).
- Recursos AWS cobrados por hora ficam fora do escopo sem aprovação.
- Segredos fora do Git: variáveis de ambiente, AWS profiles, SSM Parameter Store.

## Preparação para evolução futura

O lake usa formatos e particionamento que permitem uma migração posterior para uma arquitetura baseada em Spark e Delta Lake. Não faz parte do escopo atual.

