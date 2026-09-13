"""Implementação de seleção nativa para uma janela pywebview (sem Tk)."""
from pathlib import Path


class WebViewDialogs:
    def __init__(self, window):
        self._window = window

    def selecionar_arquivo(self):
        from webview import FileDialog
        values = self._window.create_file_dialog(
            FileDialog.OPEN, allow_multiple=False,
            file_types=("Documentos (*.pdf;*.rtf)",),
        )
        return Path(values[0]) if values else None

    def selecionar_pasta(self):
        from webview import FileDialog
        values = self._window.create_file_dialog(FileDialog.FOLDER)
        return Path(values[0]) if values else None

    def salvar_arquivo(self, nome_inicial="documento.pdf"):
        from webview import FileDialog
        values = self._window.create_file_dialog(
            FileDialog.SAVE, save_filename=Path(nome_inicial).name,
            file_types=("PDF (*.pdf)",),
        )
        return Path(values[0]) if values else None
