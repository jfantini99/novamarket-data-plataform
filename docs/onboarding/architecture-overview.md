# Visão da arquitetura

Resumo; o documento completo é `ARCHITECTURE.md`.

```
Fontes (E-commerce API, Marketing API, ERP, Logística CSV, CX)
        -> Airflow (ingestão) -> S3: raw -> staging -> processed -> curated
                                   |-> quarantine (rejeitados)   |-> archive
        -> (Fase 6) Snowflake: RAW -> STAGING -> CORE -> MART
Transversais: Data Quality (configs/quality), Observabilidade (SLA, métricas), CI (GitHub Actions)
```

Convenções do lake: `docs/architecture/data-lake-conventions.md`.
