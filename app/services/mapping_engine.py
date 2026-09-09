"""Aplica as regras de preenchimento salvas em cada perfil."""

from collections.abc import Callable
from typing import Any

from utils.cpf_validator import CpfInvalidoError, formatar_cpf
from utils.date_formatter import DataInvalidaError, formatar_data_completa_por_extenso
from utils.pis_pasep_validator import formatar_pis_pasep


def _normalizar(valor: Any) -> str:
    return str(valor if valor is not None else "").strip()


def _condicoes_atendidas(
    alternativas: list[dict[str, list[str]]],
    resolver: Callable[[str], str],
) -> bool:
    if not alternativas:
        return True
    return any(
        all(_normalizar(resolver(origem)) in [_normalizar(v) for v in aceitos]
            for origem, aceitos in alternativa.items())
        for alternativa in alternativas
    )


def _aplicar_formato(valor: str, formato: str) -> str:
    formato = (formato or "TEXTO").upper()
    if formato == "CPF":
        try:
            return formatar_cpf(valor) if valor else ""
        except CpfInvalidoError:
            return valor
    if formato == "PIS_PASEP":
        return formatar_pis_pasep(valor)
    if formato == "DATA_EXTENSO":
        try:
            return formatar_data_completa_por_extenso(valor)
        except DataInvalidaError:
            return ""
    if formato == "MOEDA_SEM_SIMBOLO":
        return valor.replace("R$", "").strip()
    if formato == "MAIUSCULAS":
        return valor.upper()
    return valor


def resolver_especificacao(especificacao: str | dict[str, Any], resolver: Callable[[str], str]) -> str:
    """Resolve mapeamentos legados ou uma regra declarativa serializável em JSON.

    Regras suportam ``origem``, ``formato``, ``condicoes`` (OR de grupos AND),
    ``valor_verdadeiro``, ``valor_falso``, ``constante`` e ``valor_padrao``.
    """
    if isinstance(especificacao, str):
        return _normalizar(resolver(especificacao))
    if not isinstance(especificacao, dict):
        return ""

    condicoes = especificacao.get("condicoes", []) or []
    atende = _condicoes_atendidas(condicoes, resolver)
    if condicoes and not atende:
        return _normalizar(especificacao.get("valor_falso", ""))
    if condicoes and "valor_verdadeiro" in especificacao:
        return _normalizar(especificacao.get("valor_verdadeiro", ""))
    if "constante" in especificacao:
        return _normalizar(especificacao.get("constante", ""))

    origem = _normalizar(especificacao.get("origem", ""))
    valor = _normalizar(resolver(origem)) if origem else ""
    if not valor:
        valor = _normalizar(especificacao.get("valor_padrao", ""))
    return _aplicar_formato(valor, _normalizar(especificacao.get("formato", "TEXTO")))
