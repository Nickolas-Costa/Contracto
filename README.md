# Gerador de Declarações — Contratos Habitacionais CAIXA

Aplicativo desktop (Windows) em Python para preencher automaticamente os PDFs e gerenciar a organização e conformidade de:

- **Declaração de Pessoa Politicamente Exposta (PPE)**
- **Declaração de Primeiro Imóvel**

usados em contratos de financiamento habitacional da Caixa Econômica Federal.

A **Versão 4.1** introduz o preenchimento 100% automatizado de todos os campos AcroForm (incluindo endereços e datas de assinatura), modais visuais modernos com efeito escuro translúcido (`-alpha 0.60`), substituição completa de alertas nativos do Windows por componentes do app, expansão dinâmica do editor de perfis e suporte nativo ao ícone 3D na barra de tarefas.

Os PDFs oficiais da CAIXA (`PPE.pdf` e `1_IMOVEL.pdf`) já vêm embutidos na aplicação como modelos padrão — o usuário não precisa selecioná-los manualmente (ver [Modelos oficiais embutidos](#modelos-oficiais-embutidos)).

---

## Sumário

- [Novidades da Versão 4.1](#novidades-da-versão-41)
- [Download e Atualização](#download-e-atualização)
- [Tecnologias](#tecnologias)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Instalação](#instalação)
- [Como executar](#como-executar)
- [Como usar](#como-usar)
- [Modelos oficiais embutidos](#modelos-oficiais-embutidos)
- [Mapeamento dos campos do PDF](#mapeamento-dos-campos-do-pdf)
- [Tratamento de erros](#tratamento-de-erros)
- [Testes automatizados](#testes-automatizados)
- [Gerando o executável (.exe)](#gerando-o-executável-exe)
- [Arquitetura e decisões de design](#arquitetura-e-decisões-de-design)

---

## Novidades da Versão 4.1

- **Preenchimento Completo de Formulários**: Suporte a 100% dos campos AcroForm nos PDFs da CAIXA (`NOME COMPLETO`, `CPF`, `ENDERECO`, `LOCAL ASSINATURA`, `DATA ASSINATURA`).
- **Modais Modernos e Fundo Translúcido**: Sistema de overlay translúcido nativo (`-alpha 0.60`) e cartões nítidos de alta visibilidade no topo (`-topmost`) centralizados na tela.
- **Alertas Próprios e Integrados**: Substituição de mensagens nativas do Windows (`messagebox`) por modais elegantes do Contracto para finalização de etapas, confirmação de abertura de pastas e exclusão de perfis.
- **Conversão PDF/A**: Conversão automatizada de arquivos gerados e externos para PDF/A-2b exigido no dossiê digital.
- **Organização de Pastas**: O sistema cria automaticamente a estrutura hierárquica `PDF-A/` na pasta selecionada, padronizando os nomes dos arquivos com CPFs.
- **Perfis e Temas**: Cadastro de perfis customizados, suporte ao Dark Mode e sincronização dinâmica de cores em `%APPDATA%\Contracto`.

---

## Download e Atualização

### Instalação para usuários

1. Baixe a última versão (`Contracto.zip`) na página de **Releases** do GitHub.
2. Extraia o conteúdo em um local da sua preferência.
3. Rode `Contracto.exe`. O Ghostscript e os modelos já vêm embutidos!

### Como Atualizar

Sempre que houver uma versão nova, basta baixar o `.zip` atualizado e substituir os arquivos antigos. **Suas configurações (Perfis, cor de destaque, modo claro/escuro) não serão perdidas**, pois são armazenadas separadamente no seu `%APPDATA%`.

---

## Tecnologias

- Python 3.12+
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) — interface gráfica moderna
- [pypdf](https://pypdf.readthedocs.io/) — leitura e preenchimento dos campos AcroForm
- [pikepdf](https://pikepdf.readthedocs.io/) — validação avançada
- [Ghostscript](https://ghostscript.com/) — conversão para PDF/A-2b (embutido no build)
- `pywin32` — suporte nativo à barra de tarefas do Windows e conversão local
- PyInstaller — empacotamento em `.exe`

---

## Estrutura do projeto

```
CONTRACTO/
├── README.md
├── CHANGELOG_v4.md
├── requirements.txt          # dependências da aplicação
├── requirements-dev.txt      # + dependências usadas apenas pelos testes
├── build_exe.bat             # script de geração do executável
├── app/
│   ├── main.py                       # ponto de entrada
│   ├── version.py                    # versão atual da aplicação (v4.1)
│   ├── ui/                           # componentes visuais, modais e temas
│   ├── models/                       # dataclasses
│   ├── services/
│   │   ├── pdf_service.py            # leitura/preenchimento genérico de AcroForm
│   │   ├── pdfa_converter.py         # orquestração com Ghostscript
│   │   ├── rtf_converter.py          # converte rtf via win32com
│   │   ├── generator_service.py      # lógica da Etapa 1
│   │   ├── stage2_service.py         # lógica da Etapa 2
│   │   └── process_folder_service.py # estruturação de diretórios
│   ├── utils/                        # formatação, validação e config em %APPDATA%
│   └── assets/
│       ├── templates/                # PDFs oficiais embutidos
│       └── gs/                       # dependências do Ghostscript empacotadas
└── tests/                        # testes unitários e de integração
```

---

## Instalação (Desenvolvimento)

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## Como executar

```bash
cd app
python main.py
```

## Como usar

A aplicação é dividida em etapas.

### 1. Geração de Documentos
- O Participante 1 (principal) informa Nome, CPF, Endereço e Data da assinatura. Participantes adicionais informam apenas Nome e CPF (herdam o restante).
- Os modelos PDF oficiais e a pasta de saída são definidos aqui.

### 2. Conversão e Organização
- Após gerar os formulários, você pode arrastar documentos externos complementares (ex: Contrato original, Planilha).
- O sistema criará a hierarquia `PDF-A/` na pasta destino e converterá (se escolhido PDF/A-2b) renomeando padronizadamente.

---

## Modelos oficiais embutidos

Os PDFs reais fornecidos pela CAIXA estão em `app/assets/templates/` e são carregados automaticamente ao abrir a aplicação (`utils/resource_path.py`).

## Mapeamento dos campos do PDF

O preenchimento funciona associando cada dado do participante a um **nome de campo AcroForm** dentro do PDF modelo. Os nomes exatos dos campos foram confirmados nos modelos oficiais da CAIXA e estão centralizados em `app/services/generator_service.py`:

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

## Tratamento de erros

Antes de gerar, o sistema valida:
- Nome, CPF (cálculo real de DV), Endereço e Data (obrigatórios)
- Data no formato real e correspondente
- Permissões de escrita na pasta de saída
- Disponibilidade do Ghostscript antes de iniciar conversões em lote

## Testes automatizados

Os testes rodam sem interface gráfica e incluem validação real de geração contra os PDFs nativos.

```bash
pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

## Gerando o executável (.exe)

Basta rodar o arquivo bat de build na raiz do projeto:

```cmd
build_exe.bat
```
O PyInstaller empacotará o Python, a biblioteca CustomTkinter, os PDFs oficiais, os ícones 3D e os binários do Ghostscript para gerar um executável totalmente standalone (portable).
