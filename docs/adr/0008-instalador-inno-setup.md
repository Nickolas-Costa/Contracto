# ADR 0008 — Instalador Inno Setup antes da troca de UI

- **Estado:** aceita
- **Data:** 2026-09-12
- **Atualização:** 2026-09-21
- **Contexto:** hoje a distribuição é um ZIP extraído à mão, sem entrada no Painel de Controle, sem desinstalador e sem checagem de pré-requisitos. Antes da troca de UI (que trará WebView2 como requisito), a instalação precisa ser padrão Windows.
- **Decisão:** criar `packaging/Contracto.iss` gerando `Contracto-Setup-<versão>-x64.exe`: instalação por usuário em `%LOCALAPPDATA%\Programs\Contracto` (sem admin), atalho, entrada no Painel de Controle, `AppMutex` alinhado ao mutex do app, checagem de WebView2 com mensagem (sem download silencioso) e desinstalador que remove o programa mas preserva `%APPDATA%\Contracto` (dados do usuário, conforme privacidade).
- **Alternativas consideradas:** manter só o ZIP (zero custo, mas sem padrão Windows nem checagem de requisitos); MSI/WiX (mais poderoso, porém toolchain e curva maiores para o ganho atual); MSIX/Store (exige conta, certificados e revisão externa).
- **Consequências:** build ganha etapa com Inno Setup instalado na máquina de release; versionamento do instalador acompanha `app/version.py`; dados do usuário nunca são apagados na desinstalação. A implementação foi registrada em `packaging/Contracto.iss` e na etapa de build em `build_exe.bat` com gate de dependência do Inno Setup (`ISCC.exe`).
- **Arquivos:** `packaging/Contracto.iss`, `build_exe.bat`, `scripts/build_installer.py`, `tests/test_release_installer.py`, `docs/MANUAL_DE_TESTE.md`.
- **Revisão:** compatível com `DECISIONS.md §7` (distribuição) e ADR 0007 (instalador não baixa nada sozinho; WebView2 é checagem, não download).
- **Aceite:** instala e desinstala limpo em Windows 10 e 11 sem admin; ícone e versão corretos; segunda instalação com app aberto é bloqueada; desinstalar preserva os dados e remove o programa.
- **Testes:** roteiro manual em máquina limpa (instalar, abrir, desinstalar, reinstalar); automação de release para garantir `ISCC` presente antes do build e a versão do instalador alinhada com a app.
- **Implementação registrada:** o fluxo de release agora exige a presença do Inno Setup e gera o instalador em `dist/Contracto_Installer_v<versao>.exe` como parte da etapa final de build.
