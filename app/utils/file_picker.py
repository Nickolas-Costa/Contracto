"""
Utilitário responsável exclusivamente por abrir os diálogos nativos do
sistema operacional para seleção de arquivos e pastas.

Mantido isolado da interface (ui/) para que `main_window.py` não precise
conhecer detalhes de tkinter.filedialog diretamente.
"""

from pathlib import Path
from tkinter import filedialog


def selecionar_arquivo_pdf(titulo: str = "Selecione um arquivo PDF") -> Path | None:
    """Abre o explorador de arquivos para selecionar um único PDF.

    Retorna o caminho selecionado ou None se o usuário cancelar.
    """
    caminho = filedialog.askopenfilename(
        title=titulo,
        filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")],
    )
    return Path(caminho) if caminho else None


def selecionar_pasta(titulo: str = "Selecione a pasta de saída") -> Path | None:
    """Abre o explorador de arquivos para selecionar uma pasta.

    Retorna o caminho selecionado ou None se o usuário cancelar.
    """
    caminho = filedialog.askdirectory(title=titulo)
    return Path(caminho) if caminho else None
