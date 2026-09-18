# ADR 0022 — Plano de Migração Residual Tk → WebView2 (Pós v4.5.18)

- **Estado:** futura
- **Data:** 2026-09-17
- **Contexto:** Com a migração base para WebView2 homologada na v4.5.18, a UI de produção já opera via `index.html`. Porém, várias funcionalidades que existiam no legado CustomTkinter não foram ainda replicadas com paridade completa na WebView. Este ADR registra o conjunto de lacunas identificadas, servindo de guia para as próximas versões.

- **Decisão:** Registrar formalmente todas as pendências de migração como escopo de trabalho futuro, agrupadas por área funcional. Cada item deve ser tratado em uma ADR ou tarefa específica antes de ser implementado, respeitando os limites arquiteturais do projeto.

- **Alternativas consideradas:**
  - Rastrear pendências apenas em issues de repositório — descartado, pois os ADRs são a fonte canônica de decisões arquiteturais e o histórico da migração.
  - Voltar ao Tk para funcionalidades não migradas — descartado; a decisão de migrar para WebView2 é irreversível (ADR 0005/0013).

- **Consequências:** Nenhuma mudança de código nesta ADR. Serve exclusivamente como mapa de trabalho. Cada item ao ser implementado deve referenciar esta ADR na sua ADR específica.

---

## Pendências por Área

### 1. Toolbar e Apresentação Global (prioridade imediata — ver ADR 0021)

| Item | Arquivo principal | Descrição |
|------|-------------------|-----------|
| Remover `#conexao` da toolbar | `index.html`, `layout.css` | Indicador de backend invisível ao usuário final |
| Mover seletor de modo para toolbar | `index.html`, `etapa1.js` | "Só gerar" / "Gerar e organizar" devem estar na barra de topo |
| Destacar contagem de participantes | `etapa1.js`, `layout.css` | Usar badge/chip visível sem precisar de hover |
| Remover painel lateral `.summary` | `index.html`, `layout.css` | Expandir workspace para 100% da largura |

### 2. Formulário de Preenchimento (Etapa 1)

| Item | Arquivo principal | Descrição |
|------|-------------------|-----------|
| Paginação real por páginas do perfil | `etapa1.js` | Campos devem ser agrupados por `pagina` definido no perfil JSON |
| Campos condicionais (`if_field`) | `etapa1.js` | Mostrar/ocultar campos com base em valor de outro campo |
| Campos calculados (`formula`) | `etapa1.js` | Preencher automaticamente campos com expressão de cálculo |
| Campos longos (`TEXTO_LONGO`) com resize | `layout.css` | Textarea com auto-resize e contagem de caracteres |
| Conflitos no modo simples | `etapa1.js` | Detectar e alertar quando múltiplos formulários usam o mesmo campo com valores conflitantes |
| Reaproveitamento de dados entre participantes | `etapa1.js` | Copiar valores de um participante para outro (igual ao legado Tk) |

### 3. Etapa de Conferência (Etapa 2 — Stepper)

| Item | Arquivo principal | Descrição |
|------|-------------------|-----------|
| Renderizar todos os campos preenchidos agrupados | `etapa1.js` (`conferir()`) | Exibir por seção/página, não apenas lista plana |
| Navegação condicional do stepper | `app.js` | Botões do stepper só ativados quando etapa anterior completa |
| Confirmação com validação final antes de gerar | `etapa1.js` | Re-validar servidor e campos antes de confirmar |

### 4. Etapa de Revisão e Conclusão

| Item | Arquivo principal | Descrição |
|------|-------------------|-----------|
| Paridade da etapa 2 com todos os perfis reais | `etapa2.js` | Testar cada perfil existente no diretório `formularios/` |
| Cancelamento e retomada de trabalhos em fila | `etapa2.js` | Verificar estados `cancelling`, `uncertain`, `queued` |

### 5. Fila Global

| Item | Arquivo principal | Descrição |
|------|-------------------|-----------|
| Fila acessível de qualquer tela | `app.js` | `#indicador-fila-global` deve abrir painel de fila ao clicar |
| Painel de fila com progresso individual | `app.js`, `etapa2.js` | Mostrar cada trabalho em andamento com barra e status |

### 6. Testes de Validação

| Item | Arquivo principal | Descrição |
|------|-------------------|-----------|
| Testar todos os perfis e formulários reais | `tests/smoke_webview_ui.py` | Parametrizar smoke test com todos os JSONs em `formularios/` |
| Teste de paridade modo simples | `tests/` | Cenário com múltiplos formulários selecionados e conflitos |
| Validação do stepper condicional | `tests/` | Verificar que etapa 3 e 4 não são clicáveis sem completar etapas anteriores |

---

- **Arquivos afetados (futuro):** `frontend/index.html`, `frontend/js/etapa1.js`, `frontend/js/etapa2.js`, `frontend/js/app.js`, `frontend/css/layout.css`, `tests/smoke_webview_ui.py`

- **Revisão:** ADR 0005 (API loopback), ADR 0010 (pendências visuais do shell), ADR 0012 (participante modular), ADR 0013 (bootstrap WebView), ADR 0014 (rascunho canônico), ADR 0015 (snapshot e retomada), ADR 0016 (integridade HTML), ADR 0021 (consolidação toolbar).

- **Aceite:** Cada item desta tabela deve ter sua própria ADR ou ser rastreado como concluído neste documento quando implementado.

- **Testes:** Não aplicável a esta ADR (registro de escopo apenas).
