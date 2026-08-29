"""
Utilitário para validação e formatação de CNPJ (Cadastro Nacional da Pessoa Jurídica).

Suporta:
1. CNPJ Numérico Tradicional (14 dígitos).
2. Novo CNPJ Alfanumérico (Instrução Normativa RFB nº 2.229/2024 da Receita Federal):
   - 12 primeiros caracteres alfanuméricos (letras A-Z e números 0-9).
   - 2 últimos caracteres numéricos correspondentes aos Dígitos Verificadores (DV).
   - Cálculo via Módulo 11 utilizando valores da tabela ASCII (ord(c) - 48).
"""

import re

_PESOS_DV1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
_PESOS_DV2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]


class CnpjInvalidoError(ValueError):
    """Levantada quando um CNPJ é inválido."""


def limpar_cnpj(cnpj_str: str) -> str:
    """Remove pontuações (. / - e espaços) e retorna os caracteres alfanuméricos em MAIÚSCULAS."""
    if not cnpj_str:
        return ""
    # Manter apenas letras e dígitos
    return re.sub(r"[^A-Za-z0-9]", "", cnpj_str).upper()


def _valor_caractere_cnpj(c: str) -> int:
    """Converte um caractere do CNPJ para o valor numérico oficial da Receita Federal (ASCII - 48).
    
    Exemplos:
        '0'..'9' -> 0..9 (48..57 - 48)
        'A'..'Z' -> 17..42 (65..90 - 48)
    """
    return ord(c) - 48


def validar_cnpj(cnpj_str: str) -> bool:
    """Valida um CNPJ numérico ou alfanumérico segundo as regras oficiais da Receita Federal.

    Args:
        cnpj_str: string contendo o CNPJ formatado ou não.

    Returns:
        True se o CNPJ for matematicamente válido, False caso contrário.
    """
    caracteres = limpar_cnpj(cnpj_str)

    if len(caracteres) != 14:
        return False

    # CNPJs puramente numéricos com todos os dígitos iguais são inválidos
    if caracteres.isdigit() and len(set(caracteres)) == 1:
        return False

    # Os 12 primeiros caracteres podem ser alfanuméricos (A-Z, 0-9)
    # Os 2 últimos caracteres (DVs) DEVEM ser estritamente numéricos (0-9)
    if not caracteres[:12].isalnum():
        return False
    if not caracteres[12:].isdigit():
        return False

    # 1. Cálculo do primeiro dígito verificador (DV1)
    valores_12 = [_valor_caractere_cnpj(c) for c in caracteres[:12]]
    soma1 = sum(val * peso for val, peso in zip(valores_12, _PESOS_DV1))
    resto1 = soma1 % 11
    dv1 = 0 if resto1 < 2 else 11 - resto1

    if int(caracteres[12]) != dv1:
        return False

    # 2. Cálculo do segundo dígito verificador (DV2)
    valores_13 = valores_12 + [dv1]
    soma2 = sum(val * peso for val, peso in zip(valores_13, _PESOS_DV2))
    resto2 = soma2 % 11
    dv2 = 0 if resto2 < 2 else 11 - resto2

    if int(caracteres[13]) != dv2:
        return False

    return True


def formatar_cnpj(cnpj_str: str) -> str:
    """Formata um CNPJ para o padrão XX.XXX.XXX/XXXX-XX.

    Raises:
        CnpjInvalidoError: se o CNPJ não contiver 14 caracteres ou for matematicamente inválido.
    """
    caracteres = limpar_cnpj(cnpj_str)

    if len(caracteres) != 14:
        raise CnpjInvalidoError(
            f"CNPJ deve conter exatamente 14 caracteres, mas foram informados {len(caracteres)}."
        )

    if not validar_cnpj(caracteres):
        raise CnpjInvalidoError(
            f"CNPJ {caracteres[:2]}.{caracteres[2:5]}.{caracteres[5:8]}/{caracteres[8:12]}-{caracteres[12:]} é matematicamente inválido."
        )

    return f"{caracteres[:2]}.{caracteres[2:5]}.{caracteres[5:8]}/{caracteres[8:12]}-{caracteres[12:]}"
