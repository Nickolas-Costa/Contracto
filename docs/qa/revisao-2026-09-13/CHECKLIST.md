# Roteiro de QA sênior — nova WebView

## Preparação e registro

Congelar commit e registrar Windows, Python/WebView2, Word/GS, resolução/DPI, modo/tema e pacote usado. Usar diretório temporário e perfis de teste, sem documentos pessoais. Preparar dois participantes sintéticos distintos com CPFs válidos gerados para teste; um CPF inválido; PDF de duas páginas com marcador GERADO; PDF com marcador ANEXO; RTF sintético; PDF imagem; arquivo corrompido e nomes Unicode/espaços. Conferir SHA-256 dos originais antes/depois. CPF válido matematicamente não prova identidade real.

Cada execução registra: ID, commit, passos, esperado, observado, log/screenshot, aprovado/falhou/bloqueado/não executado. Os testes abaixo são **roteiro pendente**, salvo as evidências explicitamente registradas no README. Não marcar aprovado porque existe um teste unitário parecido.

## Jornada principal, na ordem real

| ID | Passos | Resultado esperado |
|---|---|---|
| J01 | Abrir aplicativo instalado com dados vazios; aguardar conexão; fechar e reabrir 3 vezes | Catálogo aparece; conexão tem estado claro; sem erro de ponte nem handlers duplicados |
| J02 | Selecionar um perfil; comparar checkboxes, campos e resumo | Uma seleção única e consistente com contrato do backend |
| J03 | Preencher participante principal e globais válidos; escolher destino nativo | Valores persistem; destino identificável; seleção cancelada não apaga destino anterior |
| J04 | Gerar uma vez; acompanhar até terminal | Um job; feedback de progresso; arquivos esperados e conteúdo correto; originais intactos |
| J05 | Abrir cada documento e a pasta de geração | Conteúdo legível, participante correto, sem tokens pendentes; pasta corresponde ao job |
| J06 | Avançar; anexar PDF e RTF de tipos distintos; remover e recolocar um | Lista mostra identidade amigável, tipo e origem corretos; cancelar seletor não cria item |
| J07 | Conferir gerados + anexos; finalizar em PDF | Resultado contém **ambos**, com páginas/marcadores/ordem definidos; nenhuma perda silenciosa |
| J08 | Repetir com PDF/A-2b | Conversão real, conteúdo correto, originais preservados; validar conformidade com ferramenta apropriada se disponível, sem equiparar sucesso do GS a certificação |
| J09 | Visualizar todos os resultados; abrir pasta final | Viewer carrega sob CSP; pasta final correta; abrir/fechar viewer não acumula recursos |
| J10 | Iniciar novo processo com outra pessoa | Rascunho e resultados anteriores não contaminam novo processo; nenhuma troca de identidade |

## Formulários, integridade e ações concorrentes

| ID | Passos | Resultado esperado |
|---|---|---|
| F01 | Desmarcar todos; tentar gerar | Sem perfil ativo; geração bloqueada e instrução visível |
| F02 | Compor dois perfis compatíveis e depois incompatíveis | Composição válida é refletida; inválida não mantém seleção visual falsa |
| F03 | Digitar dados; trocar perfil; voltar | Preserva campos compartilhados; informa impacto sobre campos excluídos; sem apagar silenciosamente |
| F04 | Trocar seleção rapidamente com resposta atrasada | Apenas última intenção é aplicada; resposta antiga descartada |
| F05 | Exercitar texto, seleção, booleano, data, moeda, condicional e global | Widget e normalização corretos; apenas obrigatórios aplicáveis bloqueiam |
| F06 | Adicionar/remover participantes até limite do perfil | Sem mistura de campos entre pessoas; IDs estáveis; mínimo/máximo respeitados |
| F07 | Informar CPF inválido, data impossível, campo obrigatório vazio e texto longo | Erro localizável, associado ao input; foco no primeiro erro; backend confirma validação |
| F08 | Gerar por clique duplo, Enter repetido e voltar/avançar durante fila | Um comando efetivo; UI continua responsiva; dados do job imutáveis |
| F09 | Regerar com dados diferentes antes de finalizar resultado antigo | Exige escolha/reconciliação explícita; não usa silenciosamente o último resultado anterior |
| F10 | Anexar dois arquivos com mesmo tipo e mesmo arquivo duas vezes | Regra de duplicidade explícita antes de submissão; nunca sobrescreve sem avisar |
| F11 | Tentar finalizar sem gerados; testar fluxo somente anexos se for suportado | Comportamento coerente com produto, requisitos e permissões; sem botão inerte |

