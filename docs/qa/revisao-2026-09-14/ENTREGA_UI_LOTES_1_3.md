# Redesign da WebView — entrega dos lotes 1–3

Implementado em 14/09/2026 após aprovação do plano. Este é o ponto de comparação visual previsto em `PLANO_UI.md`, antes de iniciar os lotes 4–7.

## O que mudou

| Área | Antes | Implementação |
| --- | --- | --- |
| Navegação | Faixa azul dominante, modos misturados ao menu, stepper em todas as telas | Cabeçalho neutro; Documentos, Perfis e Configurações; modos junto ao formulário; etapas somente na jornada |
| Formulário | Campos de largura uniforme empilhados, sem grupos | Identificação com proporção nome/CPF, endereço, dados do formulário e dados compartilhados; duas colunas adaptáveis; assinatura e destino agrupados |
| Orientação | Contagem de pendências pouco explicativa | Resumo de modelos, participantes e pasta; instruções curtas; uma ação principal para gerar |
| Validação | Campos vermelhos antes de interação; resumo sem links | Erro após blur ou revisão explícita; resumo com rótulos humanos e botões que fecham o modal e focam o campo escolhido; assinatura também tem mensagem associada |
| Aparência | Cores e bordas pouco consistentes entre temas | Tokens semânticos para superfícies, texto, controles, foco e ação; azul mais claro no tema escuro; remoção das ondas decorativas |
| Teclado | Sem atalho ao conteúdo | Botão inicial de salto ao conteúdo, sem alterar a URL confiável da ponte; oculto até receber foco; incluído no fundo inerte dos modais |

Rascunho, condições, cálculos Python, snapshot e retomada de jobs mantêm seus contratos. A seleção de modos não apaga os campos. O resumo não persiste dados pessoais além do rascunho da sessão. Não houve alteração de dependências ou API.

## Verificação executada

- Suíte completa: **346 testes, 33,389 segundos, OK**. Após o ajuste final do salto ao conteúdo, testes básicos de frontend e jornada real com matriz de layout foram executados novamente e passaram.
- Jornada WebView2 real: 24 verificações JS, incluindo erros após blur, foco pelo resumo, stepper contextual, preservação após modo/composição, cálculo do backend, perda controlada da resposta e retomada sem duplicação. PDFs e anexo conferidos no disco.
- Matriz de layout: janelas solicitadas de 1024×768, 1280×720, 1920×1080 e 680×768, páginas Início/Etapa 2/Perfis/Configurações, temas claro/escuro. Verificados largura do documento e limites horizontais dos controles visíveis. Isso não equivale a simular DPI nem garante todas as dimensões verticais e conteúdos possíveis.
- Contraste: teste calcula luminância das cores CSS e verifica texto/superfícies com mínimo 4,5:1; bordas de controle e foco com 3:1 nos pares cobertos. Não é auditoria completa WCAG, nem mede controles desabilitados, renderização do PDF ou todas as combinações de estados.
- Inspeção manual da janela real: início, seleção de tema por teclado, grupos do formulário, assinatura/destino e modal de pendências. Janela maximizada para conferir rodapé completamente visível.
- Bundle de diagnóstico reconstruído: `ContractoBase.exe --self-test --ui` passou; HTML e `ui.js` empacotados têm hashes iguais aos arquivos finais.

Logs locais: `%TEMP%/contracto-ui-redesign-unit.log`, `contracto-ui-redesign-layout-final.log`, `contracto-ui-redesign-build-final.log`. Os motores Word/GS foram homologados na rodada anterior; não foram alterados por este bloco visual.

## Evidência visual para aprovação

Galeria local: `prints/qa-2026-09-14-redesign/index.html`, sem versionamento. Contém a referência anterior e capturas reais dos dois temas, campos e validação. As primeiras imagens mostram recortes visíveis da janela de QA; as capturas de destino e modal usam janela maximizada. Dados/perfis sintéticos; não são todos os estados possíveis nem o catálogo pessoal.

Avaliar a direção do cabeçalho neutro, densidade dos grupos, resumo lateral e contraste antes de ampliar esse padrão. A comparação serve para revisar composição; estados antes/depois não são massas idênticas para teste de diferença pixel a pixel.

## Próximo bloco e limites

1. **Lote 4:** nomes e metadados seguros dos documentos, origem/participante e categorias humanas de anexo. Nesta entrega a Etapa 2 recebeu apenas os estilos compartilhados e o título; seus botões genéricos continuam pendentes.
2. **Lotes 5–6:** revisar todos os estados de fila/retomada e resolver o carregamento vazio/rolagens concorrentes do viewer, incluindo teclado dentro do PDF. Não confundir os ajustes básicos de foco com homologação do iframe.
3. **Lote 7:** busca/detalhes no catálogo e capacidades nas configurações. Consulta simples e escolha de tema continuam sendo as funções disponíveis.
4. **Aceite de distribuição:** DPI 100/125/150%, Narrator, Windows limpo, instalador, atualização/desinstalação e corpus representativo continuam pendentes. A UI de produção permanece Tk; este bundle é diagnóstico.

Nenhuma extração de dados de documentos foi implementada. Publicação remota não foi feita. Prosseguir com os lotes 4–7 após a revisão visual prevista no plano aprovado.
