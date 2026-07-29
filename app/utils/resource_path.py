"""
Utilitário para localizar arquivos de recursos (assets) que acompanham a
aplicação — em especial, os modelos PDF oficiais que já vêm prontos junto
com o programa.

Funciona tanto ao rodar via `python main.py` quanto quando empacotado em um
executável com PyInstaller (`--onefile` ou `--onedir`), onde os arquivos de
dados precisam ser localizados de forma diferente (`sys._MEIPASS`).
"""

import sys
from pathlib import Path


def caminho_recurso(*partes: str) -> Path:
    """Retorna o caminho absoluto de um recurso dentro da pasta `app/`.

    Em desenvolvimento, resolve relativo à pasta `app/` (onde está `main.py`).
    Quando empacotado com PyInstaller, resolve relativo à pasta temporária de
    extração criada em tempo de execução.
    """
    base = getattr(sys, "_MEIPASS", None)
    base_path = Path(base) if base else Path(__file__).resolve().parent.parent
    return base_path.joinpath(*partes)


def modelo_padrao_ppe() -> Path | None:
    """Caminho do modelo oficial da Declaração PPE incluído com a aplicação.

    Retorna None se o arquivo não estiver presente (o usuário precisará
    selecionar um manualmente).
    """
    caminho = caminho_recurso("assets", "templates", "PPE.pdf")
    return caminho if caminho.exists() else None


def modelo_padrao_primeiro_imovel() -> Path | None:
    """Caminho do modelo oficial da Declaração de Primeiro Imóvel incluído
    com a aplicação.

    Retorna None se o arquivo não estiver presente (o usuário precisará
    selecionar um manualmente).
    """
    caminho = caminho_recurso("assets", "templates", "1 IMOVEL.pdf")
    return caminho if caminho.exists() else None
