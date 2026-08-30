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


def modelo_padrao_form_cliente() -> Path | None:
    """Caminho do modelo oficial do Form Cliente Crédito Imobiliário (FORM CLIENTE.pdf)."""
    caminho = caminho_recurso("assets", "templates", "FORM CLIENTE.pdf")
    if caminho.exists():
        return caminho
    caminho_legado = caminho_recurso("assets", "templates", "MO30844011 (PREENCHIVEL).pdf")
    return caminho_legado if caminho_legado.exists() else None


def modelo_padrao_formulario_caixa() -> Path | None:
    """Alias para compatibilidade com modelo_padrao_form_cliente."""
    return modelo_padrao_form_cliente()


def modelo_padrao_itbi() -> Path | None:
    """Caminho do modelo oficial da Declaração para Pagamento do ITBI."""
    caminho = caminho_recurso("assets", "templates", "DECLARACAO PARA PAGAMENTO DO ITBI.pdf")
    return caminho if caminho.exists() else None


def modelo_padrao_isencao_tributos() -> Path | None:
    """Caminho do modelo oficial do Requerimento de Isenção de Tributos Municipais."""
    caminho = caminho_recurso("assets", "templates", "REQUERIMENTO ISENÇÃO DE TRIBUTOS MUNICIPAIS.pdf")
    return caminho if caminho.exists() else None
