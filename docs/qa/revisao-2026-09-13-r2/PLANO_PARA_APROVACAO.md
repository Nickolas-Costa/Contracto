# Segunda revisão da WebView — plano para aprovação

Data: 13/09/2026. **Estado: proposta; correções não implementadas por esta revisão.**

## Parecer

A abertura evoluiu e está funcionando na versão testada. A jornada completa ainda não está pronta: geração rejeita endereço preenchido; Etapa 2 não conecta seus eventos; anexos continuam excluindo gerados do payload. A suíte Python e o smoke de abertura passam, mas não cobrem essas falhas de integração do frontend.

## Base exata e isolamento

Comparação: `2a5ad23` → `a682895` (merge de `9d23799`). Snapshot em `C:/Users/sousa/AppData/Local/Temp/contracto-qa-a682895-r2/source`, criado por archive e complementado com quatro arquivos locais: `app/ports/__init__.py`, `app/ports/binaries.py`, `frontend/css/layout.css`, `tests/test_webview_bridge.py`.

SHA-256 do patch local congelado: `1F2461E9A6BE4EF75E8643FB47BB47984094F56D512323D9BB594213E849A0D4`. Os resultados se referem a **commit + alterações locais congeladas**, não apenas ao commit. Dados e destino foram temporários; nome, CPF e endereço usados são massa de teste. Nenhum arquivo de implementação do agente foi alterado. Não houve commit, merge ou push.

## O que mudou e foi verificado

| Mudança | Verificação | Situação |
|---|---|---|
| Shell registra a URL local da UI na autorização | Smoke `--self-test --ui` agora passa; catálogo aparece na janela | Corrigiu bloqueio de abertura; revisar superfície pública descrita abaixo |
| Arranque espera DOM/ponte e consulta health | Janela mostra “Pronto”, formulário carrega | Caminho feliz aprovado; retry ainda defeituoso |
| Estado persistente de conexão e botão de retry | Código adicionado em app.js/index.html; CSS ainda local | Parcial: mensagem existe, recuperação não funciona em cenário testado |
| Tema inicial e persistência movidos para ui.js | Config abre, menu abre e tema claro/escuro muda na janela | Mudança visual funcional; persistência entre reinícios não rehomologada nesta rodada |
| Estilo local da mensagem de conexão | Capturado no snapshot | Ainda não commitado na origem |
| Testes adicionais de API/ponte | 339 testes passam no snapshot | Não substituem testes de fluxo frontend |

O título do commit menciona Etapa 2, mas `etapa2.js` não teve correção de composição nesse intervalo. A comparação de arquivos e o teste executado prevalecem sobre a descrição do commit.

## Resultados dos testes

| Teste | Resultado |
|---|---|
| `python -m unittest discover -s tests -v` | **339 testes, 37,121 s, OK** |
| `python -m app.webview_shell --self-test --ui` | **WEBVIEW SELF-TEST OK** |
| `python tests/smoke_api_engines.py` | **OK**: HTTP, Word, Ghostscript, conteúdo e preservação do RTF |
| Contrato JS de Etapa 2, reaproveitado da revisão anterior | Sem anexo passa; gerados + anexo **falha**, omite file_ids |
| Novo contrato JS de bootstrap | Health 200 conecta Etapa 1 uma vez, Etapa 2 **zero vezes** |
| Novo contrato JS de retry (503 inicial, próxima resposta seria 200) | Clique em retry não consulta health novamente: **1 chamada total, permanece falha** |
| UI real: início, Config, temas, Perfis, navegação | Telas acessíveis; Perfis continua vazio; etapa ativa diverge ao voltar pelo Início |
| UI real: pendências e teclado | Modal abre e Escape fecha; Tab sai para controles do fundo |
| UI real: preencher participante/data/local e escolher pasta | Funciona; chega a “Pronto para gerar” |
| UI real: gerar com endereço preenchido | Backend rejeita `endereco`; UI mantém “Pronto para gerar”; print do erro preservado |
| UI real: Anexar e Finalizar | Sem resposta; não chegou a seletor de anexos/processamento |

