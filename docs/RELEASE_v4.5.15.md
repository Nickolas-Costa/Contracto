# Contracto 4.5.15

Acumulado desde a 4.5.11: estabilidade, privacidade, interface e documentação.

## Privacidade e estabilidade

- CPF, CNPJ e e-mail mascarados no log, incluindo tracebacks.
- Segunda cópia do aplicativo avisa e encerra (mutex nomeado).
- Pastas com fallbacks graváveis; JSON corrompido gera cópia `.corrompido-<data>` antes do reset.
- Log com rotação (2 MB, 5 cópias) e nível resumido no executável.
- Word travado: aviso com contagem regressiva e encerramento só da instância filha.
- Build interrompe com causa explícita quando o Ghostscript está ausente.

## Interface

- `BaseModal`: esqueleto único dos 6 modais, com foco inicial, devolução de foco e tecla Escape.
- Toast preso à janela em qualquer escala, com dispensa por Escape; insígnia de aviso com contraste aprovado.
- Boas-vindas abrem só com a janela visível e texto refeito.
- Campos SIM/NÃO do DAMP como caixa de seleção; seletor de formulários sem sobreposição.
- Template DAMP atualizado (86 campos, geometria validada).

## Perfis e dados

- Importação e exportação de perfis em `.json` validado.
- Validação estrutural detalhada no editor, com rótulo e identificador.
- Backup em ZIP com data/hora e restauração validada.

## Dependências e licenças

- pypdf corrigido (6.14.2 → 6.16.1); PyMuPDF substituído por pypdfium2.
- Trava fiel (`requirements-lock.txt`) e auditoria com `pip-audit`.
- Avisos de terceiros com fonte do Ghostscript; pré-visualização sem AGPL.

## Documentação e design

- `docs/DESIGN.md` próprio (12 seções) e direção para a versão web.
- `CHANGELOG.md`, modelo de notas e serviço genérico de geometria de formulários.

## Instalação

Baixe `Contracto_v4.5.15.zip` e o `.sha256.txt` abaixo, extraia e execute.
Não requer Python instalado. Requer Windows 10/11 (64-bit) e Microsoft Word
para conversão de arquivos RTF.
