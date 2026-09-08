"""
Utilitário para localizar arquivos de recursos (assets) que acompanham a
aplicação — em especial, os modelos PDF oficiais que já vêm prontos junto
com o programa.

Funciona tanto ao rodar via `python main.py` quanto quando empacotado em um
executável com PyInstaller (`--onefile` ou `--onedir`), onde os arquivos de
dados precisam ser localizados de forma diferente (`sys._MEIPASS`).
"""

import json
import sys
from functools import lru_cache
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


@lru_cache(maxsize=1)
def carregar_configuracao_inicial() -> dict:
    """Lê uma vez a configuração que acompanha o aplicativo."""
    caminho = caminho_recurso("assets", "config", "perfis_iniciais.json")
    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (OSError, json.JSONDecodeError, TypeError):
        return {}


def modelo_configurado(chave: str) -> Path | None:
    """Localiza um modelo informado na configuração que acompanha o aplicativo."""
    if not chave:
        return None
    caminho_relativo = (carregar_configuracao_inicial().get("modelos") or {}).get(chave, "")
    if not caminho_relativo:
        return None
    caminho = caminho_recurso("assets", "templates", *Path(caminho_relativo).parts)
    return caminho if caminho.exists() else None


def mapeamento_configurado(chave: str) -> dict:
    """Lê o mapeamento inicial de um modelo."""
    if not chave:
        return {}
    return (carregar_configuracao_inicial().get("mapeamentos") or {}).get(chave, {}).copy()


def listar_modelos_configurados() -> list[Path]:
    """Retorna os modelos que acompanham o aplicativo."""
    chaves = list((carregar_configuracao_inicial().get("modelos") or {}).keys())
    return [caminho for chave in chaves if (caminho := modelo_configurado(chave)) is not None]
