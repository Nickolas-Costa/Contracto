"""Port de binários externos: Ghostscript + Word.

Decisão registrada (DECISIONS §5-6): Windows-only com Word por enquanto.
Este port expõe capacidades p/ o futuro shell decidir como informar falhas,
sem iniciar o Word durante a verificação.
"""

from dataclasses import dataclass
from pathlib import Path

from utils.ghostscript_setup import localizar_ghostscript


@dataclass
class BinaryStatus:
    nome: str
    caminho: Path | None
    disponivel: bool
    detalhe: str = ""


def ghostscript_status() -> BinaryStatus:
    caminho = localizar_ghostscript()
    return BinaryStatus(
        nome="ghostscript",
        caminho=caminho,
        disponivel=caminho is not None,
        detalhe="embutido assets/gs/bin ou PATH/C:/Program Files/gs" if caminho else "não encontrado",
    )


def word_status() -> BinaryStatus:
    import sys

    com_ok = False
    try:
        if sys.platform == "win32":
            import win32com.client  # noqa: F401
            import winreg

            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"Word.Application\CLSID"):
                com_ok = True
    except (ImportError, OSError):
        pass
    disponivel = com_ok
    return BinaryStatus(
        nome="word",
        caminho=None,  # a automação COM não expõe um executável estável aqui
        disponivel=disponivel,
        detalhe="Word COM registrado" if com_ok else "Word não detectado (Windows-only)",
    )
