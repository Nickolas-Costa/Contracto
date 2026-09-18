# Release Notes — Contracto v4.5.18

## Resumo das Novidades

Esta versão consolida a migração completa do **Contracto** para a arquitetura moderna de interface gráfica em **WebView2**, substituindo a antiga interface CustomTkinter por uma aplicação web desktop elegante, de altíssimo desempenho e acessível.

---

## Principais Destaques da Versão v4.5.18

### 1. Inicialização em Janela Maximizada por Padrão
- O aplicativo agora inicia automaticamente em modo maximizado, ocupando a área útil disponível na tela com layout fluido e responsivo.

### 2. Gerenciador Completo de Perfis na WebView
- Agora é possível **criar novos perfis**, **duplicar modelos existentes**, **editar propriedades declarativas**, **importar e exportar JSON** e **excluir perfis** diretamente pela interface moderna, sem a necessidade da UI legada.
- Integração total com a API REST backend local (`/api/v1/profiles`), persistindo as alterações nativamente em `%APPDATA%/Contracto/contracto_profiles.json`.

### 3. Direção Visual e Fundo Senoidal Dinâmico
- Fundo decorativo animado composto por curvas vetoriais senoidais suaves em canvas SVG, inspirado na estética clássica da aplicação com sofisticação moderna e suporte a temas Claro/Escuro e cores personalizadas (*Accent*).
- Laboratório visual isolado (`lab.html`) para validação rápida de tokens, cartões em vidro fosco e componentes.

### 4. Guia de Utilização e Componentes Auxiliares
- Modal de **Ajuda** com guia passo a passo em 4 etapas (Modo e modelo, Preenchimento, Conferência, Geração).
- Modal **Sobre** com detalhes da versão, motores (pypdf, ReportLab, Word COM, Ghostscript) e política de privacidade 100% local (LGPD sem telemetria).
- Barra de tarefas responsiva e acessível com suporte completo a navegação por teclado e leitores de tela.

### 5. Robustez e Integridade do Sistema
- Retentativa e polling seguro de 50ms para inicialização da ponte nativa `pywebview`, prevenindo corridas de carregamento em ambientes de baixa especificação.
- Validador estrito de integridade do documento HTML para impedir IDs duplicados ou estruturas corrompidas.
- 100% de aprovação na suíte de 355 unit tests e 37 verificações do smoke test WebView2.

---

## Instruções de Atualização

Não há necessidade de migração manual de dados. Ao abrir o executável `Contracto_v4.5.18.exe`, suas configurações e perfis anteriores mantidos em `%APPDATA%/Contracto/` serão importados e preservados automaticamente.

---

*Contracto v4.5.18 — Desenvolvido com Google DeepMind Antigravity Pair-Programming.*
