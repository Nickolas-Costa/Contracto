# Contracto - Release Notes (V4.0)

## 🚀 Novidades e Melhorias

* **Sistema Inteligente de Bordas Arredondadas:** Foi implementada uma técnica de *anti-aliasing dinâmico* que resolve definitivamente o problema dos "pixels fantasmas" ao redor das bordas dos painéis. As bordas voltam a ser suavemente arredondadas e se mesclam perfeitamente sobre o fundo gradiente da aplicação sem falhas.
* **Layout Dinâmico e Responsivo:** A configuração de "Tamanho dos Quadros" agora reflete instantaneamente sem a necessidade de mudar de abas. Ajuste a margem da janela na hora para telas maiores ou menores.
* **Overlays Nativos:** Reformulamos os popups (Avisos, Confirmações e Tela de Ajuda) para utilizarem uma camada preta sólida (`#000000`) totalmente nativa do sistema. Resultado: velocidade de exibição instantânea e escurecimento perfeito do fundo.
* **Scrollbars Inteligentes:** As barras de rolagem nos quadros de "Formulários Dinâmicos", "Documentos Extras" e Popups de Erros receberam uma inteligência visual, ficando invisíveis até que o conteúdo ultrapasse a altura limite, mantendo a tela limpa.
* **Novo Seletor de Perfil na Toolbar:** O menu de perfis foi promovido para um autêntico componente que respeita o esquema de cores escolhido, livrando-se da antiga borda padrão do Windows.
* **Legibilidade Elevada:** Melhoramos o contraste das cores. Botões de ação, avisos e a barra superior agora suportam cores personalizadas sem prejudicar a leitura dos textos (calculando automaticamente tons de Hover e Contrastes).

## 🐛 Correções de Bugs

* Corrigido o seletor da Etapa 2 que congelava quando um popup de erro era acionado simultaneamente.
* Corrigido o bug onde botões da Etapa 1 e Etapa 2 não acompanhavam a cor de destaque quando ela era alterada nas configurações.
* Ajustado o recarregamento instantâneo do painel de Configurações ao alterar Tema ou Cor, dispensando a necessidade de reiniciar abas.
