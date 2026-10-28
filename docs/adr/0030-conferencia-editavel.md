# ADR 0030 — Conferência editável

- **Estado:** futura (registrada para a próxima rodada; **sem implementação**)
- **Data:** 2026-10-28
- **Contexto:** a Conferência (Etapa 2) é somente leitura. Ao achar um erro, o usuário
  volta à Etapa 1 e procura o campo na página certa. Isso é lento e arriscado em
  formulários longos e em vários participantes (ex.: MO 29300 com 4 páginas).
- **Decisão proposta:**
  1. Cada valor da Conferência vira um **atalho**: clicar (ou Enter) leva à Etapa 1, na
     página e no campo certos, com foco e destaque temporário. Reaproveita
     `irParaPendencia`/`paginaDoControle` e `scrollIntoView` (já com `scroll-padding` da
     topbar fixa).
  2. Campos **obrigatórios vazios** e **inválidos** aparecem na Conferência em destaque,
     com o mesmo atalho (hoje o bloqueio ocorre antes de abrir a tela).
  3. Edição **inline** só para tipos simples (texto, seleção, moeda, data) numa segunda
     entrega, reutilizando `fieldControl` e `ContractoForm` — sem duplicar regra.
  4. Ao voltar da Etapa 1, o resumo é recalculado e o stepper volta à Conferência.
- **Consequências:** `conferencia.js` (já isolado) ganha um contexto com callbacks
  (`irParaCampo(participante, campoId)`); nada muda no backend.
- **Testes previstos:** fluxo WebView com clique em valor → foco no campo certo (inclusive
  em outra página da paginação); obrigatório vazio listado; teclado-only.
- **Aceite:** corrigir um dado em ≤ 2 interações a partir da Conferência.
