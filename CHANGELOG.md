# Registro de Alterações — Contracto

Formato Keep-a-Changelog. Versão corrente em `app/version.py` (+ espelho `VERSION`).
Histórico detalhado da série 4.x em `CHANGELOG_v4.md`.

## [5.7.0] - 2026-11-17

### Leitura de documentos
- **OCR do Windows** (ADR 0027, Fase 2): páginas sem camada de texto (escaneadas) são lidas pelo `Windows.Media.Ocr` em português, via PowerShell do próprio Windows, em processo separado com limite de tempo e sem arquivos temporários. Nenhum pacote novo no instalador. As sugestões lidas da imagem aparecem como "lida da imagem; confira" e têm confiança menor (várias vêm desmarcadas).
- Botão **Ler como imagem (OCR)** em cada documento do modal: lê de novo todas as páginas pela imagem, para PDFs com texto ilegível ou com páginas escaneadas no meio.
- Sem o idioma Português (Brasil) no Windows, um PDF só de imagem mostra um erro claro em vez de "nada reconhecido".
- Cláusula "A1" lida como "Al" pelo OCR continua reconhecida.

### Corrigido
- Contrato com um só comprador: o "e" de "filho(a) de MÃE e PAI" virava um 2º participante (o pai) e levava junto o endereço do comprador. A filiação agora é ignorada na busca por participantes.

## [5.6.0] - 2026-11-17

Reúne o trabalho das versões de teste 5.4.0–5.4.5 da linha de digitação e leitura de documentos (que não tinha sido publicado) com a 5.5.1; inclui os acertos do MO 29300.

Digitação, perfis, Etapa 1 e leitura de documentos do cliente (acumula as versões de teste 5.4.0 a 5.4.5). Sem mudança no motor de geração.

### Digitação
- Máscaras mantêm o cursor ao corrigir no meio (valor, área, CPF/CNPJ, data, telefone, PIS); apagar um separador apaga o dígito vizinho e a máscara não recria mais o número.
- Valor e área: o "." digitado vira vírgula decimal (só ao colar vale a notação "1234.5"); o 3º decimal continua descartado. Área passa a ter a mesma máscara do valor (antes ia crua ao PDF; "1.200" virava 1,2).
- Telefone ganha só a máscara `(00) 00000-0000`, sem validação (também no servidor). INTEIRO e ANO aceitam só dígitos e respeitam mínimo/máximo na hora. PIS ganha máscara.
- Valor e área: um dígito depois dos centavos cheios ("100,00" + 0) sobe a casa decimal ("1.000,00") em vez de ser ignorado.
- Cálculo automático (ex.: Recursos Próprios do ITBI) usa a mesma regra do servidor: só `+`/`-`, sem negativo, `1.234,56` (antes aparecia `5000,5` até a prévia chegar).

### Formulário (modo Simples)
- **Páginas livres**: o formulário em páginas virou uma lista de abas; dá para ir a qualquer página sem preencher a anterior, e cada aba mostra quantos campos faltam nela (✓ quando nenhum).
- **Gerar mesmo assim**: só nome, CPF, data, local e pasta travam a geração. O resto vira uma lista de pendências (clicável) com **Voltar e preencher** e **Gerar mesmo assim**; a Conferência avisa quantos campos seguem em branco. O servidor só aceita isso em perfis simples (`ignorar_pendencias`); o modo Contrato continua estrito.

