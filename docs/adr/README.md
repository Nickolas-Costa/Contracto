# ADRs — Contracto

Cada implementação relevante tem seu arquivo próprio explicando o quê,
por que e como. Números sequenciais com 4 dígitos, definidos sob demanda.

## Convenção

- Arquivo: `docs/adr/NNNN-titulo-curto.md` (ver `0000-modelo.md`).
- Estados: `futura` (registrada, não implementada), `aceita` (em vigor),
  `substituída` (aponta a sucessora).
- Uma ADR por decisão; referências cruzadas só dentro de `docs/adr/`.

## Índice

| Nº | Título | Estado |
|---|---|---|
| 0000 | Modelo | — |
| 0001 | Fatiar a UI legada em mixins | aceita |
| 0002 | Identidade canônica dos módulos Python | aceita |
| 0003 | Conversão RTF pelo Microsoft Word | aceita |
| 0004 | Temporários de RTF isolados por trabalho | aceita |
| 0005 | API local loopback para o shell WebView | aceita (base na ADR 0011) |
| 0006 | API hospedada com agente local para integração empresarial | aceita (guardrail futuro) |
| 0007 | Gate de revisão contínua de dependências | aceita |
| 0008 | Instalador Inno Setup antes da troca de UI | aceita |
| 0009 | Motion em tiers com reduced-motion | aceita |
| 0010 | Pendências visuais do shell antes da WebView | aceita |
| 0011 | Base HTTP local e ponte nativa da WebView | aceita |
| 0012 | Participante modular dirigido pelo perfil | aceita |
| 0013 | Bootstrap recuperável e origem imutável da ponte | aceita |
| 0014 | Rascunho canônico e validação compartilhada | aceita |
| 0015 | Snapshot, manifesto e retomada sem duplicação | aceita |
| 0016 | Integridade de HTML e validação de DOM | aceita |
| 0017 | Persistência no backend de preferências e configurações | aceita |
| 0018 | Fundo decorativo e direção visual da WebView | aceita |
| 0019 | API CRUD no backend de perfis | aceita |
| 0020 | Gerenciador de perfis e auxiliares na WebView | aceita |
| 0021 | Consolidação da toolbar e modo na WebView | aceita |
| 0022 | Plano de migração residual Tk → WebView2 | concluída (blocos 0–6) |
| 0023 | Paridade P0 Tk → WebView para release | aceita |
| 0024 | Rota Tauri v2 pós-WebView | futura |
| 0025 | Publicação de resultados e Conferência (Etapa 2) | aceita |
| 0026 | Formato inicial pela Config, topbar fixa e arrasto na Conversão | aceita |
| — | Extração de dados de PDF geral (anexar PDF com infos do cliente e o sistema busca) | futura (pós nova UI, fora de escopo atual) |
