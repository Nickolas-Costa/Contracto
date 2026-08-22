# Contracto (v4.5)

Aplicativo desktop (Windows) em Python para preenchimento automatizado de declarações habitacionais e conversão de documentos contratuais para o padrão de conformidade **PDF/A-2b**:
- **Declaração de Pessoa Politicamente Exposta (PPE)**
- **Declaração de Primeiro Imóvel**

A **Versão 4.5** traz o aperfeiçoamento da experiência visual e de usabilidade: centralização milimétrica de todos os modais com compensação nativa de escala DPI do Windows, controle anti-acúmulo de popups com descarte limpo, responsividade dinâmica e proporção equilibrada dos quadros principais, alinhamento intuitivo na Etapa 2, diferenciação visual para participantes e Design System formal e moderno ([DESIGN_SYSTEM.md](DESIGN_SYSTEM.md)).

---

## 🚀 Novidades da Versão 4.5

- **Centralização Precisa de Modais com Compensação de DPI**: Popups (ajuda, alertas, confirmações, carregamento e perfis) perfeitamente centralizados em qualquer resolução e escala (100%, 125%, 150%, 4K).
- **Ciclo de Vida Limpo de Popups**: Prevenção total de acúmulo de janelas em segundo plano, destruição limpa de overlays e suporte a fechamento por clique externo ou tecla `Escape`.
- **Quadros Responsivos e Proporcionais**: Largura equilibrada na Etapa 1 e Etapa 2 com margem adaptativa em tempo real.
- **Alinhamento Natural na Etapa 2**: Checkboxes e opções alinhadas à esquerda sem barras de rolagem desnecessárias.
- **Design System & Ícones Semânticos**: Catálogo vetorial adaptativo Claro/Escuro com diferenciação visual entre o participante titular e adicionais.
- **Execução Headless do Ghostscript**: Conversão para PDF/A-2b rápida e 100% silenciosa em segundo plano.
- **Diagnóstico e Reparo do Backend**: Verificação e manutenção automatizada do ambiente com 1 clique em Configurações.
- **Perfis Padrão "MCMV" e "SBPE" com Duplicação**: Configuração rápida de regras de preenchimento e exportação.

---

## 📥 Download e Atualização

### Instalação para Usuários

1. Baixe a versão mais recente (`Contracto.zip`) na página de **Releases** do repositório.
2. Extraia o conteúdo em um local da sua preferência.
3. Execute `Contracto.exe`. Todas as dependências e os modelos já vêm integrados!

### Como Atualizar

Para atualizar, baixe o `.zip` da nova versão e substitua os arquivos antigos. **Suas configurações e perfis personalizados não serão perdidos**, pois são armazenados separadamente no diretório seguro `%APPDATA%\Contracto`.

---

## 🛠️ Tecnologias Utilizadas

