"""Operações de arquivo da camada de interface (sem regra de negócio).

Centraliza o que antes vivia duplicado nas telas: abrir pasta no
gerenciador do sistema e preencher campo de texto somente-leitura.
"""

import os
import subprocess
from pathlib import Path

import customtkinter as ctk

from ui.theme import COLOR_BORDER, COLOR_TEXT
from utils.logger import obter_logger


def abrir_pasta(caminho: Path | str) -> bool:
    """Abre o diretório no gerenciador de arquivos; devolve False se falhar."""
    p = Path(caminho) if isinstance(caminho, str) else caminho
    if not p.exists() or not p.is_dir():
        return False
    try:
        if os.name == "nt":
            os.startfile(str(p.resolve()))
        else:
            subprocess.run(["xdg-open", str(p.resolve())], timeout=15)
    except OSError:
        obter_logger("ui").warning("Não foi possível abrir a pasta '%s'.", p)
        return False
    return True


def atualizar_entry(entry: ctk.CTkEntry, texto: str, somente_leitura: bool = False) -> None:
    """Preenche um campo de texto, travando edição quando somente leitura."""
    if somente_leitura:
        entry.configure(state="normal")
    entry.configure(text_color=COLOR_TEXT)
    entry.delete(0, "end")
    entry.insert(0, texto)
    if somente_leitura:
        entry.configure(state="disabled")
