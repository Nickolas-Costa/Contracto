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


def formatar_moeda_progressiva(valor: str) -> str:
    """
    Aplica a máscara monetária brasileira progressiva conforme a digitação dos números.
    Exemplos:
      '5' -> '0,05'
      '50' -> '0,50'
      '50000' -> '500,00'
      '5000000' -> '50.000,00'
      '18000000' -> '180.000,00'
    """
    digitos = re.sub(r"\D", "", valor or "").lstrip("0")
    if not digitos:
        return ""
    if len(digitos) == 1:
        return f"0,0{digitos}"
    elif len(digitos) == 2:
        return f"0,{digitos}"
    else:
        inteiro = digitos[:-2]
        centavos = digitos[-2:]
        inteiro_fmt = f"{int(inteiro):,}".replace(",", ".")
        return f"{inteiro_fmt},{centavos}"


def formatar_area_progressiva(valor: str) -> str:
    """Formata progressivamente uma área em m² com casas decimais (ex: 200,00 ou 1.250,50).
    
    Exemplos:
    - "2" -> "0,02"
    - "20" -> "0,20"
    - "200" -> "2,00"
    - "20000" -> "200,00"
    - "6550" -> "65,50"
    - "125000" -> "1.250,00"
    """
    if not valor:
        return ""
    digitos = re.sub(r"\D", "", valor)
    if not digitos:
        return ""
    digitos = digitos.lstrip("0")
    if not digitos:
        return ""
    if len(digitos) == 1:
        return f"0,0{digitos}"
    elif len(digitos) == 2:
        return f"0,{digitos}"
    else:
        inteiro = digitos[:-2]
        centavos = digitos[-2:]
        inteiro_fmt = f"{int(inteiro):,}".replace(",", ".")
        return f"{inteiro_fmt},{centavos}"


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


def formatar_telefone_progressivo(valor: str) -> str:
    """Formata progressivamente um número de telefone à medida que o usuário digita.
    
    Exemplos:
    - "88" -> "(88"
    - "889" -> "(88) 9"
    - "889999" -> "(88) 9999"
    - "8836211234" -> "(88) 3621-1234" (Fixo: 10 dígitos)
    - "88999999999" -> "(88) 99999-9999" (Celular: 11 dígitos)
    """
    if not valor:
        return ""
    digitos = re.sub(r"\D", "", valor)[:11]
    n = len(digitos)
    if n == 0:
        return ""
    if n <= 2:
        return f"({digitos}"
    if n <= 6:
        return f"({digitos[:2]}) {digitos[2:]}"
    if n <= 10:
        return f"({digitos[:2]}) {digitos[2:6]}-{digitos[6:]}"
    return f"({digitos[:2]}) {digitos[2:7]}-{digitos[7:]}"


def validar_telefone(valor: str) -> bool:
    """Valida se o telefone possui 10 dígitos (fixo) ou 11 dígitos (celular)."""
    if not valor or not valor.strip():
        return True
    digitos = re.sub(r"\D", "", valor)
    return len(digitos) in (10, 11)


def validar_email(valor: str) -> bool:
    """Valida se o endereço de e-mail possui formato sintático válido."""
    if not valor or not valor.strip():
        return True
    padrao = r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(padrao, valor.strip()))
