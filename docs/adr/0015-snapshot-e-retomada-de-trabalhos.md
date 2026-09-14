# ADR 0015 — Snapshot, manifesto e retomada sem duplicação

Status: aceita e implementada em 14/09/2026. Consolida ADR-QA-PROCESSO.

## Contexto

A UI podia processar apenas anexos, reutilizar resultados após edição e enviar novamente uma operação cuja resposta havia se perdido.

## Decisão

Congelar participantes, perfis e destino ao gerar. O processamento recebe explicitamente os file_ids gerados e anexos. Edição invalida a base anterior. Bloquear mutações enquanto o estado é incerto; cancelamento só termina após confirmação do servidor. Consulta tem tentativas limitadas e retomada explícita.

Enviar request_id aleatório por comando. Durante a sessão, backend associa hash do conteúdo e operação ao trabalho sob lock; repetição igual recupera o mesmo trabalho, conteúdo diferente recebe 409. Não persistir IDs entre sessões; limite de 200 trabalhos também limita esse registro. Após reinício é necessário iniciar uma nova sessão, sem promessa de retomada durável.

## Consequências e evidência

Resultados exibidos pertencem ao trabalho concluído; reprocessamento idêntico por clique acidental fica bloqueado. Mudança explícita de formato/anexo permite nova operação. Smoke real perde uma resposta 202 deliberadamente, retoma e verifica apenas dois trabalhos: geração e processamento. Confere dois PDFs preenchidos mais anexo, preservando original. PDF viewer usa Blob local com limite de 20 MiB, descarte de URL e conteúdo autorizado. Sem dependência nova.
