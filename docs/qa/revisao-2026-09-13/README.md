# Revisão QA da primeira WebView — 13/09/2026

**Parecer: backend aprovado nos testes executados; jornada da WebView bloqueada. Não homologar a troca de UI com esta evidência.**

## Escopo e isolamento

Foram usados dois snapshots completos obtidos por `git archive`, fora do checkout do agente implementador, com APPDATA/LOCALAPPDATA temporários e dados sintéticos:

- `8d85cfb`: primeira inspeção, testes e interação na janela real, 1200 × 850.
- `2a5ad230e70117179340a10a5382c145d0e3a7ae`: integração de visualizador/Config ocorrida durante a revisão; suíte completa, smoke da UI e teste de contrato repetidos nessa versão.

As mudanças locais em `app/ports/__init__.py` e `app/ports/binaries.py` não entraram nos snapshots. Commits posteriores não estão homologados por este relatório. Não houve alteração de código de produção, branch, índice Git, merge ou push nesta revisão. Apenas esta pasta de documentação/evidências foi criada. A implementação concorrente deve incorporar as propostas após reconciliar seu estado mais recente.

## Evidências executadas

| Teste | Versão | Resultado | Limite da evidência |
|---|---|---|---|
| `python -m unittest discover -s tests -v` | 8d85cfb | 332 testes, 41,220 s, OK | Suíte existente, não uma jornada completa da nova UI |
| Mesmo comando | 2a5ad23 | 337 testes, 38,721 s, OK | Inclui novos testes do endpoint de arquivos |
| `python -m app.webview_shell --self-test` | 8d85cfb | OK | Página técnica de diagnóstico |
| `python -m app.webview_shell --self-test --ui` | ambas | FALHA: `RuntimeError: Bridge indisponível`, exit 1 | Usa o HTML real da nova UI |
| `python tests/smoke_api_engines.py` | 8d85cfb | OK | HTTP, Word, Ghostscript, conteúdo e preservação do RTF; não interação pela UI |
| Mesmo smoke de motores | 2a5ad23 | OK, exit 0 | Repetição na integração mais recente testada |
| `python -m pip check` | ambiente usado | OK, sem dependências quebradas | Não valida instalador em máquina limpa |
| `node check-etapa2.cjs <snapshot>` | 2a5ad23 | Controle sem anexo passa; gerados + anexo FALHA | Executa JS real com DOM/API simulados, não E2E |
| Abrir janela, escolher pasta, navegar Etapa 2, finalizar, abrir Perfis | 8d85cfb | Navegação funciona; formulários vazios; seleção/finalização não respondem; Perfis vazio | A jornada de geração não pôde prosseguir |

Os erros de motores/build que aparecem em casos negativos da suíte não significam que a execução completa falhou: o resultado do runner foi OK. O teste de motores reais é uma evidência separada.

Os diretórios originais dos logs são `%LOCALAPPDATA%\Temp\contracto-qa-8d85cfb-20260913` e `%LOCALAPPDATA%\Temp\contracto-qa-2a5ad23-20260913` no ambiente do usuário. A pasta `evidencias` contém os logs preservados e o teste de contrato. Não contém documentos pessoais.

## Defeitos e riscos, com origem da evidência

P0 = bloqueia uso; P1 = compromete dados ou fluxo essencial; P2 = usabilidade/acessibilidade relevante. Achado por leitura não equivale a reprodução completa na janela.