### Leitura de documentos (Simples e Contrato)
- **Faixa de destaque no topo** da tela (fora dos quadros) explica a função e abre o modal **Leitura de documentos**; arrastar arquivos para a janela (shell Tauri) também abre. Aceita PDF, RTF, DOC e DOCX (até 20); RTF/DOC/DOCX viram PDF na hora, numa pasta privada apagada ao fechar; os originais não são tocados (`POST /api/v1/jobs/intake`).
- O modal lê cada PDF (`POST /api/v1/extract`, ADR 0027 Fase 1, sem OCR) e mostra, ao lado do documento, os valores propostos para os campos do formulário: CPF, CNPJ, PIS, nascimento, e-mail, telefone, CEP, nome, endereço, matrícula e PDFs gerados pelo próprio Contracto (mapeamento inverso do AcroForm). Cada valor tem página e confiança, é editável, e quem troca algo já preenchido avisa "será substituído".
- Só o que o usuário marca entra no formulário (com as máscaras da digitação); **Desfazer última leitura** restaura. Perfis podem fixar o significado do campo com `semantica` (ex.: `pessoa.cpf`, `imovel.matricula`); sem ela, o app deduz do id e do tipo.
- **Padrões de contrato e cadastro**: nomes de comprador(es) e vendedor depois de "doravante denominado(s) DEVEDOR(ES):" / "VENDEDOR(ES):" (até a vírgula; o 2º proponente, ligado por " e ", vai para o 2º participante), endereço depois de "residente e domiciliado(a) em" (até o ponto, ignorando "nº." e "Av."), endereço em partes (CEP, logradouro, número, complemento, bairro, município, UF) montado num só e rótulos como "Nome Completo do Cliente:".
- **Cadastro de Clientes** (formulário de impressão, renda formal e informal): lê CPF, nome completo (não confunde com pai, mãe ou "nome reduzido"), nascimento, sexo, naturalidade, nacionalidade, pai, mãe, escolaridade, RG (número, órgão, emissão), estado civil, PIS/NIS, ocupação, endereço em partes e município/UF, tipo e ocupação do imóvel, telefone, e-mail, fonte pagadora e CNPJ, admissão, renda bruta e líquida, atividade e início. CPF, PIS e telefone que não conferem vêm **com aviso e desmarcados**, em vez de sumir. Campos de seleção só recebem o que casa com as suas opções ("DIVORCIADO (A)" → "DIVORCIADO(A)"), e a situação ocupacional é deduzida da ocupação. O significado do campo vem de `semantica` no perfil ou das palavras do id/rótulo.
- **Contrato com vários compradores** (modo Contrato): lê as cláusulas "A1 - VENDEDOR(ES)" e "A2 - COMPRADOR(ES)..." por pessoa (nome, nascimento, profissão, e-mail, CPF, CNH/RG), o que vale para o casal (estado civil, regime de bens, endereço), o CPF da página de assinaturas quando o da cláusula não confere, e a data e o local do contrato. O modal tem "Todos os compradores do documento", que preenche o participante 1, o 2 e assim por diante. A empresa vendedora não herda CPF nem CNH do representante.
- **Participantes sem "e seu cônjuge"** (união estável, parentes, até 4 pessoas): cada pessoa do contrato é reconhecida pela assinatura "NOME EM MAIÚSCULAS, nacionalidade/brasileiro/nascido(a)...", venha depois de ponto final, de " e " ou de vírgula. Endereço, estado civil, regime, união estável (com a data) e data de casamento são lidos **por pessoa**; só "residentes e domiciliados" (plural) vale para todas, e o estado civil e o regime do cônjuge vêm do primeiro quando o texto diz "cônjuge" ou "companheiro(a)". Campos de marcar (SIM/NÃO) como "mantém união estável" também são propostos.
- **Só compradores usam a denominação branda**: "NOME, qualificação" só cria participante dentro da cláusula dos compradores; no vendedor vale apenas " e NOME,", e a cláusula da credora (gerente da Caixa), o representante legal da empresa e nomes que começam com representante/procurador/gerente/diretor/sócio/administrador não viram participantes.
- **RG**: o formulário de Isenção de Tributos já tinha o campo e passa a ser preenchido (número do RG do cadastro e do contrato; número de CNH vem com aviso "É o número da CNH, não de um RG").
- **Padrões de leitura editáveis** (Configurações): o usuário cadastra "o dado X vem depois da frase Y e vai até Z" sem mexer em código (`padroes_leitura`).
- Correções do modal: remover e incluir outro arquivo não deixa mais o visualizador nem os valores do anterior; sem texto de "nível de confiança"; a área de soltar preenche o modal vazio.
- O arrasto nativo passa por `window.ContractoArrasto`, que entrega à Conversão ou à Leitura conforme a tela aberta.
- A Ajuda foi separada em `ajuda.js`, com a aba "Documentos do cliente" e textos sobre páginas e pendências.

### Conferência
- Cada valor da Conferência (nome, CPF, campos, data e local) é um atalho: abre a Etapa 1 na página do campo, com foco e destaque; "Gerar documentos" volta à Conferência (ADR 0030, passo 1). O atalho agora alcança campos de qualquer página (antes, e-mail e telefone do ITBI levavam sempre à última).

### Correções
- Caixa de seleção com padrão "Sim"/"Não" (ITBI: Enquadramento na isenção) aparecia desmarcada enquanto o documento saía como "SIM".
- **Limpar dados** deixava os campos compartilhados (ITBI) e o conteúdo de data/local/pasta na tela. "Novo trabalho → preservar" agora mantém só data, local e destino.
- O app reabre no último modo usado (Simples, Contrato ou Conversão).
- Perfis com chaves desconhecidas (de versão mais nova) não são mais descartados em silêncio, o que apagaria os perfis do usuário no próximo salvamento; duplicar perfil não perde mais atributos dos campos.

### Perfis
- **Municípios do ITBI** (Configurações): cada município tem prefeitura, comarca e texto da isenção (a lei é municipal). No formulário do ITBI, escolher a prefeitura preenche a comarca e o texto; o texto sai no PDF no lugar do trecho fixo. Na primeira execução o app pergunta o local padrão e o município.
- **Endereço completo ou detalhado** (tipo `ENDERECO`): um texto só ou tipo de logradouro, logradouro, nº, complemento, bairro, cidade, UF e CEP; o texto completo é montado das partes (`Rua X, 12, bairro, Cidade-UF, CEP`) e as partes seguem como `<campo>_logradouro`, `<campo>_cep`... para PDFs com campos separados. Usado no endereço do comprador e do imóvel (ITBI) e do imóvel do MO 29300; combina com perfis que pedem só texto.
- MO 29300: campos do PDF reposicionados para não cobrir o texto fixo (CPF/PIS, anos/meses de residência, datas), com fonte fixa em vez de automática. `scripts/sugerir_geometria.py` gera a proposta a partir do texto de cada linha.
- `rotulos_opcoes` (texto exibido por opção) e `largura` (`terco`/`meia`/`cheia`) por campo; correções de perfil podem inserir campos novos (`novos_campos`), inclusive em instalações novas.
- MO 29300: opções com acento e legíveis, três campos por linha onde cabem; profissão passa a campo de uma linha.
- ITBI: novo campo **Prefeitura (município)**, com campo AcroForm `PREFEITURA` no modelo (substitui o texto fixo "CAMOCIM-CE"); áreas e fração ideal com fonte maior; valores em três colunas; ofício do cartório só números.

## [5.5.1] - 2026-11-16

Acertos no modelo MO 29300 (DAMP) e no texto dos campos. Sem mudança no motor de geração.

