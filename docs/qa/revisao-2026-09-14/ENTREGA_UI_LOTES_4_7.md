# Redesign da WebView — entrega dos lotes 4–7

Implementado em 14/09/2026, em continuidade à entrega dos lotes 1–3. Mantém a API loopback, a fila e a ponte nativa existentes; não adiciona dependências.

## Resultado entregue

- A resposta terminal de cada job agora inclui `files`: ID efêmero, nome de arquivo, tamanho, origem (`generated`, `attachment` ou `imported`) e índices de participantes. Caminhos locais não fazem parte do contrato.
- A etapa de documentos mostra nome e metadados dos PDFs gerados e resultados. Anexos usam categorias selecionáveis e legíveis; o processamento preserva o tipo técnico validado pelo backend.
- A fila comunica envio, execução, cancelamento, falha, incerteza de consulta e conclusão em um componente persistente. A orientação para retomada mantém a garantia de não duplicar a solicitação já aceita.
- O visualizador abre um diálogo com estado de carregamento, erro compreensível para PDF grande/falha e ação explícita de fechamento. O Blob é revogado e a classe de layout do viewer é removida ao fechar.
- Perfis passaram a ser cartões pesquisáveis, de consulta, com modo, limite e campos. Configurações informam capacidades locais de PDF, PDF/A e RTF sem expor binários ou caminhos.

## Verificação

- `tests.test_local_api`: **20 testes, OK**. A jornada de geração e processamento afirma metadados de arquivo, associação ao participante, tamanho e ausência de caminho local.
- `tests/smoke_webview_ui.py`: **OK** no WebView2 real. A jornada sintética valida catálogo e busca, capacidades, manifesto com metadados, anexo, processamento, viewer Blob, `inert`, fechamento e invalidação após edição.
- Sintaxe de `etapa1.js`, `etapa2.js` e `ui.js`: **OK** com `node --check`.

## Limites para o aceite final

O iframe do leitor PDF é controlado pelo WebView2/Windows. O diálogo mantém foco fora da página e fornece fechamento acessível, mas Narrator e a navegação de teclado dentro da toolbar do PDF precisam de avaliação manual em Windows com o leitor disponível. Também continuam pendentes DPI 100/125/150/200%, instalação limpa, Word/Ghostscript reais após esta alteração e corpus de documentos representativo.

## Capturas

As capturas já existentes seguem em `prints/qa-2026-09-14-redesign/`, fora do Git. Nesta máquina a janela WebView2 da fixture de captura não é exposta ao controlador de tela disponível; por isso não foi possível produzir uma imagem confiável adicional dos estados novos sem recorrer a automação gráfica fora do escopo. A execução visível foi aberta com massa sintética e o fluxo automatizado confirma esses estados. Registrar novas capturas manualmente na matriz de QA antes do README.
