# Design — Contracto

> Identidade visual própria e intransferível: o que está aqui vale
> somente para este app.

## 1. Identidade em uma frase

**Sóbrio, leve e focado:** a interface de quem trata documento oficial.
Nada compete com o conteúdo; tudo conduz ao dossiê pronto.

- **Sóbrio:** superfícies neutras, uma única cor de destaque, sem ruído.
- **Leve:** janelas rápidas, sombras rasas, movimento só funcional.
- **Focado:** uma tarefa por tela, progresso sempre visível, teclado total.

## 2. Assinatura: as Ondas (uso intencional, não decoração)

Três linhas senoidais sutis na cor de destaque atravessam os fundos
principais. Elas são a linguagem do app, com significado fixo: **o fluxo
contínuo do dossiê — da entrada dos dados à conclusão.**

Regras da assinatura:

- Aparece em: fundo da janela principal, telas vazias e boas-vindas.
- Nunca sobre conteúdo denso, nunca atrás de texto corrido.
- Opacidade baixa; 3 linhas acompanham a cor de destaque do tema.
- Com `reduced-motion` ou no modo Sólido, some sem perda de função.
- Não copiar para outros projetos: a assinatura é exclusiva deste app.

## 3. Tokens de cor

| Token | Claro | Escuro | Uso |
|---|---|---|---|
| `primary` | configurável (padrão `#005CA9`, azul institucional) | idem | ações, seleção, foco |
| `primary-hover` | 22% mais escuro | idem | hover de ação |
| `primary-light` | mistura 40/60 com branco | adaptado p/ contraste | badges, realces |
| `background` | `#F5F5F5` | `#1E1E1E` | fundo + ondas |
| `surface` | `#FFFFFF` | `#2B2B2B` | cartões, modais |
| `surface-variant` | `#F0F0F0` | `#333333` | campos inativos |
| `border` | `#E0E0E0` | `#424242` | divisórias |
| `text` | `#212121` | `#E0E0E0` | alta ênfase |
| `text-secondary` | `#666666` | `#AAAAAA` | apoio |
| `success` | `#2E7D32` | `#2E7D32` | êxito |
| `warning-badge` | `#B45309` | `#B45309` | insígnia de alerta (5.02:1 c/ branco) |
| `error` | `#D32F2F` | `#D32F2F` | erro |
| `info` | `primary` | `primary-text` | informativo |

Branco sobre cor só com contraste ≥ 4.5:1 (medido, não estimado).

## 4. Tipografia, espaço e forma

- **Família:** Segoe UI no desktop; na web, pilha do sistema
  (`"Segoe UI", system-ui, sans-serif`). Pesos 400/600; evitar 700+.
- **Escala:** título 24 / seção 20 / cartão 16 / corpo 14 / apoio 12.
- **Grade base 4:** 4, 8, 12, 16, 24, 32.
- **Raios:** cartão 12, botão 12, campo 8 (eatual: botão 12; reavaliar
  para 8 na web, ver guia do agente).
- **Elevação:** sombra rasa única em modais e toast; nada de glow.
- **Ícones:** contorno 1.5px, cantos arredondados, pares claro/escuro;
  na web, SVG em sprite (fim dos PNG por tema).

## 5. Movimento (só funcional)

- Imediato: respostas de clique e foco.
- 120–180ms: hover, abertura de modal.
- 180–250ms: transições de etapa e paginação.
- Proibido: pulse infinito, zoom em hover, cascatas e fade geral.
- `prefers-reduced-motion`: tudo vira imediato; ondas desligam.

## 6. Componentes (comportamento, não só aparência)

- **Botões:** primário (destaque) / secundário (neutro c/ borda);
  foco inicial na ação principal; `Enter`/`Espaço` acionam.
- **Cartões:** superfície + borda sutil; um assunto por cartão.
- **Campos:** rótulo acima, borda 8px, validação silenciosa com
  pendências listadas (nunca vermelhão em massa).
- **Stepper:** 2 etapas clicáveis com estado atual marcado.
- **Paginação:** barra fixa acima da ação; páginas vazias se ocultam.
- **Modais:** herdam `BaseModal` (overlay, `Esc`, foco com devolução,
  trava opcional); conteúdo curto e um caminho principal.
- **Toasts:** borda presa à janela, dispensa por `Esc` ou tempo.
- **Seletores:** controle segmentado estável (sem deslocar a barra).

## 7. Teclado (regra permanente)

Ordem de foco = ordem visual; foco sempre visível; `Esc` fecha/dispensa;
`Tab` percorre; nenhuma ação essencial exige mouse. Detalhe em
`DECISIONS.md §9`. Toda tela nova é testada só com teclado.

## 8. Tokens CSS (base para a web)

```css
:root {
  --c-primary: #005CA9;
  --c-primary-hover: #00467F;
  --c-primary-light: #99C2E2;
  --c-bg: #F5F5F5;
  --c-surface: #FFFFFF;
  --c-surface-variant: #F0F0F0;
  --c-border: #E0E0E0;
  --c-text: #212121;
  --c-text-secondary: #666666;
  --c-success: #2E7D32;
  --c-warning-badge: #B45309;
  --c-error: #D32F2F;
  --font: "Segoe UI", system-ui, sans-serif;
  --r-card: 12px; --r-button: 12px; --r-input: 8px;
}
[data-theme="dark"] {
  --c-bg: #1E1E1E;
  --c-surface: #2B2B2B;
  --c-surface-variant: #333333;
  --c-border: #424242;
  --c-text: #E0E0E0;
  --c-text-secondary: #AAAAAA;
}
```

As ondas na web: SVG com 3 `path` senoidais em `var(--c-primary)`
a ~12% de opacidade, atrás do conteúdo, `aria-hidden`, desligável.

## 9. Assinatura intransferível

A linguagem deste documento (tokens, ondas, componentes) pertence a
este app. Nada daqui migra para outros projetos sem redefinição
própria — e nada de fora entra sem passar pelo checklist §10.

## 10. Checklist antes de cada tela nova

1. Cabe em "sóbrio, leve e focado"? 2. As ondas estão no lugar certo (§2)?
3. Tokens, sem cor solta? 4. Contraste medido? 5. Funciona só com teclado?
6. `reduced-motion` respeitado? 7. Um assunto por cartão? 8. Erros listados,
não gritados? 9. Copiado de outro app? (volte ao §9) 10. Cabe em 1024px?
