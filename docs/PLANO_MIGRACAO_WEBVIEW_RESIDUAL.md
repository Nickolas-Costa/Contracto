# Plano de Implementação — Migração Residual WebView2 (Pós v4.5.18)

> **Documento de trabalho.** Não cria versão nem release. Cada bloco concluído deve ser marcado e referenciado no commit correspondente.
>
> Estado inicial: **2026-09-17**. Atualização **2026-09-20**: blocos 0–6 implementados e suíte 362 OK; pendente apenas o gate final Windows/distribuição.

---

## Bloco 0 — Consolidação da Toolbar (ADR 0021) ✅

**Objetivo:** Interface limpa, com uma única barra superior e seletor de modo em destaque.

### Tarefas

- [x] **0.1 Remover `#conexao`** de `index.html` (linha 23) e todas as referências em `app.js` / `etapa1.js`
- [x] **0.2 Remover regras CSS de `#conexao`** em `layout.css` (linha 58)
- [x] **0.3 Mover `.modos`** (botões "Só gerar" e "Gerar e organizar") para dentro da `.toolbar` em `index.html`, removendo-os do interior do `.card`
- [x] **0.4 Estilizar chip de modo na toolbar** — adicionar classe `.toolbar-mode` em `layout.css` com destaque visual (borda colorida no modo ativo, badge de count de participantes)
- [x] **0.5 Remover `<aside class="summary">`** de `index.html`; ajustar `.workspace` de `grid-template-columns: minmax(0,1fr) 260px` para `minmax(0,1fr)` em `layout.css`
- [x] **0.6 Badge de participantes** — adicionar `<span id="badge-participantes">` na toolbar com contagem visível; atualizar `etapa1.js` para sincronizar
- [x] **0.7 Atualizar testes** — `tests/test_frontend_base.py`: remover asserção de `#conexao`; adicionar verificação de `.modos` dentro de `.toolbar`

**Arquivo-chave:** `docs/adr/0021-consolidacao-toolbar-e-modo-webview.md`

---

## Bloco 1 — Campos Condicionais e Calculados (Etapa 1) ✅

**Objetivo:** Formulário com comportamento dinâmico idêntico ao legado Tk.

### Tarefas

- [x] **1.1 Resolver `if_field`** — em `etapa1.js`, ao renderizar campos de um participante, verificar propriedade `if_field` no schema do campo; ocultar/mostrar via `hidden` conforme valor do campo-gatilho; adicionar listener de `change` no campo-gatilho
- [x] **1.2 Resolver `formula`** — campos com `formula` não são editáveis pelo usuário; o valor é calculado em tempo real com base nos outros campos preenchidos do mesmo participante; usar `Function()` com escopo restrito ou parser de expressão simples
- [x] **1.3 Textarea auto-resize para `TEXTO_LONGO`** — substituir `<input>` por `<textarea>` quando `tipo === 'TEXTO_LONGO'`; adicionar CSS de `field-textarea` com `resize:vertical; min-height:80px`
- [x] **1.4 Teste unitário de condicional** — adicionar cenário em `tests/test_frontend_behavior.py` ou novo arquivo

**Arquivo-chave:** `docs/adr/0022-plano-migracao-residual-tk-webview.md` (seção 2)

---

## Bloco 2 — Paginação Real de Campos ✅

**Objetivo:** Formulário agrupado por `pagina` definido no perfil, com navegação entre páginas.

### Tarefas

- [x] **2.1 Leitura da prop `pagina`** — ao carregar um perfil, agrupar campos por `pagina` (inteiro); renderizar cada página como `<fieldset>` ou seção colapsável; exibir indicador de página atual (ex.: "Página 1 de 3")
- [x] **2.2 Botões Anterior / Próximo** dentro do card de participante; o botão "Próximo" valida a página atual antes de avançar
- [x] **2.3 Integração com stepper** — o stepper global (etapas 1–4) permanece independente da paginação interna do formulário
- [x] **2.4 Teste de paginação** — smoke test que avança pelas páginas de um perfil com múltiplas páginas

---

## Bloco 3 — Conferência (Etapa 2 do Stepper) ✅

**Objetivo:** Tela de conferência completa antes de gerar, com navegação condicional do stepper.

### Tarefas

- [x] **3.1 Renderizar `#corpo-conferencia` por seção** — agrupar campos por `pagina`/seção, mostrar nome do participante, formulários selecionados, data, local e pasta
- [x] **3.2 Navegação condicional do stepper** — botões das etapas 2, 3 e 4 desativados até a etapa anterior ser concluída com sucesso; implementado em `app.js`
- [x] **3.3 Revalidação antes de confirmar** — ao clicar em "Confirmar e gerar documentos", re-verificar todos os campos obrigatórios e exibir erros específicos

---

## Bloco 4 — Modo Simples e Conflitos ✅

**Objetivo:** Paridade completa do modo simples (multi-formulários) com detecção de conflitos.

### Tarefas

- [x] **4.1 Seleção múltipla no modo simples** — permitir múltiplos formulários selecionados; desabilitar para modo avançado
- [x] **4.2 Detecção de conflitos** — ao selecionar formulários, comparar campos de mesmo `id` entre perfis; alertar conflito quando dois formulários definem o mesmo campo com tipos ou opções distintos
- [x] **4.3 Reaproveitamento de dados** — botão "Copiar dados de [Participante X]" dentro do card de cada participante; preenche campos idênticos

---

## Bloco 5 — Fila Global Interativa ✅

**Objetivo:** Fila de trabalhos acessível de qualquer tela, com progresso individual.

### Tarefas

- [x] **5.1 `#indicador-fila-global` clicável** — ao clicar, abrir painel lateral/modal com lista de trabalhos em andamento
- [x] **5.2 Painel de fila** — cada trabalho exibe nome, status, progresso (barra) e botão de cancelar
- [x] **5.3 Polling da fila** — `app.js` faz polling em `/api/v1/jobs` a cada 2s enquanto há trabalhos ativos; para o polling quando a fila esvazia

---

## Bloco 6 — Testes de Paridade com Perfis Reais ✅

**Objetivo:** Smoke test parametrizado cobrindo todos os perfis existentes.

### Tarefas

- [x] **6.1 Listar todos os JSONs** em `formularios/` e parametrizar `smoke_webview_ui.py` para carregar cada um
- [x] **6.2 Verificar renderização de campos** — garantir que todos os campos de cada perfil são renderizados sem erro JS
- [x] **6.3 Verificar modo simples vs avançado** para cada perfil

---

## Rastreamento de Progresso

| Bloco | Descrição | Estado | Versão alvo |
|-------|-----------|--------|-------------|
| 0 | Consolidação da toolbar | ✅ Concluído | v4.5.19 |
| 1 | Campos condicionais e calculados | ✅ Concluído | v4.5.20 |
| 2 | Paginação real de campos | ✅ Concluído | v4.5.20 |
| 3 | Conferência com navegação condicional | ✅ Concluído | v4.5.21 |
| 4 | Modo simples e conflitos | ✅ Concluído | v4.5.21 |
| 5 | Fila global interativa | ✅ Concluído | v4.5.22 |
| 6 | Testes de paridade com perfis reais | ✅ Concluído | v4.5.22 |

---

## Referências

- `docs/adr/0021-consolidacao-toolbar-e-modo-webview.md`
- `docs/adr/0022-plano-migracao-residual-tk-webview.md`
- `docs/BASE_UI_STATUS.md` (estado da migração base)
- `docs/SPEC_PRE_WEBVIEW.md`
- `docs/ARCHITECTURE.md`
