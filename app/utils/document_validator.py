"""
Validador e formatador universal de documentos (CPF, CNPJ e CPF/CNPJ híbrido) e datas.
Inclui auto-máscaras progressivas que preenchem pontos, barras e traços em tempo real.
"""

import re
from utils.cpf_validator import validar_cpf, formatar_cpf
from utils.cnpj_validator import validar_cnpj, formatar_cnpj


def limpar_documento(valor: str) -> str:
    """Remove pontuação e caracteres de formatação mantendo apenas caracteres alfanuméricos."""
    if not valor:
        return ""
    return re.sub(r"[^A-Za-z0-9]", "", valor).strip().upper()


def limpar_apenas_digitos(valor: str) -> str:
    """Remove tudo que não for dígito numérico."""
    if not valor:
        return ""
    return re.sub(r"\D", "", valor).strip()


def formatar_cpf_progressivo(valor: str) -> str:
    """Aplica a máscara de CPF em tempo real conforme o usuário digita."""
    digitos = limpar_apenas_digitos(valor)[:11]
    tam = len(digitos)
    if tam <= 3:
        return digitos
    elif tam <= 6:
        return f"{digitos[:3]}.{digitos[3:]}"
    elif tam <= 9:
        return f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:]}"
    else:
        return f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}"


def formatar_cnpj_progressivo(valor: str) -> str:
    """Aplica a máscara de CNPJ numérico ou alfanumérico em tempo real."""
    limpo = limpar_documento(valor)[:14]
    tam = len(limpo)
    if tam <= 2:
        return limpo
    elif tam <= 5:
        return f"{limpo[:2]}.{limpo[2:]}"
    elif tam <= 8:
        return f"{limpo[:2]}.{limpo[2:5]}.{limpo[5:]}"
    elif tam <= 12:
        return f"{limpo[:2]}.{limpo[2:5]}.{limpo[5:8]}/{limpo[8:]}"
    else:
        return f"{limpo[:2]}.{limpo[2:5]}.{limpo[5:8]}/{limpo[8:12]}-{limpo[12:]}"


def formatar_cpf_ou_cnpj_progressivo(valor: str) -> str:
    """Formata dinamicamente como CPF (<= 11 caracteres) ou CNPJ (> 11 caracteres)."""
    limpo = limpar_documento(valor)[:14]
    if len(limpo) > 11:
        return formatar_cnpj_progressivo(limpo)
    else:
        # Se contiver apenas dígitos e até 11, formata como CPF
        return formatar_cpf_progressivo(limpo)


def formatar_data_progressiva(valor: str) -> str:
    """Aplica a máscara de Data (DD/MM/AAAA) em tempo real conforme a digitação."""
    digitos = limpar_apenas_digitos(valor)[:8]
    tam = len(digitos)
    if tam <= 2:
        return digitos
    elif tam <= 4:
        return f"{digitos[:2]}/{digitos[2:]}"
    else:
        return f"{digitos[:2]}/{digitos[2:4]}/{digitos[4:]}"


def validar_cpf_ou_cnpj(valor: str) -> tuple[bool, str]:
    """
    Valida um documento que pode ser CPF ou CNPJ (tradicional ou alfanumérico).
    Retorna (valido: bool, msg_erro: str).
    """
    if not valor or not valor.strip():
        return False, "Documento não informado."

    limpo = limpar_documento(valor)
    if len(limpo) == 11:
        # Tentar validar como CPF
        if not limpo.isdigit():
            return False, "CPF deve conter apenas dígitos numéricos."
        valido = validar_cpf(limpo)
        if valido:
            return True, ""
        return False, "CPF inválido. Verifique os dígitos informados."
    elif len(limpo) == 14:
        # Tentar validar como CNPJ
        valido = validar_cnpj(limpo)
        if valido:
            return True, ""
        return False, "CNPJ inválido. Verifique os dígitos informados."
    else:
        return False, f"Documento inválido: esperado 11 dígitos (CPF) ou 14 dígitos (CNPJ). Informado: {len(limpo)} caracteres."
