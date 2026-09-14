# Revisão visual após estabilização — plano para aprovação

> Atualização: lotes 1–7 implementados após aprovação; ver [entrega dos lotes 1–3](ENTREGA_UI_LOTES_1_3.md) e [complemento dos lotes 4–7](ENTREGA_UI_LOTES_4_7.md). A homologação completa continua pendente.

14/09/2026. Escopo proposto, ainda não implementado. Referência: WebView2 real com massa sintética e prints locais em `prints/qa-2026-09-14-correcoes/`. O protótipo ZIP ignorado não foi usado como fonte nesta revisão.

## Avaliação

A jornada central agora gera, mantém anexos, processa e mostra o PDF. São acertos a separação entre geração e processamento opcional, o tema alternável, a indicação de etapa, a validação próxima ao campo, o manifesto e o bloqueio de comandos duplicados. Preservar essas capacidades no redesenho.

A apresentação continua básica: cartões ocupam toda a largura sem organizar grupos, campos curtos ficam muito largos, o cabeçalho compete com o conteúdo, os resultados aparecem como botões genéricos e a tela de Perfis é apenas um inventário. O visualizador tem rolagem do documento, modal e página ao mesmo tempo. Configurações ocupa uma tela inteira para uma opção. O stepper continua visível fora da jornada. Erros aparecem antes de o usuário interagir. Essas observações não equivalem a homologação de todas as combinações de DPI, tema e perfil.

## Ordem de implementação

| Lote | Alterações e locais | Critério de aceite |
| --- | --- | --- |
| 1. Estrutura e linguagem | `index.html`, `ui.js`, CSS: navegação de trabalho separada de Perfis/Configurações; retirar stepper dessas duas telas; títulos claros, uma ação principal por estado; substituir “Config” e jargão técnico | Usuário identifica onde está, o que falta e a próxima ação sem conhecer geração/COM/API |
| 2. Sistema visual | CSS: tokens únicos de cor, fonte, espaços, raio e foco; reduzir brilho decorativo; largura de conteúdo limitada; controles consistentes; contraste medido nos dois temas | Texto normal com razão mínima 4,5:1, foco/controles 3:1; nenhuma ação cortada em 1024×768, 1280×720 e 1920×1080 a 100/125/150% |
| 3. Formulário | `etapa1.js`: identidade, endereço e dados do documento em grupos; duas colunas quando houver espaço, uma no estreito; CPF/data com largura adequada; resumo de participantes; erros após blur/tentativa, resumo com links de foco | Trocar perfil/modo preserva rascunho; remover pede confirmação; campos condicionais e calculados continuam corretos; erro leva ao campo sem rolagem obscura |
| 4. Documentos e resultados | Implementado: `etapa2.js` e resposta de job retornam nome seguro, origem, participantes e tamanho; anexos têm categoria humana | Duas pessoas e três documentos são distinguidos; nenhum caminho absoluto é exposto; original continua preservado |
| 5. Estados operacionais | Implementado: estados persistentes de envio, fila, execução, cancelamento, falha, resultado incerto e retomada | Cliques repetidos não criam jobs; a retomada usa o mesmo comando; progresso não anuncia sucesso antecipado |
| 6. Viewer e modais | Implementado: painel de carregamento/falha, modal amplo, título seguro, fechamento, `inert` e revogação Blob | Foco de página é restaurado; Escape e Tab no diálogo foram exercitados. O teclado interno do leitor PDF depende do componente WebView2 e exige teste assistivo manual |
| 7. Perfis e configurações | Implementado: busca no catálogo, cartões de consulta e capacidades PDF/PDF-A/RTF sem caminhos | Nenhum botão promete edição inexistente; CRUD/importação seguem como incremento separado |
| 8. Homologação | Capturas comparáveis, checklist abaixo, build onedir e instalação limpa | Só substituir Tk após gates de Windows, motores, acessibilidade e distribuição; regressões documentadas |

Não introduzir framework ou dependências apenas para refazer CSS. Caso necessário, aplicar `DEPENDENCY_REVIEW.md`. Manter regras de negócio no backend e os contratos das ADRs 0013–0015.

## Checklist de QA sênior para o próximo aceite

1. Instalar em usuário Windows novo: com/sem WebView2, Word e GS; PDF comum funciona sem os motores opcionais; erros de capacidade são claros. Atualizar/desinstalar sem perder dados. Verificar assinatura, permissões e logs.
2. Abrir/reabrir e recuperar conexão; repetir evento de prontidão; atrasar catálogo/composição; alterar seleção rapidamente durante respostas lentas. Não duplicar handlers ou aplicar resposta antiga.
3. Exercitar zero/um/vários perfis compatíveis e incompatíveis; catálogo vazio; máximo de participantes; adicionar/remover/cancelar remoção. Verificar ordem e associação de cada pessoa ao PDF.
4. Campos vazios, espaços, acentos, textos longos, CPF/data inválidos, seleção, checkbox, globais, cálculo, condicionais encadeadas e limpeza de ocultos. Tentar enviar cálculo adulterado e campos extras. Backend mantém autoridade.
5. Cancelar seletores; selecionar arquivo removido ou pasta sem permissão; expirar seleção; anexar PDF/RTF, repetir tipo/arquivo e mudar formato. Falha não destrói rascunho.
6. Clique duplo, resposta perdida após aceite, falha de consulta, cancelar em fila e execução, encerrar app durante processamento. Verificar originais, staging, completude e ausência de publicação parcial.
7. Abrir cada PDF; conferir nome, CPF, endereço e campos dinâmicos; texto/páginas dos anexos, dois participantes distintos; abrir pasta do job correto. Validar PDF/A externamente se houver exigência de conformidade.
8. Navegar só por teclado, leitor Narrator, zoom/DPI, janela estreita, dois temas e movimento reduzido. Avaliar foco após fechamento e campos ocultos fora da ordem de Tab.
9. Registrar prints de cada tela e modal: vazio, preenchido, erro, carregando, executando, cancelando, concluído, viewer, seletores e recuperação. Usar massa sintética; excluir prints do Git até seleção explícita para README.

## Entrega para agente remoto

Partir da main que contém as ADRs 0013–0015 e este relatório, conferindo o commit antes de editar. Implementar lotes 1–3 primeiro e entregar comparação visual para aprovação; depois 4–7. Não recriar servidor/fila/bridge. Executar unittest e testes JS disponíveis; registrar skips de WebView2/COM no Linux. Preparar roteiro Windows para o aceite final. Não marcar instalação ou acessibilidade como homologadas por uma suíte headless. Não implementar extração documental neste trabalho.

## Extração de documentos permanece fora da implementação

O plano anterior `../revisao-2026-09-13/` continua referência: extração assistida com esquema canônico, aliases/versionamento, evidência por campo, validação determinística e revisão humana antes de preencher. IA/OCR pode sugerir candidatos quando estrutura e nomes variam; não substitui validação nem autoriza preenchimento automático ambíguo. Nenhum motor de IA ou envio de documentos a terceiros foi adicionado.
