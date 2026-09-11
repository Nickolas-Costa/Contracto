# Design — Contracto

> Sistema visual e de interação do Contracto. Identidade: **sóbrio, leve e focado**. Nada compete com o conteúdo; tudo conduz ao dossiê pronto.

**Revisão:** 2.0 · 10 de setembro de 2026  
**Base examinada:** Contracto 4.5.14, conforme `app/version.py`.  
**Destino deste arquivo:** substituir `docs/DESIGN.md` no repositório Contracto.  
**Situação:** especificação para a futura UI web; não representa uma migração já implementada.

## 1. Decisão de design system

Adotar o **Design System Contracto**, próprio, com Fluent 2 como referência principal de interação desktop e Carbon como referência complementar de formulários extensos. Manter a neutralidade já defendida em `GUIA_OPEN_DESIGN.md`; shadcn permanece referência de contenção, sem constituir uma terceira linguagem visual ou dependência obrigatória.

Essa direção atende a profissionais que preenchem documentos habitacionais repetidamente, trabalham com dados pessoais e precisam identificar pendências, conferir arquivos e concluir processos com previsibilidade. O critério de decisão continua sendo:

**clareza > confiabilidade > simplicidade > performance > estética**

| Referência | O que orienta | Limite de adoção |
|---|---|---|
| Fluent 2 | Tokens semânticos, controles previsíveis, foco, temas e profundidade discreta | Não copiar a aparência de um produto Microsoft nem exigir Fluent UI React |
| Carbon | Agrupamento de campos, exposição progressiva e orientação para correção | Não importar a marca IBM, sua paleta ou seu shell de navegação |
| Guia próprio do Contracto | Azul configurável, Segoe UI, ondas, fluxo em duas etapas, simplicidade | Governa a composição e os valores visuais do aplicativo |

