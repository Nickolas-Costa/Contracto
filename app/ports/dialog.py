"""Port de diálogos: isola tkinter.filedialog da regra de negócio.

- Hoje: delega p/ utils.file_picker (Tk).
- Futuro pywebview: pywebview.open_file_dialog / save_file_dialog.
- Futuro Tauri: @tauri-apps/plugin-dialog (open/save/message).
"""

from pathlib import Path


def selecionar_arquivo_pdf(titulo: str = "Selecione um arquivo PDF") -> Path | None:
    from utils.file_picker import selecionar_arquivo_pdf as _tk_pdf

    return _tk_pdf(titulo)


def selecionar_pasta(titulo: str = "Selecione a pasta de saída") -> Path | None:
    from utils.file_picker import selecionar_pasta as _tk_pasta

    return _tk_pasta(titulo)
