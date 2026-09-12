# ADR 0010 — Pendências visuais do shell antes da WebView

- **Estado:** futura
- **Data:** 2026-09-12
- **Contexto:** quatro pontos onde o shell Tk atual mais difere de uma janela web e que, se levados como estão, viram retrabalho no frontend: stepper só recolore (não navega), toolbar com larguras fixas estoura abaixo de 1100px, processo sem DPI-awareness (blur em 125%/150%) e modais com tamanho fixo sem limite de viewport.
- **Decisão:** especificar antes da primeira tela web e implementar no shell novo (no Tk, só correções seguras e isoladas): stepper clicável com rota por etapa; toolbar com colapso/hambúrguer abaixo de 1100px; `PerMonitorV2` no processo com teste em 100/125/150/200%; modais com `clamp()` nunca maiores que a viewport.
- **Alternativas consideradas:** levar o layout Tk como está para a web (reproduz os mesmos defeitos em outra tecnologia); corrigir tudo no Tk antes (retrabalho que a migração descartaria); ignorar DPI e telas pequenas (base real de usuários em 125%).
- **Consequências:** o frontend web nasce responsivo; o Tk recebe apenas correções que não mudam comportamento. O protótipo fora do versionamento serve de referência visual, não de código.
- **Arquivos:** futuros shell web e tokens; `main_window.py` (stepper/toolbar), `app/main.py` (DPI), `theme.configurar_janela_modal`, `docs/DESIGN.md`, `docs/GUIA_OPEN_DESIGN.md`.
- **Revisão:** compatível com `DESIGN.md` (checklist de tela, grade base 4, responsividade) e ADR 0001 (mixins `mw_stepper`/`mw_layout` são o mapa do que migrar); sem nova dependência (ADR 0007 ok).
- **Aceite:** stepper navega por clique com estado atual marcado; toolbar íntegra em 1024px; texto nítido em 125%/150%; nenhum modal excede a viewport em 1366x768.
- **Testes:** roteiro manual de responsividade (1024/1366/1920, DPI 100–200); teste de `clamp()` unitário quando existir; navegação do stepper coberta por teste de ponta a ponta headless.
