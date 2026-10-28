# ADR 0026 — Formato inicial pela Config, topbar fixa e arrasto na Conversão

- **Estado:** aceita / implementada
- **Data:** 2026-10-27
- **Contexto:** o uso real da 4.5.25 mostrou que o formato de saída da Etapa 2 e da
  Conversão abria sempre em PDF (nada lia `formato_saida`), que o visualizador de PDF
  ficava cortado no modal (quatro regras CSS de largura em conflito), que arrastar um
  arquivo para a Conversão reabria o seletor e descartava o arquivo, e que a barra
  superior rolava junto com a página.
- **Decisão:**
  - **Formato inicial:** `etapa2.js` e `conversao.js` leem `GET /api/v1/settings`
    (`formato_saida`). Vale `PDF/A-2b` só se o Ghostscript existe; senão `PDF`. Uma
    escolha manual do usuário nunca é sobrescrita (flag por tela; a Etapa 2 a reinicia
    ao começar novo trabalho). O perfil **não** entra na decisão: o formato do perfil
    continua só informativo e `profile_composer` segue sem propagá-lo.
  - **Controle:** `ContractoUI.segmentar(select)` troca a lista por botões
    (`aria-pressed`, `disabled` por opção). O `<select>` permanece oculto como fonte do
    valor, então a lógica existente não muda.
  - **Arrasto:** o WebView2 só entrega o caminho ao Python (`pywebviewFullPath`). O
    `ShellBridge` liga o evento `drop` da `#drop-conversao`, valida a página com
    `_authorized()`, registra cada caminho como seleção `convert` e chama
    `ContractoConversao.receberArrasto` apenas com IDs e nomes. Nenhum caminho chega
    ao JS e nenhum método público novo é exposto na ponte. Soltar fora da área é
    bloqueado (`preventDefault` no documento) para não navegar a janela.
  - **Topbar:** `position: sticky` com `z-index` abaixo de calendário, toasts, modais e
    skip-link; abaixo de 1100px (onde a barra quebra em linhas) volta a estática.
  - **Botões:** ação primária por último em Etapa 2, Conversão e Configurações.
  - **Perfis:** lista em seções "Modo Simples" e "Modo Contrato" (qualquer valor que
    não seja `formulario_simples` conta como contrato, igual ao badge e a
    `perfis_por_modo`).
- **Alternativas:** formato pelo perfil (descartado: composição de vários perfis não tem
  um formato único); upload do arquivo arrastado pela API (descartado: teto de 1 MB na
  ponte e novo vetor de entrada); sticky em todas as larguras (descartado: consome
  altura útil quando a barra quebra).
- **Consequências:** o arrasto depende do suporte de DOM do pywebview 6.2.1; sem ele o
  clique continua abrindo o seletor. Mudar o formato padrão nas Configurações vale a
  partir do próximo trabalho.
- **Aceite:** `tests/test_webview_bridge.py::test_drop_na_conversao_entrega_ao_js_so_ids`,
  `tests/test_composicao_perfis.py::test_damp_real_compoe_sozinho_e_com_os_demais_simples`,
  `tests/test_frontend_base.py::test_ajustes_v4526_topbar_viewer_formato_e_perfis` e
  `tests/webview_flow.js` (perfis agrupados, formato inicial, ordem dos botões,
  visualizador dentro do modal, topbar sticky).
- **Limite não automatizado:** o arrasto real de um arquivo do Explorador exige teste
  manual no WebView2 (`tests/smoke_webview_ui.py --visible`).
