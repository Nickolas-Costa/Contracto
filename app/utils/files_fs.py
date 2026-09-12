"""Operações de arquivo puras (sem interface): abrir pasta no gerenciador.

Importável sem tkinter — pronto para endpoints e testes headless.
"""

import os
import subprocess
from pathlib import Path

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