### Correções
- **Acentos e hífen errados no visualizador** (ex.: "COMUNH˜O", "62400›000"): o valor dos campos era gravado com escapes octais (`Ã`, `-`), que alguns visualizadores leem errado ao redesenhar o campo. Agora vai em hexadecimal. A impressão não mudava.
- MO 29300: a data do casamento não cobre mais a vírgula e o ponto final; "Sob regime de" termina antes da vírgula.
- MO 29300: o campo do município de "Possuo imóvel em" ficou maior e o ponto final acompanha.
- MO 29300: o campo do endereço do imóvel ocupa a linha inteira (de ~300 pt para ~460 pt), então a letra encolhe bem menos em endereços longos. O ponto final foi para o fim da linha.

## [5.5.0] - 2026-11-15

### Novo
- **Atualização pelo aplicativo** (ADR 0032): "Verificar atualizações" em Configurações consulta a lista de versões no GitHub, mostra a novidade e, se confirmado, baixa o instalador, confere a assinatura e instala. Só roda quando o usuário clica; nada é consultado ao abrir. Com trabalho em andamento a instalação é recusada. Na cópia portátil o botão abre a página de versões.
- Quem está na 5.4.0 ou anterior instala esta versão à mão uma última vez; daqui em diante a atualização é pelo app.

### Build
- `tauri-plugin-updater` 2.14.1 (gate em `DEPENDENCY_REVIEW.md`). O build assina o instalador com a chave em `%USERPROFILE%\.tauri\contracto-updater.key` e grava `dist/latest.json`, que precisa ir junto na release.

### Documentação
- `PRIVACIDADE.md` e README passam a citar a única conexão externa do aplicativo.

## [5.4.0] - 2026-11-15

Contrato em uma etapa só e correções da auditoria de 11/11/2026 (ADR 0032). Sem mudança no motor de geração.

### Fluxo
- **Contrato conclui em uma etapa.** O formato de saída foi para a Conferência, junto dos formulários e dos documentos extras. "Confirmar e gerar documentos" gera, converte e organiza de uma vez; a Etapa 3 mostra o resultado. "Finalizar processo" virou "Tentar concluir de novo" e só aparece se a organização falhar depois da geração.
- A pergunta sobre documentos extras que faltam vem antes de gerar, e só quando o perfil tem extras.
- Os PDFs finais do Contrato não levam mais o prefixo `1-`, `2-` no nome.
- O app avisa antes de fechar a janela com trabalho em andamento.

### Correções
- **Editar perfil** nunca salvava (erro 500): a tela envia a entrada do catálogo. O servidor agora junta a edição ao perfil salvo, preservando caminho, mapeamento e identificador; chave desconhecida é recusada com o nome dela. O JSON copiado da tela também passa a ser aceito em "Importar texto colado" (perfis sem formulário).
- Perfil que acompanha o aplicativo não pode mais ser excluído (ele voltava sozinho na abertura seguinte).
- **PDF/A sem confirmação falha** em vez de entregar PDF comum em silêncio (Conversão e Contrato).
- **Falha na geração ou organização prendia a tela** em "Processando…" e mostrava `[object Object]`: o erro do trabalho é um objeto e era tratado como texto. Agora aparece o motivo e a tela é liberada.
- **Cancelar** (Contrato/Simples) não cancelava no shell Tauri: a chamada ia sem corpo e a API respondia 422.
- **PDF/A falhava em pasta ou arquivo com `%` no nome** (ex.: "entrada 50% paga"): o Ghostscript lia o `%` como formato.
- **Reparo do sistema fechava o Word do usuário** (com o que estivesse sem salvar) e, no shell Tauri, apontava o atalho da Área de Trabalho para o servidor sem janela. O Word saiu da lista de processos encerrados e o atalho volta a abrir o `Contracto.exe`.
- Perfis: perfil excluído continuava na lista até reiniciar; nome repetido ou JSON inválido devolviam "Operação local indisponível" em vez do motivo; restaurar backup não atualizava a lista.
- Backup criado antes de salvar qualquer perfil ou configuração saía incompleto e não restaurava.
- Um PDF gerado aberto num leitor fazia o trabalho já publicado aparecer como falho.
- "Limpar campos" esvaziava o campo da pasta de saída mas seguia usando a pasta antiga.

### Interface
- A barra de progresso da geração e da organização passa a andar (documento N de M).
- Textos: "Formulários do contrato", descrição da tela Perfis sem jargão, "Reiniciar" em Novo trabalho (o botão dizia preservar o que apagava).

### Removido
- Código sem uso: caminho antigo da fila (era do Tk), par duplicado de exportar/importar perfil com outro formato, aviso "Word travado" que nunca disparava, diagnóstico do WebView2 e o cálculo local de campos (bloqueado pela CSP; o valor calculado já vinha do servidor).

### Documentação
- `ARCHITECTURE.md`, `BASE_UI_STATUS.md`, `MAPA_PROJETO.md`, `TAURI_CONTRATO.md` e `AGENTS.md` deixam de citar arquivos removidos (`utils/files.py`, `ports/dialog.py`, scripts do Inno Setup, `CONTINUIDADE_CODEX_WEB.md`) e de dizer que o Tauri não existe.
- ADR 0032: Contrato em uma etapa e plano (ainda sem código) de atualização dentro do app sem certificado de assinatura.

## [5.3.0] - 2026-11-02

O aplicativo passa a rodar no shell **Tauri** (ADR 0029 e 0031), com instalador NSIS no lugar do Inno Setup. Acumula tudo desde a 5.1.0 (a 5.2.0 só circulou como teste). Sem mudança no motor de geração nem nos dados.

