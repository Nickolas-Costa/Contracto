# ADR 0021 — Consolidação da Toolbar e Promoção do Seletor de Modo

- **Estado:** aceita
- **Data:** 2026-09-17
- **Contexto:** Após a migração completa para WebView2 (v4.5.18), a interface passou a exibir duas barras superiores simultâneas: a `.toolbar` principal e o `.stepper`. O indicador de estado de conexão com o backend (`#conexao`, "Conectando…") estava exposto ao usuário final, que não tem contexto técnico para interpretá-lo. O seletor de modo ("Só gerar" / "Gerar e organizar") e a contagem de participantes ficavam enterrados dentro de um card, passando despercebidos. O painel lateral `.summary` ("Resumo do trabalho") consumia espaço horizontal do workspace sem benefício proporcional na tela de preenchimento.

- **Decisão:** Consolidar a interface em uma única barra de navegação superior (`.toolbar`) sem indicadores de backend. O seletor de modo de geração é promovido para dentro da `.toolbar`, tornando-o imediatamente visível. A contagem de participantes recebe destaque visual adequado (badge/chip). O painel lateral `.summary` é removido do layout de colunas; seu conteúdo resumido é integrado na barra de ações fixada (`form-actions`). O workspace passa a ocupar 100% da largura disponível.

- **Alternativas consideradas:**
  - Manter o `#conexao` com texto mais amigável ("Sistema pronto") — descartado, pois qualquer estado de infra-estrutura é irrelevante para o usuário final do Contracto.
  - Mover `.summary` para o topo como breadcrumb — descartado, pois fragmenta a hierarquia visual; as informações são mais úteis próximas ao botão de ação.
  - Usar um segundo toolbar colapsável — descartado, adiciona complexidade de estado sem ganho de usabilidade.

- **Consequências:**
  - `frontend/index.html`: remoção do `<span id="conexao">` e do bloco `<aside class="summary">`; inserção do grupo `.modos` dentro da `.toolbar`; ajuste na estrutura do `.workspace` de grid 2 colunas para 1.
  - `frontend/css/layout.css`: remoção das regras de `#conexao`; novos estilos para `.toolbar-mode` (chip de modo na barra), `.participant-badge` (contagem de participantes em destaque); ajuste de `.workspace` para `grid-template-columns: minmax(0,1fr)`.
  - `frontend/js/app.js` e `etapa1.js`: migração das referências ao `#conexao` para tratamento silencioso; atualização do renderizador de participantes para refletir o novo componente de badge.
  - Testes: o `tests/test_frontend_base.py` deve ser atualizado para não exigir `#conexao` no DOM; o `tests/smoke_webview_ui.py` deve validar a presença do seletor de modo na toolbar.

- **Arquivos:**
  - `frontend/index.html`
  - `frontend/css/layout.css`
  - `frontend/js/app.js`
  - `frontend/js/etapa1.js`
  - `tests/test_frontend_base.py`
  - `tests/smoke_webview_ui.py` (ou `tests/webview_flow.js`)

- **Revisão:** confrontada com ADR 0010 (pendências visuais do shell), ADR 0018 (direção visual), ADR 0016 (integridade HTML).

- **Aceite:** A toolbar exibe o seletor de modo e botões de navegação sem nenhum indicador de estado de backend. O workspace de preenchimento ocupa toda a largura. A contagem de participantes é imediatamente legível sem hover.

- **Testes:**
  - `tests/test_frontend_base.py`: `#conexao` não presente no DOM (ou presente e `hidden`).
  - `tests/test_frontend_base.py`: `#modo-simples` e `#modo-avancado` dentro de `.toolbar` (não dentro de `.card`).
  - `tests/smoke_webview_ui.py`: clicar no seletor de modo na toolbar e verificar mudança de estado visual.
