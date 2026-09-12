# ADR 0007 — Gate de revisão contínua de dependências

- **Estado:** aceita
- **Data:** 2026-09-12
- **Contexto:** o Contracto combina bibliotecas Python, binários externos e automação Windows para gerar documentos. Uma dependência conveniente no desktop pode impedir portabilidade, aumentar superfície de ataque ou inviabilizar API hospedada. Essas trocas precisam ser avaliadas de forma recorrente, não apenas quando surge um problema.
- **Decisão:** toda dependência nova, atualização relevante ou mudança de ambiente deve passar pelo checklist em `DEPENDENCY_REVIEW.md`: capacidade entregue, alternativa em código puro ou já distribuída, custo de processo/licença/rede, compatibilidade por ambiente, teste e estratégia de substituição. Word continua restrito ao desktop/agente Windows assistido; alternativas de RTF devem passar por prova de fidelidade antes de qualquer troca. O gate se aplica também a dependências transitivas que passem a ser distribuídas ou executadas diretamente.
- **Alternativas consideradas:** decidir caso a caso sem registro (perde rastreabilidade e repete discussão); trocar dependências por preferência técnica (pode degradar documentos ou criar custo comercial); reescrever PDF/RTF em código próprio (não justificado pelo risco e pela complexidade atuais).
- **Consequências:** mudanças de dependência exigem uma decisão breve e teste proporcional. O inventário torna explícito que API local e hospedada têm restrições diferentes. A equipe ganha um caminho para reduzir dependências, mas não remove uma biblioteca sem ganho concreto de segurança, fidelidade, custo ou portabilidade.
- **Arquivos:** `docs/DEPENDENCY_REVIEW.md`, `docs/DECISIONS.md`, `docs/SPEC_PRE_WEBVIEW.md`, ADRs futuras de API e conversão.
