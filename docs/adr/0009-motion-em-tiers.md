# ADR 0009 — Motion em tiers com reduced-motion

- **Estado:** futura
- **Data:** 2026-09-12
- **Contexto:** animações e timers hoje são incondicionais (spinner, gradiente, toasts, countdown), sem escala de duração nem respeito a `prefers-reduced-motion`. Na UI nova, movimento sem regra vira ruído e barreira de acessibilidade.
- **Decisão:** adotar tiers — imediato (clique, foco), 120–180ms (hover, abertura de modal), 180–250ms (transições de etapa e paginação). Proibidos: pulse infinito, zoom em hover, cascatas e fade geral. Com `prefers-reduced-motion`, tudo vira imediato e as ondas desligam. Vale para a UI nova; no Tk atual só entra se for trivial e sem risco.
- **Alternativas consideradas:** biblioteca de animação (poder sem necessidade para motion funcional); manter timers ad hoc (estado atual, sem previsibilidade); animar tudo com a mesma duração (ignora hierarquia de atenção).
- **Consequências:** cada animação nova declara seu tier; auditoria mapeia os timers existentes para tiers antes da migração; `DESIGN.md` é a referência de movimento.
- **Arquivos:** futuros tokens CSS/tema, `docs/DESIGN.md`, inventário de timers (`animated_loader`, modais, toasts).
- **Revisão:** compatível com `DESIGN.md` (movimento só funcional) e `DECISIONS.md §9` (teclado/acessibilidade); passa pelo gate da ADR 0007 sem nova dependência (CSS/atributos Tk nativos).
- **Aceite:** nenhuma animação fora de tier; com reduced-motion ativo, zero movimento não essencial; countdown e progressos continuam informando sem animar.
- **Testes:** checklist manual com reduced-motion ligado; teste de presença de tiers nos tokens (quando existirem); sem teste de pixel.
