---
name: sql-review
description: Revisar SQL do engenheiro (correção, idempotência, performance, estilo sqlfluff). Use ao revisar arquivos em sql/ ou queries de tickets.
---

# sql-review

**Regra do laboratório:** o engenheiro (João Victor) resolve o ticket. Investigue, faça perguntas, dê dicas graduais e revise. NÃO entregue a solução pronta nem leia `.novamarket/_sealed/` (causas raiz seladas), a menos que o engenheiro peça explicitamente a solução completa para estudo.

## Checklist
- Chaves de join corretas e sem fan-out (conte linhas antes/depois).
- NULLs em filtros, joins e agregações; `COUNT(*)` vs `COUNT(col)`.
- Duplicidades: há `PRIMARY KEY`/dedupe? Reexecutar gera duplicata (idempotência)?
- Filtros por partição/data para evitar full scan; `SELECT *` em produção.
- Fuso horário e `date` vs `timestamp`.
- Estilo: `.venv/Scripts/sqlfluff lint sql/` deve passar.

## Formato da revisão
Liste achados por gravidade (bloqueante / sugestão / elogio) com a linha. Descreva o problema e um caminho, não reescreva a query inteira.
