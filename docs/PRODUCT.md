# Contracto — Produto

> Resumo operacional do produto. Decisões normativas em `DECISIONS.md`
> (source of truth). Visual em `DESIGN_SYSTEM.md`. Técnica em `ARCHITECTURE.md`.

## O que é

**Contracto é automação local de contratos habitacionais e declarações.**

Ferramenta desktop Windows, 100% offline, para imobiliárias, correspondentes
bancários e profissionais do setor habitacional. Preenche formulários PDF
(AcroForm), organiza dossiês e converte para **PDF/A-2b (ISO 19005-2)**.

Princípio central:

> **O sistema não altera cláusulas legais. Ele preenche campos com os dados
> fornecidos pelo usuário e organiza o dossiê.**

## Modos de operação

1. **Avançado (Contratos Habitacionais)** — fluxo 2 etapas:
   Etapa 1 gera documentos de 1–4 participantes (CPF/CNPJ validado, data,
   destino). Etapa 2 anexa documentos extras, converte em lote p/ PDF/A-2b e
   cria a estrutura de pastas padronizada.
2. **Simples (Formulários Únicos, v4.5.9+ multi-seleção)** — emissão rápida:
   seletor `✓ Formulários selecionados: N` com checkboxes, composição via
   `profile_composer.combinar_perfis`, `[x] Preservar dados para Reutilizar`
   para emitir em sequência sem redigitar.

## Modelos oficiais suportados

- Declaração PPE, Primeiro Imóvel, FORM CLIENTE / MO 30.844,
  ITBI (isenção Lei 1648/2023), Isenção Tributos Municipais,
  DAMP MO 29.300-039, Seguro MO 30.825-005, Form Cliente MO 30.844-012,
  perfis MCMV / SBPE / personalizados.

## Limites (não é)

Editor jurídico, validador legal de cláusulas, CRM/ERP, substituto de
sistemas bancários/governamentais, serviço em nuvem, chatbot.

## Privacidade

Local-first absoluto: zero nuvem, zero telemetria. Detalhes em
`docs/PRIVACIDADE.md`. Dados nunca saem da máquina salvo cópia manual
pelo usuário.
