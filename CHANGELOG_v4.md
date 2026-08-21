# Contracto - Release Notes

## 🎯 Centralização de Modais, Responsividade dos Quadros e Otimizações de Interface (v4.5)

* **Centralização Geométrica Perfeita dos Modais com Compensação DPI:**
  * Implementação da função centralizada `configurar_janela_modal` no `theme.py` que calcula dimensões físicas reais e posição relativa à janela do app.
  * Eliminação de offsets e descentralizações em monitores com escalonamento de DPI do Windows (125%, 150%, 4K).
  * O overlay escuro translúcido cobre exatamente os limites da janela da aplicação com fidelidade visual.
* **Prevenção de Acúmulo e Encerramento Seguro de Popups:**
  * Controle de instância única ativa (`_instancia_ativa`) em todos os modais (`WelcomeModal`, `AlertModal`, `ConfirmModal`, `LoadingModal` e modais do gerenciador de perfis).
  * Destruição limpa de popups/overlays anteriores em cliques múltiplos ou aberturas concorrentes.
  * Suporte a fechamento ao clicar no overlay escuro de fundo ou pressionar a tecla `Escape`.
  * Liberação imediata de recursos e atualização de ciclo de eventos do Tkinter no método `dismiss()`.
* **Ajuste de Largura e Responsividade dos Quadros:**
  * Redução proporcional da largura dos quadros na tela inicial (Etapa 1 e Etapa 2) para garantir visualização harmoniosa em telas compactas e janelas restauradas.
  * Margem responsiva dinâmica (`_calcular_margem_responsiva`) calculada em tempo real ao redimensionar a janela.
* **Alinhamento e Otimização na Etapa 2:**
  * Alinhamento à esquerda dos checkboxes e campos de formulários dinâmicos.
  * Eliminação de barras de rolagem desnecessárias e transições fluidas.
* **Diferenciação Visual de Participantes:**
  * Ícone semântico próprio e destacado para o Participante Principal vs Participantes Adicionais.
* **Refinamento do Calendário Pop-up:**
  * Posicionamento ancorado ao botão de calendário com limites de tela preservados.

---

## 🎨 Renovação Visual, Design System e Loaders Dinâmicos (v4.3)

* **Design System Formal & Catálogo Semântico (`DESIGN_SYSTEM.md`):**
  * Especificação completa de tokens de cor, tipografia Segoe UI, espaçamentos e raios de borda.
  * Catálogo de 30 ícones vetoriais em alta resolução (128x128 com canal alfa).
  * Suporte nativo a temas Claro (`_dark.png`) e Escuro (`_light.png`) via `theme.get_icon(name, size)` com cache em memória.
* **Sistema de Loaders Animados em Rotação Circular:**
  * Implementação de player animado nativo de GIF (`AnimatedGifLabel`) em `app/ui/animated_loader.py`.
  * Rotação dinâmica circular entre 10 modelos de spinners GIF a cada nova ação de carregamento do usuário.
* **Centralização Unificada de Versão:**
  * Ponto único de verdade em `app/version.py` (`__version__ = "4.3"`).
  * Título da aplicação, scripts de compilação PyInstaller (`build_exe.bat`), gerador de pacote zip (`create_dist_package.py`) e criador de atalhos (`create_shortcut.py`) consomem dinamicamente a versão configurada.
* **Renovação de Ícones em Toda a Interface:**
  * Toolbar: Início, Perfis, Ajuda, Configurações.
  * Etapa 1: Calendário, Destino/Pasta, Participantes, Gerar e Avançar.
  * Etapa 2: Documentos extras com ícones semânticos de contrato, pasta e botão finalizar.
  * Perfis: Novo Perfil, Ativar, Editar, Duplicar e Excluir.
  * Configurações: Aparência, Cor de Destaque, Local Padrão, Tamanho dos Quadros, Restauração de Padrões, Diagnóstico/Reparo e Salvar.
  * Modais: Alerta, Confirmação e Guia Rápido com novos ícones vetoriais.

---

## 🚀 Novidades e Melhorias (v4.2)

* **Execução Headless do Ghostscript:** Processamento 100% em segundo plano (`CREATE_NO_WINDOW`), eliminando qualquer janela preta do prompt de comando durante conversões PDF/A.
* **Modal de Carregamento em Etapas com Cancelamento Seguro:**
  * Indicador de etapas e contador compacto (`Gerando documento 1/2`, `Convertendo documento 1/5`).
  * Botão **"⏹ Parar Processo"** com cancelamento cooperativo via `threading.Event`, limpando arquivos residuais e devolvendo o controle à interface.
