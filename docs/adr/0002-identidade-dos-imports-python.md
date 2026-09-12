# ADR 0002 — Identidade canônica dos módulos Python

- **Estado:** aceita
- **Data:** 2026-09-12
- **Contexto:** o mesmo código é importável como `app.*` a partir da raiz ou com nomes curtos a partir de `app/`. Importar `app.utils.file_picker` e `utils.file_picker` no mesmo processo cria dois objetos de módulo. Isso separa mocks e estado em memória: o port de diálogos abria uma janela real durante o teste de cancelamento, que então ficava bloqueado.
- **Decisão:** dentro dos ports atuais, usar os imports curtos de `utils` como identidade canônica. O bootstrap de `app/__init__.py` adiciona `app/` ao caminho de módulos quando o pacote `app.*` é importado, de modo que os mesmos ports funcionam nos dois pontos de entrada. O import da implementação Tk no port de diálogos continua tardio para preservar o carregamento headless.
- **Alternativas consideradas:** preferir `app.utils` com fallback para `utils` (mantém módulos duplicados no processo); converter todos os imports internos para `app.*` de uma vez (mudança ampla antes da migração de shell).
- **Consequências:** os ports passam a compartilhar o estado de `utils` com o restante da aplicação e os mocks alcançam a implementação chamada. A coexistência dos dois estilos de import permanece temporária; novos módulos devem evitar carregar o mesmo arquivo sob dois nomes. Testes do port e da prova headless validam o comportamento.
- **Arquivos:** `app/ports/dialog.py`, `app/ports/storage.py`, `app/ports/binaries.py`, `tests/test_port_dialog.py`, `tests/test_headless_backend.py`.
