# NovaMarket Data Platform - alvos de desenvolvimento.
# Fase 1: apenas esqueleto. Cada alvo ganha implementacao na fase indicada.
# No Windows sem `make`, use o equivalente `novamarket ...` (Fase 10) ou instale: winget install GnuWin32.Make

.PHONY: help up down test lint quality airflow generate-data validate

help:            ## Lista os alvos
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/ -/'

COMPOSE = docker compose --env-file .env -f docker/docker-compose.yml

up:              ## Sobe o ambiente local (Postgres ERP + MinIO)
	$(COMPOSE) up -d

down:            ## Derruba o ambiente local (mantém os dados)
	$(COMPOSE) down

ps:              ## Mostra o estado dos containers
	$(COMPOSE) ps

test:            ## Roda pytest
	.venv/Scripts/python -m pytest

lint:            ## Roda ruff (Fase 9)
	@echo "TODO Fase 9: ruff check ."

quality:         ## Roda checks de Data Quality (Fase 7)
	@echo "TODO Fase 7: novamarket quality run"

airflow:         ## Abre/inicializa o Airflow (Fase 5)
	@echo "TODO Fase 5"

generate-data:   ## Gera dados sinteticos e carrega o ERP
	.venv/Scripts/novamarket data generate --scale small
	.venv/Scripts/novamarket data load-erp

validate:        ## Valida o ambiente completo (Fase 12)
	@echo "TODO Fase 12: novamarket environment check"
