# Revisão contínua de dependências

Toda dependência nova, atualização relevante ou componente que passe a executar em outro ambiente deve responder a este documento antes de ser aceito. A pergunta não é apenas “funciona?”, mas “é a menor dependência segura que preserva o resultado exigido?”.

## Gate obrigatório

Para cada dependência, registrar no PR, ADR ou especificação:

1. Qual capacidade concreta ela entrega e qual fluxo do Contracto deixa de funcionar sem ela?
2. A capacidade pode ser feita com código puro, biblioteca já distribuída ou recurso nativo do sistema?
3. Quais alternativas preservam a fidelidade necessária, e qual delas é mais leve, segura ou portável?
4. Ela exige processo externo, interface gráfica, licença, acesso à rede, arquivos temporários ou privilégios especiais?
5. Ela funciona em desktop local, agente corporativo e servidor hospedado? Se não, a falha é explícita e isolada?
6. Qual teste protege o comportamento real que justifica mantê-la?
7. Como a dependência será removida ou substituída sem reescrever os serviços?

Não introduzir dependência sem resposta explícita a essas perguntas. Reavaliar a matriz abaixo antes de lançar uma API hospedada, mudar o instalador ou alterar modelos de documento.

## Matriz atual

| Componente | Uso atual | Alternativas e código próprio | Decisão no escopo atual |
|---|---|---|---|
| `pypdf` | Ler e preencher AcroForms | Código próprio de PDF não compensa; bibliotecas alternativas não trazem benefício claro para os formulários atuais | Manter: é o núcleo do preenchimento e já há testes com modelos reais. |
| `pikepdf` | Inspeção e validação complementar de PDF/A | `pypdf` sozinho tem menos capacidade de validação; validação externa é complemento de release | Manter enquanto a validação atual depender dele; revisar se a validação for delegada a ferramenta oficial. |
| Ghostscript | Converter PDF para PDF/A-2b | Ferramenta comercial de PDF, serviço externo ou código próprio não entregam a mesma relação custo/fidelidade | Manter embutido e isolado com `-dSAFER`. Só é necessário para PDF/A; PDF comum não depende dele. |
| Word COM + `pywin32` | Converter RTF para PDF com maior fidelidade aos documentos Windows | LibreOffice headless: sem licença Office e multiplataforma, mas exige corpus de comparação; Aspose.Words: adequado a servidor e sem Word, porém comercial; código puro: não compensa para renderização RTF completa | Manter apenas no desktop/agente Windows assistido. Não usar como motor de API hospedada não interativa. |
| LibreOffice | Não é dependência atual | Pode converter por CLI/headless, inclusive RTF para PDF; aumenta tamanho e ainda requer validação de layout | Avaliar em prova isolada, nunca como fallback silencioso. Só adotar se cumprir fidelidade definida. |
| Aspose.Words | Não é dependência atual | Pode renderizar RTF/Word para PDF sem Office e atende melhor cenário servidor | Avaliar somente após oportunidade comercial que pague licença e teste de fidelidade. |
| `customtkinter`, `darkdetect`, `Pillow` | Shell Tk atual, tema e imagens | HTML/CSS/WebView substitui a camada visual; Pillow pode permanecer para recursos de imagem usados pelo núcleo | Manter apenas durante convivência com a UI legada; não levar widgets Tk para a API. |
| `pypdfium2` | Pré-visualização/renderização de PDF | Ghostscript e renderizadores comerciais são alternativas mais pesadas ou com licença diferente | Manter enquanto houver pré-visualização local; medir tamanho no pacote WebView. |
| `lxml` | Processamento de XML associado a PDF | Biblioteca padrão não oferece substituição equivalente de forma geral | Manter como dependência transitiva/necessária enquanto pikepdf e fluxos XML a exigirem. |
| FastAPI + Uvicorn | Contrato loopback entre WebView e núcleo | Chamada direta pywebview aumenta acoplamento; servidor próprio seria código adicional e menos padronizado | Adotar apenas na Fase A, limitado a loopback, token efêmero e testes HTTP. |
| `pywebview` + WebView2 | Shell WebView desktop | Tauri é futuro possível; navegador externo não entrega integração desktop | Adotar na Fase A após API local estar testada. |

## Prova obrigatória antes de trocar conversor RTF

Uma troca de Word exige uma amostra representativa dos RTF reais da operação, incluindo tabelas, cabeçalhos, fontes, quebras de página, assinaturas e caracteres acentuados. Para cada arquivo, comparar PDF atual e candidato visualmente e por número de páginas; registrar divergências, tempo, memória, tamanho de pacote e licença. Só aprovar se não houver alteração material no documento final.

Microsoft informa que automação Office não interativa em componentes de servidor não é recomendada nem suportada, por risco de bloqueios e comportamento instável. LibreOffice documenta a conversão headless por `--convert-to`; isso prova capacidade técnica, não equivalência de layout. Aspose documenta conversão de RTF/Word para PDF sem Word instalado, mas exige avaliação comercial.

Referências: [Microsoft Learn — automação Office não atendida](https://learn.microsoft.com/en-us/office/client-developer/integration/considerations-unattended-automation-office-microsoft-365-for-unattended-rpa), [LibreOffice — parâmetros e conversão headless](https://help.libreoffice.org/latest/en-GB/text/shared/guide/start_parameters.html), [LibreOffice — filtros de conversão](https://help.libreoffice.org/latest/ast/text/shared/guide/convertfilters.html), [Aspose.Words — conversão para PDF](https://docs.aspose.com/words/python-net/convert-a-document-to-pdf/), [pypdf — formulários PDF](https://pypdf.readthedocs.io/en/3.17.3/user/forms.html).
