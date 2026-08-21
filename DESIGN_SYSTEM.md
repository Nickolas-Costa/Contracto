# Design System & Asset Catalog — Contracto (v4.3)

Este documento estabelece o **Design System**, a identidade visual e o catálogo semântico de ativos do **Contracto**. Todos os componentes da interface devem seguir rigorosamente estes padrões para manter a consistência, a elegância e a experiência de alto nível no Windows.

---

## 1. Filosofia de Design

O Contracto adota uma estética moderna, limpa e profissional inspirada no **Material Design 3** e na fluidez visual de ferramentas corporativas de alta produtividade (como o PDFCreator e interfaces modernas do Windows 11).

### Pilares Visuais:
- **Clareza e Alto Contraste**: Suporte nativo e adaptativo aos modos **Claro (Light)** e **Escuro (Dark)**.
- **Micro-Interações e Feedback Imediato**: Validação de campos em tempo real, transições suaves, loaders animados dinâmicos e notificações toast contextuais.
- **Superfície Translúcida**: Diálogos e modais com efeito de vidro fosco escuro (`-alpha 0.60`) sobre a interface.
- **Fundo com Gradiente Senoidal Super-Sampled**: Fundo com ondas senoidais sutis onde 3 linhas acompanham dinamicamente a cor de destaque do tema.

---

## 2. Tokens de Cores (Color Tokens)

### 2.1. Cor Primária e Variações Dinâmicas
A cor de destaque é configurável pelo usuário no menu **Configurações** (padrão `#1E6FB3` - Azul Institucional). A partir dela, o sistema calcula dinamicamente:

| Token | Cálculo / Função | Descrição |
| :--- | :--- | :--- |
| `COLOR_PRIMARY` | `get_color_primary()` | Cor de destaque principal (botões primários, seleções). |
| `COLOR_PRIMARY_HOVER` | `get_color_primary_hover()` | Tom 22% mais escuro para estados de hover. |
| `COLOR_PRIMARY_LIGHT` | `get_color_primary_light()` | Mistura 40% cor + 60% branco para badges e realces. |
| `COLOR_PRIMARY_DARK_GRADIENT` | `get_color_primary_dark_gradient()` | Variação saturada para linhas do gradiente no Dark Mode. |
| `COLOR_PRIMARY_TEXT` | `get_color_primary_text()` | Cor primária adaptada para leitura com contraste no Dark Mode. |

### 2.2. Superfícies e Textos (Modo Claro vs Modo Escuro)

| Token | Light Mode | Dark Mode | Aplicação |
| :--- | :--- | :--- | :--- |
| `COLOR_BACKGROUND` | `#F5F5F5` | `#1E1E1E` | Fundo principal da janela e gradiente. |
| `COLOR_SURFACE` | `#FFFFFF` | `#2B2B2B` | Superfície dos cards, modais e containers. |
| `COLOR_SURFACE_VARIANT` | `#F0F0F0` | `#333333` | Fundos de campos inativos, botões secundários. |
| `COLOR_BORDER` | `#E0E0E0` | `#424242` | Bordas sutis de cartões e divisórias. |
| `COLOR_TEXT` | `#212121` | `#E0E0E0` | Títulos e textos de alta ênfase. |
| `COLOR_TEXT_SECONDARY` | `#666666` | `#AAAAAA` | Subtítulos, labels secundárias e instruções. |
| `COLOR_TEXT_DISABLED` | `#9E9E9E` | `#757575` | Textos desabilitados ou placeholders. |

### 2.3. Cores de Estado e Feedback

| Estado | Cor Hex | Uso na UI |
| :--- | :--- | :--- |
| **Sucesso** | `#2E7D32` | Notificações de sucesso, botão de finalizar, status concluído. |
| **Alerta** | `#F57C00` | Aviso de campos pendentes, confirmações de ação irreversível. |
| **Erro** | `#D32F2F` | Bordas de validação de CPF inválido/data, exclusão de perfis. |

---

## 3. Tipografia (Typography)

A aplicação utiliza a família **Segoe UI** nativa do ecossistema Windows:

| Nível | Tamanho | Peso | Uso |
| :--- | :--- | :--- | :--- |
| **H1** | 24px | `bold` | Títulos principais de tela e cabeçalhos de destaque. |
| **H2** | 20px | `bold` | Título da Toolbar e seções principais. |
| **H3** | 16px | `bold` | Títulos de cartões, títulos de modais e botões de ação principal. |
| **Body** | 14px | `normal` / `bold` | Textos de formulários, campos de entrada, labels e botões. |
| **Caption** | 12px | `normal` / `bold` | Mensagens de apoio, tags, sublabels e metadados. |

---

## 4. Espaçamentos e Raios de Borda

### 4.1. Espaçamento (Spacing Scale)
- `SPACING_XSMALL` = `4px`
- `SPACING_SMALL` = `8px`
- `SPACING_MEDIUM` = `12px`
- `SPACING_LARGE` = `14px`
- `SPACING_XLARGE` = `24px`
- `SPACING_XXLARGE` = `32px`

