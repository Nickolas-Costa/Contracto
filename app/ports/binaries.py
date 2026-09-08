"""Port de binários externos: Ghostscript + Word/LibreOffice.

Decisão registrada (DECISIONS §5-6): Windows-only com Word por enquanto.
Este port expõe capabilities p/ o futuro shell decidir (sidecar vs erro
amigável), sem espalhar `shutil.which` / `Program Files` pelo código.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class BinaryStatus:
    nome: str
    caminho: Path | None
    disponivel: bool
    detalhe: str = ""


def ghostscript_status() -> BinaryStatus:
    from utils.ghostscript_setup import localizar_ghostscript

    caminho = localizar_ghostscript()
    return BinaryStatus(
        nome="ghostscript",
        caminho=caminho,
        disponivel=caminho is not None,
        detalhe="embutido assets/gs/bin ou PATH/C:/Program Files/gs" if caminho else "não encontrado",
    )


def word_status() -> BinaryStatus:
    import shutil

    soffice = shutil.which("soffice")
    try:
        import win32com.client  # noqa: F401

        com_ok = True
    except Exception:
        com_ok = False
    disponivel = com_ok  # Word COM; LibreOffice ainda só fallback documentado
    return BinaryStatus(
        nome="word",
        caminho=Path(soffice) if soffice else None,
        disponivel=disponivel,
        detalhe="Word COM disponível" if com_ok else "Word não detectado (Windows-only)",
    )
