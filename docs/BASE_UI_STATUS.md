# Base de Migração de UI — WebView2 Concluída

> **Estado:** a migração do **Contracto** de CustomTkinter para **WebView2** foi concluída e homologada na v4.5.18; os ajustes posteriores estão nas atualizações abaixo e no `CHANGELOG.md`.
> A suíte unitária e o fluxo de ponta a ponta em WebView real (`tests/smoke_webview_ui.py`) são o critério; contagens de testes mudam a cada versão e não são fixadas aqui.

> **Atualização v5.0.0 (28/10/2026):** Tk aposentado (ADR 0028), `sidecar` e contrato
> nativo para o Tauri (ADR 0029, `docs/TAURI_CONTRATO.md`), CNPJ corrigido, moeda com
> máscara, conferência reformulada e Etapa 1 fatiada em módulos. A troca para o shell
> Tauri aguarda os aceites listados na ADR 0029. Planejado: extração de PDF (0027) e
> conferência editável (0030).

> **Atualização v4.5.26 (27/10/2026):** formato de saída inicial pela Config (botões), visualizador responsivo, arrasto real na Conversão, perfis por modo, topbar fixa. Ver ADR 0026.

> **Atualização v4.5.24 (17/10/2026):** publicação com nome legível
> (`Contrato <Nomes>` / `(gerados)`), publicação inline em Simples/Conversão,
> conferência (formulários/extras) movida para a Etapa 2 e cores derivadas
> por tema. Ver ADR 0025. Suíte: 390 testes OK.

> **Atualização (18/10/2026):** preparação pré-Tauri na branch
> `chore/pre-tauri-prep` (ADR 0024 §1: `pywebview`/WebView2 isolados em
> `frontend/js/api.js`), correção de `POST /api/v1/system/repair` (importava
> um módulo inexistente) e do alvo do atalho de reparo. O instalador Inno
> Setup passa a reconhecer a instalação por usuário (`scripts/build_installer.py`,
> `packaging/Contracto.iss` — ADR 0008). Versão 4.5.25.
>
> **Correção (18/10/2026):** o modo Simples deixava a Etapa 1 em branco ao
> selecionar formulários com campo `TEXTO_LONGO` (`fieldControl` gravava
> `input.type` num `<textarea>` — propriedade somente leitura — e `render()`
> abortava antes de anexar o card). Reproduzido no WebView2 real com os
> perfis do usuário via probe; correção em `frontend/js/etapa1.js` e
> cobertura de regressão no fluxo do `tests/smoke_webview_ui.py`.

---

## O que foi Concluído e Entregue (v4.5.18)

1. **Integridade de HTML e Janela Maximizada**:
   - Correção de duplicação do documento HTML e adição de teste sintático estrito de parser DOM e IDs únicos (`test_integridade_html_e_ids_unicos`).
   - Shell pywebview (`app/webview_shell.py`) configurado para abrir por padrão em janela maximizada (`maximized=True`).
   - ADR 0016 registrada.

2. **Direção Visual, Fundo Decorativo e Laboratório Visual**:
   - Criação do laboratório isolado de testes de UI (`frontend/lab.html`).
   - Gerador de fundo decorativo vetorial senoidal dinâmico em canvas SVG (`desenharFundoSenoidal`) com orbes de brilho ambiente radial.
   - Refinamento de `tokens.css` e `layout.css` com cartões em vidro fosco (`backdrop-filter: blur(12px)`), tipografia moderna Inter/Roboto e paleta HSL.
   - ADR 0018 registrada.

3. **Fluxo Principal, Conferência e Proteção de Etapas**:
   - Implementação da Etapa 2 de Conferência (`<section id="tela-conferir">` em `index.html` e `conferir()` em `etapa1.js`).
   - Guardas de navegação do stepper condicionadas ao estado composto e preenchimento válido.
   - Suporte completo a áreas de texto para campos longos (`TEXTO_LONGO`, `MULTILINHA`).
   - Indicador de fila global no topo (`#indicador-fila-global`) e modal de travamento do Word COM (`alertaWordTravado()`).

4. **API de Configurações e Preferências**:
   - Endpoints REST `/api/v1/settings` (GET, POST) e `/api/v1/system/repair` (POST) na API FastAPI local.
   - Integração das telas com persistência nativa em `%APPDATA%/Contracto/contracto_config.json`.
   - ADR 0017 registrada.

5. **Gerenciador de Perfis (API REST + UI WebView)**:
   - Endpoints REST `/api/v1/profiles` (GET, POST, PUT, DELETE, POST duplicate) na API FastAPI local.
   - Interface interativa em `#tela-perfis` em WebView (`etapa1.js` e `api.js`) permitindo:
     - Criação de novos perfis.
     - Duplicação de perfis existentes.
     - Edição de campos e propriedades JSON.
     - Exportação e Cópia de JSON.
     - Exclusão com confirmação.
     - Importação via JSON payload.
   - ADRs 0019 e 0020 registradas.

