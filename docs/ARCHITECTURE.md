# Contracto — Arquitetura

> Estado técnico atual (v4.5.15) e direção alvo (`DECISIONS.md §7`).
> Complexidade só entra com problema concreto que a justifique.

## Estado atual (v4.5.15) — desktop CustomTkinter + PyInstaller

```
app/main.py             → entrypoint (CTk, maximizado, instância única via mutex)
app/version.py          → fonte única (__version__ = "4.5.15", espelho em VERSION)
app/ui/main_window.py   → orquestra mixins (toolbar/stepper/modos/telas/
                          layout/etapa1/etapa2/fila em mw_*.py)
app/ui/                 → profiles (orquestra pf_lista/pf_editor) + settings/
                          participant/document/campo_dinamico/
                          date_picker/base_modal+6 modais/toast/animated_loader/theme
app/services/           → puros, sem tkinter: generator, pdf_service (AcroForm),
                          pdfa_converter (Ghostscript -dSAFER), rtf_converter
                          (Word COM + aviso com prazo), stage2_service, queue_manager,
                          profile_composer, mapping_engine/audit, field_calculator,
                          geometria_formulario, system_repair
app/utils/              → cpf/cnpj/pis/document/date/filename/profile/config/
                          resource_path/caminhos/json_storage/logger (PII mascarado,
                          rotação)/backup/files(+files_fs puro)/instancia_unica
                          file_picker (implementação Tk do port de diálogos)
app/ports/              → dialog/storage/binaries (importáveis como app.* ou curto)
app/models/participant  → dataclass puro, JSON-serializável
app/assets/             → config/perfis_iniciais.json + geometria_modelos.json,
                          templates/*.pdf, icons/, gs/bin (embutido)
dados usuário            → %APPDATA%/Contracto/ (gitignored; sobrevive a updates)
                          config, perfis, logs/app.log (2 MB x5), backups/
build                    → build_exe.bat (lê app/version.py, SHA-256 do ZIP)
                          + PyInstaller + scripts/ (setup_gs com falha explícita)
testes                   → suíte unittest + prova headless (Etapa 1+2 sem UI)
deps web                 → pywebview + fastapi + uvicorn travados (Fase A)
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
└── build PyInstaller + WebView2

Fase B (futura): Tauri v2 + React+TS+Vite + Python sidecar + SQLite
├── Interface: React + TS + Vite (+ Design System)
├── Núcleo: comandos Tauri ↔ Python sidecar (geração, PDF/A, pastas)
└── Armazenamento: appDataDir (migração de %APPDATA%/Contracto/*.json)
```

Migração incremental: ports → headless proof → shell pywebview →
Design System web → Etapa 1/2 → perfis/settings → updater/bundler.

O shell WebView chama uma API FastAPI apenas em loopback, documentada em `SPEC_PRE_WEBVIEW.md`. Essa fronteira também prepara futura integração empresarial por agente local; não representa uma API pública nem hospedada.

## Regras do shell web (Fase A)

Valem para qualquer implementação do shell, antes da primeira tela:

- Stepper clicável com rota por etapa (o atual só recolore).
- Toolbar com colapso abaixo de 1100px (larguras fixas não passam).
- DPI por monitor no processo; janelas e modais com limite de viewport
  (nada de tamanho fixo maior que a tela).
- Diálogos pelo `ports/dialog.py`; abrir-pasta devolve `{ok, erro}`.
- Referência visual e de fluxos: protótipo fora do versionamento
  (`Protótipo-webview-do-sistema.zip`: telas, fluxos, PNGs por modelo,
  handoff e manifesto) + `docs/DESIGN.md` como autoridade.

## Contrato de camadas (vale desde já, não só na migração)

- `ui/` desenha e coleta: monta widgets, lê valores, exibe resultados.
  Não decide regra de negócio nem faz I/O de documentos.
- `services/` decide por dados: recebe `Path`, `Perfil`, `Participant`
  e devolve resultados. Nunca importa `tkinter`/`customtkinter`.
- `utils/` sustenta os dois: caminhos, validadores, arquivos, backup.
  Exceção documentada: `utils/files.py` conhece widgets só para
  `atualizar_entry` (ponte fina da interface, sem regra).
- `ports/` isola o que muda de shell (diálogos, pastas, binários).

Exemplo aplicado: `abrir_pasta` e `atualizar_entry` saíram duplicados
de `main_window.py`/`document_frame.py` para `utils/files.py`; as telas
mantêm delegadores finos de compatibilidade.

## Regras

- Loopback estrito futuro (`127.0.0.1`), zero telemetria, sem CDN/fontes externas.
- `services/` nunca importa `tkinter/customtkinter`; `file_picker` morre no web
  (trocado por `plugin-dialog` / `pywebview.open_file_dialog`).
- `rtf_converter` segue **Windows-only com Word** (decisão registrada);
  fallback LibreOffice documentado como evolução, não implementado.
- Versionamento: `app/version.py` + espelho `VERSION` + tags `vX.Y.Z`.
