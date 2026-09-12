"""Ponte fina da interface (conhece widgets, sem regra de negócio).

- `abrir_pasta`: reexportado de `files_fs` (puro, headless).
- `atualizar_entry`: único ponto que toca em widget.
"""

import customtkinter as ctk

from ui.theme import COLOR_TEXT
from utils.files_fs import abrir_pasta

__all__ = ["abrir_pasta", "atualizar_entry"]


def atualizar_entry(entry: ctk.CTkEntry, texto: str, somente_leitura: bool = False) -> None:
    """Preenche um campo de texto, travando edição quando somente leitura."""
    if somente_leitura:
        entry.configure(state="normal")
    entry.configure(text_color=COLOR_TEXT)
    entry.delete(0, "end")
    entry.insert(0, texto)
    if somente_leitura:
        entry.configure(state="disabled")
