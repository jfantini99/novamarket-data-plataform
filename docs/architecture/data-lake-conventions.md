# Convenções do Data Lake

Bucket: `novamarket-data-<env>-<account_id>` (em dev local: `novamarket-data-dev-local`).

## Camadas

| Camada | O que contém | Regra |
|---|---|---|
| `raw/` | Dado exatamente como veio da fonte | Imutável. Nunca corrigir aqui. |
| `staging/` | Tipado e padronizado, mesmo grão da fonte | Pode ser recriado a partir do raw. |
| `processed/` | Limpo, deduplicado, regras de negócio aplicadas | |
| `curated/` | Pronto para consumo (marts, features) | Contrato estável. |
| `quarantine/` | Registros rejeitados por Data Quality | Com motivo da rejeição. Expira em 30 dias (dev). |
| `archive/` | Retenção longa | Ninguém apaga (a policy bloqueia delete). |

## Caminho

```
<camada>/<domínio>/<entidade>/year=YYYY/month=MM/day=DD/<arquivo>
```

Exemplos: `raw/inventory/products/year=2026/month=10/day=08/products_20261008.csv`

## Nomes

- Domínios: `sales`, `inventory`, `logistics`, `marketing`, `customer_service`, em minúsculas.
- Entidades: plural, `snake_case` (`order_items`).
- Arquivos de **snapshot ou janela fixa**: `<entidade>_<AAAAMMDD>.<ext>`. O nome é determinístico, então reexecutar o mesmo dia sobrescreve o mesmo arquivo (idempotente).
- Cargas que não têm janela fixa (ex.: eventos sob demanda): `<entidade>_<timestamp UTC compacto>_<run_id>.<ext>`, para rastrear cada execução.

## Datas

- A partição `year/month/day` usa a **data de negócio em UTC** do registro (ou da janela de ingestão no raw), documentada por entidade.
- Timestamps nos arquivos: manter o original no raw; padronizar para UTC no staging.

## Versionamento

- O bucket tem versionamento ligado; versões antigas expiram em 30 dias.
- Reprocessar escreve em um novo `run_id` e substitui a partição de forma controlada, nunca no append cego.

## Formatos

- raw: o formato da fonte (JSONL/CSV).
- staging em diante: Parquet comprimido, porque é colunar e leva bem a uma evolução futura da plataforma.
