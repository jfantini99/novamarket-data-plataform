# Ambiente local

## Subir e descer

```powershell
make up      # sobe Postgres (ERP) e S3 local (RustFS)
make ps      # mostra o estado
make down    # desliga (os dados ficam nos volumes)
```

Sem `make` no PATH (terminal novo após instalar resolve), use:
`docker compose --env-file .env -f docker/docker-compose.yml up -d`

## Serviços

| Serviço | Endereço | Credenciais |
|---|---|---|
| Postgres ERP | `localhost:5433`, db `erp` | `.env` (ERP_DB_*) |
| S3 local (API) | `http://localhost:9000` | `.env` (S3_LOCAL_*) |
| S3 local (console) | `http://localhost:9001` | `.env` (S3_LOCAL_*) |

## Python

```powershell
.venv\Scripts\activate
pytest
novamarket version
```

## Observações
- O S3 local tem a mesma API do S3. Código que funciona com `AWS_ENDPOINT_URL=http://localhost:9000` funciona na AWS sem esse endpoint.
- Outro Airflow (projeto antigo) pode estar rodando no seu Docker e usando a porta 8080 e RAM. Pare-o antes da Fase 5.
