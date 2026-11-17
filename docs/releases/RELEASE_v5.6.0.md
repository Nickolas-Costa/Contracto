## Contracto v5.6.0

Reúne o trabalho que ficou de fora das últimas versões (a linha "5.4.x" de digitação e leitura de documentos, que nunca tinha sido publicada) com os acertos do MO 29300 da 5.5.1.

### Novo
- **Formulário em páginas livres**: dá para ir a qualquer página sem preencher a anterior; cada aba mostra quantos campos faltam.
- **Gerar mesmo assim**: só nome, CPF, data, local e pasta travam a geração; o resto vira lista de pendências.
- **Leitura de documentos do cliente** (PDF, RTF, DOC, DOCX): propõe valores para os campos, com revisão ao lado do documento.
- Máscaras com cursor correto, telefone, PIS, área; Conferência com atalho para o campo; ITBI por município; endereço completo ou em partes; perfis com rótulos e largura de campo.

### Corrigido
- Acentos e hífen errados em alguns visualizadores (valor dos campos gravado em hexadecimal).
- MO 29300: data do casamento, "Possuo imóvel em" e endereço do imóvel (campos maiores, pontos finais acompanhando).
- Detalhes completos no `CHANGELOG.md`.

### Validação
- 424 testes unitários: OK. Modelo MO 29300 renderizado e conferido.
- **Não verificado:** o executável instalado (arrasto de arquivos e conversão de RTF/DOC/DOCX), `smoke_webview_ui.py` no shell Tauri e o caminho de atualização pelo app.

### Artefatos
- Preenchidos na publicação.
