# Data Quality

Framework simples e extensível. Os checks são **funções Python registradas** e os datasets/checks são **configurados em YAML**.

```powershell
novamarket quality list                      # datasets e quantidade de checks
novamarket quality checks                    # tipos de check disponíveis
novamarket quality run                       # roda tudo
novamarket quality run ecommerce.orders      # roda um dataset
novamarket quality run --only-failures
novamarket quality run --as-of 2026-10-09T06:00:00Z   # referência de "agora" para freshness
```

Sai com **código 1** se algum check com `severity: error` falhar (serve para CI e para DAGs). Cada execução grava um relatório em `data/quality_reports/`.

## Checks embutidos

`not_null`, `unique`, `accepted_values`, `range`, `regex`, `row_count` (volume), `freshness`, `referential_integrity`, `schema`.

Além deles, todo dataset de arquivo ganha um check automático **`readable`**, que conta linhas ilegíveis (JSON inválido, CSV truncado).

## Adicionar um check a um dataset

Em `configs/quality/datasets.yaml`:

```yaml
ecommerce.orders:
  checks:
    - {check: range, column: discount_amount, min: 0, key: order_id}
```

- `severity: warn` informa mas não bloqueia.
- `key` mostra uma coluna identificadora nos exemplos de falha.

## Adicionar um dataset

```yaml
logistics.delivery_events:
  source: {type: csv, path: "data/generated/logistics/delivery_events_*.csv"}
  checks:
    - {check: unique, column: event_id}
```

Fontes: `jsonl`, `csv` (aceitam glob), `postgres` (`query`), `s3` (`prefix`, `format: jsonl|csv`).

## Criar um novo TIPO de check

```python
from novamarket.quality import Outcome, check

@check("positive")
def positive(rows, ctx, column):
    """Valor precisa ser maior que zero."""
    bad = [r for r in rows if r[column] <= 0]
    return Outcome(failed=len(bad), samples=[{column: r[column]} for r in bad[:5]])
```

Coloque a função em `src/novamarket/quality/checks.py` (ou importe seu módulo em `quality/__init__.py`) e use `check: positive` no YAML. Um check que lança exceção vira `status: error` e não derruba os demais.

## Leitura dos resultados

| status | significado |
|---|---|
| `pass` | nenhuma linha falhou |
| `fail` | o dado não atende à regra (veja `falhas/total` e os exemplos) |
| `error` | o próprio check quebrou (config errada, fonte indisponível) |

Um check falhando **não diz a causa**: diz onde olhar.
