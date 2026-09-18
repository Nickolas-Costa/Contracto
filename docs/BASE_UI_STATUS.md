# Base de Migração de UI — WebView2 Concluída

> **Estado em 17/09/2026:** A migração do aplicativo **Contracto** de CustomTkinter para a nova interface **WebView2** foi integralmente concluída e homologada (v4.5.18).
> A suíte completa de 355 testes unitários e os testes de fluxo de ponta a ponta DOM em WebView real (`tests/smoke_webview_ui.py`) passam com 100% de sucesso.

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
   - Botões "Ajuda" (guia intuitivo em 4 passos) e "Sobre" (detalhes da versão 4.5.18, arquitetura local loopback sem telemetria LGPD).
   - Layout responsivo adaptado com fallback em 1024px e navegação por teclado (foco e skip-link).
   - Polling automático seguro no arranque do frontend para conectar o `ShellBridge` com zero latência.

---

## Validação e Smoke Tests Executados

| Verificação | Resultado | Evidência |
| --- | --- | --- |
| Suíte unitária completa | **PASS** | 355 testes em 33.361s, 0 falhas, 0 erros |
| Testes base frontend | **PASS** | 12/12 testes (`tests/test_frontend_base.py`) |
| Testes comportamento JS | **PASS** | `tests/test_frontend_behavior.py` |
| Testes backend isolado | **PASS** | 4/4 testes (`tests/test_headless_backend.py`) |
| Smoke WebView2 UI completo | **PASS** | 37/37 verificações de DOM, modal, fila e PDF/A em WebView2 real (`tests/smoke_webview_ui.py`) |

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
