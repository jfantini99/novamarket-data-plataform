# Como contribuir

## Fluxo de trabalho

```
Ticket → Branch → Implementação → Testes → Commit → Pull Request → Code Review → Correções → Merge
```

Nenhum trabalho começa sem ticket. Nenhum merge acontece sem review.

## Branches

| Prefixo | Uso |
|---|---|
| `feature/NM-123-descricao-curta` | Nova funcionalidade |
| `bugfix/NM-123-descricao-curta` | Correção não urgente |
| `hotfix/INC-001-descricao-curta` | Correção urgente em produção |

`main` é protegida: só recebe merge via PR.

## Commits

Formato: `tipo(escopo): descrição no imperativo, em inglês`, com o ticket no corpo.

```
fix(orders): deduplicate by order_id before load

Refs NM-042
```

Tipos: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`.

## Pull Request

Título: `[NM-123] Descrição`. O corpo deve ter:

- **O quê e por quê**
- **Como testar** (comandos)
- **Riscos / impacto** (dados, custo, SLA)
- **Checklist:** testes, idempotência, logs, docs, sem segredos

## Code Review

Severidades: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`. CRITICAL e HIGH bloqueiam o merge. O revisor não corrige por você.

## Regras de qualidade

- Pipelines idempotentes (rodar duas vezes não duplica).
- Teste para o que você alterou.
- Logs estruturados e mensagens de erro úteis.
- Sem segredos no código ou no histórico.
- Mudanças de schema e SQL documentadas.

## Segurança e custo

- Não rode `terraform apply/destroy` sem revisar o plano.
- Não crie recursos cobrados por hora sem aprovação (ver [custos](docs/cost-control.md)).
