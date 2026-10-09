# NovaMarket Group

Varejo omnichannel com operação na América Latina. Fundada em 1998 em Campinas (SP) como rede regional de eletrodomésticos; hoje vende moda, casa, eletrônicos, supermercado e marketplace.

## Números (aproximados, 2026)

| Item | Valor |
|---|---|
| Funcionários | ~42.000 (Tecnologia: ~1.100; Dados: ~140) |
| Países | Brasil, México, Colômbia, Chile, Argentina |
| Lojas físicas | ~680 (Brasil 420, México 120, Colômbia 60, Chile 45, Argentina 35) |
| Centros de distribuição | 14 |
| Clientes ativos (12 meses) | ~18 milhões (programa de fidelidade "Nova+": ~11 milhões) |
| Pedidos | ~2,3 milhões/dia em média; pico de ~7 milhões na Black Friday |
| Itens de pedido | ~40 milhões de registros/dia somando todos os canais e eventos |
| Produtos (SKUs ativos) | ~450 mil |
| Fornecedores | ~6.500 |
| Receita anual | ~R$ 38 bilhões |

> **Escala do laboratório:** estes números são a história da empresa. O ambiente local roda amostras (`NOVAMARKET_DATA_SCALE=tiny|small|medium`), mantendo proporções, relacionamentos e defeitos realistas.

## Canais

Lojas físicas · E-commerce · App (iOS/Android) · Marketplace (vendedores terceiros) · Televendas.

## Departamentos

Technology · Data · Analytics · Finance · Marketing · Operations · Logistics · Customer Experience · Security · Infrastructure

## Times de dados

| Time | Foco |
|---|---|
| Data Platform | Plataforma, ingestão, orquestração, infra de dados (**seu time**) |
| Data Engineering | Pipelines de domínio |
| Analytics Engineering | Modelagem e marts |
| BI | Dashboards e relatórios |
| Data Science | Modelos analíticos |
| ML Engineering | Produtivização de modelos |
| Data Governance | Qualidade, catálogo, políticas, LGPD |

O Data Platform é dividido em squads por domínio. Seu squad: **Sales Data**.

## Sistemas de origem

| Sistema | Tecnologia | Dono | Observações |
|---|---|---|---|
| E-commerce API | REST (JSON) | Time E-commerce | Customers, orders, order_items, payments. Instável em picos. |
| ERP | PostgreSQL | TI Corporativa | Products, stores, suppliers, inventory. Sistema antigo, nomes inconsistentes. |
| Logística | CSV via drop de arquivos | Logistics | Shipments, delivery_events. Arquivos às vezes chegam incompletos. |
| Marketing API | REST (JSON) | Marketing | Campaigns, clicks, impressions, conversions. |
| Customer Service | Exportações JSON/CSV | CX | Tickets, interactions, complaints. |

## Contexto da plataforma de dados

- Data Lake em S3 (raw/staging/processed/curated/quarantine/archive).
- Airflow para orquestração, Python para ingestão e transformação.
- Snowflake como Data Warehouse principal (RAW → STAGING → CORE → MART).
- Dívida técnica conhecida: pipelines herdados com pouca documentação, nomenclatura inconsistente entre ERP e e-commerce, e processos manuais de reprocessamento.
- Existe uma discussão de longo prazo na diretoria sobre modernização da plataforma. Ainda não é prioridade.
