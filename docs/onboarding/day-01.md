# Dia 1

Bem-vindo à NovaMarket. Seu objetivo hoje **não é entregar código**: é entender o ambiente.

## Roteiro
1. Leia `docs/company/novamarket-group.md` (a empresa) e `team.md` (as pessoas).
2. Suba o ambiente (`environment-setup.md`) e rode `novamarket environment check`.
3. Abra o Airflow em http://localhost:8080 e o console S3 em http://localhost:9001.
4. Rode `novamarket pipeline status` e `novamarket quality run --only-failures`.
5. Leia `architecture-overview.md` e desenhe, com suas palavras, o caminho de um pedido da API até o lake.
6. Só então abra seu primeiro ticket: `novamarket ticket show NM-001` (ou `/show-ticket NM-001`).

## Perguntas para você responder sozinho antes do ticket
- Quais fontes de dados existem e quem é dono de cada uma?
- Qual DAG existente mais se parece com o que o ticket pede?
- O que pode dar errado numa API compartilhada e instável?
