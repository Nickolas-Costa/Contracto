## Contracto v5.4.0

No modo **Contrato**, gerar e concluir viraram **uma etapa só**, e uma auditoria completa corrigiu falhas de fluxo. O motor de geração e os dados do usuário não mudam.

### Novo
- **Contrato em uma etapa.** O formato (PDF ou PDF/A-2b) foi para a Conferência, junto dos formulários e dos documentos extras. "Confirmar e gerar documentos" gera, converte e organiza de uma vez; a Etapa 3 só mostra o resultado. Se a organização falhar depois da geração, aparece "Tentar concluir de novo" (não gera outra vez).
- A pergunta sobre documentos extras que faltam vem antes de gerar, e só quando o perfil tem extras.
- **Aviso ao fechar** a janela com trabalho em andamento.
- A barra de progresso da geração e da organização passa a andar (documento N de M).
- Os PDFs finais do Contrato não levam mais o prefixo `1-`, `2-` no nome.

### Corrigido
- **Tela presa em "Processando…"** com `[object Object]` quando um trabalho falhava. Agora aparece o motivo e a tela é liberada.
- **Cancelar** (Contrato/Simples) não cancelava.
- **PDF/A falhava em pasta ou arquivo com `%` no nome** (ex.: "entrada 50% paga").
- **PDF/A não confirmado agora falha** em vez de entregar PDF comum em silêncio.
- **Reparo do sistema fechava o Word do usuário**, com o que estivesse sem salvar, e apontava o atalho da Área de Trabalho para o servidor sem janela.
- **Perfis:** "Editar" nunca salvava; perfil excluído continuava na lista até reiniciar; nome repetido ou JSON inválido mostravam "Operação local indisponível" em vez do motivo; restaurar backup não atualizava a lista. Perfil que acompanha o aplicativo não pode mais ser excluído (ele voltava sozinho).
- **Backup** feito antes de salvar qualquer perfil ou configuração saía incompleto e não restaurava.
- Um PDF gerado aberto num leitor fazia o trabalho já publicado aparecer como falho.
- "Limpar campos" esvaziava o campo da pasta de saída mas seguia usando a pasta antiga.

### Alterado
- Removido código sem uso (caminho antigo da fila, exportar/importar perfil duplicado, aviso "Word travado", diagnóstico do WebView2, cálculo local de campos).
- O reparo do sistema não encerra mais o Word: um Word oculto que tenha ficado preso precisa ser fechado pelo Gerenciador de Tarefas.
- Documentação alinhada ao código (ARCHITECTURE, BASE_UI_STATUS, TAURI_CONTRATO, AGENTS). ADR 0032 registra o fluxo novo e o **plano de atualização dentro do app** sem certificado de assinatura (ainda sem código).
- Sem auto-update nesta versão: atualizar é rodar o instalador novo.

### Validação
- 373 testes unitários, testes de comportamento do front (Node), 2 testes Rust e o smoke de WebView2 real (`smoke_webview_ui.py`): OK.
- Fluxo do Contrato percorrido de ponta a ponta com dados sintéticos (um clique, PDF/A real) e todas as telas revisadas nos temas claro e escuro, em 1366 px e 1024 px.
- Verificado no executável de release: janela em 1,5 s com o título da versão, servidor empacotado (aperto de mão, perfis, PDF/A em pasta com `%`, cancelar), e fechar a janela encerra o servidor.
- **Não verificado:** instalação pelo instalador sobre a 5.3.0; o aviso ao fechar com trabalho em andamento no executável (só compilado e revisado); conversão de RTF/DOC pelo Word (`smoke_api_engines.py`); arrasto e diálogos nativos; DPI 100–200%. O instalador não tem assinatura de código (o SmartScreen pode alertar).

### Artefatos
- `Contracto_Setup_v5.4.0.exe` (50.6 MiB), instalador. SHA-256: `0E7D607D66B34A7CF5B046169F19C18A4A6F0520045C1A73F8F85BD7C62636DD`
- `Contracto_v5.4.0.zip` (65.7 MiB), portátil (`Contracto.exe` + pasta `sidecar/`). SHA-256: `104CB281B4F93BACFA9CEEA50F8B2DB3358E132901EF1237BF49B4FD1E74A6AC`
