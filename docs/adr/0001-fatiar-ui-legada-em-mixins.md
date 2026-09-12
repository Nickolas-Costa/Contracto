# ADR 0001 — Fatiar a UI legada em mixins

- **Estado:** aceita
- **Data:** 2026-09-12
- **Contexto:** `MainWindow` e `ProfilesFrame` concentravam, respectivamente, a navegação, a geração, a fila e a edição de perfis em arquivos extensos. Isso dificultava revisar mudanças antes da transição para a WebView e aumentava o risco de alterar um fluxo não relacionado.
- **Decisão:** manter as classes e suas interfaces atuais, distribuindo seus métodos em mixins por responsabilidade. `MainWindow` orquestra toolbar, stepper, modos, telas, layout, etapas e fila; `ProfilesFrame` orquestra lista e editor. A extração preserva os corpos dos métodos e a UI Tk continua sendo a implementação vigente. Os mixins são uma organização transitória do shell legado; o backend web reutilizará `services/` e `ports/`, não esses widgets.
- **Alternativas consideradas:** manter os monólitos (revisões e manutenção continuariam difíceis); reescrever a UI já na WebView (misturaria reorganização e mudança de comportamento sem uma linha de base estável); substituir imediatamente por composição de objetos (exigiria reescrever chamadas internas e estado compartilhado).
- **Consequências:** a resolução de métodos depende da ordem de herança e os mixins ainda compartilham o estado das classes principais; futuras mudanças precisam verificar imports no módulo que contém o método. A guarda de imports Tk deve permitir apenas os módulos que de fato o usam. A suíte automatizada e a inicialização real da janela são os gates de regressão; a jornada manual da UI continua necessária antes de lançar uma versão.
- **Arquivos:** `app/ui/main_window.py`, `app/ui/mw_*.py`, `app/ui/profiles_frame.py`, `app/ui/pf_*.py`, `tests/test_port_dialog.py`, `tests/test_visual_assets.py`, `docs/ARCHITECTURE.md`.
