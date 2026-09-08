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

## 3. Apagar seus dados

- Para remover tudo: apague `%APPDATA%/Contracto/` e os PDFs gerados.
- Desinstalar **não apaga** `%APPDATA%/Contracto` de propósito. Apague
  manualmente se desejar (LGPD: controle total do titular).

## 4. Compartilhamento

Sem conta/nuvem: dados só saem se **você** copiar/ enviar arquivos.
Não envie dossiês com CPF/CNPJ para serviços públicos sem necessidade.
