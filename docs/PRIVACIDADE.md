# Privacidade — Contracto

> Resumo: o Contracto roda **inteiro na sua máquina**, não envia nada para
> a internet e não tem telemetria.

## 1. Arquitetura local

- Todo processamento (preenchimento, pastas, conversão PDF/A via Ghostscript
  `-dSAFER`) ocorre em memória/disco local.
- Preferências em **`%APPDATA%/Contracto/`** (`contracto_config.json`,
  perfis, `logs/app.log`) — sobrevivem a atualizações.
- Zero telemetria, zero analytics, zero chamadas externas.

## 2. O que fica gravado

- Dados digitados temporariamente em memória; PDFs gerados onde o usuário
  escolher (padrão `USERPROFILE/Downloads` configurável).
- Configurações de tema, diretórios e `formularios_basicos_selecionados`.
- Logs operacionais locais (sem PII além do necessário ao diagnóstico).

## 2.1 Leitura de documentos do cliente

- Os PDFs/RTF/DOC/DOCX anexados são lidos **localmente** (texto do PDF; sem OCR, sem IA em nuvem, sem envio).
- RTF, DOC e DOCX viram PDF numa pasta temporária privada da sessão, **apagada ao fechar o aplicativo**; os originais não são alterados.
- Os valores lidos ficam só em memória, não vão para log nem para mensagens de erro, e só entram no formulário depois da confirmação do usuário.
- Padrões de leitura, municípios do ITBI e local padrão ficam em `contracto_config.json`.

## 3. Apagar seus dados

- Para remover tudo: apague `%APPDATA%/Contracto/` e os PDFs gerados.
- Desinstalar **não apaga** `%APPDATA%/Contracto` de propósito. Apague
  manualmente se desejar (LGPD: controle total do titular).

## 4. Compartilhamento

Sem conta/nuvem: dados só saem se **você** copiar/ enviar arquivos.
Não envie dossiês com CPF/CNPJ para serviços públicos sem necessidade.
