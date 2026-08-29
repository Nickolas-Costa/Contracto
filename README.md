# Contracto (v4.5.5)

Aplicativo desktop (Windows) moderno e ultrarrápido para preenchimento automatizado de declarações habitacionais e conversão de documentos contratuais para o padrão de conformidade e arquivamento perene **PDF/A-2b**:
- **Declaração de Pessoa Politicamente Exposta (PPE)**
- **Declaração de Primeiro Imóvel**
- **Formulário Cliente Crédito Imobiliário CAIXA (MO 30.844 v011)**
- **Suporte a Modelos Personalizados e Perfis Customizados (MCMV, SBPE, Formulário CAIXA, etc.)**

---

## 🔒 Segurança, Privacidade e Execução 100% Local

O **Contracto** foi arquitetado com foco absoluto na **segurança dos dados e no sigilo profissional**:

- **Zero Nuvem (100% Offline e Local)**: Todo o processamento de dados, preenchimento de formulários e conversão de documentos ocorrem exclusivamente dentro da memória e do disco da sua própria máquina. **Nenhum dado é enviado para servidores externos, APIs ou serviços de terceiros.**
- **Conformidade Natural com a LGPD**: Como nenhuma informação de clientes (Nome, CPF, CNPJ, dados bancários, endereços ou rendas) trafega pela internet ou fica armazenada em servidores externos, seu escritório ou imobiliária mantém total controle e conformidade com a Lei Geral de Proteção de Dados.
- **Isolamento e Proteção de Processos**: A conversão de PDFs e renderização operam com interpretadores isolados em sandbox nativa de segurança (`-dSAFER`), prevenindo qualquer execução indevida de arquivos adulterados.
- **Armazenamento Seguro de Preferências**: Configurações de tema, diretórios e perfis são salvos localmente na pasta segura do seu usuário do Windows (`%APPDATA%\Contracto`).

---

## 🚀 Principais Recursos da Versão 4.5.5

- **Novo Validador Universal de CNPJ**: Suporte completo ao CNPJ tradicional (14 dígitos numéricos) e ao **novo padrão de CNPJ Alfanumérico da Receita Federal** (*IN RFB nº 2.229/2024*), com cálculo via Módulo 11 ASCII e auto-formatação em tempo real.
- **Interface e Tipografia Uniforme**: Alinhamento milimétrico de todos os campos da Etapa 1 e Etapa 2 (145px de largura uniforme para todos os rótulos), eliminando desalinhamentos e cortes visuais.
- **Design System Dinâmico & Temas**: Suporte a temas Claro e Escuro, paletas de cores personalizáveis e ícones vetoriais de alta resolução em SVG rasterizados sob demanda.
- **Centralização Inteligente com Compensação de DPI**: Modais e popups perfeitamente centralizados em qualquer escala de monitor (100%, 125%, 150%, 4K).
- **Gerenciador Modular de Perfis**: Crie, edite e duplique perfis com campos customizáveis em tipos padronizados (`TEXTO`, `CPF`, `CNPJ`, `DATA`, `MOEDA`, `SELECAO`, `CHECKBOX`).
- **Conversão Silenciosa para PDF/A-2b**: Geração de documentos em conformidade ISO 19005-2 sem janelas piscando ou travamentos.
- **Diagnóstico e Reparo Automatizado**: Verificação de integridade do ambiente com 1 clique na aba de Configurações.

---

## 📥 Download e Atualização

### Instalação para Usuários Finais

1. Baixe o pacote comprimido `Contracto_v4.5.5.zip` na página de [Releases](https://github.com/Nickolas-Costa/Contracto/releases).
2. Extraia o conteúdo em um local da sua preferência no computador.
3. Execute `Contracto_v4.5.5.exe`. Todos os modelos, utilitários e o interpretador Ghostscript já vêm embutidos!

### Como Atualizar

Para atualizar o aplicativo, basta baixar o novo `.zip` e substituir o executável anterior. **Suas configurações salvas e perfis personalizados são preservados**, pois ficam protegidos no diretório `%APPDATA%\Contracto`.

---

## 🛠️ Tecnologias e Bibliotecas Utilizadas

O ecossistema do **Contracto** utiliza tecnologias consagradas de código aberto:

- **[Python 3.12+](https://www.python.org/)** — Linguagem de programação principal de alta confiabilidade
- **[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)** — Biblioteca de interface gráfica moderna, com temas e responsividade
- **[pypdf](https://pypdf.readthedocs.io/)** — Leitura e preenchimento técnico de formulários PDF (AcroForm)
- **[pikepdf](https://pikepdf.readthedocs.io/)** — Validação estrutural de metadados e integridade de arquivos PDF
- **[Ghostscript](https://ghostscript.com/)** — Motor de renderização e conformidade com o padrão internacional PDF/A-2b (ISO 19005-2)
- **[Pillow (PIL)](https://python-pillow.org/)** — Processamento de imagens, rasterização de ícones e geração de gradientes em tempo real
- **[darkdetect](https://github.com/alfaifi/darkdetect)** — Detecção automática do modo Claro/Escuro do sistema operacional Windows
- **[pywin32](https://github.com/mhammond/pywin32)** — Integração nativa com a API do Windows, barra de tarefas e automação COM
- **[PyInstaller](https://pyinstaller.org/)** — Empacotador autônomo para compilação em executável único independente (`.exe`)

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