### Interface
- **Carregamentos em modal**: geração, organização e conversão abrem um modal com giratório e barra (medida quando há progresso, deslizante quando não), tempo decorrido e Cancelar. Saem o toast de "iniciado" e o cartão de status dentro do quadro; a conclusão continua em modal.
- **Novo ícone**: "C" redondo azul e plano, com lateral em azul mais escuro deslocada (no estilo do ícone anterior), sobre tile azul-marinho, no app, no `.ico`, no cabeçalho e no README. Propostas alternativas e comparativo em `docs/icone/propostas/`; `python scripts/gerar_icone.py <S1|S2|S3|...>` troca o ícone (padrão S3).
- Carregamento segue animado mesmo com as animações do Windows desligadas (antes o giratório ficava parado, parecendo travado).
- Giratório e barra de carregamento legíveis no modo escuro com qualquer cor de destaque (usam o azul claro do tema).
- O servidor local (`Contracto_sidecar.exe`) agora tem o ícone e o nome "Contracto" no Gerenciador de Tarefas.
- Tela de espera "Iniciando o Contracto…" até o servidor local ficar pronto.
- Conversão: a zona de soltar volta a ter o destaque ao arrastar e só aceita arquivos soltos nela.

### Desempenho
- Sidecar em pasta (PyInstaller onedir) em vez de arquivo único: não extrai 60 MB para o `%TEMP%` (e passa pelo antivírus) a cada abertura. Custo: ~136 MB em disco no lugar de ~70 MB; o instalador tem ~50 MB.
- A janela abre em cerca de 0,8 s; o servidor local carrega em segundo plano e a primeira chamada espera por ele. Latência de chamada à API: ~5 ms (era ~16 ms no shell anterior).
- Segunda instância é detectada antes de carregar o servidor e sai em ~0,3 s, sem janela.

### Distribuição
- `build_exe.bat` gera o shell Tauri + sidecar Python: `dist/Contracto_Setup_v<versão>.exe` (instalador NSIS) e `dist/Contracto_v<versão>.zip` (portátil), cada um com `.sha256.txt`. O Inno Setup saiu do build.
- O instalador remove a instalação antiga do Inno Setup e o `Contracto_sidecar.exe` órfão das builds 5.2; `%APPDATA%\Contracto` (perfis, configurações, backups) não é tocado.
- Sem auto-update: atualizar é rodar o instalador novo.
- Requisitos de build: Rust (`stable-x86_64-pc-windows-msvc`), VS Build Tools (C++) e Node, além do Python atual.

### Correções
- Conversão ficava em "Convertendo…" para sempre mesmo com o arquivo já entregue: a lista de resultados lançava erro (campo de renomear colado por engano) e o acompanhamento engolia o erro.
- Anexar arquivo na Conversão falhava com caminhos acentuados (o sidecar lia o pipe na página de código do Windows): agora UTF-8.
- Tema e configurações podiam voltar ao padrão sem ninguém mexer: uma falha passageira do antivírus ao testar a pasta de dados jogava a leitura para outra pasta. A pasta é testada com repetição e fixada por sessão.
- Janela reduzida (≤ 1100 px): a faixa da barra superior cobria o fundo e se cortava ao meio.
- `build_exe.bat` com caminhos corrompidos (``/`	`) e sem CRLF.

### Shell
- `src-tauri/`: janela, diálogos nativos, arrasto de arquivos e ponte `request` com a mesma lista de caminhos permitidos e limite de 1 MiB da ponte anterior.
- Instância única (mutex do sidecar): abrir de novo traz a janela existente para a frente.
- O sidecar ganhou `import_profile`/`export_profile`; `ShellBridge` e sidecar usam o mesmo código (`app/api/profile_files.py`). Variável `CONTRACTO_MUTEX` permite testes ao lado do app aberto.

## [5.1.0] - 2026-10-31

Polimento visual e correções de fluxo. Sem mudança no motor de geração.

### Interface
- Ícones em SVG na barra superior, botões de ação e botões criados pelo JavaScript; galeria no laboratório visual.
- Azul padrão `#1E6FB3` (vale para instalações novas; quem já tem cor salva mantém a sua).
- Animações de entrada de telas, janelas, avisos e cartões; tooltips; stepper com etapas concluídas e trilho preenchido.
- Guia de ajuda em abas (F1) e tour guiado de seis passos.
- Barra superior fixa agora é uma faixa de borda a borda, sem a "quebra" nas laterais.
- Avisos (toast) maiores, com fundo sólido, borda e selo na cor do tipo; legíveis no modo escuro.
- Menus suspensos com seta própria, foco em azul e opções mais espaçosas.
- Removido o desfoque dos cartões, que deixava áreas sem repintar no WebView2.
- Estado vazio na lista da Conversão.

### Formulário
- O cartão "Dados compartilhados" só aparece quando tem campo visível na página.
- Agência e Conta CAIXA passam a ser obrigatórias (perfis novos).
- Data de nascimento no futuro é recusada, na tela e no backend.
- CNPJ e CPF/CNPJ recebem a máscara `00.000.000/0000-00` enquanto se digita.

### Conversão
- Cada arquivo da lista tem seu próprio campo de novo nome. A API passa a usar `nomes_saida` (um nome por arquivo) no lugar de `nome_saida`.

### Pastas do modo Contrato
- Os arquivos finais vão para `PDF-A/` direto na pasta escolhida, sem pasta extra com o nome do cliente.
- A pasta intermediária "(gerados)" é apagada depois da conversão (somente os PDFs criados pelo app e só se a pasta ficar vazia).

### PDF/A
- Os arquivos agora declaram OutputIntent sRGB com perfil embutido, corrigindo o erro "Page Group entry is missing in a document without OutputIntent" dos validadores. Teste real com Ghostscript incluído.

## [5.0.0] - 2026-10-28

