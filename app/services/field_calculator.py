"""Executa cálculos simples configurados nos campos dos perfis."""

import re
from decimal import Decimal, InvalidOperation


_TERMO = re.compile(r"([+-]?)\s*([A-Za-z_][A-Za-z0-9_]*)")


def _numero(valor: str) -> Decimal:
    texto = str(valor or "").replace("R$", "").replace(" ", "")
    if not texto:
        return Decimal("0")
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    try:
        return Decimal(texto)
    except InvalidOperation:
        return Decimal("0")


def validar_calculo(expressao: str) -> bool:
    """Aceita somente nomes de campos ligados por + ou -."""
    texto = str(expressao or "").strip()
    if not texto:
        return True
    posicao = 0
    termos = 0
    for resultado in _TERMO.finditer(texto):
        if texto[posicao:resultado.start()].strip():
            return False
        if termos == 0 and resultado.group(1) == "-":
            return False
        posicao = resultado.end()
        termos += 1
    return termos > 0 and not texto[posicao:].strip()


def calcular(expressao: str, valores: dict[str, str]) -> str:
    """Calcula uma expressão válida e retorna moeda sem o símbolo R$."""
    if not validar_calculo(expressao):
        return ""
    total = Decimal("0")
    for indice, resultado in enumerate(_TERMO.finditer(expressao)):
        sinal, campo = resultado.groups()
        numero = _numero(valores.get(campo, ""))
        if indice and sinal == "-":
            total -= numero
        else:
            total += numero
    total = max(Decimal("0"), total)
    return f"{total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
