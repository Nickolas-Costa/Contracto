# ADR 0018 — Fundo Decorativo Orgânico, Glassmorphism e Direção Visual na WebView

Status: aceita e em implementação em 17/09/2026.

## Contexto

A versão legada Tkinter do Contracto apresentava uma identidade visual marcante caracterizada por linhas e ondas sinusoidais diagonais desenhadas no Canvas (inspiradas em softwares de alta produtividade como PDFCreator), aliadas a um esquema de cores primárias dinâmicas configuráveis pelo usuário. A migração inicial para WebView necessita resgatar e evoluir essa personalidade visual, adicionando recursos modernos como Glassmorphism (efeito vidro translúcido com `backdrop-filter`), micro-interações responsivas, suporte estrito a `prefers-reduced-motion`, modo escuro aprimorado e alto contraste.

## Decisão

1. **Laboratório Visual Isolado (`frontend/lab.html`)**:
   - Implementar um ambiente de testes visual desacoplado para exibição e validação contínua de todos os tokens CSS, variações de estado (hover, focus, disabled), cartões translúcidos, stepper em 4 passos, modais e o fundo decorativo.

2. **Sistema de Fundo Decorativo Orgânico (SVG + CSS/Canvas)**:
   - Renderizar em camada de fundo (`z-index: -1`) ondas senoidais vetoriais dinâmicas com destaque nas linhas primárias, acompanhando a cor de destaque do tema.
   - Adicionar orbes de brilho ambiente gradiente (radial glow) nas extremidades para proporcionar profundidade visual e sensação *premium*.
   - Respeitar a preferência `prefers-reduced-motion` e a configuração de alto contraste, suavizando ou desativando animações quando indicado.

3. **Evolução do Design System (Tokens e Layout)**:
   - **Superfícies**: Adicionar elevação com profundidade e Glassmorphism (`backdrop-filter: blur(12px)` com bordas sutis `rgba(255,255,255,0.12)`).
   - **Tipografia**: Gradientes sutis em cabeçalhos principais (`h1`) e hierarquia tipográfica límpida com a fonte Segoe UI / Inter.
   - **Micro-interações**: Transições fluidas em botões, campos de texto com anéis de foco coloridos (`ring-focus`) e modais com entrada em escala/suavização.

## Consequências e Evidência

O aplicativo Contracto ganha uma atmosfera *premium*, viva e moderna na WebView, preservando a familiaridade visual da versão clássica com desempenho de renderização vetorial a 60 FPS sem impacto de CPU. O laboratório visual passa a servir como referência viva e isolada para QA visual de novos componentes.
