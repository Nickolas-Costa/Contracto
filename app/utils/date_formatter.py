"""
Utilitário responsável exclusivamente pela validação e transformação de
datas digitadas no formato brasileiro DD/MM/AAAA.

Usado principalmente para a Declaração PPE, cuja data deve ser separada em
DIA / MÊS (por extenso, em português) / ANO.
"""

from datetime import datetime

FORMATO_ENTRADA = "%d/%m/%Y"

MESES_POR_EXTENSO = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}


class DataInvalidaError(ValueError):
    """Levantada quando uma string de data não está no formato DD/MM/AAAA
    ou não representa uma data real (ex.: 31/02/2026)."""


def validar_data(data_str: str) -> bool:
    """Retorna True se `data_str` está no formato DD/MM/AAAA e é uma data válida."""
    if not data_str:
        return False
    try:
        datetime.strptime(data_str.strip(), FORMATO_ENTRADA)
        return True
    except ValueError:
        return False


def separar_data_por_extenso(data_str: str) -> tuple[str, str, str]:
    """
    Recebe uma data no formato DD/MM/AAAA e retorna uma tupla (dia, mes, ano),
    onde o mês é o nome por extenso em português, com a primeira letra maiúscula.

    Exemplos:
        separar_data_por_extenso("15/07/2026") -> ("15", "Julho", "2026")
        separar_data_por_extenso("01/01/2026") -> ("01", "Janeiro", "2026")
        separar_data_por_extenso("22/08/2027") -> ("22", "Agosto", "2027")
        separar_data_por_extenso("05/11/2028") -> ("05", "Novembro", "2028")

    Levanta DataInvalidaError se a data não estiver no formato correto.
    """
    if not data_str or not data_str.strip():
        raise DataInvalidaError("Data não informada.")

    try:
        data = datetime.strptime(data_str.strip(), FORMATO_ENTRADA)
    except ValueError as exc:
        raise DataInvalidaError(
            f"Data inválida: '{data_str}'. Utilize o formato DD/MM/AAAA."
        ) from exc

    dia = f"{data.day:02d}"
    mes = MESES_POR_EXTENSO[data.month]
    ano = str(data.year)
    return dia, mes, ano
