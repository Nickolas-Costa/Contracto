# ADR 0031 — Shell Tauri e instalador NSIS (v5.3.0)

- **Estado:** aceita. Conclui os passos 2–5 da ADR 0029 e substitui a ADR 0008.
- **Data:** 2026-11-02

## Decisão

1. **Shell Tauri 2** (`src-tauri/`) é a produção. O Rust abre a janela com `frontend/` (`tauri.localhost`, sem
   capabilities para a página), guarda origem e token do sidecar só em memória e implementa os comandos de
   `docs/TAURI_CONTRATO.md` com a mesma lista de caminhos permitidos e o mesmo limite de 1 MiB do `ShellBridge`.
2. **Sidecar em pasta** (PyInstaller onedir, `resources` → `sidecar/`). O arquivo único extraía ~60 MB no `%TEMP%`
   a cada abertura (e o antivírus examinava tudo de novo); a pasta é instalada uma vez. Custo: ~136 MB em disco no
   lugar de ~70 MB; o instalador continua com ~50 MB por causa da compressão.
3. **Janela imediata**: nasce oculta, aparece quando o sidecar diz `starting` (mutex adquirido) e os comandos
   esperam o `ready`. Segunda instância: `already_running`, sem janela (instância única vem do sidecar).
4. **Instalador NSIS do Tauri** por usuário; hook remove a instalação antiga do Inno Setup (preserva
   `%APPDATA%\Contracto`) e o `Contracto_sidecar.exe` órfão das builds 5.2 em arquivo único. **Sem auto-update.**
5. **UTF-8 no pipe do sidecar** (caminhos acentuados) e pasta de dados resolvida uma vez por sessão, com repetição
   no teste de escrita (o antivírus segura o arquivo de teste e a leitura caía em outra pasta).
6. **Carregamentos em modal** (`ContractoUI.abrirProgresso`): giratório + barra (medida ou deslizante), sem X/Esc,
   com Cancelar quando o trabalho permite. Substitui toast de "iniciado" e o cartão de status dentro do quadro.

## Consequências

- Build: Rust (MSVC), VS Build Tools (C++) e Node, além do Python (`build_exe.bat` → `scripts/build_tauri.py`).
- O shell pywebview (`app/main.py`, `webview_shell.py`) fica só como legado de desenvolvimento e referência de testes.
- Pendentes: `smoke_webview_ui.py` no shell Tauri, teste de atualização sobre o Inno real, assinatura de código.
