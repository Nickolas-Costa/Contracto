# ADRs propostas pela revisão QA

Estado de todas: **futura**. Data: **2026-09-13**. Estes são rascunhos para promover a arquivos individuais em `docs/adr/NNNN-*.md` após reconciliar o trabalho concorrente. Não reservar números agora nem registrar decisões como aceitas antes da implementação. Cada seção contém uma decisão independente e os campos do modelo do repositório. As referências abaixo identificam decisões existentes sem alterar seu índice.

## ADR-QA-BOOT — Inicialização da UI condicionada à ponte e à origem confiável

- **Estado:** futura.
- **Data:** 2026-09-13.
- **Contexto:** smoke de diagnóstico passa, mas frontend real falha; autorização de about:blank conflita com a página carregada e DOMContentLoaded pode preceder a ponte.
- **Decisão proposta:** usar bootstrap idempotente que coordene DOM pronto e `pywebviewready`, confira saúde/capacidades e exponha estado persistente de conexão. A ponte autoriza exclusivamente a origem/documento local de produção definido pelo shell; mudança de navegação revoga acesso. Manter token no nativo. Adotar primeiro a URL local exata controlada pelo shell; eventual transporte por servidor local deve ser decisão explícita, nunca wildcard de origens. Ajustar CSP apenas para recursos necessários e testados, incluindo viewer local.
- **Alternativas consideradas:** timeout fixo é frágil; permitir qualquer `file:`/origem elimina fronteira; teste só do HTML diagnóstico não protege produção.
- **Consequências:** estado de disponibilidade explícito; testes reais adicionais; tratamento de navegação/reconexão. URL pode ser transformada pelo runtime: verificar URL efetiva e política de normalização sem aceitar caminhos vizinhos/externos.
- **Arquivos previstos:** `app/webview_shell.py`, `frontend/js/app.js`, `frontend/js/api.js`, `frontend/index.html`, testes da ponte e smoke WebView.
- **Revisão:** complementa ADRs 0005/0011; preserva loopback, token efêmero e autorizações de arquivo. Considerar gate 0007 se transporte introduzir dependência.
- **Aceite:** UI real lista perfis e abre seletor; segunda inicialização não duplica handlers; falha tem recuperação clara; página externa não invoca API/diálogo/viewer.
- **Testes:** ponte antes/depois do DOM, evento duplicado, servidor indisponível, navegação não autorizada, smoke `--self-test --ui` e jornada instalada.

## ADR-QA-PROCESSO — Composição explícita e estado imutável por trabalho

- **Estado:** futura.
- **Data:** 2026-09-13.
- **Contexto:** anexos substituem gerados no payload; estado global e polling podem associar resultado anterior à tarefa atual.
- **Decisão proposta:** representar o rascunho do processo com conjunto explícito de documentos gerados e anexados; criar snapshot validado ao submeter, com identificador de revisão. Estados de comando/fila/execução/terminal controlam ações disponíveis. Cada resposta/poll pertence a um job e revisão; respostas antigas não alteram a tela atual. O resultado final controla abrir pasta e visualizar. Validar a composição no backend, com manifesto esperado quando necessário para detectar omissões.
- **Alternativas consideradas:** corrigir apenas `else if` resolve a perda imediata, mas não a mistura de trabalhos; duas listas independentes sem reconciliação mantêm inconsistência.
- **Consequências:** mais estado explícito e testes de transição; facilita cancelamento, falhas parciais e extração futura. Política de parcialidade e processo só com anexos precisa ser definida na UX, sem suprimir suporte existente inadvertidamente.
- **Arquivos previstos:** `frontend/js/etapa1.js`, `frontend/js/etapa2.js`, módulo de estado a definir; contratos/validação de jobs somente se necessário; testes de integração frontend/backend.
- **Revisão:** preserva fila, IDs opacos e isolamento das ADRs 0004/0011; não substitui serviços existentes.
- **Aceite:** gerados + anexos chegam juntos e aparecem no resultado; duplo envio não duplica operação; cancelamento tem resultado confirmado; nova tarefa não reutiliza silenciosamente dados anteriores.
- **Testes:** contrato JS incluído nesta revisão, composição real com marcadores, dupla submissão, resposta atrasada, cancelamento, retry limitado, erro parcial e abrir pasta do job final.

