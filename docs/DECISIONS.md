# Contracto — Product & Engineering Decisions

> **Source of truth:** decisões fundamentais de produto, experiência,
> arquitetura e limites. Consultar antes de nova feature, dependência ou
> mudança visual/arquitetural.

**Status:** Em definição
**Versão:** 1.0 (Contracto v4.5.9)
**Última atualização:** 2026-09-08

## 1. Propósito

Automação local de contratos habitacionais e declarações, sem alterar
cláusulas legais. Reduzir digitação, erro e tempo de dossiê.

> **O sistema preenche campos e organiza pastas. A responsabilidade legal
> dos dados é do usuário.**

## 2. O que o Contracto é / não é

É: preenchedor AcroForm, organizador de dossiês, conversor PDF/A-2b offline,
gestor de perfis MCMV/SBPE/custom.
Não é: editor jurídico, CRM/ERP, substituto bancário/governamental, SaaS.

## 3. Modos e multi-seleção (v4.5.9)

Modo Avançado = contrato completo 2 etapas. Modo Simples = emissão rápida
com **multi-seleção por checkboxes** (`combinar_perfis`); incompatibilidade
de `id/tipo/escopo` bloqueia com `AlertModal` explicativo, sem merge
silencioso. `formularios_basicos_selecionados` persiste em config.

## 4. Local-first e LGPD

100% offline, `-dSAFER`, sem `shell=True`, `taskkill /FI USERNAME`,
sanitização `CON/PRN/AUX/NUL/COM1-9/LPT1-9`. Dados em
`%APPDATA%/Contracto/`. Detalhes em `PRIVACIDADE.md`.

## 5. RTF/Word — Windows-only temporário

`rtf_converter` exige MS Word via COM. Decisão: **manter Windows-only**,
detectar e falhar com mensagem amigável se ausente. Evolução futura:
sidecar LibreOffice (`soffice`) ou serviço headless — registrado, não
implementado. Não bloquear pywebview por isso.

## 6. Ghostscript

Embutido em `assets/gs/bin`, headless `CREATE_NO_WINDOW`, `-dSAFER`.
Futuro: `externalBin`/sidecar + allowlist `capabilities shell`.

## 7. Direção UI: pywebview intermediário → Tauri V2

Tauri foi avaliado (mesmo dilema OSSYNC: toolchain Rust/Node cara).
Decisão: **Fase A pywebview + FastAPI loopback** (reuso `services/`),
**Fase B Tauri V2 + React+TS+Vite + sidecar Python** (updater assinado).
Nada de Fase A/B implementado — ver `ARCHITECTURE.md`.

## 8. Regras para agentes IA

- Não introduzir dependência sem problema concreto + custo avaliado.
- Não tocar `services/` com imports UI; UI não faz I/O direto de PDF.
- `clareza > confiabilidade > simplicidade > performance > estética`.
- Todo novo perfil precisa de teste em `tests/test_*formulario*.py`.

## 9. Decisões abertas

Protocolo pywebview↔Python, estrutura sidecar Tauri, updater, logging/
backup, port `pdf_service` p/ Rust vs manter Python (bundle ~100MB+).
