"""Validação e formatação de PIS/PASEP (11 dígitos)."""


def limpar_pis_pasep(valor: str) -> str:
    return "".join(ch for ch in str(valor or "") if ch.isdigit())


def formatar_pis_pasep(valor: str) -> str:
    digitos = limpar_pis_pasep(valor)[:11]
    if len(digitos) <= 3:
        return digitos
    if len(digitos) <= 8:
        return f"{digitos[:3]}.{digitos[3:]}"
    if len(digitos) <= 10:
        return f"{digitos[:3]}.{digitos[3:8]}.{digitos[8:]}"
    return f"{digitos[:3]}.{digitos[3:8]}.{digitos[8:10]}-{digitos[10]}"


def validar_pis_pasep(valor: str) -> bool:
    digitos = limpar_pis_pasep(valor)
    if len(digitos) != 11 or len(set(digitos)) == 1:
        return False
    pesos = (3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
    soma = sum(int(numero) * peso for numero, peso in zip(digitos[:10], pesos))
    resto = soma % 11
    verificador = 0 if resto < 2 else 11 - resto
    return int(digitos[-1]) == verificador
