# Base pronta para iniciar a migração de UI

> **Estado de 14/09/2026:** a primeira WebView já existe e teve a jornada estabilizada. Leia [relatório atual](qa/revisao-2026-09-14/RELATORIO.md) e [plano visual para aprovação](qa/revisao-2026-09-14/PLANO_UI.md). Bootstrap recuperável, rascunho canônico, validação prévia, manifesto completo, retomada idempotente e viewer foram implementados (ADRs 0013–0015). A produção continua Tk. A descrição abaixo registra a entrega anterior; as pendências 1 e 3 já avançaram e não devem ser reiniciadas do zero.

Atualizado em 13/09/2026. Esta entrega implementa a infraestrutura da Fase A e um shell técnico de diagnóstico. O aplicativo de produção continua CustomTkinter v4.5.15; o diagnóstico não é uma nova versão para distribuir aos usuários.

## O que está implementado

- Servidor FastAPI/Uvicorn em socket exclusivo de loopback e porta livre, token efêmero em memória e revogação no encerramento.
- Rejeição de Host/Origin/token inválidos, cabeçalhos repetidos, métodos indevidos, query strings, corpo maior que 1 MiB e JSON inválido. Modelos rejeitam campos extras, IDs com formato inválido e números não finitos. Sem API pública de registro de caminhos.
- Catálogo de perfis por IDs de sessão e composição de campos simples. Perfil e templates são carregados pelo Python, não enviados pelo cliente.
- Geração e processamento como operações separadas. Validação de participantes e campos declarativos, defaults, opções, limites, condições e cálculos sem Tk. Resultados calculados são recalculados no backend; campos ocultos são limpos conforme configuração.
- Fila reutilizada, com correção da corrida ao criar/encerrar workers e do callback de cancelamento executado sob lock. Operações HTTP podem chegar simultaneamente e os trabalhos executam sequencialmente.
- Estado/progresso, cancelamento de trabalho ativo e pendente, preservação dos originais, staging exclusivo, publicação apenas no sucesso e erro explícito quando a limpeza falha.
- Falhas de Word/GS isoladas. PDF comum funciona sem ambos. RTF requer Word; PDF/A requer GS. As respostas não incluem exceções internas ou caminhos.
- Ponte nativa `ShellBridge` e port de diálogos WebView. JavaScript não recebe token; seleção retorna ID, cancelamento de diálogo retorna `cancelled`. `open_result(job_id)` abre somente a pasta de um trabalho concluído, sem receber caminhos do cliente. Navegação para página externa bloqueia a ponte.
- Contexto privado de logs da API, inclusive no worker COM, e correção do fechamento de arquivos de ícones no tema Tk.
- Script de build separado, sem alterar a distribuição atual, mais autoteste no executável de diagnóstico.

## Como desenvolver a UI sobre esta base

Iniciar `LocalServer`, anexar `ShellBridge` à janela e manter o servidor no context manager até o fechamento da WebView. O exemplo está em `app/webview_shell.py`. Para integração JS:

```javascript
// Depois do evento pywebviewready:
const api = window.pywebview.api;
const profiles = await api.request('GET', '/api/v1/profiles');
const output = await api.select_output();
// Se output.cancelled, permanecer na tela. Tratar output.code como erro.
const created = await api.request('POST', '/api/v1/jobs/generate', {
  profile_ids: [profiles.data[0].profile_id],
  output_id: output.selection_id,
  participants: [{
    nome_completo: 'Pessoa de Teste', cpf: '52998224725',
    data_assinatura: '13/09/2026', local_assinatura: 'CAMOCIM-CE',
    campos_dinamicos: {} // Preencher conforme fields do perfil escolhido.
  }]
});
// Validar created.status === 202 antes de acessar job_id.
const state = await api.request('GET', `/api/v1/jobs/${created.data.job_id}`);
// Repetir consulta enquanto queued/running/cancelling; parar em estado terminal.
// state.data.file_ids podem alimentar POST /jobs/process opcionalmente.
```

`/api/v1/health`, `/capabilities`, `/profiles`, `/profiles/compose`, `/jobs/generate`, `/jobs/process`, `/jobs/{id}` e `/jobs/{id}/cancel` estão implementados. Cancelar usa POST com `{}`. `ShellBridge.request` retorna `{status, data}`; falhas HTTP retornam `{code, message}` em `data`, com `issues: [{participant, field}]` quando há campos declarativos inválidos. Estado terminal: `completed`, `failed` ou `cancelled`; erro de trabalho em `error`. Para abrir a pasta concluída, chamar `api.open_result(job_id)` e tratar `{ok, code}`.

Processamento recebe `participants`, `output_id`, `file_ids` de PDFs e/ou `attachments: [{file_id, document_type}]`, além de `format: 'PDF' | 'PDF/A-2b'`. Selecionar anexos via `select_file`. `document_type` aceita letras ASCII, números, `_` e `-`, sem caminho. A saída é sempre uma subpasta exclusiva `Contracto-<job_id>` da pasta escolhida, preservando trabalhos anteriores.

Seleções expiram após uma hora. Há limite de 200 trabalhos e 2.000 seleções por sessão; reiniciar limpa o estado em memória. IDs de perfis e arquivos não devem ser persistidos no frontend. A API não oferece autenticação contra malware ou outro processo comprometido executado sob a mesma conta Windows.

