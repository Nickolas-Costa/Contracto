# Plano de Transposição MVP — Legado Tk → WebView + Modo Conversão

> Documento de trabalho (pós v4.5.18). Fases 0–4 e modo Conversão
> implementados na v4.5.19 (branch `feat/mvp-transposicao-e-conversao`).
> Rodada de 10 ajustes visuais/fluxo (fotos do usuário) na v4.5.20.
> Rodada de 15 ajustes (toolbar/toast, stepper 3 passos, conferência,
> MO 29300, Cliente/Seguro, larguras 760/1080/1400, perfis, viewer PDF)
> na v4.5.21 (branch `fix/ui-feedback-15-ajustes`).
> Resta o gate manual Windows/distribuição.

## v4.5.20 — rodada de ajustes (fotos 1–10)

| Foto | Correção |
|---|---|
| 1a | `gerar()` com 202 avança para "Revisar documentos" (não prende na Conferência); toasts de início/conclusão/falha/cancelamento. |
| 1b | Pill de fila removido da toolbar (`#indicador-fila-global` excluído); fila acessível pelo botão "Fila" na Etapa 2 (`painelFila`). |
| 2 | Contrato: modelos sempre em pills lado a lado (`renderSeletorLista`, sem radio nativo); Simples mantém checkboxes. |
| fundo | Sonda WebView2 real mostrou `prefers-reduced-motion=True`: o guard da Fase 4 apagava as ondas. Ondas são estáticas → só `forced-colors` remove. |
| 3 | `#modal-corpo` (o `div` tem id, não classe — a regra `.modal-corpo` nunca aplicava): padding/margem corrigidos. |
| 4 | "Recursos deste computador" removido da UI (v4.5.21); capacidades seguem internas como gate de PDF/A + diagnóstico via `POST /system/repair`. |
| 5 | `.acoes` gap 12→14px + row-gap; `.field-section` com respiro. |
| 6 | Seção Sobre removida da Config; versão no modal de Ajuda (`#versao-app`). |
| 7 | `#lista-formularios` em coluna com gap 12px (removida regra concorrente em linha); "Selecionar todos" com margem 16px. |
| 8 | Check marcado com `color` explícito + borda 2px; foco visível global já existente; botões secundários mantêm borda. |
| 9 | "Revise os dados" virou modal estilo Ajuda com itens clicáveis (navegam à página e focam o campo). |
| 10 | Conflito no Simples restaura a última seleção válida (não zera mais os campos); toast explica. |

## Fase 0 — Desbloqueio do fluxo (IMPLEMENTADA)

Sintoma relatado: na UI atual não era possível concluir o fluxo; selecionar
um modelo "apenas piscava e nada alterava", sendo preciso voltar ao legado.

### Correções aplicadas

| # | Arquivo | Correção |
|---|---|---|
| 0.1 | `frontend/js/etapa1.js` (`sincronizarSelecao`) | Sincroniza também `#seletor-modelos .seletor-item` via `aria-pressed`. Antes só `#lista-formularios input` era atualizado, então o seletor de lista (>2 contratos) nunca refletia a seleção — o "pisca e nada altera". |
| 0.2 | `frontend/js/etapa1.js` (`renderSeletorLista`) | Contador "N modelos" agora aparece 1 vez acima da lista; antes era clonado para dentro de cada botão. |
| 0.3 | `frontend/js/etapa1.js` (`fieldControl`, `SELECAO` + `apresentacao:"checkbox"`) | Listeners de `change` agora vão nos checkboxes criados, atualizando `owner[id]` + `changed()`. Antes o listener era anexado ao `<select>` já removido do DOM (noop) — a escolha nunca chegava ao rascunho. |
| 0.4 | `frontend/js/etapa1.js` (`mode`) | Padrão `"avancado"` → `"contrato"`, alinhado à toolbar (`#modo-contrato` com `aria-current`) e aos filtros de catálogo. O valor antigo só funcionava por acidente. |
| 0.5 | `frontend/js/etapa1.js` (`renderProfilesList`) | Removida a amarração de `#buscar-perfis` a `renderProfilesList()`. Esse input pertence à tela Perfis (gerenciado por `ligar()`/`carregarTelaPerfis()` via `renderProfilesManagement`); o duplo dono disparava dois renders conflitantes ao digitar. |
| 0.6 | `frontend/js/etapa1.js` (`limparCampos`/`novoTrabalho` + `preservarAtivo()`) | `chk-preservar-dados` (persistido em `localStorage contracto-preservar`) passa a ser respeitado: com a flag ligada, limpar/novo-trabalho mantém pessoas + assinatura/destino e só invalida o trabalho — paridade com o `chk_preservar_dados` do legado. |
| 0.7 | `frontend/js/etapa2.js` | Novo `reconectar()` exportado (recarrega `capabilities`, retoma polling se havia trabalho ativo, atualiza controles). |
| 0.8 | `frontend/js/app.js` | Boot defensivo: chama `reconectar()` só se existir (fallback para `atualizar()`). Antes, `ContractoEtapa2.reconectar()` inexistente lançava `TypeError` e caía no catch "interface não pôde ser inicializada". |

