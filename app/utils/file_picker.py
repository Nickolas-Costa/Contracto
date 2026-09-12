"""
Utilitário responsável exclusivamente por abrir os diálogos nativos do
sistema operacional para seleção de arquivos e pastas.

Implementação Tk da interface `ports/dialog.py`: quando o shell mudar
(pywebview/Tauri), só este arquivo sai de cena — os chamadores usam o port.
"""

from pathlib import Path
from tkinter import filedialog

TIPOS_PDF = [("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")]
TIPOS_PDF_RTF = [("Arquivos PDF e RTF", "*.pdf;*.rtf"), ("Todos os arquivos", "*.*")]


def selecionar_arquivo(
    titulo: str = "Selecione um arquivo",
    tipos: list[tuple[str, str]] | None = None,
) -> Path | None:
    """Abre o explorador para selecionar um arquivo existente."""
    caminho = filedialog.askopenfilename(
        title=titulo, filetypes=tipos or TIPOS_PDF,
    )
    return Path(caminho) if caminho else None


def salvar_arquivo(
    titulo: str = "Salvar arquivo",
    nome_inicial: str = "",
    tipos: list[tuple[str, str]] | None = None,
    extensao_padrao: str = "",
) -> Path | None:
    """Abre o explorador para escolher onde salvar (não cria o arquivo)."""
    caminho = filedialog.asksaveasfilename(
        title=titulo,
        defaultextension=extensao_padrao,
        filetypes=tipos or TIPOS_PDF,
        initialfile=nome_inicial,
    )
    return Path(caminho) if caminho else None


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
