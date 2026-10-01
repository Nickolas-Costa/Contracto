"""Implementação de seleção nativa para uma janela pywebview (sem Tk)."""
from pathlib import Path
import os


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

    def selecionar_backup(self):
        from webview import FileDialog
        values = self._window.create_file_dialog(
            FileDialog.OPEN, allow_multiple=False,
            file_types=("Backup Contracto (*.zip)",),
        )
        return Path(values[0]) if values else None

    def selecionar_json(self):
        """Abre um arquivo .json (importação de perfil)."""
        from webview import FileDialog
        values = self._window.create_file_dialog(
            FileDialog.OPEN, allow_multiple=False,
            file_types=("Perfil Contracto (*.json)",),
        )
        return Path(values[0]) if values else None

    def salvar_json(self, nome_inicial="perfil.json"):
        """Destino .json para exportação de perfil."""
        from webview import FileDialog
        seguro = "".join(c for c in Path(nome_inicial).name if c not in '<>:"/\\|?*') or "perfil.json"
        if not seguro.lower().endswith(".json"):
            seguro += ".json"
        downloads = Path(os.path.expanduser("~/Downloads"))
        values = self._window.create_file_dialog(
            FileDialog.SAVE, save_filename=seguro,
            file_types=("Perfil Contracto (*.json)",), directory=str(downloads)
        )
        return Path(values[0]) if values else None

    def selecionar_documentos(self):
        """Multi-seleção para o modo Conversão (PDF, RTF, DOC, DOCX)."""
        from webview import FileDialog
        values = self._window.create_file_dialog(
            FileDialog.OPEN, allow_multiple=True,
            file_types=("Documentos (*.pdf;*.rtf;*.doc;*.docx)",),
        )
        return [Path(v) for v in values] if values else []

    def selecionar_pasta(self):
        from webview import FileDialog
        # Default to Downloads folder
        downloads = Path(os.path.expanduser("~/Downloads"))
        values = self._window.create_file_dialog(
            FileDialog.FOLDER, directory=str(downloads)
        )
        return Path(values[0]) if values else None

    def salvar_arquivo(self, nome_inicial="documento.pdf"):
        from webview import FileDialog
        downloads = Path(os.path.expanduser("~/Downloads"))
        values = self._window.create_file_dialog(
            FileDialog.SAVE, save_filename=Path(nome_inicial).name,
            file_types=("PDF (*.pdf)",), directory=str(downloads)
        )
        return Path(values[0]) if values else None