Versão maior: a interface Tk deixa de existir e dependências saem do pacote
(ADR 0028); o backend e o contrato nativo ficam prontos para o shell Tauri
(ADR 0029). O fluxo do usuário final não muda.

### Corrigido
- **CNPJ (crítico):** a validação do front usava os pesos do módulo 11 na ordem
  invertida e recusava todo CNPJ válido (ex.: `00.000.000/0001-91`) em campos
  `CNPJ` e `CPF_CNPJ`. Agora usa os pesos oficiais, incluindo o CNPJ
  alfanumérico, e é conferida contra o validador Python em teste.
- Cache de perfis: o clone campo a campo perdia atributos (ex.: `apresentacao`);
  agora é cópia profunda. O perfil composto informa o formato do perfil quando
  há um só.
- Campos de moeda mantêm o cursor ao editar no meio do valor.
- Reparo do sistema: o atalho nunca era recriado a partir da API (COM sem
  `CoInitialize` na thread do servidor). O teste de reparo deixou de encerrar
  Word/Ghostscript e de tocar na Área de Trabalho real.

### Removido
- Interface Tk/CustomTkinter (`app/ui/`), `--tk`, `file_picker`, `ports/dialog`,
  ícones do tema Tk e `scripts/process_assets.py`; dependências `customtkinter`
  e `darkdetect`; `tkinter` fora do bundle.

### Adicionado
- `app/sidecar.py`: backend headless para o Tauri (aperto de mão + canal de
  controle por stdin) e `docs/TAURI_CONTRATO.md` com os comandos nativos.
- `api.js` com contrato nativo único (`nativo(nome, args)`), válido para
  pywebview e Tauri.
- ADRs 0027 (extração de dados de PDF, plano detalhado), 0028 (aposentadoria
  do Tk), 0029 (Tauri Ready) e 0030 (conferência editável, próxima rodada).

### Alterado
- Etapa 1 fatiada: `perfis.js`, `conferencia.js` e `calendario.js` saem do
  `etapa1.js` (1.470 → ~850 linhas).
- Testes em Node para `form-state.js` e para o adaptador nativo.

## [4.5.26] - 2026-10-27

### Corrigido
- Etapa 2 e Conversão: o formato de saída inicial agora segue o padrão das
  Configurações (antes era sempre PDF); cai para PDF se não há Ghostscript e
  não sobrescreve uma escolha manual (ADR 0026).
- Visualizador de PDF: regras de largura conflitantes cortavam a página no
  modal; agora o iframe ocupa a largura do quadro (responsivo).
- Conversão: arrastar arquivos para a área de anexo passa a anexá-los (antes
  reabria o seletor e descartava o arrastado). O caminho só existe no shell
  nativo, que o autoriza; a interface recebe apenas IDs. Soltar fora da área
  não navega mais a janela.
- Modo Simples com MO 29300 (DAMP): teste de regressão com o perfil real
  (correção do `TEXTO_LONGO` já registrada na 4.5.25).
- Etapa 1: títulos de seção sem campo visível (campos de outra página ou
  condicionais) deixavam "resquícios" vazios; agora a seção inteira some.
- Campos de moeda (ex.: "Valor da modalidade"): milhar com ponto e vírgula
  decimal enquanto digita, e centavos completados ao sair do campo
  (`180000` → `180.000,00`).
- Visualizador: "Expandir" fechava o diálogo e só valia na reabertura; agora
  alterna para "Reduzir" sem fechar, e "Abrir no leitor padrão" também mantém
  o diálogo. Modal expandido fica centralizado.
- Build: o instalador só saía depois de rodar o build mais de uma vez (o
  antivírus/OneDrive ainda segurava o `.exe` recém-gerado); `build_installer.py`
  agora espera o arquivo liberar e repete o ISCC até 4 vezes.

### Alterado
- Formato de saída (Etapa 2 e Conversão) vira par de botões em vez de lista.
- Botões inferiores: ação primária sempre por último (Etapa 2, Conversão e
  Configurações); na Etapa 2 a ordem é Voltar, Fila, Abrir pasta, Finalizar.
- Conferência (Etapa 2): cabeçalho do participante com contagem de campos,
  seção "Identificação" (sem repetir o nome no título), grade em colunas
  adaptáveis e título "Dados do formulário" no lugar de "Geral".
- Perfis separados em "Modo Simples" e "Modo Contrato"; a busca aceita
  "simples", "contrato" e "completo".
- Barra superior fixa ao rolar (estática abaixo de 1100px, onde quebra em
  várias linhas).

## [4.5.25] - 2026-10-18

### Corrigido
- Modo Simples: ao selecionar formulários com campo `TEXTO_LONGO` a Etapa 1
  ficava inteira em branco (sem card do participante, sem campos e sem barra
  de paginação). `fieldControl` gravava `input.type = "text"` também no
  `<textarea>`, cuja propriedade é somente leitura no DOM real, e `render()`
  abortava antes de anexar o card. `composto()` continuava `true`, por isso
  o fluxo WebView2 antigo não pegava; agora cobre o caso (campo `TEXTO_LONGO`
  em aba própria).
- `POST /api/v1/system/repair` chamava um módulo inexistente
  (`services.system_repair`), então "Diagnóstico e reparo do sistema" nunca
  funcionava; passa a usar
  `system_repair_service.executar_diagnostico_e_reparo()`.
- Atalho da Área de Trabalho recriado pelo reparo: em modo de
  desenvolvimento ele mirava o primeiro `Contracto_v*.exe` em `app/dist`
  (podia ser o build mais antigo); agora escolhe o de maior versão.