| ID | Prioridade / evidência | Problema e efeito | Onde corrigir |
|---|---|---|---|
| UI-01 | P0, janela + smoke em ambas | Frontend real não conecta. `_authorized()` aceita somente URL nula/about:blank, enquanto `--ui` abre arquivo local. A ponte nega a página de produção. | `app/webview_shell.py`, autorização da origem e inicialização |
| UI-02 | P1, leitura em ambas | `app.js` inicia no DOMContentLoaded e retorna definitivamente se a ponte ainda não existe. Não aguarda `pywebviewready`. Corrigir só a autorização não resolve esta corrida. | `frontend/js/app.js`, `api.js` |
| UI-03 | P1, contrato JS reproduzido | Com anexos, `else if` exclui `file_ids` gerados. O backend aceita ambos e poderia concluir um conjunto incompleto sem detectar a intenção perdida no frontend. | `frontend/js/etapa2.js`, construção do POST de processamento |
| UI-04 | P1, leitura | Catálogo inicialmente marca todas as caixas, mas compõe somente o primeiro perfil. Desmarcar todas mantém seleção anterior; composição inválida deixa tela e estado divergentes. | `etapa1.js`, `carregar/selecionar` |
| UI-05 | P1, leitura | Mudar perfil recria os inputs e apaga valores digitados. Respostas de composição fora de ordem podem aplicar uma seleção antiga. | `etapa1.js`, estado do rascunho/renderização |
| UI-06 | P1, leitura | Campos dinâmicos viram todos inputs de texto; globais não são renderizados; quantidade de participantes fica fixa em um. Tipos, condições, limites e obrigatoriedade do perfil não estão representados corretamente. | `etapa1.js`, contrato de campos do backend, `index.html` |
| UI-07 | P1, leitura | Validação local verifica preenchimento básico; pode anunciar prontidão com CPF inválido/campo obrigatório ausente. `marcarErro` não é utilizado. Backend deve continuar validando, mas a UI precisa apontar campo e correção. | `etapa1.js`, apresentação de erros do DTO |
| UI-08 | P1, janela + leitura | Etapa 2 acessível e Finalizar habilitado sem geração. Cliques repetidos não têm proteção adequada; `ultimo` pode pertencer a geração anterior. | `etapa1.js`, `etapa2.js`, estado e comandos |
| UI-09 | P1, leitura | Polling ignora status HTTP diferente de 200, sem encerrar/explicar. Estado global mutável e timers podem misturar trabalhos. Cancelamento existe em JS, mas não possui comando visível conectado. | `etapa1.js`, `etapa2.js` |
| UI-10 | P2, leitura | Abrir pasta continua associado à geração; conclusão do processamento não atualiza essa ação para o resultado final. Anexos exibem o tipo, não um nome amigável que permita identificar o arquivo. | `etapa1.js`, `etapa2.js`, metadados seguros na ponte |
| UI-11 | P2, janela + leitura | Perfis abre uma tela vazia. Simples/Avançado não concretiza a diferença de jornada; geração segue para Etapa 2 em ambos. Navegação Início pode deixar etapa ativa inconsistente. | `ui.js`, `etapa1.js`, `index.html` |
| UI-12 | P2, visual + leitura | Azul da etapa ativa no tema escuro tem baixo contraste. Modal declara modalidade e retorna foco, mas não confina Tab nem torna fundo inerte. | `tokens.css`, `layout.css`, `ui.js` |
| UI-13 | P1 para visualizador, leitura de 2a5ad23 | Novo visualizador cria iframe com URL `blob:`, mas CSP não permite frames e cai em `default-src 'none'`. Há incompatibilidade estática a resolver; visualização real ficou bloqueada antes disso pela inicialização. | `index.html`, `etapa2.js`, política de conteúdo |

UI-01 tem uma contradição determinística entre origem usada e origem aceita. O smoke retorna indisponibilidade da ponte; não houve instrumentação completa da ordem de todos os eventos/CSP. UI-02 é um risco independente de inicialização identificado no código. Não ampliar permissões indiscriminadamente para contornar ambos.

## Avaliação de design

**Acertos observados:** identidade sóbria, agrupamentos legíveis em cartões, separação de geração/processamento, labels visíveis e navegação reconhecível. A estrutura oferece uma base adequada para evoluir sem redesenhar tudo.