## Falhas, recuperação e backend

| ID | Passos | Resultado esperado |
|---|---|---|
| R01 | Abrir sem Word; tentar RTF; repetir PDF simples | Falha explica requisito; PDF simples continua conforme capacidades; nenhum fallback silencioso |
| R02 | Abrir sem Ghostscript; pedir PDF/A e PDF | PDF/A bloqueado com orientação; PDF não é anunciado como PDF/A |
| R03 | Selecionar pasta sem escrita / indisponível / pouco espaço em ambiente de teste | Mensagem acionável; sem job falsamente completo; sem sobrescrever original |
| R04 | Anexar formato não suportado, PDF/RTF corrompido e arquivo que mudou após seleção | Rejeição segura e identificável; nenhuma leitura arbitrária |
| R05 | Forçar 403/404/503 e timeout durante polling em ambiente de teste | Falha/reconexão explícita e limitada; sem spinner infinito nem sucesso falso |
| R06 | Cancelar em fila e durante conversão; fechar aplicativo durante job | Cancelamento cooperativo coerente; estado final verificado; temporários tratados; subprocessos próprios encerrados |
| R07 | Misturar arquivo válido e inválido num processo | Política de atomicidade/parcialidade visível; lista completa de sucessos/falhas, sem declarar conjunto completo |
| R08 | Testar seleções expiradas, IDs de outra sessão, traversal, origem externa, token ausente | API/ponte negam acesso; resposta não revela caminhos/segredos |
| R09 | Repetir processo com nomes coincidentes e abrir segunda instância | Isolamento entre jobs/sessões, sem sobrescrita cruzada; política de múltiplas instâncias clara |
| R10 | Monitorar logs e saída de erros com dados sintéticos sentinela | Sem token, CPF completo ou conteúdo de documento em telemetria indevida |
| R11 | Rodar suíte Python, contratos frontend, smoke UI real e motores no commit candidato | Todos os gates necessários aprovados; skips justificados, não convertidos em sucesso |

## UX, acessibilidade e distribuição

| ID | Passos | Resultado esperado |
|---|---|---|
| A01 | Completar jornada só por Tab/Shift+Tab/Enter/Espaço/Escape | Ordem lógica, foco visível, nenhuma armadilha; ações têm nomes acessíveis |
| A02 | Abrir modal, circular Tab e Shift+Tab, Escape, reabrir | Foco contido; fundo inerte; retorno ao acionador; viewer não captura navegação indevidamente |
| A03 | Usar Narrador: labels, erros, progresso e troca de tela | Anúncios úteis, sem repetição excessiva; nome/estado de cada campo correto |
| A04 | Medir cores em claro/escuro: texto, etapas, foco, erro, desabilitado | Atender critérios aplicáveis de contraste; estado não depende só de cor |
| A05 | Testar 1024 × 768, mínimo suportado, 125%/150% DPI, maximizar e texto longo | Sem corte de ação, sobreposição, rolagem horizontal desnecessária ou foco fora da tela |
| A06 | Alternar modo/tema, navegar Início/Perfis/Config, reiniciar | Modos têm diferença funcional definida; tema persiste; etapa/nav coerentes |
| A07 | Ativar movimento reduzido e executar ações longas | Sem animação decorativa inadequada; progresso continua compreensível |
| D01 | Instalar em Windows limpo, usuário comum, offline conforme pré-requisitos | Recursos frontend incluídos; motores/capacidades explicados; inicialização real funciona |
| D02 | Atualizar instalação anterior com perfis/configuração sintéticos | Preserva dados e compatibilidade; plano de recuperação verificável |
| D03 | Executar lote representativo e repetir abrir/fechar viewer | Medir latência p95 e memória; impor orçamento após baseline; sem crescimento não limitado |

## Gate de liberação

Resolver P0/P1 de integridade e jornada; executar J01–J10 no pacote candidato, F01–F10 e falhas críticas. Revisar requisitos dos casos condicionais em vez de ignorá-los. Aprovar acessibilidade e instalação na plataforma alvo. Registrar quem executou, versão exata e evidências; repetir apenas o conjunto impactado quando nova alteração ocorrer, incluindo sempre inicialização e fluxo principal para mudanças na ponte/UI.
