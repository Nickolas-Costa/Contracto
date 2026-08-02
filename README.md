# Contracto — Gerador de Declarações para Contratos Habitacionais

Aplicativo desktop (Windows) em Python para preencher automaticamente PDFs de declarações e gerenciar a organização e conformidade digital de processos habitacionais:

- **Declaração de Pessoa Politicamente Exposta (PPE)**
- **Declaração de Primeiro Imóvel**

A **Versão 4.1** introduz o preenchimento 100% automatizado de todos os campos AcroForm (incluindo endereços e datas de assinatura), modais visuais modernos com efeito escuro translúcido (`-alpha 0.60`), substituição completa de alertas nativos do Windows por componentes do app, expansão dinâmica do editor de perfis e suporte nativo ao ícone 3D na barra de tarefas.

---

## 📋 Sumário

- [Visão Geral](#visão-geral)
- [Funcionalidades Principais](#funcionalidades-principais)
- [Página de Configurações](#página-de-configurações)
- [Gerenciador de Perfis](#gerenciador-de-perfis)
- [Licença e Isenção de Responsabilidade Legal](#licença-e-isenção-de-responsabilidade-legal)
- [Download e Atualização](#download-e-atualização)
- [Tecnologias](#tecnologias)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Instalação (Desenvolvimento)](#instalação-desenvolvimento)
- [Como Executar](#como-executar)
- [Como Usar](#como-usar)
- [Modelos Oficiais Embutidos](#modelos-oficiais-embutidos)
- [Mapeamento de Campos dos PDFs](#mapeamento-de-campos-dos-pdfs)
- [Tratamento de Erros](#tratamento-de-erros)
- [Testes Automatizados](#testes-automatizados)
- [Gerando o Executável (.exe)](#gerando-o-executável-exe)

---

## ⚙️ Página de Configurações

A tela de **Configurações** permite personalizar inteiramente a experiência visual e os padrões do aplicativo:

- **Modo de Aparência**: Alterne entre *Modo Claro (Light)*, *Modo Escuro (Dark)* ou *Sincronizado com o Sistema*.
- **Paleta de Cores de Destaque**: Escolha entre diversas cores institucionais (Azul Institucional, Azul Royal, Ciano, Verde, Roxo, Rosa, Laranja, Cinza Azulado) ou defina um código Hexadecimal customizado. Todas as cores do app, seletores e botões recalculam o contraste e tons de hover automaticamente.
- **Formato Padrão de Saída**: Selecione se os documentos gerados devem ser exportados como **PDF/A-2b** (padrão de conformidade digital com validação Ghostscript) ou **PDF Convencional**.
- **Tamanho dos Quadros**: Ajuste a largura visual dos quadros principais da interface (*Pequeno*, *Médio* ou *Grande*). A alteração é refletida em tempo real no layout.
- **Perfil Ativo Padrão**: Selecione o perfil inicial a ser carregado na inicialização da aplicação.
- **Local Padrão de Assinatura**: Defina a cidade/UF padrão (ex: `CAMOCIM-CE`) pré-carregada nos formulários.

*Nota: Todas as configurações são gravadas de forma persistente no diretório `%APPDATA%\Contracto\contracto_config.json`, garantindo que suas preferências não sejam perdidas ao atualizar a versão do aplicativo.*

---

## 📁 Gerenciador de Perfis

A tela de **Perfis** permite criar e editar combinações pré-configuradas de modelos PDF, regras de geração e anexos extras:

- **Perfis Pré-configurados**: Alterne entre perfis para diferentes tipos de operações (ex: *Financiamento Imóvel Novo*, *Imóvel Usado*, *Uso de FGTS*).
- **Modelos PDF Customizados**: Adicione seus próprios formulários PDF com campos AcroForm e vincule o mapeamento de variáveis do sistema (`participante.nome_completo`, `participante.cpf_formatado`, `participante.endereco`, `participante.data_assinatura`, `participante.local_assinatura`).
- **Regras de Geração**:
  - *Por Participante*: Gera um documento individual para cada participante cadastrado na etapa 1.
  - *Documento Único*: Gera um único documento consolidado para o processo.
- **Documentos Extras**: Defina arquivos adicionais no perfil para serem convertidos ou anexados durante a Etapa 2 de organização.
- **Editor Expansível**: O painel de edição de perfis expande verticalmente para facilitar o preenchimento sem comprometer as margens de largura das configurações.

---

## ⚖️ Licença e Isenção de Responsabilidade Legal (Disclaimer)

### 1. Licenciamento de Software
Este projeto possui código aberto para colaboração, estudo e uso pessoal sob a [Licença de Código Aberto Não-Comercial](file:///c:/Users/sousa/OneDrive/Desktop/PROJETOS/Contracto/LICENSE). Colaboradores e usuários podem visualizar, testar e propor melhorias, mas é **estritamente proibida a revenda, exploração comercial ou modificação para fins comerciais** deste software (ou de versões derivadas dele) por terceiros sem a autorização prévia, expressa e por escrito do autor titular do projeto.

### 2. Isenção de Vínculo Institucional
O **Contracto** é uma ferramenta independente desenvolvida para auxílio na preparação de documentos e automação de declarações habitacionais. Este aplicativo **NÃO possui qualquer vínculo oficial, associação, patrocínio ou homologação** com nenhuma instituição financeira, governamental ou bancária pública/privada.

### 3. Isenção de Responsabilidade sobre os Dados e Documentos
- O usuário é o **único responsável** pela exatidão, veracidade e legalidade das informações digitadas e dos documentos gerados.
- O software é fornecido **"NO ESTADO EM QUE SE ENCONTRA" ("AS IS")**, sem garantias expressas ou implícitas de qualquer tipo, incluindo, mas não se limitando a, garantias de comercialização, adequação a um propósito específico ou ausência de erros.
- Os desenvolvedores e mantenedores deste projeto **não se responsabilizam** por eventuais recusas de dossiês, erros de preenchimento, divergências de datas/valores ou quaisquer danos diretos, indiretos ou incidentais decorrentes do uso desta ferramenta.

---

## 🚀 Novidades da Versão 4.1

- **Preenchimento 100% Automatizado**: Suporte completo a todos os campos AcroForm nos modelos de declaração (`NOME COMPLETO`, `CPF`, `ENDERECO`, `LOCAL ASSINATURA`, `DATA ASSINATURA`).
- **Modais Modernos e Fundo Translúcido**: Sistema de overlay translúcido nativo (`-alpha 0.60`) e cartões nítidos de alta visibilidade no topo (`-topmost`) alinhados sobre a área de conteúdo.
- **Alertas Integrados**: Substituição de mensagens nativas do Windows (`messagebox`) por componentes próprios do Contracto para finalização de etapas, confirmação de abertura de pastas e exclusão de perfis.
- **Conversão PDF/A**: Conversão automatizada de arquivos gerados e externos para PDF/A-2b exigido no dossiê digital.
- **Organização de Pastas**: O sistema cria automaticamente a estrutura hierárquica `PDF-A/` na pasta selecionada, padronizando os nomes dos arquivos com CPFs.

---

## ⬇️ Download e Atualização

### Instalação para usuários

1. Baixe a última versão (`Contracto.zip`) na página de **Releases** do GitHub.
2. Extraia o conteúdo em um local da sua preferência.
3. Rode `Contracto.exe`. O Ghostscript e os modelos já vêm embutidos!

### Como Atualizar

Sempre que houver uma versão nova, basta baixar o `.zip` atualizado e substituir os arquivos antigos. **Suas configurações (Perfis, cor de destaque, modo claro/escuro) não serão perdidas**, pois são armazenadas separadamente no seu `%APPDATA%\Contracto`.

---

## 🛠️ Tecnologias

- Python 3.12+
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) — interface gráfica moderna (Material Design 3)
- [pypdf](https://pypdf.readthedocs.io/) — leitura e preenchimento dos campos AcroForm
- [pikepdf](https://pikepdf.readthedocs.io/) — validação avançada de PDFs
- [Ghostscript](https://ghostscript.com/) — conversão para PDF/A-2b (embutido no build)
- `pywin32` — integração com a barra de tarefas do Windows e conversão local de RTF
- PyInstaller — empacotamento em executável standalone (`.exe`)

---

## 📁 Estrutura do Projeto

```
CONTRACTO/
├── LICENSE                   # Licença MIT
├── README.md                 # Documentação principal do projeto
├── CHANGELOG_v4.md           # Histórico de alterações da v4.1
├── requirements.txt          # Dependências da aplicação
├── requirements-dev.txt      # Dependências de desenvolvimento e testes
├── build_exe.bat             # Script de compilação em executável (.exe)
├── app/
│   ├── main.py                       # Ponto de entrada da aplicação
│   ├── version.py                    # Versão atual do sistema (v4.1)
│   ├── ui/                           # Componentes visuais, modais e gerenciador de temas
│   ├── models/                       # Dataclasses (Participant, Perfil, FormularioModelo)
│   ├── services/
│   │   ├── pdf_service.py            # Leitura/preenchimento genérico de AcroForm
│   │   ├── pdfa_converter.py         # Orquestração com Ghostscript
│   │   ├── rtf_converter.py          # Conversão RTF via win32com
│   │   ├── generator_service.py      # Lógica da Etapa 1
│   │   ├── stage2_service.py         # Lógica da Etapa 2
│   │   └── process_folder_service.py # Estruturação de diretórios
│   ├── utils/                        # Formatação de CPF/datas e gerenciador de config
│   └── assets/
│       ├── templates/                # PDFs modelos oficiais embutidos
│       └── gs/                       # Binários do Ghostscript empacotados
└── tests/                        # Bateria de testes unitários e de integração
```

---

## 💻 Instalação (Desenvolvimento)

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## ⚡ Como Executar

```bash
cd app
python main.py
```

## 📖 Como Usar

A aplicação é dividida em etapas fluidas.

### Etapa 1: Geração de Documentos
- O Participante 1 (principal) informa Nome, CPF, Endereço e Data da assinatura. Participantes adicionais informam apenas Nome e CPF (herdam o restante).
- Os modelos PDF e a pasta de saída são definidos aqui.

### Etapa 2: Conversão e Organização
- Após gerar os formulários, você pode arrastar documentos externos complementares (ex: Contrato original, Planilha).
- O sistema criará a hierarquia `PDF-A/` na pasta destino e converterá (se escolhido PDF/A-2b) renomeando padronizadamente.

---

## 📄 Modelos Oficiais Embutidos

Os PDFs modelos fornecidos estão em `app/assets/templates/` e são carregados automaticamente ao abrir a aplicação (`utils/resource_path.py`).

## 🗺️ Mapeamento de Campos dos PDFs

O preenchimento funciona associando cada dado do participante a um **nome de campo AcroForm** dentro do PDF modelo. Os nomes exatos dos campos foram confirmados nos modelos oficiais e estão centralizados em `app/services/generator_service.py`:

```python
# 1º Imóvel
CAMPO_PRIMEIRO_IMOVEL_NOME     = "NOME COMPLETO"
CAMPO_PRIMEIRO_IMOVEL_CPF      = "CPF"
CAMPO_PRIMEIRO_IMOVEL_ENDERECO = "ENDERECO"
CAMPO_PRIMEIRO_IMOVEL_DATA     = "DATA ASSINATURA"
CAMPO_PRIMEIRO_IMOVEL_LOCAL    = "LOCAL ASSINATURA"

# PPE
CAMPO_PPE_NOME  = "NOME COMPLETO"
CAMPO_PPE_CPF   = "CPF"
CAMPO_PPE_DIA   = "DIA"
CAMPO_PPE_MES   = "MES"
CAMPO_PPE_ANO   = "ANO"
CAMPO_PPE_LOCAL = "LOCAL ASSINATURA"
```

## 🛡️ Tratamento de Erros

Antes de gerar, o sistema valida:
- Nome, CPF (cálculo real de DV), Endereço e Data (obrigatórios)
- Data no formato real e correspondente
- Permissões de escrita na pasta de saída
- Disponibilidade do Ghostscript antes de iniciar conversões em lote

## 🧪 Testes Automatizados

Os testes rodam sem interface gráfica e incluem validação real de geração contra os PDFs nativos.

```bash
pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

## 📦 Gerando o Executável (.exe)

Basta rodar o script de build na raiz do projeto:

```cmd
build_exe.bat
```
O PyInstaller empacotará o Python, a biblioteca CustomTkinter, os PDFs modelos, os ícones 3D e os binários do Ghostscript para gerar um executável totalmente standalone (portable).