Fluent 2 é a melhor base pelo contexto Windows e pela necessidade de uma experiência de ferramenta de trabalho. Isso é uma decisão de projeto: usar WebView2 não torna controles HTML nativos nem acessíveis automaticamente. Carbon complementa a organização dos formulários sem justificar uma segunda biblioteca de componentes. A distinção entre valores fundamentais e aliases semânticos segue a [documentação de tokens do Fluent 2](https://fluent2.microsoft.design/design-tokens); os agrupamentos e a exposição progressiva têm apoio no [padrão de formulários do Carbon](https://carbondesignsystem.com/patterns/forms-pattern/).

Não adotar Material 3 como base nesta migração: a orientação mais recente do projeto já substitui a inspiração do catálogo antigo por superfícies neutras e expressão contida. Não introduzir biblioteca, framework ou pacote de ícones sem avaliar necessidade, acessibilidade, licença, tamanho e manutenção.

## 2. Autoridade e divergências resolvidas

`DECISIONS.md` governa produto e limites arquiteturais. Este arquivo governa a futura linguagem visual e os comportamentos de apresentação. `ARCHITECTURE.md` descreve a direção técnica; o código revela o que está implementado. Uma mudança de produto não pode ser aprovada indiretamente por uma regra visual.

Para a UI web, este documento substitui regras visuais conflitantes de `DESIGN_SYSTEM.md` e do prompt em `GUIA_OPEN_DESIGN.md`. O catálogo antigo continua útil para localizar recursos da UI CustomTkinter. Ao integrar esta revisão, ajustar os apontamentos em `PRODUCT.md`, `README.md`, `ARCHITECTURE.md` e `GUIA_OPEN_DESIGN.md` para evitar duas fontes visuais concorrentes.

| Divergência observada | Resolução para a UI web |
|---|---|
| Catálogo antigo usa `#1E6FB3`; design provisório e `_DEFAULTS` usam `#005CA9`; `theme.py` ainda possui fallback antigo | Padrão é `#005CA9`. Preservar a cor já salva pelo usuário; não substituir preferências na migração |
| Catálogo antigo menciona Material 3 e vidro fosco | Fluent 2 orienta interação; superfícies de conteúdo são opacas. Overlay escurecido não implica vidro ou blur |
| `SPACING_LARGE` é 14 no código, mas a documentação define grade de 4 | Na web, usar 16 para esse passo. A regra não altera o código Python nesta revisão |
| Botão com raio 12; design provisório sugere reavaliar 8 | Manter 12 para botões e cartões, 8 para campos, como o guia existente exige. Mudança futura precisa de revisão explícita |
| Borda sutil era usada também para delimitar campos | Separar divisor decorativo de borda de controle perceptível |
| Verde/vermelho únicos para qualquer tema | Preservar preenchimentos de estado; no escuro, mensagens usam texto neutro legível acompanhado de insígnia e rótulo |
| Foco inicial sempre no botão principal | Foco contextual: primeiro campo em edição; título em conteúdo extenso; ação segura em confirmação destrutiva |
| Arquitetura registra base 4.5.9 e migração não implementada | Referência examinada é 4.5.14. Há `ports/` e teste headless, mas não foi encontrado shell pywebview/Tauri |

O termo “institucional” descreve sobriedade. Não permite sugerir vínculo oficial com banco, cartório, órgão público ou Microsoft.

## 3. Escopo e invariantes do produto

Contracto automatiza localmente o preenchimento AcroForm, a organização de dossiês e a conversão PDF/A-2b. Não edita cláusulas, não valida juridicamente documentos e não funciona como CRM, ERP ou SaaS.

- Windows continua sendo a plataforma de referência. A conversão RTF depende do Microsoft Word por COM; trocar o shell não elimina essa dependência.
- Operação offline, sem conta, nuvem, telemetria, CDN ou fonte remota. Recursos visuais e ajuda essencial acompanham o aplicativo.
- O backend mantém validações, composição de perfis, cálculos, manipulação de PDFs, arquivos e processos. A UI coleta dados e apresenta estados.
- Identificadores persistentes de perfis e campos não podem ser substituídos por nomes visuais, índices de linha ou posição no DOM.
- Não adicionar persistência de dados de clientes, histórico permanente de dossiês ou recuperação automática de rascunhos como efeito colateral da migração.
- Toda função essencial deve funcionar com teclado. Aparência personalizável nunca pode eliminar a legibilidade.
- O princípio “100% local” deve ser descrito como comportamento do produto, sem prometer conformidade jurídica automática ou certificação de documentos.

### Cobertura obrigatória

| Área | Capacidade existente a preservar | Direção de apresentação |
|---|---|---|
| Início / modo Simples | Multisseleção de formulários compatíveis; emissão PDF; reutilização opcional dos dados | Seleção explícita, contexto de formulário/página e uma ação de emissão |
| Início / modo Avançado | Perfil de contrato, 1–4 participantes conforme perfil, duas etapas | Preenchimento seguido de conversão e organização |
| Participantes e campos globais | Tipos, máscaras, cálculos, condições e limites definidos no perfil | Seções por assunto, dependências compreensíveis, ordem estável |
| Etapa 2 | Formulários selecionáveis, anexos, destino e formato PDF ou PDF/A-2b | Revisão do conjunto antes de finalizar |
| Fila | Lotes sequenciais, minimização, progresso, cancelamento e resultados | Resumo acessível no shell e detalhes sob demanda |
| Perfis | Criar, ativar, duplicar, editar, excluir, importar, exportar, backup e restaurar | Lista operacional e editor dedicado |
| Configuração de modelos | PDF, campos AcroForm, mapeamento, conferência e pré-visualização | Área de trabalho ampla; preservar página inteira e alternativa por lista |
| Configurações | Tema, destaque, local, largura dos quadros, restauração e diagnóstico/reparo | Grupos de ajustes; ações de manutenção separadas do salvamento |
| Ajuda | Boas-vindas em quatro passos, termos, privacidade e terceiros | Conteúdo local, legível e reabrível |

## 4. Composição e navegação

### Shell desktop

Preservar os acessos **Início, Perfis, Configurações e Ajuda**. O modo Simples/Avançado pertence ao contexto de Início; não é uma navegação concorrente. A fila permanece acessível durante a navegação.

Usar cabeçalho neutro com nome do aplicativo, navegação e resumo da fila. O título da tarefa, perfil ou seleção aparece na área principal. Não criar dashboard de métricas, sidebar permanente ou tela inicial promocional para um fluxo que começa no preenchimento.

Estrutura das telas de emissão:

1. Cabeçalho global e navegação.
2. Contexto da tarefa: modo, perfil/formulários e etapas quando aplicáveis.
3. Área de formulário com uma rolagem principal.
4. Barra de paginação, imediatamente acima da faixa de ações.
5. Resumo de pendências, ação de correção e ação principal.

A faixa inferior deve participar do layout, por exemplo com grade de linhas `auto auto minmax(0, 1fr) auto`, em vez de cobrir o conteúdo com posicionamento absoluto. Reservar espaço para mensagens que ocupem mais de uma linha. Não empilhar duas barras fixas sobre o último campo.

### Proporções e adaptação

- Meta desktop: 1024 × 768 CSS px; verificar também 1366 × 768 e 1920 × 1080. O mínimo atual do código é 920 × 680; preservar acesso aos controles nessa dimensão.
- Larguras máximas propostas para `tamanho_quadros`: Pequeno 880, Médio 1120, Grande 1360 CSS px. Manter as chaves persistidas; esses valores são especificação web, não reprodução das dimensões Tk.
- Margens externas de 24 px em janelas amplas, 16 px em janelas estreitas; conteúdo centralizado com `width: 100%` e limite de largura.
- Abaixo de 960 CSS px, reorganizar navegação e grupos de campos. Abaixo de 720, usar uma coluna e permitir quebra na faixa de ações. Abaixo de 520, colocar a faixa no fluxo quando a altura útil for insuficiente.
- Não fixar `min-width` global. Usar `min-width: 0` nos filhos de flex/grade e quebra de nomes/caminhos longos. Não esconder conteúdo para mascarar overflow.
- Campo curto pode compartilhar linha com outro campo relacionado; nomes, endereços e explicações precisam de largura suficiente. Não reproduzir quatro participantes comprimidos lado a lado.
- Zoom de 200% deve preservar leitura e operações. Testar reflow em 320 CSS px como condição de acessibilidade, sem transformar o aplicativo em um produto mobile.
- Pré-visualização de PDF pode ter zoom e pan próprios; o formulário e os comandos ao redor continuam utilizáveis sem rolagem horizontal da janela.

## 5. Identidade visual

### Superfícies e assinatura

Preservar os neutros e a cor principal da marca existente. Um cartão agrupa um assunto; subseções internas usam espaço e títulos, sem um cartão para cada campo. Sombras ficam restritas a superfícies flutuantes. Não aplicar gradientes de preenchimento ao shell, blur em formulários ou efeitos de brilho.

As **três ondas senoidais** representam o fluxo contínuo do dossiê e são a única assinatura expressiva. Usar SVG local, três traços, cor de destaque, opacidade máxima de 12%, `aria-hidden="true"`, sem foco e sem captura de ponteiro.

Podem aparecer nas margens livres do fundo principal, em boas-vindas e em estados vazios. Nunca atrás de texto, campos, listas de pendências ou pré-visualizações. Se não houver espaço livre, ocultar. Não animar continuamente. Desligar em `prefers-reduced-motion`, `forced-colors` e na opção Sólido prevista pelo design anterior. A preferência Sólido ainda precisa ser implementada na UI web; não presumir uma chave de configuração já existente.

No trabalho denso, reservar a cor de destaque para a ação principal; seleção e foco usam tratamento neutro de alto contraste. No máximo duas regiões de destaque visíveis: por exemplo, ação principal e ondas. Cores semânticas só aparecem quando há um estado real, sempre com texto ou ícone. Não pintar cada título, checkbox e item ativo de azul.

### Tipografia

Uma família é intencional neste produto utilitário. Preservar **Segoe UI**, com fallback local; não carregar fontes da internet. Display e corpo compartilham a família por consistência e densidade, sem introduzir tipografia editorial.

| Papel | Tamanho / entrelinha | Peso | Aplicação |
|---|---|---|---|
| Título de tela | 24 / 30 px | 600 | Uma vez por área principal |
| Título de seção/modal | 20 / 26 px | 600 | Agrupamentos e diálogos |
| Subtítulo | 16 / 24 px | 600 | Assuntos dentro do formulário |
| Corpo e controle | 14 / 22 px | 400; 600 em ação | Valores, rótulos e comandos |
| Apoio | 12 / 18 px | 400 | Metadados não essenciais |

Mensagens de erro e instruções necessárias permanecem em 14 px. Tracking 0 no corpo, 0.02em em botões e rótulos de navegação, 0.01em no apoio; usar 0.06em quando caixa alta for necessária. Preferir “Gerar documentos e avançar” a texto integralmente em maiúsculas. Parágrafos de ajuda limitados a 65ch, alinhados à esquerda. Valores e contagens usam numerais tabulares; mono apenas para identificadores técnicos e diagnóstico.

### Espaço, forma e tamanho

Grade de 4 px: **4, 8, 12, 16, 24, 32, 48**. Distância de 8 px entre rótulo e campo; 16 px entre campos; 24 px entre grupos; 24 px de padding em cartões amplos, 16 px em composição estreita.

Raios: cartão/modal **12 px**, botão **12 px**, campo **8 px**. Borda visual de 1 px; foco de 2 px com separação de 2 px. Controles interativos com alvo mínimo de **44 × 44 CSS px**; o glifo pode medir 16–20 px dentro desse alvo. Não usar botões gigantes, cápsulas generalizadas nem ícones em todo título.

## 6. Tokens canônicos para a web

Os valores abaixo convertem a paleta existente para OKLch; os neutros têm croma zero. Não foram escolhidos pela aparência de outro aplicativo. `#FFFFFF` permanece como superfície clara e texto de insígnia porque faz parte da marca já definida.

São três níveis: valores de marca, papéis semânticos e componentes. Componentes consomem os papéis; nenhum componente recalcula cores de forma independente. A cor escolhida pelo usuário é uma entrada de personalização, não autorização para substituir todos os papéis pelo mesmo valor.

```css
:root {
  color-scheme: light;
  --bg: oklch(0.970151 0 0);                /* #F5F5F5 */
  --surface: oklch(1 0 0);                 /* #FFFFFF */
  --surface-variant: oklch(0.955140 0 0);    /* #F0F0F0 */
  --fg: oklch(0.247759 0 0);               /* #212121 */
  --muted: oklch(0.510278 0 0);            /* #666666 */
  --border: oklch(0.906701 0 0);           /* #E0E0E0; divisor */
  --control-border: var(--muted);
  --accent: oklch(0.473630 0.143574 252.440);       /* #005CA9 */
  --accent-hover: oklch(0.390242 0.113709 251.070); /* #00467F */
  --accent-soft: oklch(0.795598 0.063172 242.051);  /* #99C2E2 */
  --on-accent: oklch(1 0 0);
  --accent-text: var(--accent);
  --primary-border: var(--accent);
  --success: oklch(0.523432 0.134659 144.167);      /* #2E7D32 */
  --warn: oklch(0.555283 0.145505 48.998);         /* #B45309 */
  --danger: oklch(0.567989 0.200180 26.406);       /* #D32F2F */
  --on-status: oklch(1 0 0);
  --success-text: var(--success);
  --warn-text: var(--warn);
  --danger-text: var(--danger);
  --focus: var(--fg);
  --selection-bg: var(--fg);
  --selection-fg: var(--surface);
  --overlay: oklch(0 0 0 / 0.60);
  --shadow-floating: 0 8px 24px oklch(0 0 0 / 0.16);
  --font-display: "Segoe UI", system-ui, sans-serif;
  --font-body: "Segoe UI", system-ui, sans-serif;
  --font-mono: Consolas, "Courier New", monospace;
  --text-title: 24px;
  --text-section: 20px;
  --text-subtitle: 16px;
  --text-body: 14px;
  --text-caption: 12px;
  --space-1: 4px; --space-2: 8px; --space-3: 12px;
  --space-4: 16px; --space-6: 24px; --space-8: 32px;
  --space-12: 48px;
  --radius-card: 12px; --radius-button: 12px; --radius-input: 8px;
  --control-min: 44px;
  --motion-feedback: 120ms;
  --motion-overlay: 180ms;
  --motion-step: 200ms;
  --motion-ease: cubic-bezier(0.2, 0, 0, 1);
  --layer-content: 0; --layer-actions: 10; --layer-popover: 20;
  --layer-toast: 30; --layer-modal: 40;
}
[data-theme="dark"] {
  color-scheme: dark;
  --bg: oklch(0.235031 0 0);                /* #1E1E1E */
  --surface: oklch(0.289080 0 0);           /* #2B2B2B */
  --surface-variant: oklch(0.321093 0 0);   /* #333333 */
  --fg: oklch(0.906701 0 0);               /* #E0E0E0 */
  --muted: oklch(0.738019 0 0);            /* #AAAAAA */
  --border: oklch(0.379094 0 0);           /* #424242; divisor */
  --accent-text: var(--accent-soft);
  --primary-border: var(--accent-soft);
  --success-text: var(--fg);
  --warn-text: var(--fg);
  --danger-text: var(--fg);
}
:where(button, input, select, textarea, a, [tabindex]):focus-visible {
  outline: 2px solid var(--focus);
  outline-offset: 2px;
}
.contracto-ondas { opacity: 0.12; pointer-events: none; }
@media (prefers-reduced-motion: reduce) {
  :root {
    --motion-feedback: 0ms;
    --motion-overlay: 0ms;
    --motion-step: 0ms;
  }
  .contracto-ondas { display: none; }
}
@media (forced-colors: active) {
  .contracto-ondas { display: none; }
  :where(button, input, select, textarea) { border: 1px solid ButtonText; }
  :where(button, input, select, textarea, a, [tabindex]):focus-visible {
    outline: 2px solid Highlight;
  }
}
```

Aplicar aliases no mesmo escopo de tema. Se um componente criar escopo próprio, mapear novamente os aliases dependentes para não capturar valores de outro tema. O elemento raiz recebe o tema resolvido antes da primeira pintura; a preferência “Sistema” acompanha o tema do sistema, enquanto a preferência explícita prevalece.

Migração dos nomes provisórios: `--c-bg` → `--bg`, `--c-surface` → `--surface`, `--c-text` → `--fg`, `--c-text-secondary` → `--muted`, `--c-border` → `--border`, `--c-primary` → `--accent`, `--c-primary-hover` → `--accent-hover`, `--c-primary-light` → `--accent-soft`. Manter aliases temporários somente enquanto existirem consumidores antigos.

### Contraste e personalização

Mínimos: 4,5:1 para texto normal; 3:1 para texto grande e informação gráfica essencial. Divisores decorativos podem ser sutis; bordas necessárias para reconhecer campos usam `--control-border`. Medir pares reais após composição de transparências, nos dois temas e em todos os estados.

Valores de referência calculados por luminância relativa sRGB dos valores de origem; a conversão arredondada para OKLch deve preservar os mesmos resultados a duas casas decimais:

| Par | Contraste |
|---|---:|
| Branco / azul principal | 6,77:1 |
| Branco / azul hover | 9,62:1 |
| Texto secundário claro / superfície variante clara | 5,04:1 |
| Texto secundário escuro / superfície variante escura | 5,44:1 |
| Branco / sucesso | 5,13:1 |
| Branco / alerta | 5,02:1 |
| Branco / erro | 4,98:1 |
| Azul suave / superfície variante escura | 6,72:1 |

No tema claro, os tokens `--success-text`, `--warn-text` e `--danger-text` são permitidos sobre `--surface`. Sobre `--surface-variant`, usar `--fg` acompanhado da insígnia: por exemplo, vermelho sobre essa superfície tem apenas 4,37:1. Não generalizar um par aprovado para todos os fundos.

Não usar `--danger` ou `--success` como texto sobre a superfície escura: os pares legados ficam aproximadamente em 2,84:1 e 2,76:1. Nesse tema, o texto é neutro e o estado aparece em insígnia preenchida com glifo branco e borda perceptível. Um campo inválido também precisa de mensagem, ícone e borda legível; vermelho sozinho não o identifica.

Para cores personalizadas: validar a entrada; derivar papéis em OKLch preservando matiz quando possível e reduzindo croma para caber em sRGB; ajustar luminosidade até cumprir os contrastes. Calcular `--on-accent` em conjunto. Hover não pode piorar o contraste do texto: escurecer preenchimentos com texto claro ou clarear os que usam texto escuro. Não reutilizar a antiga multiplicação RGB por 0,78 como garantia de acessibilidade.

Preservar a preferência original em configuração e explicar ajustes necessários de uso: “A tonalidade foi ajustada nos controles para manter a leitura”. Quando não for possível obter uma combinação válida, usar o padrão seguro nos controles e informar o motivo. Validar também texto de destaque, borda do botão e ícone; conferir apenas o branco sobre o botão não basta.

## 7. Contrato de componentes e estados

Componentes reutilizáveis recebem parâmetros explícitos, têm documentação curta de entrada/saída e não importam telas específicas. Na web, preservar os comportamentos genéricos de `BaseModal`, sem tentar transportar herança de widgets Python para o DOM.

| Componente | Estado normal | Hover / ativo | Foco, bloqueio e exceções |
|---|---|---|---|
| Botão primário | `accent` + `on-accent`, borda `primary-border` | Hover `accent-hover` + mesmo texto; pressionado mantém esse par e usa relevo interno | Foco exterior `focus`; desabilitado não executa e tem explicação adjacente |
| Botão secundário | `surface` + `fg`, borda `control-border` | Reforçar borda para `fg`, sem clarear texto ou reduzir contraste | Mesmo foco; não depender de tooltip para explicar bloqueio |
| Ação textual | `fg`, sublinhado quando link | Aumentar espessura do sublinhado; preservar texto/fundo | Área acionável de 44 px; nome acessível específico |
| Seleção de modo/checkbox | Neutro; marcado usa `selection-bg` + `selection-fg` | Borda e marca estáveis; sem deslocamento | Estado semântico nativo; setas em radio group; Espaço em checkbox |
| Campo | `surface` + `fg`, borda `control-border`; ajuda `muted` | Reforçar borda sem alterar legibilidade | Rótulo vinculado; `aria-invalid` e mensagem; readonly selecionável |
| Insígnia de estado | Cor de estado + `on-status`; rótulo legível ao lado | Não é botão se não tiver ação | Borda `control-border` quando necessária; não comunica só por cor |
| Cartão/lista | `surface` + `fg`, divisor `border` | Sem efeito se não for interativo | Ações internas explícitas; não transformar todo cartão em botão |
| Toast | `surface` + `fg`, insígnia e sombra flutuante | Fechar usa comportamento secundário | Um por vez; não rouba foco; `Esc` respeita contexto modal |

Uma ação principal por contexto: emitir, avançar, finalizar ou salvar. Ao abrir modal, sua ação principal substitui a prioridade da tela sob o overlay. “Voltar”, “Cancelar”, “Adicionar participante”, “Importar” e “Ver pendências” são secundárias. “Finalizar processo” usa a mesma família primária; verde fica reservado ao resultado concluído.

### Campos e validação

Usar rótulo persistente acima do controle, ajuda vinculada por `aria-describedby` e obrigatoriedade programática. Placeholder é exemplo suplementar, nunca rótulo. Essa estrutura também é recomendada no [padrão Field do Fluent 2](https://fluent2.microsoft.design/components/web/react/core/field/usage).

| Família do perfil | Representação e regra |
|---|---|
| `TEXTO`, `TEXTO_LONGO` | Input/textarea; aceitar acentos, colagem e seleção; não cortar nomes |
| `CPF`, `CNPJ`, `CPF_CNPJ`, `PIS_PASEP` | Valor textual; preservar zeros e permitir CNPJ alfanumérico; validação oficial do backend |
| `DATA`, `ANO` | Entrada digitável no formato brasileiro; calendário opcional operável por teclado |
| `MOEDA`, `AREA`, `INTEIRO` | Formatação pt-BR e limites do perfil; não usar spinner para identificadores |
| `TELEFONE`, `EMAIL` | Máscara/ajuda adequadas; preservar cursor ao editar e colar |
| `SELECAO` | Select nativo quando suficiente; opções e valor vêm do perfil |
| `CHECKBOX` | Caixa de seleção real; serializar o par configurado em `opcoes`, não um booleano arbitrário |

Manter os sete campos SIM/NÃO do DAMP como checkboxes, conforme a 4.5.13. Valor desmarcado pode ser “NÃO” ou outro valor definido no perfil: não equivale automaticamente a campo não preenchido.

Campos calculados são somente leitura, identificados como calculados e selecionáveis para cópia. `visivel_quando`, `limpar_quando_oculto`, `ate_participante`, `escopo`, limites e ordenação de dependências vêm do backend. Campo fora da página atual não é o mesmo que campo condicionalmente inaplicável; trocar de página nunca limpa dados.

No estado inicial, listar pendências sem pintar todos os campos de vermelho. Após interação e saída do campo, mostrar erro acionável; atualizar a contagem sem roubar foco. O backend revalida antes de gerar. Exibir resumo de todas as páginas e manter **Ver pendências** acessível mesmo com o botão principal bloqueado.

Abrir a lista não muda a página. Ao escolher uma pendência, navegar até a página correspondente e focar o campo. Implementar visibilidade de foco pela rolagem do contêiner, sem `scrollIntoView`. Se o campo deixar de existir por mudança de condição, devolver foco ao controle que causou a alteração ou ao título da seção.

### Diálogos, notificações e movimento

- Modal: título, descrição quando necessária, fundo inerte, foco contido, restauração do foco no elemento acionador. Usar semântica `dialog` e nome acessível. Evitar modais empilhados.
- Editor extenso de perfil ou mapeamento é uma área dedicada, não um pequeno diálogo com várias rolagens internas.
- Confirmação destrutiva: nomear o alvo e a consequência; foco inicial na opção segura. Não confirmar operações triviais como mudar página.
- `Esc` fecha o elemento transitório mais interno. Se há modal, não deve também dispensar um toast atrás dele. Diálogo nativo de arquivos mantém prioridade enquanto aberto.
- Processo em andamento: fechar/minimizar o painel de progresso não cancela o trabalho. **Parar processo** é explícito; `Esc` não dispara cancelamento irreversível.
- Toast temporário sem ação necessária pode desaparecer após 6 segundos, pausando sob hover/foco. Erro que precisa de correção permanece no contexto da tarefa; não desaparece como único registro.
- Boas-vindas: somente na primeira execução, quatro passos, fechamento explícito e reabertura em Ajuda. Nunca desaparece por temporizador.
- Resposta de foco/clique imediata; hover 120 ms, abertura até 180 ms e mudança de etapa até 200 ms. Respeitar movimento reduzido. Não bloquear interação aguardando animação.
- Usar indicador indeterminado único quando o backend não conhece a fração concluída. Não reproduzir a rotação aleatória de GIFs do catálogo antigo como requisito web.

## 8. Jornadas e contratos de dados

### Modo Simples

Selecionar um ou mais formulários por checkboxes → aplicar seleção compatível → preencher campos combinados → gerar PDFs → apresentar arquivos e destino.

O backend `combinar_perfis` decide compatibilidade. Conflitos de tipo, escopo, limites ou cálculo impedem aplicar a seleção; mostrar os perfis/campos envolvidos e como corrigir. Manter a seleção anterior válida. Reaplicar a mesma seleção não deve apagar o preenchimento.

Nomear o contexto como **Emissão de formulários**, corrigindo a ambiguidade do título legado no singular. Preservar chaves como `formulario_simples` e `formularios_basicos_selecionados`. Exibir número de formulários e página atual sem confundir essa paginação com as etapas do modo Avançado.

“Preservar dados para reutilizar” mantém os dados na sessão após a emissão conforme a opção do usuário. Não transforma dados de clientes em preferência gravada. Não exibir a Etapa 2 nesse modo. O resultado é PDF conforme o fluxo atual; não rotular como PDF/A por associação ao outro modo.

### Modo Avançado

**1. Geração de documentos** → **2. Conversão e organização**. O stepper indica estado atual e permite revisitar etapas disponíveis. Avançar exige validação; clicar na segunda etapa não contorna pendências.

Preservar limites do perfil, ocultação de quadros sem campos e data/local/destino somente na última página aplicável. Voltar mantém dados. Se uma alteração tornar a revisão anterior inválida, informar que o conjunto precisa ser atualizado; não apresentar documentos antigos como se refletissem novos valores.

Na Etapa 2, mostrar formulários selecionados, anexos previstos pelo perfil, arquivos associados, destino e formato real. Não finalizar sem pelo menos um formulário selecionado ou anexo. Extras recomendados ausentes permitem confirmação explícita, como no fluxo existente; não inventar obrigatoriedade.

Depois de finalizar, confirmar a entrada na fila. O resultado só é concluído após retorno do backend. Documentos duplicados devem seguir a política existente de nomes, sem sobrescrita silenciosa. Informar falhas de acesso e os arquivos efetivamente produzidos.

### Fila e operações longas

| Estado do domínio | Texto de UI | Ação / evidência |
|---|---|---|
| `na_fila` | Aguardando | Exibir posição quando conhecida; permitir cancelar esse item |
| `executando` | Processando | Etapa e arquivo quando informados; minimizar ou parar |
| `cancelando` | Cancelando | Aguardar confirmação; impedir solicitações repetidas |
| `concluido` | Concluído | Resumo real dos arquivos e ação Abrir pasta |
| `erro` | Não foi possível concluir | Motivo acionável e situação dos arquivos já produzidos |
| `cancelado` | Cancelado | Informar efeito confirmado da interrupção e limpeza |

As duas etapas da jornada não são as três fases internas da fila. Usar nomes como “Gerando formulários”, “Convertendo arquivos” e “Concluindo processo” no progresso; não inserir uma terceira etapa no stepper do formulário.

Percentuais só quando representam uma unidade mensurável do trabalho informado pelo serviço. `etapa_atual / etapa_total` não prova percentual de tempo restante. Não inventar estimativas ou apresentar progresso indeterminado como 99%.

O painel da fila pode fechar, perder foco e reabrir sem reiniciar o trabalho. Alterações em um novo formulário não podem modificar o lote enviado; o adaptador precisa tratar a requisição como uma fotografia dos dados. Duplicidade de clique deve gerar no máximo uma requisição de trabalho.

Se o transporte desconectar, mostrar “Conexão com o processamento interrompida” e consultar o estado pelo identificador ao reconectar; não reenviar a geração automaticamente. Fechar a aplicação com trabalho ativo exige fluxo de saída explícito; não prometer continuidade após encerrar o processo do aplicativo.

Word ausente: explicar a dependência apenas na operação que precisa dele. Word travado: exibir contagem regressiva real e a ação prevista pelo backend, limitada ao processo filho. Não oferecer LibreOffice como recurso implementado.

### Perfis, mapeamento e configurações

Lista de perfis deve distinguir modo, formato, quantidade de formulários e perfil ativo com dados reais. Ações por item: ativar, editar, duplicar, exportar e excluir quando permitido. Importar, backup e restaurar ficam no contexto da lista. Identificador estável mantém seleção mesmo após renomear.

Editor organiza: identificação, modo/formato/participantes, formulários PDF, campos de entrada, páginas, condições/cálculos, documentos extras e mapeamento. Essas são seções do mesmo perfil; a UI não inventa um novo modelo de negócio. Salvar exige validação estrutural e apresenta pendências. Sair com alterações não salvas pede uma decisão explícita.

Na conferência de mapeamento, a prévia deve corresponder ao PDF local real. Mostrar página inteira em proporção natural, seleção de página e zoom, acompanhados de lista dos campos. Não usar mock de contrato como evidência de mapeamento correto. Busca, seleção e associação precisam de alternativa por teclado; operações não dependem apenas de clicar nas coordenadas da página. Diagnósticos de geometria são apresentados conforme o serviço, sem “correção automática” inventada pela UI.

Limites atuais para PDFs personalizados: 50 MB, 100 páginas e 1.000 campos. Exibir mensagens para limites excedidos usando o resultado do validador; não duplicar esses limites como autoridade independente no frontend.

Configurações preservam Claro/Escuro/Sistema, cor personalizada, local padrão e Pequeno/Médio/Grande. Tema pode ser pré-visualizado, mas a ação Salvar configurações confirma a persistência; ao sair sem salvar, restaurar o estado anterior ou pedir decisão, sem descartar silenciosamente. Restaurar padrões informa quais preferências serão alteradas. Diagnóstico/reparo é uma ação explícita e apresenta o resultado do serviço; nunca ocorre automaticamente ao abrir a tela.

## 9. Fronteira entre UI e shell

### pywebview primeiro

Preservar a direção `pywebview + FastAPI` em loopback estrito `127.0.0.1`, reutilizando `services/`. HTML, CSS, JS, ícones e textos são empacotados localmente. Esta revisão não cria API nem escolhe bibliotecas de estado.

Separar quatro responsabilidades: componentes → estado de apresentação → adaptador de capacidades → backend/shell. A tela não chama diretamente `window.pywebview`, `fetch`, API Tauri, Word ou Ghostscript. Esses acessos ficam no adaptador correspondente.

Contratos lógicos necessários, ainda a formalizar na implementação:

- carregar/salvar preferências e consultar perfis por identificador;
- validar/compor formulários e resolver campos aplicáveis;
- selecionar arquivos/pastas e abrir destino por diálogo/ação nativa;
- solicitar geração, consultar trabalho, receber progresso e cancelar;
- carregar a representação de prévia e resultados de mapeamento;
- executar diagnóstico/reparo solicitado e obter seu resultado.

Definir resultados assíncronos com identificador, estado, dados e erro estruturado. Não serializar widgets, callbacks Python ou caminhos como comandos executáveis. Mensagens de negócio retornam ao contexto correto; detalhes técnicos e stack traces ficam no diagnóstico local.

O contrato de protocolo continua uma decisão técnica em aberto. Loopback não equivale a autenticação: a implementação deve validar origem, sessão e requisições, limitar operações expostas e proteger contra CSRF. A [documentação de segurança do pywebview](https://pywebview.flowrl.com/guide/security.html) descreve o uso do token de sessão para proteger chamadas à API local. A proteção precisa ser integrada ao backend escolhido, não apenas citada no design.

### Tauri V2 depois

Preparar substituição do adaptador por comandos Tauri e, se confirmado, backend Python sidecar. Tokens, componentes, identidade e jornadas permanecem. O design não exige reescrever os serviços em Rust.

Tauri V2 continua evolução futura a reavaliar conforme `DECISIONS.md`. React/TypeScript/Vite, SQLite, updater e migração de armazenamento citados em `ARCHITECTURE.md` não são pré-requisitos para esta UI nem decisões já implementadas. Evitar código de componente preso ao shell reduz retrabalho mesmo que essas escolhas mudem.

Permissões e escopos de arquivos, diálogo e execução devem ser mínimos e associados às janelas necessárias, com validação no backend. Não tratar instalação de plugin como concessão irrestrita. As [capabilities do Tauri V2](https://v2.tauri.app/security/capabilities/) fornecem o mecanismo de delimitação; a configuração efetiva será responsabilidade da implementação.

### Persistência e recursos

Preferências e perfis continuam sob gestão do backend, preservando os dados existentes de `%APPDATA%/Contracto/` e os fallbacks reais de armazenamento. Não usar `localStorage` para CPF, CNPJ, nomes, conteúdo dos formulários, tokens de sessão ou fila. Manter dados de preenchimento em memória e destinos persistidos somente quando já previstos.

Usar ícones locais de contorno consistente, 1,5–1,8 px, `currentColor`; manter a semântica do catálogo de assets. Migrar pares PNG por tema para SVG revisado, sem exigir novos downloads em execução. Logotipos e documentos oficiais não são recriados. A UI não deve solicitar imagens externas para ilustrar formulários.

Não usar `innerHTML` com dados de perfis, nomes de arquivo ou mensagens do backend. Recursos HTML/JS locais obedecem a uma política de conteúdo restrita definida na implementação. Links externos em Ajuda são opcionais, identificados e só abrem mediante ação explícita; a operação principal permanece offline.

## 10. Critérios de aceite antes de cada tela nova

P0 significa bloqueio de entrega. Os itens abaixo são requisitos da UI futura, não testes já executados por esta revisão documental.

### P0 — identidade, conteúdo e acessibilidade

- [ ] Paleta, fonte, raios e espaços vêm dos tokens; não há divergência local de tema.
- [ ] Ação principal é única no contexto, rótulos são pt-BR e contagens vêm de dados reais.
- [ ] Ondas aparecem apenas em área livre e somem em Sólido, movimento reduzido e alto contraste.
- [ ] Todos os pares de texto, ícone, controle e foco passam contraste nos temas e estados, inclusive com cor personalizada.
- [ ] Tela funciona com Tab, Shift+Tab, Enter/Espaço conforme o controle, setas nos seletores e Esc contextual.
- [ ] Rótulos, ajuda, erros, regiões e estados têm semântica acessível; atualizações de status usam anúncio moderado sem roubar foco.
- [ ] Modal contém foco, torna fundo inerte e devolve foco corretamente; nenhum diálogo continua sobre outros aplicativos.
- [ ] 920 × 680, 1024 × 768, DPI 125/150/200%, zoom 200% e reflow estreito não cortam texto nem escondem ações.
- [ ] Paginação e faixa de ações não cobrem campos; nomes longos, caminhos e mensagens quebram sem perda de informação.

### P0 — paridade funcional e integridade

- [ ] Simples aceita multisseleção compatível, explica conflitos e preserva IDs ao renomear perfis.
- [ ] Tipos de campos, CNPJ alfanumérico, máscaras, cálculos, pares de checkbox e condições mantêm os contratos existentes.
- [ ] Trocar página mantém dados; resumo de pendências abrange todas as páginas e permite focar a correção escolhida.
- [ ] Avançado respeita participantes do perfil, duas etapas, seleção mínima e confirmação de extras ausentes.
- [ ] PDF e PDF/A-2b são identificados pelo formato real; conclusão depende do retorno do serviço.
- [ ] Fila preserva todos os estados, minimiza sem cancelar, impede envio duplicado e lida com desconexão sem reenviar trabalho.
- [ ] Cancelamento só anuncia limpeza ou remoção que o backend confirmou; erros não apagam dados de entrada.
- [ ] Perfis, importação/exportação, backup/restauração, mapeamento e manutenção continuam acessíveis.
- [ ] Ausência/travamento do Word e falhas de pasta, PDF ou backend exibem causa e próximo passo possível.
- [ ] Recursos funcionam offline; não há chamadas externas automáticas ou armazenamento adicional de dados pessoais.

### Evidência mínima na implementação

Percorrer uma emissão Simples com múltiplos formulários, um contrato Avançado completo, um conflito de perfis, uma falha de validação entre páginas, um cancelamento e uma edição de mapeamento somente com teclado. Verificar fila após minimizar/retornar e bloqueio de duplicidade no envio. Conferir os documentos reais gerados, não apenas o toast.

Usar `MANUAL_DE_TESTE.md` e testes existentes de composição, campos, modos, geração, cancelamento, import/export e backend headless como base de regressão. Testes Tk de modal, toast e foco precisam de equivalentes na UI web; não devem ser considerados prova de acessibilidade do DOM. Executar no shell efetivo antes de liberar, com leitor de tela e temas do Windows.

## 11. Aplicação incremental

1. **Fundação:** implementar tokens, tema, semântica e componentes básicos; validar estados e contraste com dados sintéticos claramente identificados.
2. **Adaptador:** formalizar operações e estados; comprovar integração headless sem importar UI nos serviços.
3. **Fluxo Simples:** multisseleção, renderização do perfil, validação, paginação e emissão com paridade.
4. **Fluxo Avançado e fila:** revisão, anexos, processamento, minimização, cancelamento e resultado.
5. **Ferramentas de configuração:** perfis completos, mapeamento, backup, configurações e ajuda.
6. **Validação do shell:** teclado, DPI, recursos offline, diálogos nativos, integração Word/Ghostscript e empacotamento.
7. **Evolução Tauri:** quando a decisão arquitetural for confirmada, substituir integração do shell e repetir os mesmos critérios de aceite.

Não liberar a substituição integral do CustomTkinter com telas de perfis, mapeamento ou manutenção omitidas. A ordem de implementação não altera o escopo final de paridade.

## 12. Base da revisão e integração documental

Fontes locais examinadas: `docs/DESIGN.md`, `DESIGN_SYSTEM.md`, `docs/DECISIONS.md`, `docs/PRODUCT.md`, `docs/ARCHITECTURE.md`, `docs/GUIA_OPEN_DESIGN.md`, `docs/MANUAL_DE_TESTE.md`, privacidade, termos, avisos de terceiros, README e releases 4.5.12–4.5.14. O escopo foi confrontado com `main_window.py`, `theme.py`, `settings_frame.py`, `profiles_frame.py`, modelos de perfil, configuração, composição, fila, ports e inventário de testes. Não se trata de auditoria linha a linha de todo o código.

A decisão visual mantém os valores de marca, reduz ambiguidades e especifica comportamentos que antes estavam apenas no código. Nenhuma implementação Python, dependência ou documento normativo de produto foi alterado por esta revisão. A linguagem definida aqui é exclusiva deste aplicativo e não se aplica a outros projetos.

Pendências de integração, fora da alteração visual: alinhar links e status dos documentos antigos; revisar a divergência entre `requirements.txt`, que ainda lista PyMuPDF, e o aviso de remoção em 4.5.12; formalizar o protocolo UI/backend. Não usar o design system para declarar essas pendências resolvidas.

Referências externas consultadas em 10/09/2026: documentação oficial Fluent 2 (tokens, Field e acessibilidade), Carbon (formulários), pywebview (segurança) e Tauri V2 (capabilities). Os links são referências de desenvolvimento; não são dependências de rede da aplicação.
