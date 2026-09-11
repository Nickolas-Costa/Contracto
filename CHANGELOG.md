# Registro de Alterações — Contracto

Formato Keep-a-Changelog. Versão corrente em `app/version.py` (+ espelho `VERSION`).
Histórico detalhado da série 4.x em `CHANGELOG_v4.md`.

## [Não lançado]

## [4.5.14] — 2026-09-11

### Adicionado
- `docs/DESIGN.md`: identidade própria (sóbrio, leve, focado) com as
  ondas como assinatura, tokens CSS e checklist por tela.
- `docs/GUIA_OPEN_DESIGN.md`: direção de design systems e prompt para
  o agente de design da versão web.

### Corrigido
- Toast preso à janela em qualquer escala, com dispensa por Escape.
- Boas-vindas abrem só com a janela visível e texto refeito.

## [4.5.13] — 2026-09-10

### Alterado
- Campos SIM/NÃO do DAMP viraram caixa de seleção (checkbox preserva os
  valores SIM/NÃO das regras); checkbox aceita par de opções configurável.

## [4.5.12] — 2026-09-09

### Corrigido
- Pré-visualização de mapeamento sem PyMuPDF (pypdfium2, licença permissiva).
- Avisos de terceiros com fonte do Ghostscript e seção de terceiros no README.

### Adicionado
- Serviço genérico de geometria de formulários: auditoria (área zerada,
  fora da página, sobreposição) e correções declarativas por modelo via
  `geometria_modelos.json` (`scripts/corrigir_geometria.py`); script
  específico do DAMP removido.

## [4.5.11] — 2026-09-09

### Corrigido
- Mascaramento de CPF, CNPJ e e-mail no log, incluindo tracebacks.
- Segunda cópia do aplicativo agora avisa e encerra (mutex nomeado).
- Pastas com fallbacks graváveis; JSON corrompido gera cópia `.corrompido-<data>` antes do reset.
- Log com rotação (2 MB, 5 cópias) e nível resumido no executável.
- Word travado: aviso com contagem regressiva e encerramento só da instância filha.
- Build interrompe com causa explícita quando o Ghostscript está ausente.
- `AlertModal` aceita lista de erros opcional (corrige crash em chamadas sem lista).
- Seis vulnerabilidades conhecidas no pypdf corrigidas (6.14.2 → 6.16.1).

### Adicionado
- `BaseModal`: esqueleto único dos 6 modais, com foco inicial, devolução de foco e tecla Escape.
- Trava fiel de dependências (`requirements-lock.txt`) e auditoria com `pip-audit`.
- `THIRD_PARTY_NOTICES.md`, este registro e modelo de notas de release.

## [4.5.10] — 2026-09-08

Versão estável: paginação fixa, quadros que se ocultam, contador de pendências,
seleção por identificador, correções aplicadas a perfis, limites de segurança
para PDFs e pacote com verificação SHA-256.

## [4.5.9] — 2026-09-08

Multi-seleção de formulários no modo simples e documentação base (`docs/`).
