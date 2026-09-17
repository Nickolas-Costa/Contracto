# ADR 0016 — Integridade do HTML, validação rígida de DOM e Janela Maximizada

Status: aceita e implementada em 16/09/2026.

## Contexto

Identificou-se um problema no documento principal do frontend (`frontend/index.html`), onde o arquivo sofreu duplicação acidental de trechos estruturais (múltiplas tags `<!doctype html>`, `<head>`, `<header class="toolbar">` e `#app`). A suíte de testes existente validava apenas a presença de fragmentos e tokens isolados via expressões regulares e strings, permitindo que corrupções estruturais e duplicidade de IDs passassem despercebidas. Além disso, identificou-se a necessidade de o aplicativo iniciar maximizado na janela pywebview por padrão para melhor aproveitamento de tela.

## Decisão

1. **Correção de Estrutura**: Limpar o arquivo `frontend/index.html`, garantindo um único `<!doctype html>`, `<html>`, `<head>`, `<body>` e `<div id="app">`.
2. **Validação Rígida no Teste Automated**: Adicionar asserções estritas no `tests/test_frontend_base.py` utilizando o parser nativo HTML (`html.parser`) para:
   - Garantir que tags estruturais de topo ocorram exatamente uma vez.
   - Garantir que todos os atributos `id` declarados no HTML sejam absolutamente únicos no DOM.
3. **Janela Maximizada**: Definir `maximized=True` na criação da janela pywebview em `app/webview_shell.py`, assegurando que o app abra maximizado em desktop.

## Consequências e Evidência

A integridade do documento HTML fica garantida por testes automatizados contínuos. Qualquer duplicação futura de trecho HTML ou repetição acidental de ID causará falha imediata nos testes unitários e de integração (`test_frontend_base.py`). O aplicativo abre com aproveitamento de tela maximizado no Windows.