Contratos JS executam os scripts reais com adaptadores simulados de DOM/API. Não são E2E. Os screenshots foram obtidos pela janela Windows real, sem editar sua aparência ou fabricar estados.

## Pendências em ordem de risco

### P1 — fronteira da ponte

`ShellBridge.allow_url()` é um método público entregue no objeto `js_api`. O runtime pywebview instalado enumera métodos públicos para expô-los ao JavaScript (`webview/util.py`, função interna `get_functions`, exclui nomes iniciados por `_`). Logo, a função que altera a lista confiável também integra a superfície exposta. **Constatação por leitura do código/runtime; não foi executado ataque com navegação externa.**

Tornar a configuração da origem exclusivamente nativa, preferencialmente no construtor ou método privado, e testar explicitamente a lista de métodos exportados. Não apenas renomear o teste de autorização; ele hoje chama a função diretamente em Python e não protege essa superfície. Reavaliar autorização de `None/about:blank` no modo UI e navegação durante carregamento. Preservar token nativo, loopback e IDs opacos.

### P1 — geração e identidade dos campos

`etapa1.js/lerParticipantes()` envia `endereco: ""`, enquanto o input preenche `campos_dinamicos.endereco`. Na janela, o backend rejeitou o endereço apesar de ele estar visivelmente preenchido. Unificar serialização com a fonte canônica de Participante (ADR 0012), definindo precedência para aliases e eliminando duplicação conflitante. Testar o payload real da UI até a geração, não só o modelo Python com DTO montado manualmente.

Critério: preencher endereço uma vez, validar e gerar o documento com o valor correto. A UI não pode anunciar prontidão quando ainda tem erro obrigatório retornado pelo servidor; mostrar erro no campo e resumo acionável.

### P1 — bootstrap incompleto e retry

`finalizarArranque()` chama apenas `ContractoEtapa1.ligar()`. Restaurar ligação idempotente da Etapa 2. `iniciado=true` ocorre antes do health; se health falhar, o botão “Tentar novamente” chama `iniciar()`, que retorna imediatamente. Separar “inicializando”, “eventos ligados” e “conectado”, evitando duplicar handlers durante recuperação. Considerar que atualizar pendências também habilita gerar, enquanto o bootstrap controla o mesmo botão: centralizar o estado habilitado.

Critério: 503 → retry → 200 recupera sem recarregar a janela; listeners uma vez; Anexar abre seletor, Finalizar valida/submete; desconexão desabilita operações dependentes.

### P1 — composição e estado do processo

Permanece o `if (anexos) ... else if (file_ids)` que perde PDFs gerados. Enviar os dois conjuntos, exibir manifesto e validar resultado contra intenção. Proteger duplo envio, rascunho alterado durante job, respostas antigas, `ultimo` de outra geração e erro permanente de polling. Cancelamento precisa de ação visível e terminal confirmado. Pasta final deve corresponder ao job de processamento.

### P1/P2 — formulário, visualizador e UX

- Seleção inicial marca todos os perfis visualmente, mas compõe o primeiro. Seleção vazia/inválida mantém estado anterior; troca de perfil apaga dados; respostas podem chegar fora de ordem.
- Campos globais, tipos, condições e quantidade de participantes continuam incompletos. Priorizar os perfis efetivamente suportados pela distribuição, deixando limitações explícitas.
- Viewer ainda cria iframe `blob:` sem permissão compatível na CSP (`default-src 'none'`, sem `frame-src`). Não foi acessível para teste real. Revisar somente permissões necessárias, tamanho de PDF, liberação de Blob e falha de leitura.
- Perfis vazio; modos não têm jornada funcional claramente distinta; Início não sincroniza o stepper.
- Modal não contém foco; contraste da etapa ativa escura continua fraco; mensagens de erro são temporárias e distantes do campo. Captura demonstra foco fora do modal.
- Documentos de estado do repositório ainda descrevem apenas a base anterior; atualizar após estabilizar a implementação, sem afirmar antecipadamente que é UI de produção.

