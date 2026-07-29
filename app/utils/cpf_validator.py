"""
Utilitário responsável exclusivamente pela validação e formatação de CPF.

O CPF (Cadastro de Pessoa Física) possui 11 dígitos, onde os dois últimos
são dígitos verificadores calculados a partir dos nove primeiros.
"""


class CpfInvalidoError(ValueError):
    """Levantada quando um CPF é inválido."""


def limpar_cpf(cpf_str: str) -> str:
    """Remove pontos, traços e outros caracteres não numéricos."""
    return ''.join(c for c in cpf_str if c.isdigit())


def validar_cpf(cpf_str: str) -> bool:
    """Valida um CPF matematicamente (verifica os dois dígitos verificadores).

    Aceita CPF com ou sem formatação (pontos e traço).
    Retorna True se válido, False se inválido.
    """
    digitos = limpar_cpf(cpf_str)

    if len(digitos) != 11:
        return False

    # CPFs com todos os dígitos iguais são considerados inválidos
    if len(set(digitos)) == 1:
        return False

    # Validação do primeiro dígito verificador
    soma = sum(int(digitos[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    if int(digitos[9]) != digito1:
        return False

    # Validação do segundo dígito verificador
    soma = sum(int(digitos[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    if int(digitos[10]) != digito2:
        return False

    return True


def formatar_cpf(cpf_str: str) -> str:
    """Formata um CPF para o padrão NNN.NNN.NNN-NN.

    Raises:
        CpfInvalidoError: se o CPF não contiver exatamente 11 dígitos
                          ou se os dígitos verificadores forem inválidos.
    """
    digitos = limpar_cpf(cpf_str)

    if len(digitos) != 11:
        raise CpfInvalidoError(
            f"CPF deve conter exatamente 11 dígitos, mas foram informados {len(digitos)}."
        )

    if not validar_cpf(digitos):
        raise CpfInvalidoError(
            f"CPF {digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]} é matematicamente inválido."
        )

    return f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}"
