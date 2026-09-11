# Guia — Direção de Design System + Prompt p/ o agente Open Design

## Veredito: quais famílias servem ao Contracto-web (e por quê)

1. **Fluent 2 (Microsoft) — base principal.** Usuário 100% Windows,
   futuro em WebView2/Tauri: integração nativa de graça (controles,
   profundidade rasa, motion). Tom institucional combina com "sóbrio".
2. **Carbon (IBM) — referência de formulários.** Nascido para apps densos
   de formulários e documentos: padrões de campos, validação silenciosa,
   tabelas e assistentes. Copiar os padrões, não a cara.
3. **shadcn — régua de neutralidade.** Paleta neutra funcional e raios
   contidos; usar como controle de "menos é mais".

Evitar: Material 3 (colorido e arredondado demais p/ documento oficial),
Ant Design (datado e pesado p/ este escopo), qualquer coisa
"glassmorphism/neon" (quebra o §1 do DESIGN.md).

## O que pegar de cada um

- Fluent 2: controles, foco visível, motion e profundidades.
- Carbon: padrões de formulário, validação, stepper, empty states.
- shadcn: neutralidade de cor e contenção visual.
- Próprio (intransferível): ondas na cor de destaque (§2 do DESIGN.md).

## Prompt pronto (colar no agente)

> Desenhe o design system web do **Contracto**, app desktop Windows de
> automação de contratos habitacionais (preenche formulários PDF,
> organiza dossiês, converte para PDF/A). Identidade: **sóbrio, leve e
> focado** — interface de documento oficial, nada compete com o conteúdo.
>
> **Assinatura obrigatória:** 3 linhas senoidais sutis na cor de destaque
> (#005CA9, configurável) como fundo — significam o fluxo do dossiê.
> Opacidade ~12%, atrás do conteúdo, `aria-hidden`, desligável, nunca
> sobre texto denso. É proposital e intransferível.
>
> **Base:** controles e motion do Fluent 2, padrões de formulário do
> Carbon, neutralidade do shadcn. Sem Material colorido, sem glassmorphism.
>
> **Tokens (obrigatórios):** light bg #F5F5F5 / surface #FFFFFF /
> text #212121; dark bg #1E1E1E / surface #2B2B2B / text #E0E0E0;
> success #2E7D32, warning-badge #B45309, error #D32F2F; raios 12/12/8;
> grade base 4; fonte pilha do sistema (Segoe UI primeiro); pesos 400/600.
> Contraste AA medido (branco sobre cor ≥ 4.5:1).
>
> **Componentes:** botão primário/secundário, cartão de assunto único,
> campo com rótulo acima e validação silenciosa, stepper clicável de
> 2 etapas, paginação fixa acima da ação, modal com Esc + foco inicial +
> devolução de foco, toast ancorado dispensável por Esc, seletor
> segmentado estável.
>
> **Teclado total:** ordem de foco = ordem visual, foco visível,
> Enter/Espaço acionam, Tab percorre, nenhuma ação exige mouse.
> Respeitar prefers-reduced-motion (ondas desligam).
>
> **Entregar:** tokens CSS (`:root` + `[data-theme="dark"]`), SVG das
> ondas parametrizável por cor, e as telas Etapa 1 / Etapa 2 / Perfis /
> Configurações / modais em HTML+CSS estático navegável por teclado.
> Não invente nova assinatura visual.

## Critério de aceite do resultado

Roda o checklist §10 do DESIGN.md sobre cada tela entregue; qualquer
"não" volta para ajuste antes da implementação.
