# Correções aprovadas — resultado de 14/09/2026

## Resultado

Jornada central estabilizada no WebView2 real: formulário preservado, dois participantes, cálculo vindo do backend, dois PDFs preenchidos, anexo preservado, processamento com três resultados e PDF aberto na própria UI. Não substitui ainda a aplicação Tk de produção. O redesenho visual está em [PLANO_UI.md](PLANO_UI.md), para aprovação.

O trabalho partiu de `a682895` e incorporou as quatro alterações locais anteriores em ports, CSS e testes de bridge. Desenvolvimento em worktree separado; integração local na main após testes, sem publicação automática conforme escopo aprovado. As imagens ficam fora do Git.

## Alterações implementadas

- Bootstrap separa conexão, prontidão e eventos vinculados; falha seguida de retry não exige recarregar nem duplica listeners. Origem da ponte é definida pelo Python, sem método público de ampliação de confiança.
- Endereço dinâmico não é apagado por default legado. Dados duplicados conflitantes recebem erro estruturado. Identidade, globais e campos selecionados têm serialização explícita.
- Rascunho sobrevive à composição de perfis; seleção, checkbox, condições, limite/remoção de participantes e erros por campo têm tratamento. Pré-validação e cálculos usam o mesmo serviço Python da geração.
- Geração congela dados/destino; manifesto reúne gerados e anexos. Edição invalida resultados antigos. Cliques duplos e falha de resposta não criam novo comando na retomada: request_id é idempotente durante a sessão.
- Polling tem limite de tentativas e retomada explícita; cancelamento aguarda estado confirmado. Processamento concluído não se repete sem alteração explícita. Pasta e resultados pertencem ao job concluído.
- Viewer autorizado por ID abre PDF local sob CSP, limita tamanho a 20 MiB e descarta Blob ao fechar. Modal bloqueia fundo e possui tratamento de foco. Navegação e stepper ficam coerentes entre etapas; catálogo deixou de ser vazio.
- Build de diagnóstico inclui frontend; ausência de GS é explícita. Sem dependências novas. ADRs 0013, 0014 e 0015 consolidam as propostas anteriores implementadas.

## Evidência de validação

Windows, Python da `.venv` do projeto, massa sintética e diretórios temporários. Nenhum perfil pessoal foi alterado.

| Execução | Resultado |
| --- | --- |
| Suíte completa final | 345 testes, 33,605 s, OK, sem skips |
| API HTTP incluindo novo teste de preview | 20 testes, 7,852 s, OK; valor calculado adulterado é recalculado, sem job criado |
| `tests/smoke_webview_ui.py` | OK: eventos DOM no motor WebView2, bridge e HTTP reais; inclui resposta 202 deliberadamente perdida, retomada e invalidação após editar |
| Mesmo smoke com fixture de cálculo, `--visible` | OK: cálculo 20,00 visível, geração e processamento conferidos no disco; 13 verificações JS, exatamente dois jobs concluídos e três resultados finais |
| `tests/smoke_test_gui.py` | OK: dois participantes e quatro PDFs preenchidos no Tk real |
| `tests/smoke_webview.py` | OK: JS, bridge, HTTP e encerramento reais |
| `tests/smoke_api_engines.py` | OK: Word e GS reais via HTTP, conteúdo e original RTF preservados |
| Backend isolado | 4 testes, OK |
| `python -m pip check` | Nenhuma dependência quebrada |
| PyInstaller + `ContractoBase.exe --self-test --ui` | Build final concluído e autoteste OK, código de saída 0 |

O smoke da jornada usa adaptador sintético de seleção para garantir isolamento; não equivale a clicar em todos os diálogos nativos. Houve inspeção visual adicional da janela real e abertura do PDF carregado. Testes negativos de conexão/cancelamento usam falhas controladas onde necessário. Logs completos permanecem locais em `%TEMP%/contracto-fixes-*`; erros de fixtures durante desenvolvimento foram corrigidos antes da validação final.

## Prints

Pasta do projeto: `prints/qa-2026-09-14-correcoes/`, com galeria `index.html`. Oito imagens: conclusão/manifesto, viewer carregado, Perfis, Configurações, formulário/cálculo, participante/destino, confirmação de remoção e viewer carregando. Capturas reais, sem montagem. Massa de QA não representa o catálogo pessoal. A seleção para README deve usar telas estáveis; carregamento serve como evidência de QA.

Não há cobertura fotográfica de todos os estados: inicialização, processamento ativo, cancelamento, cada erro e todos os seletores ainda precisam da rodada visual dedicada. As capturas anteriores de 13/09 ficam em sua pasta histórica; representam a versão com falhas e não devem ser apresentadas como UI final.

## O que falta, por motivo e prioridade

1. **Redesenho visual e acessibilidade completa (próximo trabalho):** executar o plano por telas, medir contraste, testar teclado dentro do iframe, Narrator, resoluções e DPI. A correção de foco no código não homologa todos esses casos. Viewer ainda tem rolagens concorrentes e transição vazia enquanto o PDF carrega.
2. **Instalador e máquina limpa (gate de distribuição):** o executável onedir foi testado neste notebook. Faltam instalador Inno Setup, detecção de WebView2, ciclo de atualização/desinstalação e Windows 10/11 limpos. Portanto o lote 6 tem build e smoke concluídos, mas homologação de instalação permanece pendente; não anunciar release da nova UI.
3. **Gestão de perfis:** WebView possui consulta/composição; edição/importação/exportação ainda pertence ao Tk. Exige contrato de persistência e conflitos próprio antes de acrescentar botões de edição.
4. **Resiliência de processo:** cancelamento Word não é instantâneo durante COM; retomada idempotente só vale na sessão. Queda abrupta pode deixar staging; recuperação exige comprovar propriedade, sem apagar por prefixo. São pendências arquiteturais anteriores, não resolvidas por alterações visuais.
5. **Corpus e PDF/A:** smoke sintético não comprova fidelidade de todos os contratos. Homologar documentos representativos e usar validador externo para certificação PDF/A; nesta rodada foi usado o validador interno.
6. **Execução remota:** confirmar que o GitHub contém os commits locais antes de iniciar o agente web. Esta rodada não fez push nem alterou permissões GitHub. Linux não homologa COM/WebView2; manter aceite Windows explícito.
7. **Extração documental:** somente plano, em `../revisao-2026-09-13/PLANO_EXTRACAO.md`; não implementada, conforme pedido. IA opcional propõe candidatos, esquema e validação controlam o preenchimento, revisão humana resolve ambiguidades.

## Reproduzir

Usar os comandos do AGENTS.md. Para observar a nova UI: `.venv/Scripts/python.exe -m app.webview_shell --ui`. Para revisão sem dados pessoais: `.venv/Scripts/python.exe tests/smoke_webview_ui.py --visible`. A pasta temporária desse teste é removida ao fechar. Build: `.venv/Scripts/python.exe scripts/build_webview_diagnostic.py`; bundle em `dist/webview-diagnostic/ContractoBase/` no checkout em que o build for executado.
