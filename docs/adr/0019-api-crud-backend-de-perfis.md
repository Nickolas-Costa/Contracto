# ADR 0019 — API CRUD Backend de Perfis e Editor na WebView

Status: aceita e em implementação em 17/09/2026.

## Contexto

Anteriormente, a interface web só consultava e pesquisava a lista de perfis disponíveis via `GET /api/v1/profiles`, enquanto as operações de edição, criação, duplicação, exclusão, importação e exportação de perfis dependiam exclusivamente da interface CustomTkinter legada (`app/ui/profiles_frame.py`). Para permitir a substituição definitiva do Tkinter, o backend necessita expor endpoints REST locais para operações CRUD de perfis.

## Decisão

1. **Endpoints REST Locais para CRUD de Perfis**:
   - `GET /api/v1/profiles` — Lista todos os perfis cadastrados com detalhes estruturais.
   - `POST /api/v1/profiles` — Cria um novo perfil de documento (`adicionar_perfil`).
   - `PUT /api/v1/profiles/{nome}` — Atualiza as propriedades e mapeamentos de um perfil existente (`atualizar_perfil`).
   - `DELETE /api/v1/profiles/{nome}` — Remove um perfil cadastrado (`excluir_perfil`).
   - `POST /api/v1/profiles/{nome}/duplicate` — Cria uma cópia independente de um perfil (`duplicar_perfil`).
   - `POST /api/v1/profiles/import` — Importa um perfil a partir de arquivo JSON validado (`importar_perfil`).
   - `GET /api/v1/profiles/{nome}/export` — Exporta o perfil no envelope padrão de formato/versão (`exportar_perfil`).

2. **Integração no Frontend WebView**:
   - Atualizar a tela `tela-perfis` (`frontend/index.html` e `etapa1.js`/`ui.js`) disponibilizando os botões de **Criar**, **Editar**, **Duplicar**, **Excluir**, **Importar** e **Exportar**.
   - Incluir um editor visual de campos declarativos em modal (rótulo, ID, tipo, obrigatoriedade, escopo, opções e condições).

## Consequências e Evidência

A gestão da biblioteca de perfis e formulários passa a ser integralmente realizável através da interface WebView, garantindo total autonomia e paridade com o aplicativo clássico sem dependências de Tkinter.