- Instalador: `packaging/Contracto.iss` corrigido (identificador de versão
  inexistente, flags inválidas, arquitetura obsoleta) — ver ADR 0008.

### Alterado
- Contrato UI↔shell isolado em `frontend/js/api.js` (`aoPronto`,
  `ehShellWebView2`); `app.js` não referencia mais `pywebview`/WebView2 —
  trocar de shell passa a ser um arquivo só (ADR 0024 §1).
- `scripts/build_installer.py` reconhece o Inno Setup instalado apenas para
  o usuário (`%LOCALAPPDATA%`, fora do PATH) e o gate do `build_exe.bat`
  passou a usá-lo (`--check`).

## [4.5.24] - 2026-10-17

### Corrigido
- Legibilidade no tema claro: as variáveis derivadas da cor de destaque
  (`--c-primary-light`/`--c-primary-hover`) são recalculadas por tema; antes
  os badges/pills claros recebiam azul-escuro sobre azul-escuro. A cor é
  reaplicada ao trocar de tema (manual ou do sistema).
- Modo Contrato: a geração intermediária publica em
  `Contrato <Nomes> (gerados)` (nome legível, Title Case com acentos) em vez
  de `Contracto-<job_id>`; o trabalho final usa `Contrato <Nomes>`.
  Colisões recebem sufixo ` (2)` — nunca sobrescreve (ADR 0025).
- Modos Simples/Conversão publicam os arquivos direto na pasta escolhida
  (sem subpasta), com o mesmo sufixo de colisão; paridade com o legado.

### Alterado
- Formulários Dinâmicos Gerados e Documentos Extras agora ficam na Etapa 2
  (Conferir), refletindo a composição atual antes de gerar; a Etapa 3
  (Concluir) fica enxuta e seu modal final só abre a pasta ou fecha.
- Documentos extras de um perfil único deixam de ser descartados ao compor
  (`combinar_perfis`); combinações de múltiplos perfis seguem sem extras.

## [4.5.23] - 2026-10-14

### Corrigido
- Segunda instância silenciosa: em vez do modal "já está aberto", o app
  apenas traz a janela existente para frente (`SetForegroundWindow` +
  `SW_RESTORE`) e encerra sem nenhuma mensagem.
- Fluxo de finalização (modos Simples/Contrato): o motivo real do backend
  (`message`+`issues`, nunca `detail`) agora aparece no toast em vez do
  genérico "Falha ao iniciar processamento"; "Recuperar andamento" só
  aparece em envio ambíguo (5xx/rede) ou trabalho ativo com polling perdido.
- Etapa Concluir no modelo da interface antiga: `Formulários Dinâmicos
  Gerados` (checkboxes por formulário) + `Adicionar documentos extras`
  nomeados por perfil (`document_type` = `nome_padrao`, ex. CONTRATO);
  vazio bloqueia, parcial pede confirmação; botão `FINALIZAR PROCESSO`.
- Configurações: tema/cor agora reconciliam com o backend
  (`%APPDATA%/Contracto/contracto_config.json`) pós-conexão — limpar o
  Local Storage do WebView não reseta mais para o padrão.
- Layout: quadro Salvar/Descartar com margem; `Restaurar padrões` e
  `Diagnóstico e reparo` em seção de alerta separada; lista de Perfis com
  ritmo vertical; footer da Etapa 1 realinhado.
- Build: `dist/_versoes_anteriores/` arquiva artefatos de versões antigas
  antes de gerar a nova; raiz de `dist/` fica só com a versão corrente.

### Atualizado (MO 29300 v039)
- Template `MO29300-039 (DAMP).pdf` substituído pelo modelo novo (6 págs.,
  65 campos; checkboxes normalizados para `/Yes`/`/Off`; geometria dos
  campos de valor aplicada).
- Mapeamento do perfil refeito para os nomes novos preservando
  origens/condições/formatos; tabela de contas FGTS (20 campos) e total de
  saque removidos — sem célula preenchível no modelo novo.
- Migração automática de perfis salvos (`%APPDATA%`) com nomes antigos para
  os novos; `geometria_modelos.json` atualizado (`dividir_campo` removido —
  dia/mês/ano já são campos separados).

## [4.5.22] - 2026-10-01

### Corrigido (paridade prod: P0 + principais)
- Form Cliente/ITBI: checkboxes "Boleto/WhatsApp", "tarifa de avaliação" e
  isenção voltam a marcar o PDF — condições `["Sim"]` canonizadas para
  `["SIM"]` no seed e comparador insensível a caixa em `mapping_engine`,
  `form_validation` e `form-state.js`.
- Catálogo da sessão atualiza após criar/editar/excluir/duplicar/importar
  perfil (`Jobs.refresh_profiles`, IDs preservados) — perfil novo aparece
  sem reiniciar o app, inclusive na Etapa 1.
- Importar/exportar perfil por arquivo `.json` (diálogos nativos +
  `ShellBridge.import_profile/export_profile`).
- `local_padrao` da Config pré-preenche o Local da assinatura (paridade Tk).
- Validações `MOEDA/AREA/INTEIRO` no frontend + `inputmode`
  email/tel/decimal; conferência com rótulos legíveis e valores calculados.
- Docs temporários concluídos anotados para exclusão futura (nada movido).

## [4.5.21] - 2026-09-30

### Corrigido (rodada 15 ajustes + auditoria)
- Toolbar sem quebra de linha (`toolbar-actions`); toast com leve
  transparência, blur e fundo mais escuro; foco de teclado restrito a
  controles (fim do "quadro completo" ao dar Tab); stepper centralizado em
  3 passos (Preencher → Conferir → Concluir).
