# Contracto 4.5.18

Estabilização da base WebView, validação estrutural do HTML, janela maximizada por padrão e roteiro de migração total.

## Destaques da Release

- **Correção da Integridade do HTML**: Remoção de duplicação estrutural no `index.html` (linhas 27-52 contendo doctype, head e toolbar redundantes).
- **Validação Estrita de DOM no Teste Automatizado**: Introdução do parser nativo `HTMLParser` em `tests/test_frontend_base.py` assegurando estrutura única de tags base (`<!DOCTYPE>`, `<head>`, `<body>`, `#app`) e asserção de unicidade de todos os IDs do DOM.
- **Janela Maximizada na Inicialização**: Adicionada a flag `maximized=True` na criação da janela pywebview (`app/webview_shell.py`), alinhando o comportamento de abertura ao padrão da aplicação.
- **ADR 0016**: Documentada e registrada a norma de integridade estrutural e prevenção de duplicações no frontend da WebView.
- **Plano Mestre de Migração (10 Etapas)**: Registrada a arquitetura de transição com alinhamento de persistência no backend (ADR 0017) e nova identidade visual com fundo dinâmico e laboratório isolado (ADR 0018).

## Instalação

Baixe `Contracto_v4.5.18.zip` e o `.sha256.txt` abaixo, extraia e execute.
Não requer Python instalado. Requer Windows 10/11 (64-bit) e Microsoft Word para conversão de arquivos RTF.
