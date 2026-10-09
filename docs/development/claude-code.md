# Claude Code no laboratório

O Claude Code atua como Tech Lead: investiga com você, revisa seu trabalho e **não resolve os tickets**.

## Comandos (`.claude/commands/`)
| Comando | Para quê |
|---|---|
| `/show-ticket [ID]` | Ver um ticket e começar a pensar nele |
| `/investigate-incident <ID>` | Triagem e investigação guiada |
| `/debug-pipeline <pipeline>` | Bisseção por camada |
| `/check-data-quality` | Rodar e interpretar os checks |
| `/review-sql <arquivo>` | Revisão de SQL |
| `/review-pipeline <arquivo>` | Revisão de DAG/módulo |
| `/validate-environment` | Checar Docker, portas e ferramentas |

## Skills (`.claude/skills/`)
airflow-debugging, aws-investigation, snowflake-analysis, sql-review, data-quality,
pipeline-debugging, incident-response, data-engineering-review. Todas seguem a regra:
investigar antes de propor, e nunca ler `.novamarket/_sealed/`.

## CLI
`novamarket ticket list|show`, `novamarket incident show`, `novamarket environment check`,
`novamarket pipeline status`, `novamarket quality run`.
Os tickets e incidentes passam a existir na Fase 11 (`tickets/*.yaml`, `incidents/*.yaml`).
