# ADR 0028 — Aposentadoria da interface Tk (CustomTkinter)

- **Estado:** aceita / implementada
- **Data:** 2026-10-28
- **Substitui:** ADR 0001 (fatiar a UI legada em mixins) e as partes de Tk das ADRs 0012 e 0019.
- **Contexto:** a UI de produção é a WebView2 desde a v4.5.18 e o `--tk` era só fallback.
  Manter ~10 mil linhas de `app/ui/` dobrava a manutenção (toda regra de formulário
  existia em Python e em JS), travava a matriz de dependências (`customtkinter`,
  `darkdetect`), inflava o pacote e impedia o contrato único UI↔shell exigido pela
  ADR 0024. O uso real confirmou a paridade (ADR 0023).
- **Decisão:** remover a interface Tk e tudo que só existia para ela.

## O que saiu

| Item | Destino |
|---|---|
| `app/ui/` (≈30 módulos: janela, telas, modais, tema, toast…) | removido |
| `app/utils/file_picker.py`, `app/utils/files.py` (`atualizar_entry`), `app/ports/dialog.py` | removidos; `ports/webview_dialog.py` e `utils/files_fs.py` já cobriam o necessário |
| `customtkinter`, `darkdetect` | removidos de `requirements*.txt`; `tkinter` excluído do bundle |
| Ícones PNG do tema Tk (`app/assets/icons/*_light/_dark`) e `scripts/process_assets.py` | removidos; ficam `app_icon.ico/.png` e `LOGO_OFICIAL_CONTRACTO.png` |
| `--tk` e `escolher_interface()` em `app/main.py` | removidos; a flag passa a ser ignorada |
| Testes e smoke de Tk (`smoke_test_gui`, `test_base_modal`, `test_toast_*`, `test_checkbox_opcoes`, `test_abrir_informa`, `test_port_dialog`, partes de `test_visual_assets`/`test_performance`/…) | removidos ou reescritos sem Tk |

O erro fatal não tratado passa a usar um `MessageBoxW` nativo (sem Tk).

## Consequências

- Uma única implementação de cada regra de formulário (a do front + a revalidação no servidor).
- Pacote menor e matriz de dependências enxuta (`Pillow` permanece: renderização de
  conferência de mapeamento em `mapping_audit.py`).
- Quem precisar do Tk antigo usa a tag `4.5.26` (último release com a interface).
- **Bump para 5.0.0**: remoção de um modo de execução e de dependências é mudança de
  arquitetura, mesmo sem alterar o fluxo do usuário final.
- Corrigido de passagem: `system_repair_service` usava COM sem `CoInitialize` na thread
  da API (o atalho nunca era recriado em produção); o teste de reparo deixou de encerrar
  Word/Ghostscript e de tocar na Área de Trabalho real.

## Aceite

`python -m unittest discover -s tests` verde sem `customtkinter` instalado;
`tests/smoke_webview.py` afirma que `tkinter` não é importado; `pip check` limpo; build
do `.exe` e instalador sem `tkinter` no bundle.
