<div align="center">

<img src="assets/LOGO_OFICIAL_CONTRACTO.png" alt="Contracto" width="120"/>

# Contracto
### Automação de Contratos Habitacionais, Preenchimento de Declarações & Conversão PDF/A-2b

[![Versão](https://img.shields.io/badge/versão-v5.7.0-1E6FB3?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Nickolas-Costa/Contracto/releases)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Plataforma](https://img.shields.io/badge/Plataforma-Windows%2010%20%7C%2011%20(64--bit)-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/Nickolas-Costa/Contracto)
[![Padrão ISO](https://img.shields.io/badge/Padrão-ISO%2019005--2%20(PDF%2FA--2b)-E02424?style=for-the-badge&logo=adobeacrobatreader&logoColor=white)](https://ghostscript.com/)
[![Testes](https://img.shields.io/badge/Testes-unittest%20%2B%20smoke%20WebView2-success?style=for-the-badge&logo=pytest&logoColor=white)](https://github.com/Nickolas-Costa/Contracto)

<br/>

**[📥 Baixar Instalador (.exe) ou ZIP](https://github.com/Nickolas-Costa/Contracto/releases)** &nbsp;•&nbsp;
**[📖 Guia de Uso](#-modos-de-opera%C3%A7%C3%A3o-e-fluxos-de-trabalho)** &nbsp;•&nbsp;
**[🔒 Segurança & Privacidade](#-seguran%C3%A7a-privacidade-e-execu%C3%A7%C3%A3o-100-local)** &nbsp;•&nbsp;
**[🎨 Design System](docs/DESIGN_SYSTEM.md)** &nbsp;•&nbsp;
**[📝 Alterações](CHANGELOG.md)**

</div>

---

## 💡 Sobre o Contracto

O **Contracto** é uma solução desktop Windows nativa, moderna e de alto desempenho desenvolvida para correspondentes bancários, imobiliárias e profissionais do setor habitacional. Ele automatiza o preenchimento de formulários cadastrais, organiza dossiês de financiamento e converte documentos contratuais para o formato de conformidade **PDF/A-2b (ISO 19005-2)**.

### 📋 Modelos Oficiais Suportados Nativamente:
- **Declaração de Pessoa Politicamente Exposta (PPE)**
- **Declaração de Primeiro Imóvel**
- **Form Cliente Crédito Imobiliário (FORM CLIENTE / MO 30.844)**
- **Declaração para Pagamento do ITBI** (com enquadramento de isenção via Lei 1648/2023)
- **Requerimento de Isenção de Tributos Municipais** (com herança automática de assinatura)
- **Perfis Personalizados** (MCMV, SBPE, customizáveis pelo usuário)

---

## 🔄 Modos de Operação e Fluxos de Trabalho

O sistema dispõe de um seletor dinâmico de modo na barra superior (*TopBar*), permitindo alternar instantaneamente entre dois modos especializados:

### 1. 📂 Modo Contrato (Contratos Habitacionais)
Projetado para processos contratuais completos:
- **Etapa 1 (Preencher)**: 1 a 4 participantes com validação de CPF/CNPJ em tempo real, data e pasta de destino.
- **Etapa 2 (Conferir)**: escolha dos formulários, inclusão dos documentos do processo (Contrato, Planilha de Evolução, etc.) e do formato. Ao confirmar, tudo é gerado, convertido para **PDF/A-2b** e organizado na estrutura de pastas padronizada, de uma vez.
- **Etapa 3 (Concluir)**: resultado final, visualização dos PDFs e atalho para a pasta.

### 🧾 Leitura de documentos do cliente (Simples e Contrato)
Na faixa de destaque do topo, **Ler documentos** (ou simplesmente arrastar os arquivos para a janela) abre o modal de leitura:
- Aceita **PDF, RTF, DOC e DOCX** (até 20); RTF, DOC e DOCX viram PDF na hora, com o Word instalado. Os originais nunca são alterados e a cópia de trabalho some ao fechar o app.
- O Contracto lê o texto do PDF (sem OCR; imagens escaneadas não têm texto) e propõe valores para os campos do modelo escolhido: nome, CPF/CNPJ, PIS, nascimento, RG, estado civil, regime de bens, união estável, profissão, e-mail, telefone, endereço (inclusive em partes), matrícula, data e local, e dados do **Cadastro de Clientes**.
- **Contratos com vários compradores** (até 4, com cônjuge, união estável ou parentes): cada comprador é lido separadamente, só dentro da cláusula dos compradores; vendedor, representante da empresa e credora não viram participantes.
- Cada valor aparece **ao lado do documento**, editável, com a página de origem; números que não conferem (CPF, PIS, CNPJ, telefone) vêm com aviso e desmarcados. **Nada entra no formulário sem a sua confirmação**, e há **Desfazer última leitura**.
- Em **Configurações > Padrões de leitura** você ensina onde o dado aparece nos seus contratos ("depois de tal frase, até a vírgula").

### 2. 📄 Modo Simples (Formulários Únicos & Declarações Avulsas)
Projetado para emissão rápida e direta de formulários individuais com **1 clique**:
- Interface simplificada sem necessidade de Etapa 2.
- Geração instantânea do PDF preenchido e abertura direta da pasta de destino.
- Possibilidade de preencher mais de um formulário no mesmo fluxo e com divisão dos campos por páginas: **abas livres** (vá a qualquer página sem preencher a anterior; cada aba mostra quantos campos faltam).
- **Gerar mesmo assim**: só nome, CPF, data, local e pasta são obrigatórios; os demais campos viram uma lista de pendências, com a opção de gerar com eles em branco (o modo Contrato continua exigindo todos).
- **ITBI por município**: prefeitura, comarca e texto da lei de isenção cadastrados em Configurações (e perguntados na primeira execução); endereços aceitam texto completo ou em partes (logradouro, número, bairro...).
- **Opção `[x] Preservar dados para Reutilizar`**: Mantém dados preenchidos na tela para que você possa emitir formulários sequenciais (ex: Contrato e logo após ITBI/Isenção) sem precisar digitar nada novamente.

---

## 🔒 Segurança, Privacidade e Execução 100% Local

O **Contracto** foi arquitetado com foco absoluto na **segurança dos dados e no sigilo profissional**:

- **Zero Nuvem (100% Offline e Local)**: Todo o processamento de dados, preenchimento de formulários e conversão de documentos ocorrem exclusivamente dentro da memória e do disco da sua própria máquina. **Nenhum dado pessoal ou financeiro é enviado para servidores externos, APIs ou serviços em nuvem.** A única conexão é a consulta de atualização, feita só quando você clica em "Verificar atualizações".
- **Conformidade Natural com a LGPD**: Como nenhuma informação de clientes (Nome, CPF, CNPJ, dados bancários, endereços ou rendas) trafega pela internet, seu escritório mantém total controle e conformidade com a Lei Geral de Proteção de Dados.
- **Isolamento e Proteção de Processos**: A conversão de PDFs opera com interpretadores isolados em sandbox nativa de segurança (`-dSAFER`), prevenindo qualquer execução indevida de arquivos adulterados.
- **Leitura de documentos 100% local**: os PDFs do cliente são lidos no seu computador (texto do PDF, sem serviço externo nem IA em nuvem); os valores lidos não vão para log e só entram no formulário depois da sua conferência.
- **Armazenamento Seguro de Preferências**: Configurações de tema, diretórios e perfis são salvos localmente na pasta segura do seu usuário do Windows (`%APPDATA%\Contracto`).

---

## Atualizações da Versão 5.7.0

**Leitura de documentos escaneados (OCR do Windows):** páginas sem texto são lidas pela imagem, e o botão **Ler como imagem (OCR)** força a leitura de um documento inteiro. Nada a instalar além do idioma Português (Brasil) do Windows. Em contratos com um só comprador, o "e" de "filho(a) de MÃE e PAI" não cria mais um 2º participante (e o endereço fica com o comprador certo).

## Atualizações da Versão 5.6.0

**Leitura de documentos do cliente** (Simples e Contrato), com revisão ao lado do documento, contratos com vários compradores e cadastro de clientes; **páginas livres** e **Gerar mesmo assim** no modo Simples; máscaras de digitação que mantêm o cursor; ITBI por município (isenção modular), prefeitura no PDF e endereço completo ou em partes; campos do MO 29300 reposicionados no PDF; Conferência com atalho para o campo. Detalhes no [CHANGELOG.md](CHANGELOG.md) e na ADR 0027.

## Atualizações da Versão 5.5.0

**Atualização pelo próprio aplicativo:** em Configurações, "Verificar atualizações" consulta a lista de versões, baixa o instalador, confere a assinatura e instala, sem passar pelo navegador nem pelo alerta do SmartScreen. Só acontece quando você clica; nada é consultado ao abrir. Detalhes na ADR 0032 e em [PRIVACIDADE.md](docs/PRIVACIDADE.md).

## Atualizações da Versão 5.4.0

No modo **Contrato**, gerar e concluir viraram **uma etapa só**: o formato (PDF ou PDF/A-2b) e os documentos extras são escolhidos na conferência e, ao confirmar, os documentos são gerados, convertidos e organizados de uma vez. Correções: falha que prendia a tela em "Processando…", botão Cancelar, PDF/A em pasta com `%` no nome, reparo do sistema que fechava o Word do usuário, edição e exclusão de perfis, backup. O app agora avisa antes de fechar com trabalho em andamento. Detalhes no [CHANGELOG.md](CHANGELOG.md) e na ADR 0032 (que também traz o plano de atualização dentro do app).

## Atualizações da Versão 5.3.0

O app passa a rodar no **shell Tauri** (janela nativa + servidor local em Python), com instalador NSIS no lugar do Inno Setup. Abertura bem mais rápida (a janela aparece em menos de 1 s), instância única, carregamentos em **modal com giratório/barra** em vez de avisos no canto, novo ícone e várias correções: anexar arquivos com acento, tema que voltava ao padrão, Conversão presa em "Convertendo…" após concluir e barra superior quebrada em janela reduzida. Detalhes no [CHANGELOG.md](CHANGELOG.md) e na ADR 0031.

## Atualizações da Versão 5.1.0

Polimento visual e correções de fluxo: ícones, toast legível, barra fixa sem emenda, máscara de CNPJ, renomeio por arquivo na Conversão, pastas do Contrato simplificadas e PDF/A com OutputIntent. Detalhes no `CHANGELOG.md`.

## Atualizações da Versão 5.0.0

Interface Tk aposentada (a WebView é a única UI), backend `sidecar` e contrato nativo prontos para o Tauri, validação de CNPJ corrigida, máscara de moeda, conferência reformulada e Etapa 1 fatiada em módulos. Detalhes em [CHANGELOG.md](CHANGELOG.md) e ADRs 0027–0030.

## Atualizações da Versão 4.5.26

Formato de saída inicial pelas Configurações (botões em vez de lista), visualizador de PDF responsivo, arrastar e soltar na Conversão, perfis separados por modo e barra superior fixa. Detalhes em [CHANGELOG.md](CHANGELOG.md) e ADR 0026.

## Atualizações da Versão 4.5.25

Preparação pré-Tauri (contrato UI↔shell isolado em `api.js`), correção do endpoint de reparo do sistema e do alvo do atalho de reparo; o instalador Inno Setup passa a reconhecer a instalação por usuário. Detalhes em [CHANGELOG.md](CHANGELOG.md).

## Atualizações da Versão 4.5.24

Pastas de destino com nome legível (`Contrato <Nomes>` / `(gerados)`), conferência de formulários/documentos extras na Etapa 2 e cores derivadas por tema. Detalhes em [CHANGELOG.md](CHANGELOG.md).

## Atualizações da Versão 4.5.17

Interface web sobre a API local (Etapa 1 e 2, visualizador, Config), participante modular por perfil e revisão visual. Detalhes em [CHANGELOG.md](CHANGELOG.md).

## Atualizações da Versão 4.5.16

Correções de robustez na fila de processamento, nos registros e nos diálogos, além de base técnica interna para a interface. Detalhes em [CHANGELOG.md](CHANGELOG.md).

## Atualizações da Versão 4.5.15

Acumulado desde a 4.5.11: privacidade e estabilidade (log, instância única, Word), interface (modais, toast, boas-vindas, DAMP), perfis (import/export, validação, backup), dependências e documentação própria de design. Detalhes em [CHANGELOG.md](CHANGELOG.md).

## Atualizações da Versão 4.5.14

Identidade visual própria (`docs/DESIGN.md`), guia para o design da versão web e toast contido na janela com dispensa por teclado. Detalhes em [CHANGELOG.md](CHANGELOG.md).

---

## 📂 Estrutura do Projeto
Para uma visão organizada de onde cada parte do código fica, consulte [docs/MAPA_PROJETO.md](docs/MAPA_PROJETO.md).
```
CONTRACTO/
├── LICENSE                             # Licença MIT
├── README.md                           # Documentação oficial do projeto
├── CHANGELOG.md                        # Histórico de versões (série 4.x detalhada em docs/releases/)
├── VERSION                             # Espelho de app/version.py
├── AGENTS.md                           # Regras de trabalho para agentes e contribuidores
├── docs/                               # ADRs, arquitetura, contrato Tauri, design system, QA e releases
├── frontend/                           # UI de produção (WebView2), JS puro sem bundler
│   ├── index.html, lab.html            # Telas e laboratório visual
│   ├── css/                            # tokens.css (design tokens) e layout.css
│   └── js/                             # api.js (único ponto que conhece o shell), app.js, ui.js,
│                                       # form-state.js (validadores/máscaras), etapa1.js, etapa2.js,
│                                       # perfis.js, conferencia.js, calendario.js, conversao.js, leitura.js (leitura de
│                                       # documentos), paginacao.js, municipios.js, padroes.js, endereco.js, ajuda.js
├── src-tauri/                          # Shell Tauri (Rust): janela, ponte nativa, diálogos, instalador NSIS (ADR 0029/0031)
├── package.json                        # Só o CLI do Tauri (@tauri-apps/cli)
├── requirements.txt / -dev / -lock     # Dependências de execução, desenvolvimento e travadas
├── build_exe.bat                       # Build automatizado (sidecar + Tauri: instalador NSIS e ZIP portátil)
├── app/
│   ├── main.py                         # Shell pywebview legado (desenvolvimento e smokes)
│   ├── webview_shell.py                # Shell pywebview/WebView2 legado e referência da ponte
│   ├── sidecar.py                      # Backend headless do shell Tauri (UTF-8, instância única, ADR 0029)
│   ├── server.py                       # API FastAPI loopback (token efêmero)
│   ├── version.py                      # Versão centralizada do sistema (v5.7.0)
│   ├── api/                            # Rotas, jobs, seleções autorizadas e fila
│   ├── services/                       # Geração, PDF/A, RTF, etapa 2, reparo, composição de perfis, leitura de PDFs (pdf_extraction)
│   ├── models/                         # Entidades (participante)
│   ├── ports/                          # Diálogos WebView, binários (Word/GS) e armazenamento
│   ├── utils/                          # Validadores, perfis, config, logger, arquivos, instância única
│   └── assets/                         # config/perfis_iniciais.json, templates/, icons/, gs/ (Ghostscript)
├── scripts/                            # build_tauri.py, build_sidecar.py, sugerir_geometria.py/corrigir_geometria.py (campos dos PDFs), gerar_icone.py, setup_gs.py, arquivamento do dist
└── tests/                              # Suíte unittest, smokes (WebView2, motores) e checagens em Node
```

---

## 💻 Instalação em Ambiente de Desenvolvimento

```bash
# 1. Clonar o repositório
git clone https://github.com/Nickolas-Costa/Contracto.git
cd Contracto

# 2. Criar e ativar ambiente virtual
python -m venv .venv
.venv\Scripts\activate        # No Windows

# 3. Instalar dependências
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## ▶️ Executando em Desenvolvimento

```bash
cd app
python main.py            # shell pywebview legado (mais rápido para iterar na interface)
```

Para rodar o shell Tauri real é preciso o build do sidecar (`.venv\Scripts\python.exe scripts\build_sidecar.py`) e do Tauri (`npx tauri build`). Requisitos: Rust (`stable-x86_64-pc-windows-msvc`), Visual Studio Build Tools (C++) e Node.

## 🧪 Executando os Testes Automatizados

```bash
python -m unittest discover -s tests -v
```

## 📦 Compilação (Tauri + sidecar)

Pré-requisitos: Python 3.12+ com o `.venv` e `requirements-dev.txt`, Rust (rustup, `stable-x86_64-pc-windows-msvc`), Visual Studio Build Tools com C++ e Node. Para compilar a versão 5.7.0:

```cmd
build_exe.bat
```

O build baixa o NSIS (uma vez, com hash verificado), gera o sidecar Python com o Ghostscript embutido, compila o shell Tauri e entrega em `dist/`:

- `Contracto_Setup_v5.7.0.exe`: instalador NSIS por usuário (remove a instalação antiga do Inno Setup, se houver, e preserva `%APPDATA%\Contracto`);
- `Contracto_v5.7.0.zip`: versão portátil (`Contracto.exe` + pasta `sidecar/`);
- `*.sha256.txt` de cada um, `latest.json` (lido pelo atualizador do app; precisa ir junto na release) e `RELEASE_NOTES_5.7.0.md`.

> O build assina o instalador para o atualizador do app com a chave em `%USERPROFILE%\.tauri\contracto-updater.key` (ou `TAURI_SIGNING_PRIVATE_KEY`). **Guarde uma cópia dessa chave fora do computador:** sem ela, as versões já instaladas não aceitam mais atualizações. O instalador não tem assinatura de código da Microsoft, então o SmartScreen pode alertar em quem baixa pelo navegador. Se o antivírus bloquear o build, exclua a pasta do projeto da verificação em tempo real.

---

## ⚖️ Termos de Uso e Avisos Legais

### 1. Finalidade do Aplicativo
O **Contracto** é uma ferramenta técnica de produtividade desenvolvida exclusivamente para automatizar o preenchimento de campos em formulários PDF (AcroForm), organizar arquivos em pastas e converter documentos para o padrão PDF/A-2b. O aplicativo não altera o conteúdo legal ou as cláusulas das declarações, atuando apenas como preenchedor de campos com base nos dados fornecidos pelo usuário.

### 2. Isenção de Vínculo Institucional
O **Contracto** é uma ferramenta independente. Este aplicativo **NÃO possui qualquer vínculo oficial, associação, patrocínio ou homologação** com nenhuma instituição financeira ou governamental.

### 3. Isenção de Responsabilidade sobre os Dados e Documentos
- O usuário é o **único responsável** pela exatidão, veracidade e legalidade das informações digitadas e dos documentos gerados.
- O software é fornecido **"NO ESTADO EM QUE SE ENCONTRA" ("AS IS")**, sem garantias expressas ou implícitas de qualquer tipo.
- Os desenvolvedores e mantenedores deste projeto **não se responsabilizam** por eventuais recusas de dossiês, erros de digitação ou divergências de dados decorrentes do uso desta ferramenta.

### 4. Componentes de Terceiros
A lista de componentes distribuídos com o aplicativo está em [THIRD_PARTY_NOTICES.md](docs/THIRD_PARTY_NOTICES.md). O motor de conversão PDF/A (Ghostscript 10.07.1, AGPL) tem código-fonte em: [Ghostscript](https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/tag/gs10071).

---
