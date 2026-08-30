<div align="center">

# 📑 Contracto
### Automação de Contratos Habitacionais, Preenchimento de Declarações & Conformidade PDF/A-2b

[![Versão](https://img.shields.io/badge/versão-v4.5.5-005CA9?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Nickolas-Costa/Contracto/releases)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Plataforma](https://img.shields.io/badge/Plataforma-Windows%2010%20%7C%2011%20(64--bit)-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/Nickolas-Costa/Contracto)
[![Privacidade](https://img.shields.io/badge/Privacidade-100%25%20Offline%20%7C%20Zero%20Cloud-2E7D32?style=for-the-badge&logo=shield&logoColor=white)](https://github.com/Nickolas-Costa/Contracto#-seguran%C3%A7a-privacidade-e-execu%C3%A7%C3%A3o-100-local)
[![Padrão ISO](https://img.shields.io/badge/Padrão-ISO%2019005--2%20(PDF%2FA--2b)-E02424?style=for-the-badge&logo=adobeacrobatreader&logoColor=white)](https://ghostscript.com/)
[![Testes](https://img.shields.io/badge/Testes-116%2F116%20Passando-success?style=for-the-badge&logo=pytest&logoColor=white)](https://github.com/Nickolas-Costa/Contracto)

<br/>

**[📥 Baixar Executável (.zip)](https://github.com/Nickolas-Costa/Contracto/releases)** &nbsp;•&nbsp;
**[📖 Guia de Uso](#-modos-de-opera%C3%A7%C3%A3o-e-fluxos-de-trabalho)** &nbsp;•&nbsp;
**[🔒 Segurança & Privacidade](#-seguran%C3%A7a-privacidade-e-execu%C3%A7%C3%A3o-100-local)** &nbsp;•&nbsp;
**[🎨 Design System](DESIGN_SYSTEM.md)**

</div>

---

## 💡 Sobre o Contracto

O **Contracto** é uma solução desktop Windows nativa, moderna e de alto desempenho desenvolvida para imobiliárias, correspondentes bancários e profissionais do setor habitacional. Ele automatiza o preenchimento de formulários cadastrais, organiza dossiês de financiamento e converte documentos contratuais para o formato de conformidade perene **PDF/A-2b (ISO 19005-2)**.

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

### 1. 📂 Modo Avançado (Contratos Habitacionais)
Projetado para processos contratuais completos com fluxo de 2 etapas:
- **Etapa 1 (Geração de Documentos)**: Preenchimento de 1 a 4 participantes com validação de CPF/CNPJ em tempo real, data no calendário e diretório de destino.
- **Etapa 2 (Conversão e Organização)**: Inclusão de documentos do processo (Contrato, Cédula de Crédito, Planilha de Evolução, etc.), conversão em lote para **PDF/A-2b** e criação automática da estrutura de pastas padronizada.

### 2. 📄 Modo Simples (Formulários Únicos & Declarações Avulsas)
Projetado para emissão rápida e direta de formulários individuais com **1 clique**:
- Interface simplificada sem necessidade de Etapa 2.
- Geração instantânea do PDF preenchido e abertura direta da pasta de destino.
- **Opção `[x] Preservar dados para Reutilizar`**: Mantém Nome, CPF, Endereço e Local preenchidos na tela para que você possa emitir formulários sequenciais (ex: Contrato e logo após ITBI/Isenção) sem precisar digitar nada novamente.

---

## 🔒 Segurança, Privacidade e Execução 100% Local

O **Contracto** foi arquitetado com foco absoluto na **segurança dos dados e no sigilo profissional**:

- **Zero Nuvem (100% Offline e Local)**: Todo o processamento de dados, preenchimento de formulários e conversão de documentos ocorrem exclusivamente dentro da memória e do disco da sua própria máquina. **Nenhum dado pessoal ou financeiro é enviado para servidores externos, APIs ou serviços em nuvem.**
- **Conformidade Natural com a LGPD**: Como nenhuma informação de clientes (Nome, CPF, CNPJ, dados bancários, endereços ou rendas) trafega pela internet, seu escritório mantém total controle e conformidade com a Lei Geral de Proteção de Dados.
- **Isolamento e Proteção de Processos**: A conversão de PDFs opera com interpretadores isolados em sandbox nativa de segurança (`-dSAFER`), prevenindo qualquer execução indevida de arquivos adulterados.
- **Armazenamento Seguro de Preferências**: Configurações de tema, diretórios e perfis são salvos localmente na pasta segura do seu usuário do Windows (`%APPDATA%\Contracto`).

---

## 🚀 Principais Recursos da Versão 4.5.5

- **Seletor de Modos Avançado / Simples**: Chaveador integrado na barra superior com stepper dinâmico adaptativo.
- **Preservação Inteligente de Dados**: Reaproveitamento instantâneo de dados cadastrais entre formulários diferentes.
- **Novo Validador Universal de CNPJ**: Suporte completo ao CNPJ tradicional (14 dígitos numéricos) e ao **novo padrão de CNPJ Alfanumérico da Receita Federal** (*IN RFB nº 2.229/2024*), com cálculo via Módulo 11 ASCII e auto-formatação em tempo real.
- **Interface e Tipografia Uniforme**: Alinhamento milimétrico de todos os campos da Etapa 1 e Etapa 2 (145px de largura uniforme para todos os rótulos), eliminando desalinhamentos e cortes visuais.
- **Design System Dinâmico & Temas**: Suporte a temas Claro e Escuro, paletas de cores personalizáveis e ícones vetoriais de alta resolução.
- **Gerenciador Modular de Perfis**: Crie, edite e duplique perfis com campos customizáveis em tipos padronizados (`TEXTO`, `CPF`, `CNPJ`, `DATA`, `MOEDA`, `SELECAO`, `CHECKBOX`).
- **Conversão Silenciosa para PDF/A-2b**: Geração de documentos em conformidade ISO 19005-2 sem janelas piscando ou travamentos.
- **Diagnóstico e Reparo Automatizado**: Verificação de integridade do ambiente com 1 clique na aba de Configurações.

---

## 📂 Estrutura do Projeto

```
CONTRACTO/
├── LICENSE                             # Licença MIT
├── README.md                           # Documentação oficial do projeto
├── CHANGELOG_v4.md                     # Histórico de versões e alterações
├── DESIGN_SYSTEM.md                    # Especificação do Design System e catálogo visual
├── requirements.txt                    # Dependências de execução
├── requirements-dev.txt                # Dependências de desenvolvimento e testes
├── build_exe.bat                       # Script de compilação automatizada (.exe)
├── app/
│   ├── main.py                         # Ponto de entrada da aplicação
│   ├── version.py                      # Versão centralizada do sistema (v4.5.5)
│   ├── ui/                             # Componentes visuais, telas, temas e modais
│   │   ├── alert_modal.py              # Modal de alertas informativos e de erro
│   │   ├── animated_loader.py          # Indicador visual leve de carregamento
│   │   ├── campo_dinamico_widget.py    # Renderizador modular de campos com auto-formatação
│   │   ├── confirm_modal.py            # Modal de confirmações binárias
│   │   ├── date_picker.py              # Calendário pop-up para seleção de datas
│   │   ├── document_frame.py           # Gestão de documentos extras na Etapa 2
│   │   ├── feedback_toast.py           # Notificações toast temporárias
│   │   ├── loading_modal.py            # Modal de carregamento por etapas com cancelamento
│   │   ├── main_window.py              # Janela principal e fluxo das etapas
│   │   ├── participant_frame.py        # Quadro de participantes com validação em tempo real
│   │   ├── profiles_frame.py           # Gerenciador, criação e duplicação de perfis
│   │   ├── settings_frame.py           # Configurações de tema e diagnóstico do sistema
│   │   ├── theme.py                    # Sistema de cores, fontes e ícones adaptativos
│   │   └── welcome_modal.py            # Guia interativo de instruções
│   ├── models/                         # Modelos de dados e dataclasses
│   │   └── participant.py              # Entidade do participante e campos customizados
│   ├── services/                       # Serviços de negócio e processamento
│   │   ├── generator_service.py        # Preenchimento e validação de formulários PDF
│   │   ├── pdf_service.py              # Manipulação direta de formulários AcroForm
│   │   ├── pdfa_converter.py           # Conversão segura para PDF/A-2b via Ghostscript (-dSAFER)
│   │   ├── process_folder_service.py   # Criação da estrutura de pastas padronizada
│   │   ├── rtf_converter.py            # Conversão de RTF para PDF via Microsoft Word COM
│   │   ├── stage2_service.py           # Orquestrador da esteira da Etapa 2
│   │   └── system_repair_service.py    # Diagnóstico e manutenção preventiva do sistema
│   ├── utils/                          # Utilitários, validações e persistência
│   │   ├── cnpj_validator.py           # Validador de CNPJ (tradicional e novo alfanumérico)
│   │   ├── config_manager.py           # Persistência de preferências do usuário
│   │   ├── cpf_validator.py            # Validação e formatação de CPF
│   │   ├── date_formatter.py           # Conversão e formatação de datas
│   │   ├── file_picker.py              # Diálogos nativos de seleção de arquivos
│   │   ├── filename_utils.py           # Sanitização e padronização de nomes de arquivos
│   │   ├── ghostscript_setup.py        # Verificação e inicialização do Ghostscript
│   │   ├── logger.py                   # Registro de logs operacionais
│   │   ├── profile_manager.py          # Gestão e persistência de perfis
│   │   └── resource_path.py            # Resolução de caminhos estáticos no executável
│   └── assets/                         # Recursos visuais e modelos
│       ├── icons/                      # Catálogo de ícones vetoriais (Light/Dark)
│       ├── loaders/                    # Animações visuais leves
│       ├── templates/                  # PDFs modelos oficiais (PPE e 1º Imóvel)
│       └── gs/                         # Binários do Ghostscript para empacotamento
├── scripts/                            # Scripts auxiliares de build e distribuição
│   ├── create_dist_package.py          # Geração do pacote zip de distribuição
│   ├── create_shortcut.py              # Criação do atalho na Área de Trabalho
│   ├── process_assets.py               # Rasterizador de ícones vetoriais
│   └── setup_gs.py                     # Preparação do Ghostscript para build
└── tests/                              # Suíte de testes automatizados (unittest)
    ├── smoke_test_gui.py
    ├── test_cancellation.py
    ├── test_cnpj_validator.py
    ├── test_cpf_validator.py
    ├── test_date_formatter.py
    ├── test_filename_utils.py
    ├── test_generator_service.py
    ├── test_modelos_oficiais.py
    ├── test_process_folder.py
    ├── test_profile_manager.py
    ├── test_security_hardening.py
    ├── test_system_repair.py
    └── test_visual_assets.py
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

Para compilar o executável autônomo da versão 4.5.5, execute:

```cmd
build_exe.bat
```

O executável e o arquivo comprimido para distribuição serão gerados em `dist/Contracto_v4.5.5.zip`.

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

---