- Conferência redesenhada (chips de modelos, grade de assinatura/destino,
  seções por participante/aba, valores humanizados); `Dados compartilhados`
  agrupados por aba; MO 29300 com campos por seção e paginação.
- Labels de `SELECAO` normalizadas (ex. "Autorizar ou alterar débito",
  "Desconheço possuir") e valor-padrão exibido no controle; "Seguro"
  exibido como "Form Seguro"; larguras 760/1080/1400.
- "Recursos deste computador" removido da UI (capacidades seguem como gate
  interno + Diagnóstico); label de backup removida dos Perfis; ações por
  perfil em [Ativar][Editar][Mais ações]; formulários simples em grade de
  cards; viewer PDF maior com Expandir + Abrir no leitor padrão
  (`ShellBridge.open_file`, `abrir_arquivo` multiplataforma).
- Auditoria: `open_file` corrigido no Linux (`abrir_pasta` rejeita arquivos),
  classe `modal-viewer-expandido` limpa ao fechar, fluxo `webview_flow.js`
  atualizado para botões do contrato/modal de pendências (smoke WebView2 e
  motores reais OK: Word + Ghostscript).

## [4.5.20] - 2026-09-29

### Corrigido (rodada visual/fluxo com fotos do uso real)
- Fluxo avança da Conferência para Revisar documentos ao aceitar o trabalho;
  andamento em toast/modal, sem pill de fila na toolbar (botão "Fila" na
  Etapa 2).
- Contrato com pills lado a lado (sem radio); fundo decorativo mantido sob
  `prefers-reduced-motion` (sonda WebView2 real); padding do modal;
  recursos em badges; margens de botões/listas; seção Sobre removida
  (versão no modal de Ajuda); pendências em modal com itens navegáveis;
  conflito no Simples preserva a seleção anterior.

## [4.5.19] - 2026-09-29

### Adicionado
- Modo Conversão (terceiro botão Simples/Contrato): tela com dropzone,
  `POST /api/v1/jobs/convert` (PDF/RTF/DOC/DOCX → PDF ou PDF/A-2b, nome e
  pasta de saída), `select_documents()` na ponte, `tests/test_convert_api.py`.
- Transposição MVP (Fases 0–4, `docs/PLANO_MVP_TRANSPOSICAO.md`): correção do
  seletor de modelos, boot resiliente, modais centralizados, SuccessModal de
  conclusão, confirmação sem anexos, copiar-dados, pendências com navegação,
  tema do sistema, editor de perfil com cabeçalho, largura dos quadros.
- Build: `dist/Contracto_v4.5.19.exe` + ZIP + SHA-256 gerados (~74 MB);
  instalador pulado sem Inno Setup; corrigido parêntese não escapado no
  `echo` do passo 6/6 do `build_exe.bat` (quebrava o bloco `if`).

## Sem versão própria (P0 de 26/09/2026, publicado na série 4.5.x)

### Adicionado (P0 release 26/09/2026, ADR 0023/0024)
- API: `LocalOnly` aceita PUT/DELETE; `POST /settings/restore`, `POST /profiles/active`, `POST /system/backup|restore` (backup via `selection_id`, sem vazar caminho); `select_backup()` na ponte.
- WebView: Ativar perfil, Backup/Restaurar, `tamanho_quadros` + `formato_saida` + Restaurar padrões, Ajuda 4 passos + Sobre + boas-vindas (`primeira_execucao`), validações `CNPJ/CPF_CNPJ/PIS/EMAIL/TELEFONE/ANO`, `chk-preservar-dados`.
- Testes: `tests/test_p0_release.py`. Tauri documentado sem código (ADR 0024).
- Popups WebView auditados e corrigidos: alerta de Word travado com DOM (antes exibia tags literais), modais de perfil sem `innerHTML` com dados (XSS/quebra com `</textarea>`), calendário com botão de próximo mês (só havia anterior).
- Isolamento de suíte: `gc.collect()` no `setUp` de `test_p0_release`/`test_local_api` — finalizadores `tkinter.font` pós-Tk travavam o worker Uvicorn em `json.dump` conforme a ordem dos testes.
- Build: `app/dist/Contracto_v4.5.18.exe` gerado (~74 MB); instalador bloqueado sem Inno Setup (`ISCC.exe` ausente — falha explícita, sem fallback).

### Adicionado
- Migração residual Tk → WebView2 (ADR-0021/0022, blocos 0–6):
  toolbar consolidada com seletor de modo e badge de participantes;
  campos condicionais (`if_field`) e calculados (`formula`);
  paginação real por `pagina`; conferência agrupada por seção com
  stepper condicional; modo simples com detecção de conflitos e cópia
  de dados entre participantes; fila global interativa com polling;
  paridade validada sobre todos os perfis reais
  (`tests/test_frontend_parity.py`).
- Espelho `VERSION` sincronizado com `app/version.py` (4.5.18).

### Pendente (gate final, sem release)
- WebView2 real, Word/GS reais, DPI 100/125/150/200%,
  encerramento/cancelamento e instalador Inno Setup (ADR-0008).

### Corrigido (finalização 20/09/2026, branch `fix/ui-escopos-validacao`)
- Seleção inicial do perfil não aparecia marcada: a lista era montada
  antes da composição (`sincronizarSelecao` em `etapa1.js`).
- Tela Config nunca exibia as capabilities (`mostrarCapacidades` em
  `app.js` + `capacidades()` exposta em `etapa2.js`; antes, a chamada a
  `ContractoEtapa2.capacidades` inexistente abortava o bloco em silêncio).
