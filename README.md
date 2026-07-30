# Gerador de Declarações — Contratos Habitacionais CAIXA

Aplicativo desktop (Windows) em Python para preencher automaticamente os PDFs e gerenciar a organização e conformidade de:

- **Declaração de Pessoa Politicamente Exposta (PPE)**
- **Declaração de Primeiro Imóvel**

usados em contratos de financiamento habitacional da Caixa Econômica Federal.

A **Versão 2.0** introduz a estruturação automática de pastas, conversão em lote para **PDF/A-2b** via Ghostscript (garantindo a conformidade digital), e um novo sistema de Perfis e Temas. Os dados dos participantes são digitados manualmente e o sistema gera os PDFs preenchidos e organizados.

Os PDFs oficiais da CAIXA (`PPE.pdf` e `1_IMOVEL.pdf`) já vêm embutidos na aplicação como modelos padrão — o usuário não precisa selecioná-los manualmente (ver [Modelos oficiais embutidos](#modelos-oficiais-embutidos)).

---

## Sumário

- [Novidades da Versão 2.0](#novidades-da-versão-20)
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

## Novidades da Versão 2.0

- **Conversão PDF/A**: Conversão automatizada de arquivos gerados (e externos, como planilhas e contratos) para PDF/A-2b exigido no dossiê digital.
- **Organização de Pastas**: O sistema cria automaticamente a estrutura hierárquica `PDF-A/ASSINADOS` e `PDF-A/REGISTRADOS` na pasta selecionada, padronizando os nomes dos arquivos com CPFs.
- **Perfis**: É possível cadastrar perfis combinando diferentes modelos PDF e formatos de saída (PDF comum ou PDF/A).
- **Temas e Configurações**: Interface gráfica modernizada (Material Design 3) com gradiente institucional. Preferências como Dark Mode e cores ficam salvas em `%APPDATA%\Contracto`.

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
- `pywin32` — conversão local de RTF para PDF
- `pathlib` / `tkinter.filedialog` — biblioteca padrão do Python
- PyInstaller — empacotamento em `.exe`

Nenhuma dependência do Microsoft Word é necessária para o preenchimento (embora o Word seja usado silenciosamente em background caso adicione arquivos `.rtf` na etapa de organização).

---

## Estrutura do projeto

```
CONTRACTO/
├── README.md
├── Contracto/
    ├── requirements.txt          # dependências da aplicação
    ├── requirements-dev.txt      # + dependências usadas apenas pelos testes
    ├── build_exe.bat             # script de geração do executável
    ├── app/
    │   ├── main.py                       # ponto de entrada
    │   ├── ui/                           # componentes visuais e temas
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
    └── tests/                        # 70+ testes unitários e de integração
```

---

## Instalação (Desenvolvimento)

```bash
cd Contracto
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

Os PDFs reais fornecidos pela CAIXA estão em `app/assets/templates/` e são carregados automaticamente ao abrir a aplicação (`utils/resource_path.py`). Se algum dia a CAIXA emitir uma nova versão desses formulários, basta substituir os arquivos nessa pasta — nenhum código precisa mudar, desde que os nomes dos campos internos continuem os mesmos.

## Mapeamento dos campos do PDF

O preenchimento funciona associando cada dado do participante a um **nome de campo AcroForm** dentro do PDF modelo. Os nomes abaixo foram **confirmados diretamente nos PDFs reais** e estão centralizados em `app/services/generator_service.py`:

```python
CAMPO_PRIMEIRO_IMOVEL_NOME     = "NOME COMPLETO"
CAMPO_PRIMEIRO_IMOVEL_CPF      = "CPF"
CAMPO_PRIMEIRO_IMOVEL_ENDERECO = "ENDEREÇO"
CAMPO_PRIMEIRO_IMOVEL_DATA     = "DATA"

CAMPO_PPE_NOME = "NOME COMPLETO"
CAMPO_PPE_CPF  = "CPF"
CAMPO_PPE_DIA  = "DIA"
CAMPO_PPE_MES  = "MES"   # sem acento
CAMPO_PPE_ANO  = "ANO"
```

Para descobrir nomes exatos dos campos de um novo PDF específico, rode:

```bash
# dentro da pasta app/
python -c "from services.pdf_service import obter_campos_do_formulario; from pathlib import Path; print(obter_campos_do_formulario(Path('caminho/do/modelo.pdf')))"
```

Como rede de proteção, o sistema avisa caso o modelo escolhido falte campos.

## Tratamento de erros

Antes de gerar, o sistema valida:
- Nome, CPF (cálculo real de DV), Endereço e Data (obrigatórios)
- Data no formato real e correspondente
- Permissões de escrita na pasta de saída
- Disponibilidade do Ghostscript antes de iniciar conversões massivas em lote

## Testes automatizados

Os testes rodam sem interface gráfica e incluem validação real de geração contra os PDFs nativos. Se a CAIXA atualizar os modelos e algum nome de campo mudar, o `test_modelos_oficiais.py` apontará a falha imediatamente.

```bash
pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

## Gerando o executável (.exe)

Basta rodar o arquivo bat de build na raiz de `Contracto/`:

```cmd
build_exe.bat
```
O PyInstaller empacotará o Python, a biblioteca CustomTkinter, os PDFs oficiais, e até os binários do Ghostscript para gerar um executável totalmente standalone (portable).

## Arquitetura e decisões de design

- **Baixo acoplamento**: `ui/` só conhece `models/` e chama funções de `services/`.
- **Preenchimento Genérico**: `pdf_service.py` não sabe o que é "PPE", ele preenche dicionários de campos em AcroForms, o que permite o uso por qualquer outra declaração no futuro.
- **Configuração Desacoplada**: A V2 desacopla todas as configurações (`settings_frame.py` e `profiles_frame.py`) gravando-as no `%APPDATA%`, o que garante persistência entre updates.
- **Nomes de arquivo sanitizados** para caracteres inválidos no Windows e lógica de fallback.
