# NovaMarket Data Platform - alvos de desenvolvimento.
# Fase 1: apenas esqueleto. Cada alvo ganha implementacao na fase indicada.
# No Windows sem `make`, use o equivalente `novamarket ...` (Fase 10) ou instale: winget install GnuWin32.Make

.PHONY: help up down test lint quality airflow generate-data validate

help:            ## Lista os alvos
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/ -/'

COMPOSE = docker compose --env-file .env -f docker/docker-compose.yml

up:              ## Sobe o ambiente local (Postgres ERP + S3 local)
	$(COMPOSE) up -d

down:            ## Derruba o ambiente local (mantém os dados)
	$(COMPOSE) down

ps:              ## Mostra o estado dos containers
	$(COMPOSE) ps

test:            ## Roda pytest
	.venv/Scripts/python -m pytest

lint:            ## Roda ruff e sqlfluff
	.venv/Scripts/python -m ruff check .
	.venv/Scripts/python -m sqlfluff lint sql docker/postgres/init

quality:         ## Roda os checks de Data Quality
	.venv/Scripts/novamarket quality run

airflow:         ## Mostra o estado do Airflow e a URL
	@docker ps --filter name=nm-airflow --format "{{.Names}}  {{.Status}}"
	@echo "UI: http://localhost:8080  (usuario admin; senha em AIRFLOW_ADMIN_PASSWORD no .env)"

generate-data:   ## Gera dados sinteticos e carrega o ERP
	.venv/Scripts/novamarket data generate --scale small
	.venv/Scripts/novamarket data load-erp

validate:        ## Valida o ambiente completo (lint, testes, servicos, config)
	@echo "== 1/5 lint" && $(MAKE) --no-print-directory lint
	@echo "== 2/5 ambiente" && .venv/Scripts/novamarket environment check
	@echo "== 3/5 testes (unitarios + integracao)" && .venv/Scripts/python -m pytest -q
	@echo "== 4/5 config" && $(COMPOSE) config -q && .venv/Scripts/novamarket quality list > /dev/null && .venv/Scripts/novamarket ticket list
	@echo "== 5/5 pipelines" && .venv/Scripts/novamarket pipeline status
	@echo "VALIDACAO OK"