**Acertos por implementação:** tokens de cor centralizados, texto dinâmico inserido por `textContent`, estilos de foco, `aria-current`, modal com título e retorno de foco, tratamento de `prefers-reduced-motion`. São boas escolhas, mas ainda exigem validação de teclado/leitor de tela. Em 2a5ad23 o tema ganhou persistência; a ausência de persistência observada na versão anterior não deve ser aberta como defeito novo.

**Melhorias prioritárias:**

1. Mostrar estado persistente “Conectando / Pronto / Falha ao conectar / Tentar novamente”. Desabilitar ações dependentes enquanto indisponível. Toast que desaparece não deve ser a única explicação de uma tela inutilizável.
2. Fazer a tela representar um único rascunho: formulários escolhidos, participantes, globais, destino e documentos esperados. Antes de gerar, mostrar pendências clicáveis e resumo do que será produzido.
3. Na Etapa 2, listar gerados e anexados juntos, com origem, nome amigável, tipo, participante e ação de remover apenas quando permitida. Confirmar a composição exata do processo antes de iniciar.
4. Exibir resultado final com lista verificável, contagem, falhas parciais, pasta correta e opção de novo processo. Status técnico como `completed` deve virar texto compreensível.
5. Definir comportamento real dos modos: Simples conclui a tarefa mínima; Avançado expõe organização/conversão adicional. Evitar controles que só alteram aparência.
6. Ajustar token da etapa ativa no escuro, foco por teclado, erros associados via `aria-describedby`, foco no primeiro erro e anúncio de progresso sem repetir a cada polling. Medir contraste por componente; não depender apenas da avaliação visual.
7. Completar Perfis ou apresentar estado vazio explícito e caminho útil. Validar 1024 × 768, mínimo suportado, 125%/150% DPI, janela maximizada, textos longos e zoom. Esses cenários não foram homologados nesta sessão.

## Plano de implementação, em ordem

| Ordem | Entrega | Critério de conclusão |
|---|---|---|
| 1 | Bootstrap seguro e recuperável (ADR-QA-BOOT) | Smoke com `--ui` passa; catálogo carrega; seletor nativo funciona; origem externa continua negada; inicializar duas vezes não duplica listeners |
| 2 | Corrigir composição do processo e estado dos jobs (ADR-QA-PROCESSO) | Gerados + anexos preservados; duplo clique não duplica tarefa; cancelamento e falha são terminais claros; nova geração não herda resultado antigo |
| 3 | Formulários dirigidos pelo perfil (ADR-QA-FORMULARIOS) | UI e payload têm seleção idêntica; rascunho preservado; globais, tipos e participantes atendidos; erros apontam campos |
| 4 | Fechar jornada, viewer e acessibilidade | Ver resultado real, abrir pasta final, retorno/nova tarefa, modal/teclado, contraste e modos aprovados |
| 5 | Homologação da distribuição | Suíte + contratos frontend + jornada Windows instalada com Word/GS; testar ausência de motores; registrar skips e artefatos |

Não misturar esta correção com extração documental. Primeiro estabilizar rascunho, evidências e validação que a futura importação reutilizará. Corrigir em branch própria após término ou divisão explícita de arquivos com o agente atual; executar o checklist na revisão final, depois decidir integração. Esta revisão não autoriza afirmar que todas as branches/commits anteriores foram homologados.

## Entregáveis relacionados

- [Roteiro de QA sênior](CHECKLIST.md)
- [Plano detalhado de extração, sem implementação](PLANO_EXTRACAO.md)
- [ADRs propostas](ADRS_PROPOSTAS.md)
- [Evidência do contrato de anexos](evidencias/check-etapa2.cjs)

## Pendências concretas

Não foi possível completar geração → anexação → processamento → visualização na janela por causa de UI-01/UI-02. Não foram testados instalador limpo, upgrade, leitor de tela, DPI múltiplo, documentos reais do usuário, grande volume ou commits posteriores a 2a5ad23. O checklist discrimina os passos para executar depois da correção; resultados de testes simulados não substituem essas verificações.
