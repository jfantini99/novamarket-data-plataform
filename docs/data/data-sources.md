# Fontes de dados

Visão de um funcionário novo: o que cada sistema entrega e como acessar. Esta página **não** é exaustiva. Como em qualquer empresa, o dicionário de dados está incompleto e algumas colunas dependem de conversa com o time dono do sistema.

Os dados são sintéticos e ficam em `data/generated/` (gerados por `novamarket data generate`).

## E-commerce API (REST)

Base: `http://localhost:8081` · Header `X-API-Key` (veja `MOCK_API_KEY` no `.env`).

| Endpoint | Conteúdo |
|---|---|
| `GET /ecommerce/v1/customers` | Clientes |
| `GET /ecommerce/v1/orders` | Pedidos |
| `GET /ecommerce/v1/order_items` | Itens dos pedidos |
| `GET /ecommerce/v1/payments` | Pagamentos |

Parâmetros: `updated_since` (ISO-8601), `page`, `page_size` (máx. 1000). A resposta traz `data`, `page`, `next_page`, `total`.

Atenção: a API é compartilhada com outros times e nem sempre está estável. Quem chama deve se proteger.

## Marketing API (REST)

Mesma base e autenticação: `/marketing/v1/{campaigns,impressions,clicks,conversions}`.

## ERP (PostgreSQL)

`localhost:5433`, banco `erp` (credenciais no `.env`).

| Schema.tabela | Conteúdo |
|---|---|
| `erp.products` | Produtos (SKU `NM-000000`) |
| `erp.stores` | Lojas, CDs e a loja virtual |
| `erp.suppliers` | Fornecedores |
| `inventory.stock` | Estoque por loja/produto |

Recarregar o seed: `novamarket data load-erp` (reinicia as tabelas do ERP).

## Logística (arquivos CSV)

Drop diário em `data/generated/logistics/`: `shipments_AAAAMMDD.csv` e `delivery_events_AAAAMMDD.csv`. Os arquivos vêm das transportadoras e do WMS.

## Customer Service (exportações)

`data/generated/customer_service/`: `tickets.csv`, `interactions.jsonl`, `complaints.csv`.

## Relacionamentos principais

```
customer -> order -> order_item -> product (via SKU)
                 \-> payment
order -> shipment -> delivery_event
campaign -> impression -> click -> conversion -> order
order -> ticket -> interaction / complaint
```

## Escalas

| Escala | Pedidos | Uso |
|---|---|---|
| `tiny` | ~2 mil | Testes rápidos |
| `small` | ~100 mil | Padrão do laboratório |
| `medium` | ~600 mil | Problemas de performance |

## Cenários de incidente

O gerador aceita `--inject schema_drift`, `truncated_file` ou `corrupt_records`. Eles ficam desligados no dia a dia e são ativados em tickets/incidentes específicos.