## Validação executada nesta máquina

| Verificação | Evidência |
| --- | --- |
| Suíte unittest completa | 297 testes em 18,585 s, OK, sem skips; inclui os 269 anteriores e 28 novos testes HTTP/bridge/validação/fila; sem ResourceWarnings de ícones |
| HTTP real | Porta loopback, autenticação, origem, validação, composição, geração/processamento, concorrência, cancelamento, privacidade e shutdown |
| Tk real | Smoke com dois participantes e quatro PDFs preenchidos |
| WebView2 real | JavaScript chama bridge, HTTP responde e servidor encerra |
| Word + GS reais via API | RTF → PDF → PDF/A, texto conferido, original preservado, staging removido |
| PyInstaller | `ContractoBase.exe --self-test` inicia WebView2/HTTP e encerra com sucesso |

PDF/A foi verificado pelo validador interno de metadados, não certificado por veraPDF. Os testes de falha de capacidade/cancelamento usam simulações controladas; o smoke de motores é uma execução real separada. Os diálogos de seleção têm teste de contrato com janela simulada, não homologação manual botão a botão.

## Pendências detalhadas e ordem sugerida

1. **Nova interface de produção.** Ainda faltam páginas HTML/CSS/JS, navegação entre etapas, seleção múltipla de formulários, formulários dinâmicos, fila visível, estados de erro e conclusão. O shell atual desta entrega só confirma a base técnica. Começar pelos tokens/layout e por uma jornada completa de geração usando o contrato acima.
2. **Gestão de perfis e configurações na API.** Há leitura/composição por snapshot. Criar contratos de edição, importação/exportação e backup, reutilizando validação estrutural e serviços existentes. Definir atualização de catálogo e conflitos durante jobs ativos. Perfis/configurações continuam gerenciáveis pela UI Tk.
3. **Pré-visualização de resultados na UI nova.** A pasta concluída já pode ser aberta por `open_result(job_id)`, e os arquivos têm IDs utilizáveis no processamento. Falta um visualizador PDF embutido com acesso autorizado por ID e nomes apresentados ao usuário. Não criar endpoints que aceitem caminho arbitrário e não registrar conteúdo nos logs.
4. **Reutilização da validação no legado.** A API já retorna os índices/IDs dos campos declarativos inválidos, sem valores. Os widgets antigos continuam com sua própria validação visual. Consolidar seu uso do serviço puro durante a convivência e ampliar a comparação com os perfis reais para evitar divergências; a nova UI pode consumir o contrato já implementado.
5. **Cancelamento de Word mais imediato.** O evento já cancela a operação de fila, porém uma chamada COM em andamento pode levar até o timeout/aviso do conversor existente para retornar. Cancelamento imediato e garantia de isolamento contra COM irrecuperável exigem separar o conversor em processo filho controlável e testar encerramento sem afetar documentos do usuário. Não declarar cancelamento instantâneo de Word. Shutdown acusa falha se a fila não encerrar no limite.
6. **Temporários após queda abrupta.** Erro/cancelamento normal limpa staging; queda de energia/kill do processo pode deixar `.contracto-*` na pasta escolhida. Antes de distribuir, implementar recuperação com manifesto de propriedade e identificação de sessão; jamais apagar pastas por prefixo sem comprovar que pertencem ao aplicativo e não estão em uso.
7. **Instalador e homologação de distribuição.** O bundle de diagnóstico foi testado na máquina de desenvolvimento. Ainda faltam `packaging/Contracto.iss`, checagem/orientação de WebView2, mutex de produção, atalhos/desinstalador preservando dados e testes Windows 10/11 limpos. Não executar o instalador no computador de uso como substituto de uma VM limpa.
8. **Homologação visual/acessibilidade.** Testar teclado, foco, leitores de tela, toolbar em 1024px, modais em 1366×768, DPI 100/125/150/200% e reduced-motion, conforme ADRs 0009/0010. Isso depende da UI nova; não é comprovado pelo diagnóstico técnico.
9. **Fidelidade dos documentos.** Comparar um corpus representativo de RTF reais, fontes, tabelas, quebras e assinaturas. Um smoke sintético comprova integração, não equivalência visual de todos os contratos. Acrescentar verificação PDF/A externa no gate de release.
10. **Ambiente remoto/Linux e CI.** A execução desta entrega foi Windows/Python 3.14.6. Preparar um runner reproduzível, testar a suíte com Xvfb e registrar skips específicos de Windows. Resolver permissões GitHub do Codex web quando for retomar esse canal; isso não bloqueou o trabalho local.

O ZIP de referência continua local/ignorado. Está disponível neste notebook para a próxima fase visual; não foi necessário para implementar a API. API empresarial pública, autenticação corporativa e documentos hospedados continuam fora desta fase.

## Comandos

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe tests/smoke_test_gui.py
.\.venv\Scripts\python.exe tests/smoke_webview.py
.\.venv\Scripts\python.exe tests/smoke_api_engines.py
.\.venv\Scripts\python.exe -m app.webview_shell --self-test
.\.venv\Scripts\python.exe scripts/build_webview_diagnostic.py
.\dist\webview-diagnostic\ContractoBase\ContractoBase.exe --self-test
```