## ADR-QA-FORMULARIOS — Rascunho estável e renderização pelo esquema do perfil

- **Estado:** futura.
- **Data:** 2026-09-13.
- **Contexto:** seleção visual diverge da efetiva, inputs são recriados perdendo dados e metadados de campo não orientam a UI completa.
- **Decisão proposta:** manter rascunho por IDs estáveis de participante/campo fora do DOM. Renderizar tipos, escopos e restrições do contrato de perfil; backend continua autoridade de validação/cálculo. Composição é aplicada atomicamente, descartando respostas antigas e preservando campos compatíveis. Erros retornam mapeamento a campos, resumo e foco útil. Campos removidos/reinterpretados exigem indicação de impacto antes de perder dados.
- **Alternativas consideradas:** valores apenas em inputs são perdidos no rerender; duplicar regras de domínio em JS cria divergência; aliases de label como chave quebram ao renomear.
- **Consequências:** contrato de campos precisa ser suficiente e versionável; testes por tipos/condições e múltiplos participantes; base reutilizável para importação revisada.
- **Arquivos previstos:** `frontend/js/etapa1.js`, componentes de formulário a definir, DTO de perfis se insuficiente, testes de composição/validação.
- **Revisão:** complementa ADR 0012, mantendo Participante como fonte única; respeita serviços sem UI e limites da ADR 0011.
- **Aceite:** seleção e payload coincidem; globais/tipos/condições funcionam; dados não desaparecem ao trocar perfil; erros são anunciados e corrigíveis por teclado.
- **Testes:** seleção vazia/incompatível, troca rápida, preservação, tipos e globais, múltiplos participantes, CPF/data inválidos e navegação por teclado.

## ADR-QA-EXTRACAO — Candidatos com evidência e aplicação mediante revisão

- **Estado:** futura, fora da implementação atual.
- **Data:** 2026-09-13.
- **Contexto:** documentos usam labels e layouts variáveis, podem conter várias pessoas e erros de OCR; um valor plausível não garante preenchimento correto.
- **Decisão proposta:** importar documentos como dados não confiáveis e extrair candidatos para esquema canônico, preservando evidência e entidade. Pipeline modular: leitura estruturada/texto, OCR quando necessário, regras com contexto e IA opcional avaliada. Validadores determinísticos, conflitos explícitos e revisão humana precedem aplicação transacional ao rascunho. Modelo não escreve diretamente, não escolhe ferramentas e pode abster-se. Padrão local-first; processamento remoto depende de decisão de dados/fornecedor explícita.
- **Alternativas consideradas:** labels exatos têm baixa cobertura; fuzzy global confunde papéis; LLM direto no formulário produz erros plausíveis sem rastreabilidade; OCR universal perde informação de PDFs digitais e adiciona custo.
- **Consequências:** armazenamento de evidência e custo de revisão; corpus/gabarito e governança de regras; nenhum fornecedor/modelo escolhido nesta ADR. Não promete ausência absoluta de erro nem autenticação documental.
- **Arquivos previstos:** nenhum nesta fase; futuramente serviços de importação/extração, contratos de candidato/revisão, persistência temporária e UI de conferência em módulos separados dos geradores.
- **Revisão:** compatível com local-first, ADRs 0007/0011/0012 e item futuro de extração já registrado; não duplica campos do Participante nem antecipa implementação.
- **Aceite:** valores ausentes/ambíguos não são inventados; todos têm evidência verificável; campos críticos revisados; edição manual concorrente protegida; geração bloqueia pendências exigidas pelo perfil.
- **Testes:** corpus separado por família/layout, múltiplas pessoas/papéis, conflitos, OCR difícil, prompt injection, arquivos malformados/grandes, privacidade de logs, revisão e aplicação concorrente. Critérios detalhados no plano de extração desta pasta.

## Acessibilidade no plano, sem duplicar ADR existente

A correção de contraste, foco e modalidade deve entrar como critério de aceite da implementação e ser confrontada com ADRs 0009/0010 e o design vigente. Não criar uma nova ADR apenas para corrigir cada bug visual. O padrão de modal exige foco contido e retorno ao acionador; o código atual só cobre parte disso. [W3C APG: Modal Dialog](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)