- Duplo clique em gerar criava dois trabalhos: single-flight com `busy`
  mantido no envio ambíguo e retomada idempotente pelo mesmo
  `request_id`; `recomecar()` descarta o envio incerto ao iniciar novo
  trabalho.
- `finalizar` enviava `{base_job_id, files, output_format}`, rejeitado
  pelo `ProcessInput` (`extra=forbid`): agora monta
  `{participants, output_id, file_ids, attachments, format, request_id}`
  via `pacoteProcesso()` e os gerados voltam a listar com "Visualizar".
- `tests/webview_flow.js` atualizado para o fluxo com conferência
  (`btn-gerar` → `tela-conferir` → `btn-conferir-confirmar`).
- Smoke WebView2 real: 32/32 verificações OK; smoke de motores reais
  (Word + Ghostscript + PDF/A): OK; suíte: 362 testes OK.

## [4.5.17] — 2026-09-13

### Adicionado
- Interface web da Etapa 1 e 2 sobre a API local: catálogo, composição,
  participantes, destino, geração, anexos, processamento, visualizador
  e Config com tema (shell `--ui` para testes).
- Revisão visual: scroll estilizado, logo, stepper em 4 etapas,
  Config no topo, selecionar-todos, resumo com links, fundo modular
  e modais com faixa e X.
- Participante modular dirigido pelo perfil (ADR-0012).

### Corrigido
- Bateria adversarial da API sem vulnerabilidade real.
- DOM da Etapa 2, capabilities no arranque e rótulo do anexo.
- Teste JS detecta Node fora do PATH (sem skip).

## [4.5.16] — 2026-09-13

### Corrigido
- Robustez na fila de processamento (corrida ao criar/encerrar workers e cancelamento sob lock).
- Contexto privado de registros da API, inclusive no worker COM.
- Correção do fechamento de arquivos de ícones no tema.

### Adicionado
- Base técnica interna para a interface (servidor local, trabalhos e ponte nativa), sem mudança visível no uso.

## [4.5.15] — 2026-09-11

### Adicionado
- Revisão própria do `docs/DESIGN.md` (12 seções) com linguagem exclusiva do aplicativo.
- Ícone da pasta do projeto igual ao do app (`desktop.ini`).

### Corrigido
- Removida a linha órfã do PyMuPDF em `requirements.txt`; trava regenerada.
- Documentação sem citações cruzadas entre aplicativos.

## [4.5.14] — 2026-09-11

### Adicionado
- `docs/DESIGN.md`: identidade própria (sóbrio, leve, focado) com as
  ondas como assinatura, tokens CSS e checklist por tela.
- `docs/GUIA_OPEN_DESIGN.md`: direção de design systems e prompt para
  o agente de design da versão web.
- Importação e exportação de perfis em `.json` validado ( envelope com
  formato e versão, nome único e identificador novo em colisão).
- Validação estrutural detalhada no editor (lista todos os problemas
  com rótulo e identificador antes de salvar).
- Backup em ZIP com data/hora e restauração validada.
- `utils/files.py`: abrir pasta e preencher campo unificados.

### Corrigido
- Toast preso à janela em qualquer escala, com dispensa por Escape;
  insígnia de aviso com contraste aprovado (âmbar escuro 5.02:1).
- Boas-vindas abrem só com a janela visível e texto refeito.
- `AlertModal` aceita lista de erros opcional (corrige crash em chamadas sem lista).
- Seletor de formulários sem sobreposição de botões.
- Template DAMP atualizado (86 campos, geometria validada).

## [4.5.13] — 2026-09-10

### Alterado
- Campos SIM/NÃO do DAMP viraram caixa de seleção (checkbox preserva os
  valores SIM/NÃO das regras); checkbox aceita par de opções configurável.

## [4.5.12] — 2026-09-09

### Corrigido
- Pré-visualização de mapeamento sem PyMuPDF (pypdfium2, licença permissiva).
- Avisos de terceiros com fonte do Ghostscript e seção de terceiros no README.

### Adicionado
- Serviço genérico de geometria de formulários: auditoria (área zerada,
  fora da página, sobreposição) e correções declarativas por modelo via
  `geometria_modelos.json` (`scripts/corrigir_geometria.py`); script
  específico do DAMP removido.

## [4.5.11] — 2026-09-09

### Corrigido
- Mascaramento de CPF, CNPJ e e-mail no log, incluindo tracebacks.
- Segunda cópia do aplicativo agora avisa e encerra (mutex nomeado).
- Pastas com fallbacks graváveis; JSON corrompido gera cópia `.corrompido-<data>` antes do reset.
- Log com rotação (2 MB, 5 cópias) e nível resumido no executável.
- Word travado: aviso com contagem regressiva e encerramento só da instância filha.
- Build interrompe com causa explícita quando o Ghostscript está ausente.
- `AlertModal` aceita lista de erros opcional (corrige crash em chamadas sem lista).
- Seis vulnerabilidades conhecidas no pypdf corrigidas (6.14.2 → 6.16.1).

### Adicionado
- `BaseModal`: esqueleto único dos 6 modais, com foco inicial, devolução de foco e tecla Escape.
- Trava fiel de dependências (`requirements-lock.txt`) e auditoria com `pip-audit`.
- `THIRD_PARTY_NOTICES.md`, este registro e modelo de notas de release.

## [4.5.10] — 2026-09-08

Versão estável: paginação fixa, quadros que se ocultam, contador de pendências,
seleção por identificador, correções aplicadas a perfis, limites de segurança
para PDFs e pacote com verificação SHA-256.

## [4.5.9] — 2026-09-08

Multi-seleção de formulários no modo simples e documentação base (`docs/`).
