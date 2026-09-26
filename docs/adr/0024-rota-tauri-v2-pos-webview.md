# ADR 0024 — Rota Tauri V2 pós-WebView (planejada, sem código)

- **Estado:** proposta (sem implementação até o release WebView estabilizar)
- **Data:** 2026-09-26
- **Contexto:** `DECISIONS.md §7` e `ARCHITECTURE.md Fase B` mantêm Tauri V2 como futuro opcional. O P0 WebView (ADR 0023) congela o contrato UI↔backend para reuso.
- **Decisão:** quando o release WebView estiver homologado:
  1. Congelar o contrato (`api.js` como adaptador; componentes sem `window.pywebview` direto).
  2. Passar o gate `DEPENDENCY_REVIEW.md` para Rust/Node/sidecar/bundler/updater.
  3. Prova isolada `src-tauri/` + sidecar Python reutilizando `services/`; `capabilities` mínimas (dialog, fs escopo `appDataDir`, shell allowlist GS); migração `%APPDATA%/Contracto/*.json` → `appDataDir` com fallback.
  4. Repetir aceite `DESIGN.md §10` (Simples multi, Avançado, conflito, falha entre páginas, cancelamento, teclado-only, fila, PDFs reais).
  5. Trocar `Contracto.iss` por bundler/updater Tauri somente se confirmado; preservar dados na desinstalação; versionar por `app/version.py` + `VERSION` + tag.
- **Consequências:** nenhum código Tauri neste release; nenhum serviço reescrito em Rust; sem SQLite/updater antes da decisão.
- **Testes:** os mesmos do gate WebView, reexecutados no shell Tauri quando existir.
