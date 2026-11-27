## Contracto v5.8.0

**Formulários que não podem ser alterados** depois de gerados.

### Novo
- Os PDFs gerados saem **achatados**: os valores fazem parte da página e não há campos para editar.
- Na Conferência, a opção **Manter os campos editáveis nos PDFs gerados** volta ao comportamento anterior. Vale por trabalho e começa desmarcada.
- Botão **Começar do zero** na Conferência e na Etapa 3: pede confirmação, apaga o trabalho da tela e recarrega.

### Importante
- Achatar não substitui assinatura digital: um editor de PDF ainda altera a página. A prova de integridade é a assinatura do cliente no arquivo achatado.
- A leitura de documentos não reconhece campo a campo um PDF achatado gerado pelo app (só pelo texto). Para reaproveitar os dados, gere com campos editáveis.

### Validação
- 430 testes unitários e `smoke_webview_ui.py`: OK. Os 8 modelos renderizam igual nos dois modos; PDF/A-2b de um achatado validado.
- **Não verificado:** o executável instalado e o caminho de atualização pelo app.

### Artefatos
- Preenchidos na publicação.
