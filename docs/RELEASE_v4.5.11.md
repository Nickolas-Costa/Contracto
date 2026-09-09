# Contracto 4.5.11

Versão de manutenção da série 4.5.x, com correções de privacidade, estabilidade
e build. Recomendada sobre as anteriores.

## Privacidade e estabilidade

- CPF, CNPJ e e-mail passaram a ser mascarados no arquivo de log, inclusive em tracebacks.
- O aplicativo não abre duas vezes: a segunda tentativa exibe um aviso e encerra.
- Configurações e perfis ilegíveis geram uma cópia de segurança com data antes de serem restaurados.
- O log agora tem rotação automática e registra menos detalhe no executável.
- Se o Word travar durante uma conversão, um aviso com contagem regressiva permite fechar de imediato; esgotado o prazo, somente a instância criada pelo aplicativo é encerrada.

## Build e dependências

- Sem Ghostscript, o build interrompe com a causa explícita (antes gerava um executável sem o motor de PDF/A).
- pypdf atualizado para correção de vulnerabilidades conhecidas; dependências com trava fiel (`requirements-lock.txt`).
- Pacote distribuído com verificação SHA-256.

## Interface

- Modais unificados em uma base comum, com foco inicial, devolução de foco e tecla Escape.
- Corrigida falha ao exibir alertas sem lista de erros.

## Instalação

Baixe `Contracto_v4.5.11.zip` e o `.sha256.txt` abaixo, extraia e execute.
Não requer Python instalado. Requer Windows 10/11 (64-bit) e Microsoft Word
para conversão de arquivos RTF.
