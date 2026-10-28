<div align="center">

<img src="assets/LOGO_OFICIAL_CONTRACTO.png" alt="Contracto" width="120"/>

# Contracto
### Automação de Contratos Habitacionais, Preenchimento de Declarações & Conversão PDF/A-2b

[![Versão](https://img.shields.io/badge/versão-v5.0.0-005CA9?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Nickolas-Costa/Contracto/releases)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Plataforma](https://img.shields.io/badge/Plataforma-Windows%2010%20%7C%2011%20(64--bit)-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/Nickolas-Costa/Contracto)
[![Padrão ISO](https://img.shields.io/badge/Padrão-ISO%2019005--2%20(PDF%2FA--2b)-E02424?style=for-the-badge&logo=adobeacrobatreader&logoColor=white)](https://ghostscript.com/)
[![Testes](https://img.shields.io/badge/Testes-unittest%20%2B%20smoke%20WebView2-success?style=for-the-badge&logo=pytest&logoColor=white)](https://github.com/Nickolas-Costa/Contracto)

<br/>

**[📥 Baixar Executável (.zip)](https://github.com/Nickolas-Costa/Contracto/releases)** &nbsp;•&nbsp;
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
Projetado para processos contratuais completos com fluxo de 2 etapas:
- **Etapa 1 (Geração de Documentos)**: Preenchimento de 1 a 4 participantes com validação de CPF/CNPJ em tempo real, data e diretório de destino.
- **Etapa 2 (Conversão e Organização)**: Inclusão de documentos do processo (Contrato, Cédula de Crédito, Planilha de Evolução, etc.), para conversão em lote **PDF/A-2b** e criação automática da estrutura de pastas padronizada.

### 2. 📄 Modo Simples (Formulários Únicos & Declarações Avulsas)
Projetado para emissão rápida e direta de formulários individuais com **1 clique**:
- Interface simplificada sem necessidade de Etapa 2.
- Geração instantânea do PDF preenchido e abertura direta da pasta de destino.
- Possibilidade de preencher mais de um formulário no mesmo fluxo e com divisão dos campos por páginas.
- **Opção `[x] Preservar dados para Reutilizar`**: Mantém dados preenchidos na tela para que você possa emitir formulários sequenciais (ex: Contrato e logo após ITBI/Isenção) sem precisar digitar nada novamente.

---

## 🔒 Segurança, Privacidade e Execução 100% Local

O **Contracto** foi arquitetado com foco absoluto na **segurança dos dados e no sigilo profissional**:

- **Zero Nuvem (100% Offline e Local)**: Todo o processamento de dados, preenchimento de formulários e conversão de documentos ocorrem exclusivamente dentro da memória e do disco da sua própria máquina. **Nenhum dado pessoal ou financeiro é enviado para servidores externos, APIs ou serviços em nuvem.**
- **Conformidade Natural com a LGPD**: Como nenhuma informação de clientes (Nome, CPF, CNPJ, dados bancários, endereços ou rendas) trafega pela internet, seu escritório mantém total controle e conformidade com a Lei Geral de Proteção de Dados.
- **Isolamento e Proteção de Processos**: A conversão de PDFs opera com interpretadores isolados em sandbox nativa de segurança (`-dSAFER`), prevenindo qualquer execução indevida de arquivos adulterados.
- **Armazenamento Seguro de Preferências**: Configurações de tema, diretórios e perfis são salvos localmente na pasta segura do seu usuário do Windows (`%APPDATA%\Contracto`).

---

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
│                                       # perfis.js, conferencia.js, calendario.js, conversao.js
├── packaging/Contracto.iss             # Instalador Inno Setup
├── requirements.txt / -dev / -lock     # Dependências de execução, desenvolvimento e travadas
├── build_exe.bat                       # Build automatizado (.exe, .zip, instalador)
├── app/
│   ├── main.py                         # Ponto de entrada (instância única + shell WebView)
│   ├── webview_shell.py                # Shell pywebview/WebView2 e ponte nativa
│   ├── sidecar.py                      # Backend headless para o shell Tauri (ADR 0029)
│   ├── server.py                       # API FastAPI loopback (token efêmero)
│   ├── version.py                      # Versão centralizada do sistema (v5.0.0)
│   ├── api/                            # Rotas, jobs, seleções autorizadas e fila
│   ├── services/                       # Geração, PDF/A, RTF, etapa 2, reparo, composição de perfis
│   ├── models/                         # Entidades (participante)
│   ├── ports/                          # Diálogos WebView, binários (Word/GS) e armazenamento
│   ├── utils/                          # Validadores, perfis, config, logger, arquivos, instância única
│   └── assets/                         # config/perfis_iniciais.json, templates/, icons/, gs/ (Ghostscript)
├── scripts/                            # Build, spec do PyInstaller, pacote de distribuição, atalho
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
python main.py
```

## 🧪 Executando os Testes Automatizados

```bash
python -m unittest discover -s tests -v
```

## 📦 Compilação do Executável (.exe)

Para compilar o executável autônomo da versão 5.0.0, execute:

```cmd
build_exe.bat
```

O executável e o arquivo comprimido para distribuição serão gerados em `dist/Contracto_v5.0.0.zip` (+ `.sha256.txt`). O instalador Windows é gerado na etapa final do build pelo Inno Setup, em `dist/Contracto_Installer_v5.0.0.exe`.

> O Inno Setup pode estar instalado só para o usuário (`%LOCALAPPDATA%\Programs\Inno Setup 6`), fora do PATH; `scripts/build_installer.py` (e o passo 6 de `build_exe.bat`) já localiza essa instalação. Sem Inno Setup, o `.exe` e o `.zip` ainda são gerados e o instalador é apenas pulado.

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
