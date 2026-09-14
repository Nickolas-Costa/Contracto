# ADR 0014 — Rascunho canônico e validação compartilhada

Status: aceita e implementada em 14/09/2026. Consolida ADR-QA-FORMULARIOS.

## Contexto

Reconstruir campos apagava dados; o default legado de endereço sobrescrevia o endereço dinâmico. Cálculos e condições não podem ganhar regras divergentes no navegador.

## Decisão

Manter rascunho fora do DOM, por participante e campos globais. Serializar identidade e campos dos perfis selecionados, copiando globais para cada participante. Campos calculados são autoritativos no Python; o endpoint autenticado POST /api/v1/profiles/preview reutiliza preparação e validação da geração, sem criar arquivos ou trabalhos. A UI descarta respostas de revisões antigas e bloqueia geração durante validação. Condições usam os valores calculados retornados.

O backend aplica exclude_unset aos DTOs legados: ausência não equivale a vazio explícito. Valores duplicados conflitantes retornam 422 com participante/campo, sem ecoar valores sensíveis. Valores legados e duplicatas iguais continuam aceitos. Geração sempre revalida o snapshot; preview não autoriza geração por si só.

## Consequências e evidência

Novo endpoint exige conexão local, com mesmos limites/token da API. Regressões cobrem endereço, aliases, globais, campos ocultos, CPF/data e preservação após composição. Smoke WebView2 verifica cálculo retornado pelo backend. Não implementa edição persistente de perfis. Complementa ADR 0012.
