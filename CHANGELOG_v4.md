# Contracto - Release Notes

## 🚀 Novidades e Melhorias (v4.2)

* **Execução Headless do Ghostscript:** Processamento 100% em segundo plano (`CREATE_NO_WINDOW`), eliminando qualquer janela preta do prompt de comando durante conversões PDF/A.
* **Modal de Carregamento em Etapas com Cancelamento Seguro:**
  * Indicador de etapas e contador compacto (`Gerando documento 1/2`, `Convertendo documento 1/5`).
  * Botão **"⏹ Parar Processo"** com cancelamento cooperativo via `threading.Event`, limpando arquivos residuais e devolvendo o controle à interface.
* **Diagnóstico e Reparo Automático do Backend:**
  * Nova ferramenta integrada em Configurações para encerrar processos órfãos (`WINWORD.EXE`, `gswin64c.exe`), limpar arquivos temporários, validar integridade dos modelos e ferramentas, e restaurar atalhos.
* **Perfis Padrão "MCMV" e "SBPE":**
  * Perfil padrão atualizado para **"MCMV"** (5 documentos extras clássicos).
  * Novo perfil padrão **"SBPE"** (5 documentos clássicos + *Cédula de Crédito*).
  * Migração automática transparente de perfis legados denominados "Padrão".
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
