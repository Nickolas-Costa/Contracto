# ADR 0029 — Preparação "Tauri Ready"

- **Estado:** aceita (preparação concluída); **a troca de shell depende de aceite**
  (ver *Precisa do seu aceite*). Detalha e atualiza a ADR 0024.
- **Data:** 2026-10-28
- **Contexto:** a ADR 0024 manteve o Tauri v2 como rota futura, com cinco passos. O
  passo 1 (congelar o contrato) estava feito pela metade: o `api.js` isolava o evento de
  prontidão, mas cada função ainda chamava `pywebview.api.*` por conta própria, e o
  backend só existia embutido no shell pywebview.
- **Decisão:** concluir tudo que **não exige instalar Rust nem trocar o instalador** e
  deixar o restante como um roteiro com pontos de aceite.

## Feito (sem nova dependência)

1. **Contrato nativo único** (`frontend/js/api.js`): todas as chamadas nativas passam por
   `nativo(nome, args)`, com comandos nomeados fixos. Sob Tauri vira
   `invoke(nome, args)`; sob pywebview, `pywebview.api[nome](...)`. Documentado em
   `docs/TAURI_CONTRATO.md` e travado por `tests/api_adapter.cjs`.
2. **Sidecar headless** (`app/sidecar.py`): mesma API loopback sem janela, com aperto de
   mão `ready` (origem + token) e canal de controle por stdin (`register`, `result_dir`,
   `file_path`, `shutdown`). Resolve o ponto que a ADR 0024 deixou aberto: como o shell
   nativo autoriza caminhos **sem** expor uma rota que a página possa chamar (o
   `ShellBridge.request` deixa a página alcançar qualquer `/api/v1/*`, então um endpoint
   HTTP que aceitasse caminho furaria o modelo de seleções).
3. **Tk removido** (ADR 0028): um frontend só, nenhuma dependência de GUI Python.
4. **Transporte confirmado**: HTTP loopback com token efêmero (alternativa A da 0024).
5. **Frontend modular** sem bundler: `perfis.js`, `conferencia.js`, `calendario.js`
   fatiados da Etapa 1; o React+TS+Vite da ADR 0024 pode entrar tela a tela.

## Roteiro da troca (passos 2–5 da ADR 0024)

| Passo | Entrega | Gate |
|---|---|---|
| 2 | Revisão de dependências Rust/Node/bundler/updater (linhas novas em `DEPENDENCY_REVIEW.md`) | aceite do §Dependências |
| 3 | `src-tauri/` mínimo: janela, `request`, diálogos, sidecar `externalBin` (`Contracto_sidecar.exe` via PyInstaller), arrasto | aceite do §Toolchain |
| 4 | Repetir o aceite de `DESIGN.md §10` e `smoke_webview_ui.py` no shell Tauri | — |
| 5 | Decidir bundler/updater Tauri **ou** manter o Inno Setup (ADR 0008); migrar `%APPDATA%/Contracto` para `appDataDir` com fallback | aceite do §Distribuição |

## Precisa do seu aceite

1. **Toolchain na máquina de build**: Rust (rustup, `stable-x86_64-pc-windows-msvc`),
   Visual Studio Build Tools (C++), Node (já presente) e `@tauri-apps/cli`. Isso cria
   `src-tauri/`, `Cargo.lock` e `package.json`/lockfile no repositório.
2. **Crates/pacotes**: `tauri` 2.x, `tauri-plugin-dialog`, `tauri-plugin-opener`
   (e, se aprovado, `tauri-plugin-updater`), `serde`, `serde_json`, `reqwest` (só
   loopback). Cada um passa pelo gate; escolho versões **fixadas** com data ≥ 2 semanas.
3. **Distribuição**: manter o **Inno Setup** (recomendado: preserva dados, mutex e fluxo
   atual) ou migrar para o bundler NSIS/MSI do Tauri; e se haverá **auto-update** (exige
   chave de assinatura e um servidor de releases — fora do local-first estrito).
4. **Tamanho/arquitetura**: o PyInstaller continua gerando o sidecar (~70 MB); o ganho do
   Tauri é o shell (WebView2 já presente), não o pacote total.
5. **Frontend**: continuar em JS puro modular (recomendado agora) ou migrar para
   React+TS+Vite — decisão que muda o processo de build e a matriz de dependências.

## Riscos e mitigação

- **Paridade de segurança do `request`**: o Rust precisa repetir a allowlist, o limite de
  1 MiB e a checagem de página autorizada; coberto por testes de contrato a escrever
  contra o sidecar real (os casos de `test_webview_bridge.py` viram a especificação).
- **Dois processos** (Rust + sidecar): o sidecar sai em EOF do stdin, então não sobra
  processo órfão se o shell morrer.
- **Assinatura de código**: sem certificado, SmartScreen continua alertando (igual hoje).

## Aceite desta preparação

`tests/api_adapter.cjs`, `tests/test_sidecar.py` e a suíte completa verdes; WebView2 real
(`smoke_webview_ui.py`) inalterado.
