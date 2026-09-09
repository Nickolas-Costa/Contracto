# Contracto — Arquitetura

> Estado técnico atual (v4.5.9) e direção alvo (`DECISIONS.md §7`).
> Complexidade só entra com problema concreto que a justifique.

## Estado atual (v4.5.9) — desktop CustomTkinter + PyInstaller

```
app/main.py             → entrypoint (CTk, maximizado, timers rastreados p/ destroy limpo)
app/version.py          → fonte única (__version__ = "4.5.9", espelho em VERSION)
app/ui/main_window.py   → monolito 2237+ linhas: toolbar, modos, stepper, fila, geração
app/ui/                 → profiles/settings/participant/document/campo_dinamico/
                          date_picker/modais/toast/animated_loader/theme (tokens + get_icon)
app/services/           → puros, sem tkinter: generator, pdf_service (AcroForm),
                          pdfa_converter (Ghostscript -dSAFER), rtf_converter
                          (Word COM, Windows-only), stage2_service, queue_manager,
                          profile_composer (combinar_perfis multi-seleção v4.5.9),
                          mapping_engine/audit, field_calculator, system_repair
app/utils/              → cpf/cnpj/pis/document/date/filename/profile/config/
                          resource_path (sys._MEIPASS)/json_storage/logger/
                          file_picker (ÚNICO com tkinter.filedialog — isolar)
app/models/participant  → dataclass puro, JSON-serializável
app/assets/             → config/perfis_iniciais.json, templates/*.pdf (todos os
                          modelos oficiais juntos, sem subpastas),
                          icons/*_dark/_light.png, gs/bin (embutido)
dados usuário            → %APPDATA%/Contracto/ (gitignored; sobrevive a updates)
                          contracto_config.json, perfis, logs/app.log
build                    → build_exe.bat (lê app/version.py) + PyInstaller
                          --noconsole --onefile --add-data assets/* + scripts/
                          setup_gs/create_shortcut/create_dist_package
```

Fluxo: **Preencher (Etapa 1) → Anexar/Converter PDF/A (Etapa 2) → Pastas padronizadas**.

## Direção futura — pywebview intermediário, depois Tauri V2 (sem implementação)

> Nenhum código `pywebview/Tauri` existe neste repo hoje — não há
> `server.py FastAPI`, `package.json`, projeto Rust ou `src-tauri`.
> Não deve ser lido como estado atual.

```
Fase A (próxima): pywebview sobre WebView2 + backend Python loopback 127.0.0.1
├── server.py FastAPI (reuso services/ puros como endpoints)
├── ui/ HTML/CSS/JS estáticos (tokens de DESIGN_SYSTEM.md → CSS)
└── build PyInstaller + WebView2 (mesmo padrão ATLAS/OSSYNC)

Fase B (futura): Tauri v2 + React+TS+Vite + Python sidecar + SQLite
├── Interface: React + TS + Vite (+ Design System)
├── Núcleo: comandos Tauri ↔ Python sidecar (geração, PDF/A, pastas)
└── Armazenamento: appDataDir (migração de %APPDATA%/Contracto/*.json)
```

Migração incremental: ports → headless proof → shell pywebview →
Design System web → Etapa 1/2 → perfis/settings → updater/bundler.

## Regras

- Loopback estrito futuro (`127.0.0.1`), zero telemetria, sem CDN/fontes externas.
- `services/` nunca importa `tkinter/customtkinter`; `file_picker` morre no web
  (trocado por `plugin-dialog` / `pywebview.open_file_dialog`).
- `rtf_converter` segue **Windows-only com Word** (decisão registrada);
  fallback LibreOffice documentado como evolução, não implementado.
- Versionamento: `app/version.py` + espelho `VERSION` + tags `vX.Y.Z`.