### 4.2. Raios de Borda (Corner Radius)
- `RADIUS_CARD` = `12px` (Cartões, modais e containers flutuantes)
- `RADIUS_BUTTON` = `12px` (Botões de ação primária e secundária)
- `RADIUS_INPUT` = `8px` (Campos de texto e entradas de formulário)

---

## 5. Catálogo de Ícones Vetoriais Adaptativos

Todos os ícones são renderizados em alta definição (128x128 com canal alfa transparente) e contam com variantes de contraste `_dark.png` (para fundos claros) e `_light.png` (para fundos escuros), selecionadas automaticamente via `theme.get_icon(name, size)`.

Para botões com fundo colorido/primário (como a Toolbar superior, "GERAR DOCUMENTOS E AVANÇAR", "FINALIZAR PROCESSO" e "SALVAR CONFIGURAÇÕES"), utiliza-se `theme.get_icon(name, size, light_only=True)` para garantir que o ícone permaneça sempre em branco puro (`#FFFFFF`) com contraste ideal independente do tema do sistema.


| Ícone | Nome do Arquivo | Tamanho Padrão | Aplicação na Interface |
| :--- | :--- | :--- | :--- |
| 🏠 | `home` | `20x20` | Botão "Início" na barra superior (Toolbar). |
| 🗂️ | `profiles` | `20x20` | Botão "Perfis" na barra superior. |
| ⚙️ | `settings` | `20x20` | Botão "Configurações" na Toolbar e cards de ajuste. |
| 🛟 | `help` | `20x20` | Botão "Ajuda" na barra superior. |
| 📅 | `calendar` | `18x18` | Botão do calendário pop-up ancorado para seleção de data. |
| 📍 | `location` | `18x18` | Campo de Local da Assinatura / Cidade. |
| 👤 | `person` | `18x18` | Cabeçalho de cada card de Participante (Comprador). |
| 👥 | `participants` | `18x18` | Botão "+ Adicionar Participante". |
| 📄 | `document` | `16x16` | Botão "Adicionar Formulário PDF" na edição de perfis. |
| 📋 | `contract` | `16x16` | Documentos extras e formulários na Etapa 2. |
| 📁 | `folder` | `18x18` | Botões de seleção de pasta e diretório de saída. |
| 🗑️ | `trash` | `16x16` | Botão de remover participante e excluir perfil. |
| 💼 | `briefcase` | `18x18` | Identificação de processos e dossiês de crédito. |
| 🔍 | `search` | `18x18` | Busca e exploração de campos AcroForm. |
| ⚠️ | `warning` | `24x24` | Badge de alerta no `AlertModal`. |
| ℹ️ | `alert_circle` | `24x24` | Badge de confirmação no `ConfirmModal`. |
| 🎉 | `success` | `20x20` | Botão "FINALIZAR PROCESSO" e confirmação de sucesso. |
| 💾 | `save` | `18x18` | Botão "SALVAR CONFIGURAÇÕES" e "Salvar Perfil". |
| 🧮 | `calculator` | `18x18` | Ícone para contratos e perfis de financiamento (SBPE). |
| ➔ | `advance` | `20x20` | Botão "GERAR DOCUMENTOS E AVANÇAR" na Etapa 1. |
| ↺ | `back` | `16x16` | Botão "Voltar" e "Restaurar Padrões de Fábrica". |
| 🌐 | `globe` | `18x18` | Seção de Aparência e Ambiente do sistema. |
| 📐 | `ratio` | `18x18` | Seção de Tamanho dos Quadros nas configurações. |
| 📖 | `book` | `18x18` | Referências e documentação embutida. |
| 🔲 | `grid_array` | `14x14` | Botão "Duplicar" nos cards de perfil. |
| 📑 | `form` | `14x14` | Botão "Editar" nos cards de perfil. |

---

## 6. Sistema de Loaders Animados (GIF Spinners)

As telas de carregamento utilizam um player animado nativo de alto desempenho ([animated_loader.py](file:///c:/Users/sousa/OneDrive/Desktop/PROJETOS/Contracto/app/ui/animated_loader.py)) que renderiza frames de GIF com temporização nativa.

### 6.1. Ciclo de Rotação Circular
A cada nova ação de carregamento (geração de documentos, conversão de PDF/A, reparo de backend, etc.), o sistema seleciona o próximo loader da fila e recomeça a lista circularmente:

1. `spinner_expand.gif` — Círculo pontilhado expansivo
2. `spinner_dots_spin.gif` — Três pontos giratórios orbitais
3. `spinner_snake.gif` — Serpente circular contínua
4. `spinner_dots_juggle.gif` — Três pontos em malabarismo vertical
5. `spinner_spiral.gif` — Espiral contínua de alta rotação
6. `spinner_turbine.gif` — Turbina radial com aceleração suave
7. `spinner_dots_queue.gif` — Fila de pontos em fluxo contínuo
8. `spinner_half_circles.gif` — Semi-círculos concêntricos pulsantes
9. `spinner_transparency.gif` — Círculo pontilhado com fade de opacidade
10. `spinner_dots_line.gif` — Três pontos oscilantes em linha horizontal
