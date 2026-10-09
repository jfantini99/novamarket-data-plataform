# NovaMarket Data Platform

Laboratório corporativo de Engenharia de Dados. Você é **João Victor, Junior Data Engineer** no time **Data Platform** da **NovaMarket Group**, squad **Sales Data**.

Este repositório é o ambiente de trabalho: código, infraestrutura, tickets, incidentes e documentação.

## Por onde começar

1. [Contexto da empresa](docs/company/novamarket-group.md)
2. [Pessoas](docs/company/people.md)
3. [Arquitetura](ARCHITECTURE.md)
4. [Como contribuir](CONTRIBUTING.md)
5. [Controle de custos](docs/cost-control.md)

O onboarding completo (`docs/onboarding/`) é criado ao final da implementação.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `airflow/` | DAGs e plugins |
| `aws/` | Scripts e políticas auxiliares da AWS |
| `data/` | Seeds e dados gerados |
| `docs/` | Documentação |
| `docker/` | Dockerfiles e compose |
| `incidents/` | Incidentes (sem a causa raiz) |
| `infrastructure/` | Terraform (módulos e ambientes) |
| `runbooks/` | Procedimentos operacionais |
| `scripts/`, `tools/` | Utilitários |
| `sql/` | DDL e transformações por camada |
| `src/novamarket/` | Código Python e CLI |
| `tickets/` | Backlog |
| `tests/` | unit, integration, data |
| `.claude/` | Skills e comandos do Claude Code |
| `.novamarket/` | Estado do laboratório |

## Configuração

Copie `.env.example` para `.env`. **Nunca** commite segredos. Detalhes de acesso virão em `docs/onboarding/access.md`.

## Status

Veja `.novamarket/state.yaml`. Fase atual: **1 – Estrutura do repositório**.