6. **Componentes Auxiliares e Responsividade**:
    - Botões "Ajuda" (guia intuitivo em 3 passos) e "Sobre" (detalhes da versão 4.5.18, arquitetura local loopback sem telemetria LGPD).
   - Layout responsivo adaptado com fallback em 1024px e navegação por teclado (foco e skip-link).
   - Polling automático seguro no arranque do frontend para conectar o `ShellBridge` com zero latência.

---

## Validação e Smoke Tests Executados

| Verificação | Resultado | Evidência |
| --- | --- | --- |
| Suíte unitária completa | **PASS** (v4.5.18) | ver execução atual; sem contagem fixa |
| Testes base frontend | **PASS** | 15/15 testes (`tests/test_frontend_base.py`) |
| Testes comportamento JS | **PASS** | `tests/test_frontend_behavior.py` |
| Testes paridade Tk→WebView | **PASS** | 4/4 testes (`tests/test_frontend_parity.py`) |
| Testes backend isolado | **PASS** | 4/4 testes (`tests/test_headless_backend.py`) |
| Smoke WebView2 UI completo | **PASS** | 32/32 verificações de DOM, conferência, envio ambíguo/retomada, fila e PDF em WebView2 real (`tests/smoke_webview_ui.py`) |
| Smoke motores reais via HTTP | **PASS** | RTF→Word→PDF/A com Ghostscript real, PDF/A validado e RTF preservado (`tests/smoke_api_engines.py`) |
| `pip check` | **PASS** | Nenhuma dependência quebrada |

Gate final restante (manual/não automatizável aqui): DPI 100/125/150/200%, homologação visual de telas/resoluções. O instalador Inno Setup é gerado por `scripts/build_installer.py` (ADR 0008 — `packaging/Contracto.iss`). Release só após esse gate.

---

## P0 de release (26/09/2026) — ADR 0023/0024

Paridade P0 Tk→WebView implementada: PUT/DELETE de perfis no `LocalOnly`, backup/restore via `selection_id` backup `.zip`, ativar-perfil, settings (`tamanho_quadros`, `formato_saida`, restaurar padrões), ajuda 3 passos + Sobre + boas-vindas (`primeira_execucao`), validações cliente `CNPJ/CPF_CNPJ/PIS/EMAIL/TELEFONE/ANO`, `chk-preservar-dados` persistido e `VERSION` sincronizado (4.5.18). Cobertura em `tests/test_p0_release.py`. Tauri segue planejado sem código (ADR 0024) até o release WebView estabilizar.

## Próximos Passos (Pós v4.5.18)

> **Atualização em 20/09/2026:** os blocos 0–6 do plano residual foram implementados na branch `fix/ui-escopos-validacao` e a suíte completa (362 testes) passa. Resta apenas o gate final Windows/distribuição.

As pendências identificadas após a entrega da v4.5.18 estão formalmente registradas em:

- **ADR 0021** — [`docs/adr/0021-consolidacao-toolbar-e-modo-webview.md`](adr/0021-consolidacao-toolbar-e-modo-webview.md): consolidação da toolbar, remoção do indicador de backend, promoção do seletor de modo — ✅ concluído.
- **ADR 0022** — [`docs/adr/0022-plano-migracao-residual-tk-webview.md`](adr/0022-plano-migracao-residual-tk-webview.md): mapa completo de todas as lacunas de migração Tk → WebView2 — ✅ blocos 0–6 concluídos.
- **Plano detalhado** — [`docs/PLANO_MIGRACAO_WEBVIEW_RESIDUAL.md`](PLANO_MIGRACAO_WEBVIEW_RESIDUAL.md): blocos de trabalho priorizados com tarefas individuais e versões-alvo — ✅ concluído, ver tabela de rastreamento.

Gate final restante (Windows/distribuição): `smoke_webview_ui.py` em WebView2 real, `smoke_api_engines.py` (Word/GS reais), DPI 100/125/150/200%, encerramento/cancelamento. O instalador Inno Setup é gerado por `scripts/build_installer.py` (ADR 0008 — `packaging/Contracto.iss`). Release só após esse gate.

---

## Comandos de Validação

```powershell
# Executar a suíte de unit tests completa (Windows)
.\.venv\Scripts\python.exe -m unittest discover -s tests -v

# Executar o smoke test de UI WebView2 real
.\.venv\Scripts\python.exe tests/smoke_webview_ui.py

# Executar a suíte de testes de backend isolado
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_headless_backend.py -v
```
