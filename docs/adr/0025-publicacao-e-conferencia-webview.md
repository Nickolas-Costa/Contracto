# ADR 0025 — Publicação de resultados e Conferência (Etapa 2)

- **Estado:** aceita / implementada
- **Data:** 2026-10-17
- **Contexto:** a publicação padronizada em `Contracto-<job_id>` (ADR 0011) não
  dizia nada ao usuário, e a Etapa 3 (Concluir) acumulava conferência de
  formulários/extras, tornando o fluxo longo. As variáveis derivadas da cor de
  destaque também assumiam base escura fixa, quebrando badges no tema claro.
- **Decisão:**
  - **Nome legível da pasta:** `nome_pasta_processo()` em
    `utils/filename_utils.py` gera `Contrato <Primeiros Nomes>` (Title Case,
    acentos preservados, nomes unidos por ` e `). Pasta intermediária da
    geração Contrato: `Contrato <Nomes> (gerados)`; pasta final do trabalho:
    `Contrato <Nomes>`.
  - **Publicação por modo:** em Contrato (`jobs._submit(..., folder_name=...)`)
    o trabalho escreve numa pasta privada `.contracto-*` e só a renomeia no
    sucesso; colisão recebe sufixo ` (2)`, ` (3)`… — nunca sobrescreve. Em
    Simples/Conversão (`inline=True`) os arquivos vão direto na pasta escolhida,
    com o mesmo sufixo de colisão. `_mover_inline`/`_destino_unico` em
    `api/jobs.py`.
  - **Conferência (Etapa 2):** `#secao-forms-dinamicos` e `#secao-docs-extras`
    vivem em `#tela-conferir`; `etapa1.conferir()` chama
    `ContractoEtapa2.sincronizarContexto()` antes de abrir. A Etapa 3 fica
    enxuta e o modal final só oferece "Abrir pasta" (primário) e "Fechar".
  - **Extras por perfil:** `combinar_perfis` preserva `documentos_extras` de um
    perfil único (antes zerava sempre); combinações de vários perfis seguem sem
    extras.
  - **Cores por tema:** `aplicarTema` reaplica a cor; `--c-primary-light` usa
    base branca no tema claro e `#0F1419` no escuro.
- **Alternativas:** manter `Contracto-<job_id>` (descartado: pasta ilegível);
  retornar lista de arquivos em vez de pasta (o shell abre pasta por ID);
  publicar direto sem staging no Contrato (perderia a atomicidade no erro).
- **Consequências:** pastas nomeadas com o cliente; Contrato mantém pasta
  intermediária `(gerados)` para revisão (não é removida automaticamente —
  decisão de não apagar dados do usuário). Simples/Conversão com paridade
  legada. Etapa 3 sem duplicar a conferência.
- **Aceite:** `tests/test_filename_utils.py`, `tests/test_composicao_perfis.py`,
  `tests/test_local_api.py`
  (`test_generate_contract_uses_legible_subfolder_and_process_final_folder`,
  colisão ` (2)`, `test_bridge_opens_only_completed_result_by_id` atualizado) e
  `tests/webview_flow.js` (confirmação de "Concluir sem documentos extras?").
