# ADR 0020: Gerenciador de Perfis e Componentes Auxiliares na WebView

## Status
Aceito

## Contexto
Até o marco anterior, a tela de perfis na WebView (`#tela-perfis`) atuava apenas como catálogo de leitura e consulta. Operações de criação, edição, duplicação, exclusão e importação/exportação de perfis JSON dependiam da interface CustomTkinter clássica.

Com a disponibilização dos endpoints REST de perfis na API local (`POST /api/v1/profiles`, `PUT /api/v1/profiles/{nome}`, `DELETE /api/v1/profiles/{nome}`, `POST /api/v1/profiles/{nome}/duplicate`), era necessário integrar a gestão completa de perfis à nova interface WebView.

## Decisão
1. **Gerenciador de Perfis em WebView**:
   - `frontend/index.html` e `frontend/js/etapa1.js` disponibilizam botões para "Novo perfil", "Importar JSON", "Duplicar", "Editar", "Exportar" e "Excluir".
   - Todas as modificações chamam `window.ContractoAPI.*` que por sua vez invocam a API REST local com persistência em `%APPDATA%/Contracto/contracto_profiles.json`.
   - Modais responsivos e acessíveis com leitores de tela e navegabilidade por teclado garantem paridade total com o aplicativo legado.

2. **Componentes Auxiliares do Shell**:
   - Adicionados botões "Ajuda" e "Sobre" na barra superior (`toolbar`).
   - Modal "Ajuda" exibe o guia intuitivo de 4 etapas de utilização do sistema.
   - Modal "Sobre" detalha a versão v4.5.18, arquitetura local sem telemetria (100% LGPD local), motores (pypdf, ReportLab, Word COM, Ghostscript) e créditos.

## Consequências
- Paridade de recursos atinge 100% entre a interface legada CustomTkinter e a nova WebView2.
- A navegação do usuário é contínua e sem necessidade de retornar à UI antiga para gerenciar modelos ou consultar a documentação.