## Plano proposto para aprovação

| Lote | Escopo e arquivos principais | Gate de conclusão |
|---|---|---|
| 1 — bootstrap e ponte | `app/webview_shell.py`, `frontend/js/app.js`, contratos da ponte/arranque | Superfície JS não altera origens; UI inicia; retry recupera; Etapa 2 ligada uma vez; navegação externa negada |
| 2 — geração correta | `frontend/js/etapa1.js`, adaptação DTO/Participante se necessária | Endereço preenchido chega ao gerador; validação no campo; documento gerado contém nome/CPF/endereço corretos |
| 3 — processo completo | `etapa1.js`, `etapa2.js`, módulo de estado se justificado | Gerados + anexos preservados; dupla submissão/estado antigo protegidos; polling e cancelamento terminais claros; pasta final correta |
| 4 — formulários confiáveis | Renderização e composição do perfil | Seleção/payload idênticos; rascunho preservado; globais, tipos, condições e participantes suportados e testados |
| 5 — UI utilizável | `ui.js`, `index.html`, CSS e viewer | Perfis tem conteúdo/estado útil; modos definidos; foco contido; contraste medido; viewer real abre sob CSP; navegação coerente |
| 6 — homologação e material GitHub | Testes, build/instalação e documentação | Suíte + contratos + jornada instalada aprovados; prints reais de carregamento, conclusão, anexos e viewer; README atualizado só com material selecionado |

Executar os lotes em ordem; lote 4 pode exigir complementos ao 2 conforme perfil. Primeiro reconciliar as quatro mudanças locais com o agente atual e definir um responsável por arquivo. Não realizar refatoração ampla simultânea dos mesmos módulos. A aprovação pedida é deste escopo de correções; não inclui IA/OCR, redesenho completo ou publicação automática.

## ADRs

Reutilizar as quatro propostas da revisão anterior, sem criar numeração concorrente:

- ADR-QA-BOOT: acrescentar configuração da origem inacessível ao JS, estados separados e retry comprovado.
- ADR-QA-FORMULARIOS: explicitar serialização canônica e precedência de aliases, com regressão de endereço.
- ADR-QA-PROCESSO: manter snapshot/manifesto e testar completude real.
- ADR-QA-EXTRACAO: continua futura e fora do escopo desta correção.

Promover para ADRs individuais numeradas quando o responsável confirmar decisão e escopo; só marcar aceita quando implementada e verificada. Confrontar com ADRs 0005, 0007, 0010, 0011 e 0012. Não criar uma ADR por bug visual.

## Prints e limitações

Pasta local: `prints/qa-2026-09-13-r2/`. Exclusão feita em `.git/info/exclude` com `/prints/`, sem alterar `.gitignore`. Nenhuma imagem está no índice Git. Há galeria HTML e índice Markdown nessa pasta, ambos locais.

Capturadas as quatro telas acessíveis (Início, Etapa 2, Perfis, Config), temas claro/escuro em Config, modal de pendências, foco fora do modal, seletor de pasta, preenchimento, prontidão e erro real de geração. Algumas imagens são estados intermediários repetidos; a galeria distingue evidências úteis de tentativas/transições.

**Não capturados:** carregamento inicial muito breve, processamento em curso/concluído, seletor de anexos e visualizador. A jornada não atingiu esses estados por bloqueios descritos; não foram fabricados screenshots. A pasta cobre a nova WebView testada, não todas as telas do aplicativo Tk legado. DPI múltiplo, instalação limpa e leitor de tela permanecem pendentes.

Para README público, selecionar imagens estáveis após correções; as atuais documentam uma versão ainda com defeitos. O seletor mostra apenas pasta de teste, mas mantém elementos do Windows e nomes locais de navegação. Avaliar esse enquadramento antes de publicação; nada foi publicado por esta revisão.
