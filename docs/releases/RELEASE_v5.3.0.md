## Contracto v5.3.0

O app passa a rodar no **shell Tauri** (janela nativa + servidor local em Python) com instalador NSIS no lugar do Inno Setup. Esta nota cobre tudo desde a última release publicada (v5.1.0); a 5.2.0 só circulou como teste. O fluxo de geração e os dados do usuário não mudam.

### Novo
- **Carregamentos em modal** (giratório + barra, tempo decorrido, Cancelar): gerar, organizar e converter. Saem o toast de "iniciado" e o status dentro do quadro; a conclusão segue em modal.
- **Novo ícone do app**: bloco "C" azul sóbrio (face plana + lateral mais escura, no estilo do ícone anterior) sobre tile azul-marinho, no executável, instalador, cabeçalho e README. O servidor local também aparece como "Contracto" com o mesmo ícone no Gerenciador de Tarefas.
- **Carregamento sempre animado**: o giratório e a barra funcionam mesmo com as animações do Windows desligadas.
- **Shell Tauri**: janela nativa, diálogos do Windows, arrasto de arquivos na Conversão (com destaque da zona), instância única (abrir de novo traz a janela existente).
- Tela de espera "Iniciando o Contracto…" até o servidor local ficar pronto.
- Instalador NSIS por usuário: remove a instalação antiga do Inno Setup e o `Contracto_sidecar.exe` órfão da 5.2, preservando `%APPDATA%\Contracto`.

### Desempenho
- A janela abre em cerca de 0,8 s (antes: vários segundos extraindo o servidor a cada abertura); app utilizável em ~2,4 s.
- Chamadas à API ~5 ms (eram ~16 ms).
- Contrapartida: ~136 MB em disco (eram ~70 MB), porque o servidor agora é uma pasta instalada uma vez. O instalador tem 50.6 MiB.

### Corrigido
- **Conversão presa em "Convertendo…"** mesmo com o arquivo entregue (erro ao desenhar a lista de resultados, engolido pelo acompanhamento).
- **Anexar arquivo com acento no caminho** falhava na Conversão (pipe do servidor na página de código do Windows; agora UTF-8).
- **Tema e configurações voltando ao padrão** sem ninguém mexer (falha passageira do antivírus ao testar a pasta de dados jogava a leitura para outra pasta).
- Janela reduzida (até 1100 px): a faixa da barra superior cobria o fundo e se cortava ao meio.
- `build_exe.bat` com caminhos corrompidos e sem CRLF.
- Da 5.1.0 em diante: polimento visual (ícones SVG, animações, tooltips, stepper, guia de ajuda, tour), máscara de CNPJ, renomeio por arquivo na Conversão, pastas do Contrato, PDF/A com OutputIntent (ver CHANGELOG).

### Alterado
- Build: `build_exe.bat` → `scripts/build_tauri.py` (sidecar PyInstaller em pasta + Tauri + NSIS). Requer Rust, VS Build Tools (C++) e Node. Inno Setup removido.
- Sem auto-update: atualizar é rodar o instalador novo.
- ADR 0031, README, CHANGELOG, TAURI_CONTRATO e DEPENDENCY_REVIEW atualizados.

### Validação
- 372 testes unitários + testes de comportamento do front (Node) e 2 testes Rust: OK.
- Verificado no executável de release: janela e UI, tema (6/6 aberturas), instância única, modal de progresso (giratório, barra, Esc ignorado), barra superior em 1482/1000/700 px, anexo com acento, PDF/A via sidecar em 0,6 s.
- **Não verificado:** atualização do instalador sobre uma instalação do Inno real; arrasto real do Windows e diálogos nativos; `smoke_webview_ui.py` no shell Tauri; DPI 100–200%. O instalador não tem assinatura de código (SmartScreen pode alertar).
- PDF/A: os modelos convertidos pelo app saem sem formulário, com fontes embutidas e sem Filter no Metadata. Se o validador online apontar NeedAppearances/fonte/Filter, confira se o arquivo é o da pasta PDF-A e não o formulário preenchido.

### Artefatos
- `Contracto_Setup_v5.3.0.exe` (50.6 MiB), instalador. SHA-256: `D1C155EB5AC85C55F65F29FA9C64C69DDF5D8447DE15B3E5A18334776E8D972B`
- `Contracto_v5.3.0.zip` (65.6 MiB), portátil (`Contracto.exe` + pasta `sidecar/`). SHA-256: `54A9EC313E82BE764D9C7A01488F1CE142EB90B60A4BEAF558B3EE2F4359F528`
