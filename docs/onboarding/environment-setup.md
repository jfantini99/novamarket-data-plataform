# Preparando o ambiente

Detalhes completos: `docs/development/local-environment.md`.

```powershell
make up                 # Postgres, S3 local, APIs mock
make airflow            # Airflow (usa ~3 GB de RAM)
novamarket environment check
make test
```

Pare tudo quando não estiver usando: `make down`.
Dados sintéticos: `novamarket data generate` e `novamarket data load-erp`.
