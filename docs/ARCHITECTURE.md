# Contracto — Arquitetura

> Estado técnico atual (v5.5.0) e direção alvo (`DECISIONS.md §7`).
> Complexidade só entra com problema concreto que a justifique.

## Estado atual (v5.5.0) — shell Tauri + sidecar Python sobre API local loopback

A UI é WebView2 desde a v4.5.18 e a interface Tk foi **removida na v5.0.0** (ADR 0028).
A produção roda no **shell Tauri** (`src-tauri/`, ADR 0031): o Rust abre a janela com `frontend/`,
fala com o backend headless `app/sidecar.py` (pasta PyInstaller `sidecar/`) e expõe a ponte nativa
de `docs/TAURI_CONTRATO.md`. `app/main.py` + `app/webview_shell.py` ficam como shell pywebview legado
(desenvolvimento e smokes).

```
app/main.py             → entrypoint (shell WebView, instância única via mutex)
app/sidecar.py          → backend headless para o Tauri (handshake + canal de controle)
app/version.py          → fonte única (__version__, espelho em VERSION)
frontend/                → UI de produção (HTML/CSS/JS sem bundler): index.html, css/,
                          js/ (api.js = único ponto que conhece o shell; etapa1/perfis/
                          conferencia/calendario/etapa2/conversao/ui/app/form-state)
app/services/           → puros, sem UI: generator, pdf_service (AcroForm),
                          pdfa_converter (Ghostscript -dSAFER), rtf_converter
                          (Word COM + aviso com prazo), stage2_service, queue_manager,
                          profile_composer, mapping_engine/audit, field_calculator,
                          geometria_formulario, system_repair (não encerra o Word do usuário)
app/utils/              → cpf/cnpj/pis/document/date/filename/profile/config/
                          resource_path/caminhos/json_storage/logger (PII mascarado,
                          rotação)/backup/files_fs/instancia_unica
app/ports/              → webview_dialog/storage/binaries (importáveis como app.* ou curto)
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

Fluxo do Contrato: **Preencher (Etapa 1) → Conferir, anexar e escolher o formato (Etapa 2) → gerar, converter e organizar em um clique → Resultado (Etapa 3)** (ADR 0032).

## Histórico das fases

`app/server.py` e `app/api/` implementam a API loopback (base de 13/09/2026, ADR 0011);
a fila existente foi estendida para operações independentes. Veja `BASE_UI_STATUS.md`.

```
Fase A (concluída, v4.5.18): WebView2 + Python loopback 127.0.0.1
├── server.py FastAPI (reuso services/ puros como endpoints)
├── frontend/ HTML/CSS/JS estáticos (tokens de DESIGN_SYSTEM.md → CSS)
└── shell pywebview (hoje legado: desenvolvimento e smokes)

Fase B (parcial, v5.3.0): shell Tauri v2 + sidecar Python (ADR 0029/0031)
├── Feito: janela, ponte nativa e diálogos em Rust; instalador NSIS
├── v5.5.0: atualização pelo app, só a pedido do usuário (ADR 0032)
└── Não adotado até aqui: React+TS+Vite e SQLite
    (a UI segue JS puro; os dados seguem em %APPDATA%/Contracto/*.json)
```

## Convenção de publicação de resultados (ADR 0025)

- **Contrato:** geração intermediária em `Contrato <Nomes> (gerados)`; trabalho
  final em `Contrato <Nomes>` (`nome_pasta_processo`, Title Case com acentos).
- **Simples/Conversão:** arquivos publicados direto na pasta escolhida.
- Colisões recebem sufixo ` (2)`, ` (3)`… — nunca sobrescreve. Em Contrato o
  trabalho usa pasta privada `.contracto-*` e só a renomeia no sucesso.

O shell WebView chama uma API FastAPI apenas em loopback, documentada em `SPEC_PRE_WEBVIEW.md`. Essa fronteira também prepara futura integração empresarial por agente local; não representa uma API pública nem hospedada.

## Regras do shell web (Fase A)

Valem para qualquer implementação do shell, antes da primeira tela:

- Stepper clicável com rota por etapa (o atual só recolore).
- Toolbar com colapso abaixo de 1100px (larguras fixas não passam).
- DPI por monitor no processo; janelas e modais com limite de viewport
  (nada de tamanho fixo maior que a tela).
- Diálogos pelo shell (`plugin-dialog` no Tauri, `ports/webview_dialog.py` no pywebview); abrir-pasta devolve `{ok, code}`.
- Referência visual e de fluxos: protótipo fora do versionamento
  (`Protótipo-webview-do-sistema.zip`: telas, fluxos, PNGs por modelo,
  handoff e manifesto) + `docs/DESIGN.md` como autoridade.

## Contrato de camadas (vale desde já, não só na migração)

- `frontend/` desenha e coleta: monta os campos, lê valores, exibe resultados.
  Não decide regra de negócio nem faz I/O de documentos.
- `services/` decide por dados: recebe `Path`, `Perfil`, `Participant`
  e devolve resultados. Nunca importa UI.
- `utils/` sustenta os dois: caminhos, validadores, arquivos, backup.
- `ports/` isola o que muda de shell (diálogos, pastas, binários).

## Regras

- Loopback estrito futuro (`127.0.0.1`), zero telemetria, sem CDN/fontes externas. Única saída para a
  internet: a consulta de atualização feita pelo Rust quando o usuário pede (a página segue sem rede).
- `services/` nunca importa UI; os diálogos nativos são do shell (`pywebview` hoje,
  `plugin-dialog` no Tauri).
- `rtf_converter` segue **Windows-only com Word** (decisão registrada);
  fallback LibreOffice documentado como evolução, não implementado.
- Versionamento: `app/version.py` + espelho `VERSION` + tags `vX.Y.Z`.
