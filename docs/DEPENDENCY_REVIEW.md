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
| `customtkinter`, `darkdetect` | Removidos na v5.0.0 (ADR 0028): eram só a UI Tk | Nada a substituir: a UI é HTML/CSS/JS | Removidos de `requirements*.txt` e do bundle. |
| `Pillow` | Renderização da conferência de mapeamento (`mapping_audit.py`) | HTML/CSS/WebView substitui a camada visual; Pillow pode permanecer para recursos de imagem usados pelo núcleo | Manter apenas durante convivência com a UI legada; não levar widgets Tk para a API. |
| `pypdfium2` | Pré-visualização/renderização de PDF | Ghostscript e renderizadores comerciais são alternativas mais pesadas ou com licença diferente | Manter enquanto houver pré-visualização local; medir tamanho no pacote WebView. |
| `lxml` | Processamento de XML associado a PDF | Biblioteca padrão não oferece substituição equivalente de forma geral | Manter como dependência transitiva/necessária enquanto pikepdf e fluxos XML a exigirem. |
| FastAPI + Uvicorn | Contrato loopback entre WebView e núcleo | Chamada direta pywebview aumenta acoplamento; servidor próprio seria código adicional e menos padronizado | Adotar apenas na Fase A, limitado a loopback, token efêmero e testes HTTP. |
| `pywebview` + WebView2 | Shell WebView desktop | Tauri é futuro possível; navegador externo não entrega integração desktop | Adotar na Fase A após API local estar testada. |

## Prova obrigatória antes de trocar conversor RTF

Uma troca de Word exige uma amostra representativa dos RTF reais da operação, incluindo tabelas, cabeçalhos, fontes, quebras de página, assinaturas e caracteres acentuados. Para cada arquivo, comparar PDF atual e candidato visualmente e por número de páginas; registrar divergências, tempo, memória, tamanho de pacote e licença. Só aprovar se não houver alteração material no documento final.

Microsoft informa que automação Office não interativa em componentes de servidor não é recomendada nem suportada, por risco de bloqueios e comportamento instável. LibreOffice documenta a conversão headless por `--convert-to`; isso prova capacidade técnica, não equivalência de layout. Aspose documenta conversão de RTF/Word para PDF sem Word instalado, mas exige avaliação comercial.

Referências: [Microsoft Learn — automação Office não atendida](https://learn.microsoft.com/en-us/office/client-developer/integration/considerations-unattended-automation-office-microsoft-365-for-unattended-rpa), [LibreOffice — parâmetros e conversão headless](https://help.libreoffice.org/latest/en-GB/text/shared/guide/start_parameters.html), [LibreOffice — filtros de conversão](https://help.libreoffice.org/latest/ast/text/shared/guide/convertfilters.html), [Aspose.Words — conversão para PDF](https://docs.aspose.com/words/python-net/convert-a-document-to-pdf/), [pypdf — formulários PDF](https://pypdf.readthedocs.io/en/3.17.3/user/forms.html).

## Shell Tauri (ADR 0029) — revisão do passo 2, adotado no `src-tauri/`

Versões fixadas em `src-tauri/Cargo.toml`/`Cargo.lock` e `package-lock.json`, todas com ≥ 2 semanas de publicação em 01/11/2026 (por isso `tauri` 2.12.4 e `tauri-plugin-dialog` 2.8.3, não as 2.12.5/2.8.4 mais novas). Tauri 3 segue em alfa: fora de escopo.

| Componente | Capacidade | Alternativa / código próprio | Decisão |
|---|---|---|---|
| Rust (rustup, MSVC) + VS Build Tools (C++) | Compilar `src-tauri/` | Manter pywebview | **Adotado** só na máquina de build; não vai ao usuário final. |
| `@tauri-apps/cli` 2.12.3 (npm, dev) | `tauri build` e bundler NSIS | Cargo + script próprio de empacotamento | **Adotado** (devDependency). O bundler baixa NSIS 3.13 e `nsis_tauri_utils` (hash validado) na 1ª execução. |
| `tauri` =2.12.4 / `tauri-build` =2.7.3 | Janela, `invoke`, CSP, bundler | pywebview | **Adotado.** |
| `tauri-plugin-dialog` =2.8.3 | Diálogos nativos (usado só pelo Rust; sem permissão exposta à página) | Código próprio sobre `rfd` | **Adotado.** Traz `tauri-plugin-fs` como transitivo, sem capability concedida. |
| `reqwest` 0.12 (sem TLS, sem proxy) | Encaminhar `request`/`get_file` ao sidecar em loopback | `std::net` + HTTP manual (mais código e risco) | **Adotado**, `default-features = false` e `no_proxy()`. |
| `base64` 0.22, `serde_json` 1 | `get_file` e DTOs | — | **Adotados** (já transitivos do Tauri). |
| `tauri-plugin-opener` | Abrir pasta/PDF | `explorer.exe <caminho absoluto>` devolvido pelo sidecar | **Não adotado**: poucas linhas, uma dependência a menos. |
| `tauri-plugin-shell` | Sidecar | `std::process::Command` sobre `Contracto_sidecar.exe` ao lado do executável | **Não adotado**: allowlist de um só executável, sem plugin. |
| `tauri-plugin-updater` | Atualização automática | Reinstalar manualmente | **Não adotar** (decisão do usuário: sem auto-update). |
| OCR (ADR 0027, Fase 2) | PDFs digitalizados | `Windows.Media.Ocr` ou Tesseract | Decidir no gate da Fase 2. |
