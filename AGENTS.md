# Contracto — instruções para trabalho no repositório

Aplicação desktop Windows, Python, CustomTkinter; preparação de API local e WebView em andamento. Antes de continuar a migração, leia `docs/CONTINUIDADE_CODEX_WEB.md`, `docs/SPEC_PRE_WEBVIEW.md`, `docs/ARCHITECTURE.md` e `docs/adr/`.

## Validação

- Windows: `.venv/Scripts/python.exe -m unittest discover -s tests -v`.
- Smoke real: `.venv/Scripts/python.exe tests/smoke_test_gui.py`.
- Linux com Tk/Xvfb: `xvfb-run -a .venv/bin/python -m unittest discover -s tests -v` e `xvfb-run -a .venv/bin/python tests/smoke_test_gui.py`.
- Backend isolado: `python -m unittest discover -s tests -p test_headless_backend.py -v`.
- Ambiente: `python -m pip check`. Instalar `requirements-dev.txt`; consultar o plano antes de usar o lock Windows em Linux.

Usar dados sintéticos e diretórios temporários; nunca alterar perfis/configuração pessoais nos testes. Registrar skips e limitações de plataforma. Word COM/WebView2/instalador exigem Windows; a suíte Linux não os homologa.

## Limites arquiteturais

Manter serviços sem UI/Tk. A API desta fase é loopback, com token efêmero e arquivos autorizados, conforme especificação. PDF simples independe de Word/Ghostscript; RTF depende de Word e PDF/A de Ghostscript. Não adicionar fallback silencioso. Toda mudança de dependência deve responder ao gate de `docs/DEPENDENCY_REVIEW.md`.

O protótipo ZIP está ignorado e não está disponível no checkout remoto. Consulte os documentos de design versionados e registre a ausência quando houver trabalho visual. Entregue mudanças focadas com testes e limitações explícitas.
