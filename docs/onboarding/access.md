# Acessos

| Sistema | Onde | Credenciais |
|---|---|---|
| Airflow | http://localhost:8080 | usuário `admin`; senha `AIRFLOW_ADMIN_PASSWORD` no `.env` |
| S3 local (console) | http://localhost:9001 | `S3_LOCAL_*` no `.env` |
| APIs mock | http://localhost:8081 | header `X-API-Key` = `MOCK_API_KEY` |
| ERP | localhost:5433 | `ERP_DB_*` no `.env` |
| AWS real | profile `novamarket-dev` | você cria (veja `docs/aws/setup.md`) |
| Snowflake | Fase 6 | trial criado depois |

O `.env` nunca vai para o Git. Gere o seu a partir de `.env.example`.
