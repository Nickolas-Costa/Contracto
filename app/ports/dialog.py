"""Port de diálogos: isola tkinter.filedialog da regra de negócio.

Contrato (vale para qualquer shell):
- `selecionar_arquivo(titulo, tipos)` -> Path | None (None = cancelou)
- `selecionar_pasta(titulo)` -> Path | None
- `salvar_arquivo(titulo, nome_inicial, tipos, extensao_padrao)` -> Path | None

- Hoje: delega p/ utils.file_picker (Tk).
- Futuro pywebview: pywebview.open_file_dialog / save_file_dialog.
- Futuro Tauri: @tauri-apps/plugin-dialog (open/save/message).
"""

from pathlib import Path


def selecionar_arquivo(
    titulo: str = "Selecione um arquivo",
    tipos: list[tuple[str, str]] | None = None,
) -> Path | None:
    from utils.file_picker import selecionar_arquivo as _tk_abrir

    return _tk_abrir(titulo, tipos)


def selecionar_arquivo_pdf(titulo: str = "Selecione um arquivo PDF") -> Path | None:
    from utils.file_picker import selecionar_arquivo_pdf as _tk_pdf

    return _tk_pdf(titulo)


def selecionar_pasta(titulo: str = "Selecione a pasta de saída") -> Path | None:
    from utils.file_picker import selecionar_pasta as _tk_pasta

    return _tk_pasta(titulo)


def salvar_arquivo(
    titulo: str = "Salvar arquivo",
    nome_inicial: str = "",
    tipos: list[tuple[str, str]] | None = None,
    extensao_padrao: str = "",
) -> Path | None:
    from utils.file_picker import salvar_arquivo as _tk_salvar

    return _tk_salvar(titulo, nome_inicial, tipos, extensao_padrao)