* **Diagnóstico e Reparo Automático do Backend:**
  * Nova ferramenta integrada em Configurações para encerrar processos órfãos (`WINWORD.EXE`, `gswin64c.exe`), limpar arquivos temporários, validar integridade dos modelos e ferramentas, e restaurar atalhos.
* **Perfis Padrão e Recurso de Duplicação Rápida:**
  * Perfil padrão atualizado para **"MCMV"** (5 documentos padrão).
  * Novo perfil padrão **"SBPE"** (5 documentos padrão + *Cédula de Crédito*).
  * Botão **"Duplicar"** integrado em cada cartão de perfil para clonar modelos existentes em 1 clique e abrir a edição imediatamente.
  * Migração automática transparente de perfis legados denominados "Padrão".
* **Guia Rápido do Usuário Otimizado:**
  * Layout do modal de ajuda redimensionado e estruturado para exibir perfeitamente os 4 passos sem barras de rolagem desnecessárias.
* **Atualização Dinâmica na Troca de Perfil (Etapa 2):**
  * Alternar o perfil no menu suspenso atualiza instantaneamente a lista de documentos extras e o formato de saída.
* **Aprimoramentos Visuais e Dark Mode:**
  * Ícones de alerta e confirmação com paleta adaptativa de alto contraste em temas claro e escuro.
  * Aplicação de configurações visuais e redimensionamento exclusivamente ao clicar em "SALVAR CONFIGURAÇÕES".
  * Eliminação de artefatos de fundo branco no modo escuro através de superfície consistente no `CTkScrollableFrame`.
  * Expansão vertical total dos quadros de Perfis e Configurações preservando a margem horizontal configurada.
  * Validação do calendário pop-up integrada com atualização imediata de bordas.
  * Reset limpo da aplicação após conclusão sem disparar erros de validação em campos vazios.
* **Reorganização das Configurações:**
  * Novo card dedicado para **"Restaurar Configurações Padrão"** com diálogo de confirmação.
  * Botão de salvamento em destaque ocupando toda a largura do footer.

---

## 📌 Histórico da Versão 4.1

* **Preenchimento Completo do Formulário 1º Imóvel:** Mapeamento exato de todos os campos AcroForm do PDF modelo oficial (`NOME COMPLETO`, `CPF`, `ENDERECO`, `LOCAL ASSINATURA`, `DATA ASSINATURA`), garantindo 100% de preenchimento de todas as informações sem placeholders pendentes.
* **Novos Modais Modernos com Fundo Translúcido:** Efeito de transparência escura fosca nativa (`-alpha 0.60`) integrado a todos os modais da aplicação (`LoadingModal`, `WelcomeModal`, `AlertModal`, `ConfirmModal`).
* **Cartões Nítidos e Posicionamento Alinhado:** Cartões de diálogo exibidos com brilho e nitidez no topo (`-topmost`) com posicionamento perfeitamente alinhado sobre a área central de conteúdo.
* **Substituição Total de Popups Nativos:** Eliminação dos diálogos cinzas nativos do Windows (`messagebox`) em favor de modais próprios e elegantes do Contracto para confirmação de geração de documentos, abertura de pastas e exclusão de perfis.
* **Expansão Inteligente dos Perfis:** O painel de criação e edição de perfis expande verticalmente para ocupar o container mantendo estritamente a largura de margem configurada pelo usuário.
* **Ícone e Identidade na Barra de Tarefas:** Integração nativa do ícone oficial 3D em alta resolução na barra de título e na barra de tarefas do Windows.

---

## 📌 Histórico da Versão 4.0

* **Padrão de Fundo Estilo PDFCreator com Linhas de Destaque:** Fundo elegante com curvas senoidais suaves em tom neutro, onde 3 linhas acompanham dinamicamente a cor do tema ativo.
* **Sistema de Bordas Arredondadas Sem Artefatos:** Eliminação de pixels fantasmas nos cantos dos quadros arredondados.
* **Layout Dinâmico e Responsivo:** A configuração de "Tamanho dos Quadros" reflete instantaneamente ao salvar.
* **Scrollbars Inteligentes:** Barras de rolagem ocultadas automaticamente quando o conteúdo cabe na tela.
* **Seletor de Perfil na Toolbar:** Componente de seleção de perfis integrado à barra superior.
+++++++++++