- **Python 3.12+**
- **[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)** — Interface gráfica moderna e responsiva
- **[pypdf](https://pypdf.readthedocs.io/)** — Leitura e preenchimento de campos de formulário (AcroForm)
- **[pikepdf](https://pikepdf.readthedocs.io/)** — Validação avançada e integridade de arquivos PDF
- **[Ghostscript](https://ghostscript.com/)** — Conversão e conformidade com o padrão PDF/A-2b (ISO 19005-2)
- **pywin32** — Integração com a barra de tarefas do Windows e conversão local de arquivos RTF via COM
- **PyInstaller** — Empacotamento em executável único e independente (`.exe`)

---

## 📂 Estrutura do Projeto

```
CONTRACTO/
├── LICENSE                             # Licença MIT
├── README.md                           # Documentação principal do projeto
├── CHANGELOG_v4.md                     # Histórico detalhado de alterações
├── DESIGN_SYSTEM.md                    # Especificação do Design System e catálogo de ícones
├── requirements.txt                    # Dependências de execução
├── requirements-dev.txt                # Dependências de desenvolvimento e testes
├── build_exe.bat                       # Script de compilação do executável (.exe)
├── app/
│   ├── main.py                         # Ponto de entrada da aplicação
│   ├── version.py                      # Versão centralizada do sistema (v4.5)
│   ├── ui/                             # Componentes visuais, telas, temas e modais
│   │   ├── alert_modal.py              # Modal de alertas informativos e erros
│   │   ├── animated_loader.py          # Player animado nativo de GIF e rotação de loaders
│   │   ├── confirm_modal.py            # Modal de confirmações com resposta binária
│   │   ├── date_picker.py              # Calendário pop-up ancorado para seleção de datas
│   │   ├── document_frame.py           # Gerenciamento de documentos extras (Etapa 2)
│   │   ├── feedback_toast.py           # Notificações toast temporárias
│   │   ├── loading_modal.py            # Modal de carregamento por etapas com cancelamento
│   │   ├── main_window.py              # Janela principal e orquestrador de navegação
│   │   ├── participant_frame.py        # Quadro de participantes com validação em tempo real
│   │   ├── profiles_frame.py           # Gestão, criação e duplicação de perfis
│   │   ├── settings_frame.py           # Configurações visuais e diagnóstico de sistema
│   │   ├── theme.py                    # Sistema de cores, fontes, ícones adaptativos e estilo dinâmico
│   │   └── welcome_modal.py            # Guia rápido de instruções
│   ├── models/                         # Modelos de dados e dataclasses
│   │   └── participant.py              # Entidade do participante do contrato
│   ├── services/                       # Camada de serviços e regras de negócio
│   │   ├── generator_service.py        # Preenchimento e validação de formulários
│   │   ├── pdf_service.py              # Manipulação de baixo nível de formulários PDF
│   │   ├── pdfa_converter.py           # Conversão para PDF/A-2b via Ghostscript
│   │   ├── process_folder_service.py   # Criação da estrutura de pastas padronizada
│   │   ├── rtf_converter.py            # Conversão de RTF para PDF via Microsoft Word COM
│   │   ├── stage2_service.py           # Orquestrador da Etapa 2
│   │   └── system_repair_service.py    # Diagnóstico e manutenção preventiva do sistema
│   ├── utils/                          # Utilitários, validações e persistência
│   │   ├── config_manager.py           # Armazenamento de preferências do usuário
│   │   ├── cpf_validator.py            # Validação e formatação de CPF
│   │   ├── date_formatter.py           # Conversão e formatação de datas
│   │   ├── file_picker.py              # Diálogos de seleção de arquivos
│   │   ├── filename_utils.py           # Padronização de nomenclatura de arquivos
│   │   ├── ghostscript_setup.py        # Localização e verificação do Ghostscript
│   │   ├── logger.py                   # Registro de logs operacionais
│   │   ├── profile_manager.py          # Gerenciamento e duplicação de perfis
│   │   └── resource_path.py            # Resolução de caminhos em ambiente PyInstaller
│   └── assets/                         # Recursos embutidos
│       ├── icons/                      # 30 ícones vetoriais em alta resolução (Light/Dark)
│       ├── loaders/                    # 10 animações GIF de carregamento dinâmico
│       ├── templates/                  # PDFs modelos oficiais (PPE e 1º Imóvel)
│       └── gs/                         # Binários do Ghostscript para empacotamento
├── scripts/                            # Scripts auxiliares de build e distribuição
│   ├── create_dist_package.py          # Geração do pacote zip de distribuição
│   ├── create_shortcut.py              # Criação do atalho na Área de Trabalho
│   ├── process_assets.py               # Rasterizador vetorial de ícones e organizador de loaders
│   └── setup_gs.py                     # Preparação do Ghostscript para o PyInstaller
└── tests/                              # Suíte de testes automatizados (unittest)
    ├── smoke_test_gui.py
    ├── test_cancellation.py
    ├── test_cpf_validator.py
    ├── test_date_formatter.py
    ├── test_filename_utils.py
    ├── test_generator_service.py
    ├── test_modelos_oficiais.py
    ├── test_process_folder.py
    ├── test_profile_manager.py
    └── test_system_repair.py
```

---

## 💻 Instalação em Ambiente de Desenvolvimento

```bash
# 1. Clonar o repositório
git clone https://github.com/Nickolas-Costa/Contracto.git
cd Contracto

# 2. Criar e ativar ambiente virtual
python -m venv .venv
.venv\Scripts\activate        # Windows

# 3. Instalar dependências
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## ▶️ Executando a Aplicação

```bash
cd app
python main.py
```

## 🧪 Executando os Testes Automatizados

```bash
python -m unittest discover -s tests -v
```

## 📦 Compilação do Executável (.exe)

Para gerar o executável autônomo, execute o script de compilação:

```cmd
build_exe.bat
```

O executável e o arquivo comprimido para distribuição serão gerados em `dist/Contracto_v4.5.zip`.

---

## ⚖️ Termos de Uso e Avisos Legais

### 1. Finalidade do Aplicativo
O **Contracto** é uma ferramenta de produtividade desenvolvida exclusivamente para automatizar o preenchimento de campos em formulários PDF (AcroForm), organizar arquivos em pastas e converter documentos para o padrão PDF/A-2b. O aplicativo não altera o conteúdo legal ou as cláusulas das declarações, atuando apenas como preenchedor técnico de campos com base nos dados fornecidos pelo usuário.

### 2. Isenção de Vínculo Institucional
O **Contracto** é uma ferramenta independente desenvolvida para auxílio na preparação de documentos e automação de declarações habitacionais. Este aplicativo **NÃO possui qualquer vínculo oficial, associação, patrocínio ou homologação** com nenhuma instituição financeira, governamental ou bancária pública/privada.

### 3. Isenção de Responsabilidade sobre os Dados e Documentos
- O usuário é o **único responsável** pela exatidão, veracidade e legalidade das informações digitadas e dos documentos gerados.
- O software é fornecido **"NO ESTADO EM QUE SE ENCONTRA" ("AS IS")**, sem garantias expressas ou implícitas de qualquer tipo, incluindo, mas não se limitando a, garantias de comercialização, adequação a um propósito específico ou ausência de erros.
- Os desenvolvedores e mantenedores deste projeto **não se responsabilizam** por eventuais recusas de dossiês, erros de preenchimento, divergências de datas/valores ou quaisquer danos diretos, indiretos ou incidentais decorrentes do uso desta ferramenta.

---
