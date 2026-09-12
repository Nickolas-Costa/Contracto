# Contracto — Product & Engineering Decisions

> **Source of truth:** decisões fundamentais de produto, experiência,
> arquitetura e limites. Consultar antes de nova feature, dependência ou
> mudança visual/arquitetural.

**Status:** Em definição
**Versão:** 1.1 (Contracto v4.5.10)
**Última atualização:** 2026-09-09

## 1. Propósito

Automação local de contratos habitacionais e declarações, sem alterar
cláusulas legais. Reduzir digitação, erro e tempo de dossiê.

> **O sistema preenche campos e organiza pastas. A responsabilidade legal
> dos dados é do usuário.**

## 2. O que o Contracto é / não é

É: preenchedor AcroForm, organizador de dossiês, conversor PDF/A-2b offline,
gestor de perfis MCMV/SBPE/custom.
Não é: editor jurídico, CRM/ERP, substituto bancário/governamental, SaaS.

## 3. Modos e multi-seleção (v4.5.9+)

Modo Avançado = contrato completo 2 etapas. Modo Simples = emissão rápida
com **multi-seleção por checkboxes** (`combinar_perfis`); incompatibilidade
de `id/tipo/escopo` bloqueia com `AlertModal` explicativo, sem merge
silencioso. `formularios_basicos_selecionados` persiste em config.
Desde v4.5.10: paginação fixa acima do botão gerar, quadros vazios se
ocultam sozinhos e contador de pendências trava o botão até tudo pronto.

## 4. Local-first e LGPD

100% offline, `-dSAFER`, sem `shell=True`, `taskkill /FI USERNAME`,
sanitização `CON/PRN/AUX/NUL/COM1-9/LPT1-9`. Dados em
`%APPDATA%/Contracto/`. Detalhes em `PRIVACIDADE.md`.

## 5. RTF/Word — Windows-only temporário

`rtf_converter` exige MS Word via COM. Decisão: **manter Windows-only**.
Se o Word estiver instalado e travar: avisar com contagem regressiva,
depois encerrar só o processo filho. Se ausente: mensagem direta
pedindo o Word instalado (sem oferecer LibreOffice). Não bloquear
pywebview por isso.

## 6. Ghostscript

Embutido em `assets/gs/bin`, headless `CREATE_NO_WINDOW`, `-dSAFER`.
Na Fase A vai como `externalBin` do bundle (mesmo binário, chamado via
allowlist do shell); sidecar dedicado só se o bundle exigir. Sem Rust:
o Python continua dono da conversão.

## 7. Direção UI: pywebview agora, Tauri V2 como futuro opcional

Decisão: seguir pelo **pywebview + FastAPI loopback** (reuso
`services/`), que resolve a dor atual sem Rust/Node. **Tauri V2 segue
como plano futuro** — será reavaliado quando o app estiver estável e
se updater/instalador/tamanho virarem necessidade real. Preparação
pronta: ports, contrato de camadas, prova headless e deps travadas.
Sem atualizador automático até a migração de shell (decisão consciente).

## 8. Regras para agentes IA

- Não introduzir dependência sem problema concreto + custo avaliado.
- Toda dependência nova, atualização relevante ou mudança de ambiente passa pelo checklist em `DEPENDENCY_REVIEW.md`.
- Não tocar `services/` com imports UI; UI não faz I/O direto de PDF.
- `clareza > confiabilidade > simplicidade > performance > estética`.
- Todo novo perfil precisa de teste em `tests/test_*formulario*.py`.

## 9. Reuso e acessibilidade por teclado (regra permanente, v4.5.10)

- **Toda função/componente reutilizável nasce genérica:** sem dependência
  de tela específica, com docstring de 1 linha, parâmetros explícitos e
  retorno documentado. Config específica herda/estende o genérico —
  nunca copia-e-cola (ex: futuros modais herdam `BaseModal`).
- **App inteiro navegável por teclado, com lógica clara:** ordem de foco =
  ordem visual (cima→baixo, esquerda→direita); foco sempre visível;
  `Esc` fecha modais e dispensa avisos temporários (toasts);
  `Enter`/`Espaço` acionam o botão focado; `Tab` percorre os controles;
  atalhos documentados; nenhuma ação essencial exige mouse. Toda tela
  nova é testada só com teclado antes de liberada.
- **Guia inicial (boas-vindas):** abre só na primeira execução, nunca se
  esconde sozinho e apresenta o fluxo em 4 passos, sem jargão interno.

## 10. Próximas decisões e evolução comercial

A próxima implementação é o protocolo pywebview↔Python: FastAPI em loopback estrito, token efêmero, contratos Pydantic e trabalhos canceláveis. Os requisitos estão em `SPEC_PRE_WEBVIEW.md` e a decisão futura em ADR 0005.

Uma integração empresarial pode evoluir para agente local Windows conectado a um CRM/ERP. API hospedada e processamento remoto ficam deliberadamente fora da Fase A: dependem de requisitos comerciais, LGPD, operação e licenciamento do Word; ver ADR 0006. Backup de dossiês permanece decisão aberta.