### Validação da Fase 0

- `node --check` nos 3 JS alterados.
- `tests/test_frontend_behavior.py` (bootstrap + modal via Node).
- `tests/test_frontend_base.py`, `tests/test_p0_release.py`.
- Manual: `tests/smoke_webview_ui.py --visible` — selecionar modelo com >2 contratos, marcar/desmarcar, `btn-gerar` habilitando.

## Fase 1 — Modais e feedback (IMPLEMENTADA)

### Correções aplicadas

| # | Arquivo | Correção |
|---|---|---|
| 1.1 | `frontend/css/layout.css` | Camada modal real: `.overlay` fixo (`inset:0`, `z-index:70`, fundo `rgba(10,20,35,.6)`), `.modal` centralizado (`width:min(560px,…)`, `max-height:calc(100dvh-48px)`, `radius:12px`, `shadow-lg`), `.modal-titulo-faixa` + `.modal-fechar` com alvo 44px, responsivo. Removidas regras fragmentadas/duplicadas. |
| 1.2 | `frontend/js/ui.js` (`toast`) | Padrão 4s→6s com pausa sob hover/foco; máximo 3 visíveis; `Escape` ignorado quando há modal aberto (o `Esc` pertence ao elemento mais interno). |
| 1.3 | `frontend/js/ui.js` (`abrirModal`) | Convenção documentada: foco inicial no 1º botão = opção segura; destrutivas listam Cancelar/Voltar primeiro; sem empilhamento. |
| 1.4 | `frontend/js/etapa2.js` (`modalConclusao`) | Paridade `SuccessModal`: ao concluir o processo, modal "Trabalho concluído" com Abrir pasta / Ver documentos / Concluir. |
| 1.5 | `frontend/js/etapa2.js` (`finalizar`→`_prosseguirFinalizar`) | Paridade `ConfirmModal` de extras: sem nenhum anexo, confirmação "Concluir sem anexos?" (Voltar e anexar × Concluir mesmo assim) antes de enviar. |

## Fase 2 — Paridade de jornada Simples + Contrato (IMPLEMENTADA)

| # | Arquivo | Correção |
|---|---|---|
| 2.1 | `frontend/js/etapa1.js` (`render`) | Botão "Copiar dados do participante 1" em cada participante adicional — paridade com o legado; preserva nome/CPF próprios. |
| 2.2 | `frontend/js/etapa1.js` (`btn-ver-pendencias`) | Escolher a pendência navega até a página do campo e foca; foco nativo dá visibilidade (sem `scrollIntoView` global, `DESIGN.md §7`). |
| 2.3 | `frontend/js/ui.js` (`irEtapa(4)`) | No modo Simples (sem "Concluir e organizar") foca `#lista-resultados` em vez de botão oculto. |
| 2.4 | `frontend/js/etapa2.js` (`alertaWordTravado`) | Contagem real de espera (tick 1s, `role=status`), "Aguardar" em vez de "Fechar" (fechar não cancela), reparo limitado ao processo filho, sem LibreOffice (`DESIGN.md §8`). |
| — | já existente, auditado | Multisseleção Simples + conflito `409`, reaplicar sem apagar, `request_id` idempotente + single-flight, `pending` retomável com o mesmo ID, fila minimizável (fechar painel não cancela) via `#indicador-fila-global`. |

## Fase 3 — Perfis e Config (IMPLEMENTADA, escopo MVP)

| # | Arquivo | Correção |
|---|---|---|
| 3.1 | `frontend/index.html` + `frontend/js/ui.js` | Tema "Padrão do sistema" (`resolverTema()` via `matchMedia` + acompanhamento de troca do SO); `localStorage` aceita `sistema`/`system` (canônico do backend); `cfgSalvar` envia `system` ao backend; restaurar usa `resolverTema` + reaplica largura. |
| 3.2 | `frontend/js/etapa1.js` (`editarPerfilModal`) | Cabeçalho estruturado (nome/modo/formato/máx. participantes) acima do JSON, mesclado ao salvar; valores do perfil escapados antes do `innerHTML` (`DESIGN.md §9`). |
| Pendente (pós-MVP) | — | Editor seccionado completo com mapeamento e prévia PDF página inteira + zoom por teclado (equivale a `pf_editor.py` ~1300 linhas; o CRUD + cabeçalho + import/export/backup cobre o uso operacional). |

## Fase 4 — Endurecimento + gate (PARCIAL — itens de código feitos; gate manual restante)

| # | Arquivo | Correção |
|---|---|---|
| 4.1 | `frontend/js/ui.js` (`aplicarLargura`) + `layout.css` | `tamanho_quadros` (Pequeno 760 / Médio 1080 / Grande 1400, `DESIGN.md §4`) aplicado via `--largura-quadros` no arranque, ao salvar e ao restaurar. Antes era persistido e ignorado. |
| 4.2 | `frontend/js/ui.js` (`desenharFundoSenoidal`) | Sem ondas sob `prefers-reduced-motion` ou `forced-colors` (`DESIGN.md §5`); remove resíduo de arranques anteriores. |
| 4.3 | auditado | `localStorage` só guarda tema/cor/preservar/local-assinatura; nenhum CPF/CNPJ/nome/token/fila (`DESIGN.md §9`); CSP `default-src 'none'` mantida. |
| Gate manual restante | — | `smoke_webview_ui.py --visible`, `smoke_api_engines.py` (Word/GS reais), DPI 100/125/150/200%, zoom 200%, teclado-only + leitor de tela, instalador (`packaging/Contracto.iss`, ADR 0008) ou decisão Tauri (ADR 0024). |

---

## Modo Conversão (IMPLEMENTADO na v4.5.19)

Terceiro botão Simples/Contrato/**Conversão** na toolbar
(`frontend/index.html` + `frontend/js/conversao.js`).

### Entregue

- Tela `#tela-conversao` fora do stepper (sem participantes/perfis):
  dropzone central (clique/diálogo nativo multi-seleção; arrastar abre o
  diálogo — o shell não expõe caminhos de drop por segurança), lista com
  remoção, formato (PDF / PDF/A-2b com gate de Ghostscript), nome opcional
  (1 arquivo, validado `^[\w\-. ]{1,100}$`), pasta de saída, progresso,
  resultados com Visualizar (reaproveita `getFile`), Abrir pasta, Cancelar.
- Backend: kind `convert` (PDF/RTF/DOC/DOCX) em `selections.py`,
  `ConvertInput` em `models.py`, `Jobs.convert()` (office→PDF via Word,
  PDF→PDF/A via GS, original preservado, `request_id` idempotente) e
  `POST /api/v1/jobs/convert`; `capabilities()` anuncia
  `convert_in`/`convert_out`.
- Ponte: `WebViewDialogs.selecionar_documentos()` (multi) +
  `ShellBridge.select_documents()` (registra `convert`, conta rejeitados).
- Testes: `tests/test_convert_api.py` (5) + `select_documents` no bridge.
- Limites mantidos: sem Word → 409 explícito p/ office; sem GS → 409 p/
  PDF/A; saída p/ DOC/DOCX/RTF não tem motor (opção nem oferecida).

### Proposta de UX original (espelho PDFCreator) — referência

- Tela própria `#tela-conversao` (fora do stepper Preencher/Conferir/
  Revisar/Enviar — conversão não usa participantes nem perfis):
  - Grande área central de drop (`drag & drop` + clique "Anexar arquivo"),
    aceitando PDF, RTF, DOC, DOCX (filtro por extensão).
  - Cada arquivo na área abre o **modal de seleção do tipo a converter**,
    nome, saída e etc.
  - Fila de conversão com progresso por arquivo, reutilizando
    o painel de fila / `#indicador-fila-global`.
- Respeitar limites arquiteturais (`AGENTS.md`): RTF↔Word exige Word COM
  (Windows-only, falha explícita sem Word); PDF/A exige Ghostscript
  (falha acionável, PDF simples segue disponível); sem fallback silencioso;
  toda conversão passa pelo gate `DEPENDENCY_REVIEW.md`.
- Backend: avaliar endpoint dedicado (ex. `POST /api/v1/jobs/convert`
  com `file_id` + `format` + `output_id`) reaproveitando `services/`
  (`pdfa_converter`, `rtf_converter`) via fachada de jobs idempotente
  (`request_id`), como `generate`/`process`. DOC/DOCX→PDF sem Word: só via
  prova de fidelidade aprovada (LibreOffice/Aspose) — nunca silencioso.

### Tarefas previstas (concluídas na v4.5.19)

1. `index.html`: botão `#modo-conversao` + `#tela-conversao` com dropzone. ✅
2. Toggle de modo sem quebrar `modo()` (`etapa2.js`) — Conversão é tela, não modo de geração. ✅
3. Novo `frontend/js/conversao.js`: dropzone, formato/nome/saída, fila. ✅
   (Decisão: formato global por lote em vez de modal por arquivo — menos
   cliques, mesmo poder; modal por arquivo pode voltar como evolução.)
4. `app/api/http.py` + `selections.py`: kind `convert` e rota de conversão; `webview_shell.py`: `select_documents()`. ✅
5. Testes: conversão PDF→PDF (GS/Word reais cobertos por `smoke_api_engines.py`
   p/ motores; `test_convert_api.py` p/ contrato), Word ausente (409
   acionável), nome/pasta de saída respeitados. ✅
